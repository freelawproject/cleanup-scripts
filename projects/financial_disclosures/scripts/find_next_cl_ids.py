#!/usr/bin/env python3
import argparse

import requests
import settings


def get_cl_ids():
    """

    :return:
    """
    headers = {
        "Authorization": "Token %s" % settings.CL_API_TOKEN,
    }
    params = (("order_by", "-date_created"),)
    s = requests.session()
    s.headers = headers
    url = "https://www.courtlistener.com/api/rest/v3/people/?format=json&court__jurisdiction=F"
    data = s.get(url, params=params).json()
    cl_ids = [x["cl_id"] for x in data["results"]]
    cd = {}
    for cl_id in cl_ids:
        parts = cl_id.rsplit("-", 1)
        if parts[0] in cd.keys():
            if int(cd[parts[0]]) >= int(parts[1]):
                continue
        cd[parts[0]] = parts[1]
        print(parts)
    while data["next"]:
        cl_ids = [x["cl_id"] for x in data["results"]]
        for cl_id in cl_ids:
            parts = cl_id.rsplit("-", 1)
            if parts[0] in cd.keys():
                if int(cd[parts[0]]) >= int(parts[1]):
                    continue
            cd[parts[0]] = parts[1]
            print(parts)
        data = requests.get(data["next"], headers=headers).json()

#     ['jud', '3695']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    VALID_ACTIONS = {
        "cl-ids": get_cl_ids,
    }
    parser.add_argument("command", choices=VALID_ACTIONS.keys())
    args = parser.parse_args()
    VALID_ACTIONS[args.command]()

# j1-38
