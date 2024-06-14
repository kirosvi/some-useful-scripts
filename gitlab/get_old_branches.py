#!/usr/bin/env python3
import requests
import json
import datetime as dt

project_id = "18"
gitlab_url = "https://gitlab.example.com"
access_token = os.environ['CI_JOB_TOKEN']
saved_branches = ("analytics-demo", "master")

date_N_days_ago = dt.datetime.now() - dt.timedelta(days = 90)

all_branches = []
branches_2_purge = {}
branches_delete = []

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
  date_time_obj = dt.datetime.strptime(date_time_string, '%Y-%m-%dT%H:%M:%S.%f')
  return date_time_obj;


for page in range(20):
    print("Getting jobs from page {}".format(page+1))
    get_all_branches = request_get_url('/api/v4/projects/'+str(project_id)+'/repository/branches?per_page=100&page='+str(page))
    all_branches += get_all_branches

#print(all_branches)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(all_branches, f, ensure_ascii=False, indent=4)


with open('data.json') as data_file:
    data_loaded = json.load(data_file)


#print(data_loaded)
#
for branch in data_loaded:
    branches_2_purge[branch["name"]]=branch["commit"]["created_at"]

print(len(branches_2_purge))
#print(branches_2_purge)


for branch in branches_2_purge:
  if branch not in saved_branches:
    if get_date_from_iso8601(branches_2_purge[branch][:-6]) < date_N_days_ago:
      branches_delete.append(branch)



print(branches_delete)
print(len(branches_delete))
