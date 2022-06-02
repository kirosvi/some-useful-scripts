#!/usr/bin/env python3
"""
BEFORE RUNNING:
---------------
1. If not already done, enable the Compute Engine API
   and check the quota for your project at
   https://console.developers.google.com/apis/api/compute
2. This sample uses Application Default Credentials for authentication.
   If not already done, install the gcloud CLI from
   https://cloud.google.com/sdk and run
   `gcloud beta auth application-default login`.
   For more information, see
   https://developers.google.com/identity/protocols/application-default-credentials
3. Install the Python client library for Google APIs by running
   `pip install --upgrade google-api-python-client`
"""
from pprint import pprint

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import copy

credentials = GoogleCredentials.get_application_default()

service = discovery.build("compute", "v1", credentials=credentials)

project = "pimpay-cloud"

zone = "europe-west1-b"

team_list = ("core", "tracking", "metaship", "rnd")

resources_without_labels = {"disks": {}, "snapshots": {}, "instances": {}}

unknown_resources = copy.deepcopy(resources_without_labels)

filter = "NOT (labels.team:*)"


def exec_request_set_label(item, object_type, team_name, labelFingerprint):
    set_labels_request_body = {"labels": {}, "labelFingerprint": ""}
    set_labels_request_body["labels"]["team"] = team_name
    set_labels_request_body["labelFingerprint"] = labelFingerprint

    if object_type == "disks":
        request = service.disks().setLabels(
            project=project, zone=zone, resource=item, body=set_labels_request_body
        )
    elif object_type == "snapshots":
        request = service.snapshots().setLabels(
            project=project, resource=item, body=set_labels_request_body
        )
    elif object_type == "instances":
        request = service.instances().setLabels(
            project=project, zone=zone, instance=item, body=set_labels_request_body
        )
    response = request.execute()
    pprint(response)


def exec_request(request, object_type):
    item_list = {}
    for team_name in team_list:
        item_list[team_name] = {}
    unknown_item_list = copy.deepcopy(item_list)
    while request is not None:
        response = request.execute()

        if "items" in response:
            for item in response["items"]:
                item_name = item["name"]
                item_label_fingreprint = item["labelFingerprint"]
                item_updated = False

                for team in team_list:
                    if team == "core" :
                        team_name = "pimpay"
                    else:
                        team_name = team

                    if team_name in item_name:
                        item_list[team][item_name] = item_label_fingreprint
                        item_updated = True

                    if object_type == "disks":
                        if "users" in item:
                            item_user = item["users"][0].split("/")[-1]
                            if team_name not in item_name and team_name in item_user:
                                item_list[team][item_name] = item_label_fingreprint
                                item_updated = True
                        else:
                            continue

                    if object_type == "snapshots":
                        if "sourceDisk" in item:
                            item_source_disk = item["sourceDisk"][0].split("/")[-1]
                            if (
                                team_name not in item_name
                                and team_name in item_source_disk
                            ):
                                item_list[team][item_name] = item_label_fingreprint
                                item_updated = True
                        else:
                            continue

                if item_updated is False:
                    unknown_resources[object_type][item_name] = item_label_fingreprint

                resources_without_labels[object_type] = item_list

        else:
            print("with {} it's all ok".format(object_type))

        if object_type == "disks":
            request = service.disks().list_next(
                previous_request=request, previous_response=response
            )
        elif object_type == "snapshots":
            request = service.snapshots().list_next(
                previous_request=request, previous_response=response
            )
        elif object_type == "instances":
            request = service.instances().list_next(
                previous_request=request, previous_response=response
            )


def main(request):
    request = service.disks().list(project=project, zone=zone, filter=filter)
    exec_request(request, "disks")

    request = service.snapshots().list(project=project, filter=filter)
    exec_request(request, "snapshots")

    request = service.instances().list(project=project, zone=zone, filter=filter)
    exec_request(request, "instances")

    for object_type in resources_without_labels:
        for team in resources_without_labels[object_type]:
            for item in resources_without_labels[object_type][team]:
                labelFingerprint = resources_without_labels[object_type][team][item]
                exec_request_set_label(item, object_type, team, labelFingerprint)

    for object_type in unknown_resources:
        for item in unknown_resources[object_type]:
            labelFingerprint = unknown_resources[object_type][item]
            team = "infra"
            exec_request_set_label(item, object_type, team, labelFingerprint)

    output = print("resources: {}. unknown resources: {}".format(resources_without_labels, unknown_resources))
    print(output)
    return("OK")

if __name__ == "__main__":
    main("arg_1")
