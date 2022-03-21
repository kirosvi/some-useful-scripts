#!/usr/bin/env python3

import requests
import os
import json
import argparse
import datetime as dt

gitlab_url = "https://gitlab.example.com"
access_token = os.environ['CI_JOB_TOKEN']
all_projects = []
registry_cleanup_schedule = {'description':'Registry cleanup','ref':'master','cron':'12 4 * * *','cron_timezone':'UTC','active':'true'}

def request_get_url ( uri ):
  "This create get request and return json"
  try:
    get_request = requests.get(gitlab_url+uri, headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
    get_request.raise_for_status()
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

  raw_json_data = get_request.json()
  jtopy=json.dumps(raw_json_data)
  json_data =json.loads(jtopy)
  return json_data;

def request_post_url ( uri, params):
  "This create get request and return json"
  try:
    get_request = requests.post(gitlab_url+uri, params=params, headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
    get_request.raise_for_status()
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

  raw_json_data = get_request.json()
  jtopy=json.dumps(raw_json_data)
  json_data =json.loads(jtopy)
  return json_data;

for page in range(10):
    get_all_projects = request_get_url('/api/v4/projects?per_page=100&page='+str(page))
    all_projects += get_all_projects

for project in all_projects:
  project_info = request_get_url('/api/v4/projects/'+str(project["id"]))
  if 'owner' not in project_info:
    if project_info["archived"] is False :
      get_schedules = request_get_url('/api/v4/projects/'+str(project["id"])+'/pipeline_schedules')
      all_schedules = []
      for schedule in get_schedules:
        all_schedules.append(schedule["description"])
      if "Registry cleanup" in all_schedules:
        print(project["path_with_namespace"]+" schedule already exist")
      else:
        print(project["path_with_namespace"]+" schedule not exist, creating...")
        create_schedule = request_post_url('/api/v4/projects/'+str(project["id"])+'/pipeline_schedules', registry_cleanup_schedule)
