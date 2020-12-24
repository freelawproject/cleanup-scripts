"""
This page is meant to be run in conjunction with a running developer
environment for courtlistener.com.  It is not meant to be perfect or to make
exact replicas of the data but to be a quick and dirty way to get data into
our systems and for testing and review purposes.
"""

import requests
from cl.lib.command_utils import VerboseCommand, logger
from cl.search.models import Opinion, OpinionCluster, Docket, Citation, Court
from cl.search.tasks import add_items_to_solr
from django.conf import settings
from django.db import transaction
import time

cluster_url = "https://www.courtlistener.com/api/rest/v3/search/?format=json"
search_url = "https://www.courtlistener.com/api/rest/v3/search/?format=json"


def get_cluster_ids(volume: str, reporter: str, page: str) -> None:
    """Get Cluster IDs

    :param volume: Citation Volume
    :param reporter: Citation Reporter
    :param page: Citation Page
    :return: None
    """
    headers = {
        "Authorization": "Token %s" % settings.CL_API_TOKEN,
    }
    params = (("citation", '"%s %s %s"' % (volume, reporter, page)),)
    s = requests.session()
    s.headers = headers
    data = s.get(cluster_url, params=params).json()
    cluster_ids = [x["cluster_id"] for x in data["results"]]

    for cluster_id in cluster_ids:
        if not OpinionCluster.objects.filter(pk=cluster_id).exists():
            get_courtlistener_data(cluster_id)

    while data["next"]:
        data = requests.get(data["next"], headers=headers).json()
        cluster_ids = [x["cluster_id"] for x in data["results"]]
        for cluster_id in cluster_ids:
            if not OpinionCluster.objects.filter(pk=cluster_id).exists():
                get_courtlistener_data(cluster_id)


def get_court_ids(court_id: str):
    """

    :param court_id:
    :return:
    """
    headers = {
        "Authorization": "Token %s" % settings.CL_API_TOKEN,
    }
    params = (
        ("court", court_id),
        ("stat_Unknown Status", "on"),
        ("stat_Precedential", "on"),
        ("stat_Non-Precedential", "on"),
    )
    s = requests.session()
    s.headers = headers
    data = s.get(search_url, params=params).json()
    if "detail" in data.keys():

        print("Sleeping for %s seconds" % data["detail"].split(" ")[6])
        time.sleep(float(data["detail"].split(" ")[6]))
        data = s.get(search_url, params=params).json()

    while data["next"]:
        cluster_ids = [x["cluster_id"] for x in data["results"]]
        for cluster_id in cluster_ids:
            if not OpinionCluster.objects.filter(pk=cluster_id).exists():
                get_courtlistener_data(cluster_id)

        data = requests.get(data["next"], headers=headers).json()
        if "detail" in data.keys():

            print("Sleeping for %s seconds" % data["detail"].split(" ")[6])
            time.sleep(float(data["detail"].split(" ")[6]))
            data = s.get(search_url, params=params).json()


def get_courtlistener_data(cluster_id: int) -> None:
    """Download data from courtlistener.com and add to local version

    This method takes a cluster id and grabs related docket and opinions
     and save it to developer courtlsitener

    :param cluster_id:
    :return: Nothing
    """
    params = (("id", cluster_id),)
    s = requests.session()
    s.headers = {"Authorization": "Token %s" % settings.CL_API_TOKEN}
    results = s.get(cluster_url, params=params).json()
    if "count" in results.keys():
        if results["count"] == 0:
            print("Cluster ID doesnt exist")
            return
    else:
        return
    cluster_datum = results["results"][0]
    docket_datum = s.get(cluster_datum["docket"]).json()
    court_datum = s.get(docket_datum["court"]).json()
    citation_data = cluster_datum["citations"]
    opinion_data = cluster_datum["sub_opinions"]
    del court_datum["resource_uri"]
    del docket_datum["clusters"]
    del docket_datum["resource_uri"]
    del docket_datum["original_court_info"]
    del docket_datum["absolute_url"]
    del cluster_datum["resource_uri"]
    del cluster_datum["docket"]
    del cluster_datum["citations"]
    del cluster_datum["sub_opinions"]
    del cluster_datum["absolute_url"]
    with transaction.atomic():
        try:
            ct = Court.objects.get_or_create(**court_datum)
        except:
            ct = Court.objects.filter(pk=court_datum["id"])
        docket_datum["court"] = ct[0]
        Docket.objects.create(**docket_datum)
        for cite_data in citation_data:
            cite_data["cluster_id"] = cluster_datum["id"]
        cluster_datum["docket_id"] = docket_datum["id"]
        OpinionCluster.objects.create(**cluster_datum)
        for cite_data in citation_data:
            cite_data["cluster_id"] = cluster_datum["id"]
            Citation.objects.create(**cite_data)
        for op in opinion_data:
            op_data = s.get(op).json()
            del op_data["opinions_cited"]
            del op_data["cluster"]
            del op_data["absolute_url"]
            del op_data["resource_uri"]
            del op_data["author"]
            op_data["cluster_id"] = cluster_datum["id"]
            op = Opinion.objects.create(**op_data)
            add_items_to_solr.delay(op.id, "search.Opinion")

        print(f"http://localhost:8000/opinion/{cluster_datum['id']}/go/")


class Command(VerboseCommand):
    help = "A helper function to collect and download opinions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cluster",
            help="Cluster id, "
            "code will cycle through all volumes of reporter on IA.",
        )
        parser.add_argument(
            "--reporter",
            help="Cluster id, "
            "code will cycle through all volumes of reporter on IA.",
        )
        parser.add_argument(
            "--volume",
            help="Volume, "
            "code will cycle through all volumes of reporter on IA.",
        )
        parser.add_argument("--page", help="Page", default="")
        parser.add_argument(
            "--court",
            help="The court identifier to download opinions by court id",
        )

    def handle(self, *args, **options):
        cluster_id = options["cluster"]
        if cluster_id:
            get_courtlistener_data(cluster_id)
        volume = options["volume"]
        reporter = options["reporter"]
        page = options["page"]
        court = options["court"]
        if volume and reporter:
            get_cluster_ids(volume, reporter, page)
        if court:
            get_court_ids(court)
