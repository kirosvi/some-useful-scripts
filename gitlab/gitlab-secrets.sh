#!/bin/bash -e

GITLAB_URL="https://gitlab."
GROU=mple.com$1

if [ -z "${CI_JOB_TOKEN}" ]; then
    echo "ERROR: please export our gitlab CI_JOB_TOKEN before start me"
    exit 1
fi

TOP=$(git rev-parse --show-toplevel)
PROJECT_NAME=${TOP##*/}

if [ -z "${GROUP}" ]; then
    PROJECT=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -H 'Content-Type: application/json' -L "${GITLAB_URL}/api/v4/search?scope=projects&search=${PROJECT_NAME}")
    PROJECT_ID=$(echo ${PROJECT} | jq '.[] | .id')
    if [ -z "${PROJECT_ID}" ]; then
        echo "Error: project '${PROJECT_NAME}' not found"
        exit 2
    fi
else
    PROJECT=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -H 'Content-Type: application/json' -L "${GITLAB_URL}/api/v4/projects/${GROUP}%2F${PROJECT_NAME}")
    RET=$(echo "${PROJECT}" | ( grep -i 'not found' || true ))
    if [ ! -z "$RET" ]; then
        echo "Project: ${GROUP}/${PROJECT_NAME} not found"
        exit 3
    fi
    PROJECT_ID=$(echo ${PROJECT} | jq '.id')
fi

if [[ ${PROJECT_ID} != +([0-9]) ]]; then
    echo "Error: multiple matches found. Use: $0 GITLAB_PROJECT_GROUP"
    exit 4
fi

curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/$PROJECT_ID/variables" |
    jq '.[] | "export \(.key)=\(.value)"' | sed 's/"//g'

