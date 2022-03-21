#!/usr/bin/env python3

import requests
import os
import json
import argparse
import datetime as dt

parser = argparse.ArgumentParser(description='script')
parser.add_argument('-p','--project',
                    required=True,
                    help='a project in gitlab')
parser.add_argument('-g','--group',
                    required=True,
                    help='a group in gitlab')

args = parser.parse_args()

if args.project:
  project_name = args.project
  print(args.project)
if args.group:
  project_group = args.group
  print(args.group)

gitlab_url = "https://gitlab.example.com"
access_token = os.environ['CI_JOB_TOKEN']
all_environments = []
all_stopped_environments = []
delete_list = []
date_N_days_ago = dt.datetime.now() - dt.timedelta(days = 10)

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

def get_date_from_iso8601 ( date_time_string ):
  date_time_obj = dt.datetime.strptime(date_time_string, '%Y-%m-%dT%H:%M:%S.%fZ')
  return date_time_obj;

get_project_info = request_get_url('/api/v4/projects/'+str(project_group)+'%2F'+str(project_name))
project_id = get_project_info["id"]
print(project_id)

for page in range(10):
    get_all_environments = request_get_url('/api/v4/projects/'+str(project_id)+'/environments?per_page=100&page='+str(page))
    all_environments += get_all_environments

for environment in all_environments:
  request_environment_status = request_get_url('/api/v4/projects/'+str(project_id)+'/environments/'+str(environment["id"]))
  env_status = request_environment_status
  if env_status["last_deployment"] is None:
    delete_list.append(env_status["id"])
    print(env_status["name"]+" has none last update")
  elif env_status["last_deployment"]:
    if get_date_from_iso8601(env_status["last_deployment"]["updated_at"]) < date_N_days_ago:
      delete_list.append(env_status["id"])
      print(env_status["name"]+" last updated at "+env_status["last_deployment"]["updated_at"])

for id_environment in delete_list:
  print("stop environment id:"+str(id_environment))
  try:
    delete_environment = requests.post(gitlab_url+'/api/v4/projects/'+str(project_id)+'/environments/'+str(id_environment)+"/stop", headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
    delete_environment.raise_for_status()
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)


for page in range(10):
  get_all_stopped_environments = request_get_url('/api/v4/projects/'+str(project_id)+'/environments?states=stopped&per_page=100&page='+str(page))
  all_stopped_environments += get_all_stopped_environments

for stopped_environment in all_stopped_environments:
  print(stopped_environment["id"])
  try:
    delete_environment = requests.delete(gitlab_url+'/api/v4/projects/'+str(project_id)+'/environments/'+str(stopped_environment["id"]), headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

