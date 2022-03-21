#!/usr/bin/env python3

import requests
import os
import json

gitlab_url = "https://gitlab.example.com"
access_token = os.environ['CI_JOB_TOKEN']
response = []
delete_response = []
delete_list = []

for i in range(8):
  r = requests.get(gitlab_url+'/api/v4/runners/all?status=offline&per_page=100&page='+str(i), headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
  response += r.json()

raw_json_data = response
jtopy=json.dumps(raw_json_data)
json_data =json.loads(jtopy)

for i in json_data:
  if i["status"] == "offline" and i["online"] == False :
    delete_list.append(i["id"])

for i in delete_list:
  print("deleting runner id:"+str(i))
  delete = requests.delete(gitlab_url+'/api/v4/runners/'+str(i), headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
  delete_response += delete.text
