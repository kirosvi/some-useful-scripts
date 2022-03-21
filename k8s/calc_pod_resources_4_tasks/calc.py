#!/usr/bin/env python3

# example curl request
# curl -s -X POST "http://prometheus.monitoring.project.example.com/api/v1/query" -d query='max(max_over_time(rate(container_cpu_usage_seconds_total{namespace="project-master",pod=~"task-command-russian-.*"}[5m]) [2w:5m]))'| jq '.data.result[].value[1]'
# curl -s -X POST "http://prometheus.monitoring.project.example.com/api/v1/query" -d query='max(max_over_time(container_memory_max_usage_bytes{namespace="project-master",pod=~"task-command-russian-.*"} [2w:5m])) /(1024* 1024)'| jq '.data.result[].value[1]'

import requests
import os
import sys
import json
import jinja2
import yaml
from argparse import ArgumentParser
from collections import OrderedDict

parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="filename",
                    help="read data from FILE", metavar="FILE")
parser.add_argument("-t", "--type", dest="type_of_objects", required=True,
                    help="type of objects to create resources file (cronjob/cj or task/pod)", metavar="TYPE_OF_OBJECTS")
parser.add_argument("-o", "--output-file", dest="output_file_path",
                    help="path to output file (if not defined file will be saved in local dir of running script {./task_resources.yaml|cronjob_resources.yaml})", metavar="OUTPUT_FILE_PATH")
args = parser.parse_args()

if not args.type_of_objects :
    parser.print_help()
    sys.exit(1)

config_file = args.filename

if args.output_file_path :
    output_file_path = args.output_file_path

if args.type_of_objects in ["cj", "cronjob"] :
    config_type = "cronjob_type"
    if args.output_file_path is None:
        output_file_path = "cronjob_resources.yaml"
elif args.type_of_objects in ["task", "pod"] :
    config_type = "pod_type"
    if args.output_file_path is None:
        output_file_path = "task_resources.yaml"

prom_request_url = "http://prometheus.monitoring.project.example.com/api/v1/query"

def read_file(file_path: str):
    with open(file_path, "r") as stream:
        try:
            data_from_file = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return data_from_file

def write_file(data, name):
    with open(name, "w") as open_file:
        open_file.write(data)

def get_response(query,query_type):
    try:
        r = requests.get(prom_request_url, params=query)
    except requests.exceptions.HTTPError as e:
        print(e.response.text, file=stderr)

    data = r.json()
    if query_type == "pod_resources":
        if len(data["data"]["result"]) != 0:
            value = data["data"]["result"][0]["value"][1]
        else:
            value = 0

    if query_type == "get_pod_list":
        value = data["data"]["result"]

    return value

def get_tasks_pod_query():
    ## Do not take data earlier 15/01/21 it wouldn't work!
    query_str = 'sum_over_time(kube_pod_info{namespace="project-master",pod=~"task-command-.*"}[14d:])'
    query = { "query" : query_str }
    return query

def get_cpu_query(pod):
    query_str = 'max(max_over_time(rate(container_cpu_usage_seconds_total{{namespace="project-master",pod=~"{}-.*"}}[5m]) [20d:5m]))'.format(pod)
    query = { "query" : query_str }
    return query

def get_mem_query(pod):
    query_str = 'max(max_over_time(container_memory_max_usage_bytes{{namespace="project-master",pod=~"{}-.*"}} [20d:5m])) /(1024* 1024)'.format(pod)
    query = { "query" : query_str }
    return query

def make_pod_list(data):
    pod_list = []
    if config_type == "cronjob_type":
        for pod in data:
            pod_list.append(pod["name"])
    pod_list.sort()
    return pod_list

def make_pod_tasks_list():
    tasks_pods = {}
    raw_data = get_response(get_tasks_pod_query(),"get_pod_list")

    for i in raw_data:
        pod = i["metric"]["pod"]
        splited_pods = pod.split("-")
        if splited_pods[2] == "manual":
            pass
        else:
            if splited_pods[2] in tasks_pods :
                pass
            else:
                tasks_pods[splited_pods[2]] = []

            if splited_pods[3] in tasks_pods[splited_pods[2]]:
                pass
            else:
                tasks_pods[splited_pods[2]].append(splited_pods[3])
    sort_dict = OrderedDict(sorted(tasks_pods.items(), key=lambda t: t[0]))
    for key in sort_dict:
        sort_dict[key].sort()

    return sort_dict

def make_default_resources(value):
    if value == 0:
        value = 10
    return value

def get_pod_resources(pod):
    pod_resources = {}
    request_cpu = str(make_default_resources(int(round((float(get_response(get_cpu_query(pod.lower()),"pod_resources"))*1000), 0))))
    request_mem = str(make_default_resources(int(round(float(get_response(get_mem_query(pod.lower()),"pod_resources")), 0))))
    pod_resources =  {'cpu': "{}m".format(request_cpu), 'memory': "{}Mi".format(request_mem)}
    return pod_resources

def create_resources_config(data, file):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = file
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(data=data)
    return outputText

if __name__ == '__main__':
    pod_resources  = {}
    if config_type == "cronjob_type" :
        cronjobs = read_file(config_file)
        pods_list = make_pod_list(cronjobs['cronjobs']['tasks'])
        for pod in pods_list:
            pod_resources[pod] = get_pod_resources(pod)
        resources_file = create_resources_config(data=pod_resources, file="resources-cronjob.j2")
    if config_type == "pod_type" :
        tasks = make_pod_tasks_list()
        for task_class in tasks:
            method_resources = {}
            for task_method in tasks[task_class]:
                pod_res = get_pod_resources("task-command-{}-{}".format(task_class,task_method))
                method_resources[task_method] = pod_res

            pod_resources[task_class] = method_resources
        resources_file = create_resources_config(data=pod_resources, file="resources-tasks.j2")
    write_file(resources_file, output_file_path)
