#!/usr/bin/env python3
import requests
import json
import os

project_id = "18"
gitlab_url = "https://gitlab.example.com"
access_token = os.environ['CI_JOB_TOKEN']

all_jobs = []
jobs_2_purge = []

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


for page in range(400):
    page += 400
    print("Getting jobs from page {}".format(page+1))
    get_all_jobs = request_get_url('/api/v4/projects/'+str(project_id)+'/jobs?per_page=100&page='+str(page))
    all_jobs += get_all_jobs

#print(all_jobs)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(all_jobs, f, ensure_ascii=False, indent=4)


with open('data.json') as data_file:
    data_loaded = json.load(data_file)

print(data_loaded)

for job in data_loaded:
    if len(job["artifacts"]) > 0:
        jobs_2_purge.append(job["id"])

print(jobs_2_purge)


for job_id in jobs_2_purge:
  print("deleting artifacts for job id:"+str(job_id))
  try:
    delete_artifacts = requests.delete(gitlab_url+'/api/v4/projects/'+str(project_id)+'/jobs/'+str(job_id)+"/artifacts", headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
    delete_artifacts.raise_for_status()
  except requests.exceptions.HTTPError as err:
    raise SystemExit(err)
