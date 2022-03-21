#!/bin/bash -e

GITLAB_URL="https://gitlab.example.com"
GROUP=$1

TAGS="k8s-builder k8s-rapid k8s-stage"
STATUS="offline"
for t in ${TAGS}; do
  echo $t
  LIST_RUNNERS=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/runners/all?tag_list=${t}&status=${STATUS}&per_page=1000" | jq '.[].id')
  for i in ${LIST_RUNNERS}; do
    set -v
    curl --request DELETE -H "PRIVATE-TOKEN: $CI_JOB_TOKEN" "${GITLAB_URL}/api/v4/runners/$i"
  done
done
