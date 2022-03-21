#!/usr/bin/env python3

import requests
import os
import json

gitlab_url = "https://gitlab.example.com"
access_token = os.environ['CI_JOB_TOKEN']
response = []
delete_response = []
delete_list = []
exclude = ["admin@example.com","kirosroot@gmail.com","igor.kucenko@simbirsoft.com", "ghost@example.com","ataman.andrew87@gmail.com","dubr.cola@gmail.com","artemio.skr@gmail.com"]

for i in range(6):
  r = requests.get(gitlab_url+'/api/v4/users?per_page=100&page='+str(i), headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
  response += r.json()

raw_json_data = response

jtopy=json.dumps(raw_json_data)
json_data =json.loads(jtopy)

for i in json_data:
  if "example.com"  not in (i["email"]):
    if "example.ru"  not in (i["email"]):
      if (i["email"]) not in exclude:
        print(i["id"],"\t",i["name"],"\t", i["email"])
        delete_list.append(i["id"])

for i in delete_list:
  print(i)
  delete = requests.delete(gitlab_url+'/api/v4/users/'+str(i), headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(access_token)})
  delete_response += delete.text
