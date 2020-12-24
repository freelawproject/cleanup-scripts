# We need to format out data into nice neat json for our CL import scripts.
# This script and functions helps generate the data from our AWS bucket into
# the preformatted design.
import argparse
import json
import logging
import os
from urllib.parse import quote

import boto3
from botocore import UNSIGNED
from botocore.client import Config

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
# We use the non-development bucket to test even though we eventually
# test save into development.  This is why we are setting these values instead
# of simply switching the defaults.

AWS_STORAGE_BUCKET_NAME = "com-courtlistener-storage"
AWS_DOMAIN = "https://%s.s3-%s.amazonaws.com" % (
    AWS_STORAGE_BUCKET_NAME,
    "us-west-2",
)

kwargs = {
    "Bucket": AWS_STORAGE_BUCKET_NAME,
    "Prefix": "financial_disclosures",
}

ROOT = os.path.dirname(os.path.abspath(__file__))


def download_urls() -> None:
    """Fetch all files in bucket and write to txt file.

    :return: None
    """
    logging.info("Fetching urls")
    urls = []

    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp["Contents"]:
            aws_file = {}
            aws_file["key"] = obj["Key"]
            aws_file["url"] = f"{AWS_DOMAIN}/{quote(obj['Key'], safe=':/')}"
            urls.append(aws_file)
        try:
            # Add the continuation token to continue iterating
            kwargs["ContinuationToken"] = resp["NextContinuationToken"]
        except KeyError:  # If no continuation token break
            break

    with open(f"{ROOT}/../data/new_grouping.json", "w") as w:
        json.dump(urls, w, indent=2)


def compare_old_and_new_groupings() -> None:
    """Find new disclosures

    Take our first group of pre-formatted files and add them into

    :return: None
    """

    with open(f"{ROOT}/../data/new_grouping.json", "r") as w:
        complete_gp = json.loads(w.read())

    with open(f"{ROOT}/../data/original_grouping.json", "r") as f:
        orginal_gp = json.loads(f.read())

    original_keys = [
        quote(file["url"], safe=":/")
        for file in orginal_gp
        if "url" in file.keys()
    ]

    for key in [file for file in orginal_gp if "urls" in file.keys()]:
        for url in key["urls"]:
            original_keys.append(quote(url, safe=":/"))

    count = 0
    for file in complete_gp:
        if file["url"] not in original_keys and ".tif" in file["url"]:
            count += 1
            print(file["url"])

    print(count)


def identify_judges() -> None:
    """

    :return:
    """
    count = 0
    with open(f"{ROOT}/../data/new_urls.json", "r") as w:
        little_list = json.loads(w.read())

    with open(f"{ROOT}/../data/original_grouping.json", "r") as f:
        big_list = json.loads(f.read())

    for person in little_list:
        hit = False
        judge_name = person['path']
        searching = judge_name[:15].split("2018")[0]
        for judge in big_list:
            if searching in judge.get("url", ""):
                # print (searching, judge['url'].split("/")[-1], judge['person_id'])
                hit = True
                person['person_id'] = judge['person_id']
                break

        if not hit:
            count += 1
            print("FAIL", searching, count)

    with open(f"{ROOT}/../data/new_urls_complete.json", "w") as w:
        json.dump(little_list, w, indent=2)


def fix_duplicates():
    """De dupe the duplicates

    :return:
    """

    with open(f"{ROOT}/../data/new_urls_complete.json", "r") as w:
        complete = json.loads(w.read())

    originals = []
    deduped = []
    for file in complete:
        if file['path'] not in originals:
            originals.append(file['path'])
            deduped.append(file)
        else:
            print("DUPE", file['path'])

    with open(f"{ROOT}/../data/deduped_list.json", "w") as w:
        json.dump(deduped, w, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    VALID_ACTIONS = {
        "download": download_urls,
        "find-new": compare_old_and_new_groupings,
        "id": identify_judges,
        "dedupe": fix_duplicates,
    }
    parser.add_argument("command", choices=VALID_ACTIONS.keys())
    args = parser.parse_args()
    VALID_ACTIONS[args.command]()
