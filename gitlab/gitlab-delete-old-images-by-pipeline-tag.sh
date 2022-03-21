#!/bin/bash -e

# Delete old format images with tag==CI_PIPLINE_ID
# Script delete maximum 100 tags for 1 image name
# Run script in git-repo folder
function echo_help() {
    echo -e "\nUsage for $0:\n
    $0 [ {GITLAB_GROUP} {MAX_PIPELINE_ID} ]

    GITLAB_GROUP..............Gitlab group of project
    MAX_PIPELINE_ID...........Delete images with pipeline_number in tag BEFORE this pipeline number
    \nKeys:
    -h                    Show this help.\n"
}

get_images () {
  for repo in ${REGISTRY_REPOS}; do
    REPO_TAGS=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories/${repo}/tags?per_page=100" | jq '.[].location')
    #echo ${REPO_TAGS}

    for i in ${REPO_TAGS};do
      tag=$(echo ${i} |sed 's/^.*://g;s/"//g')
      #echo ${i}
      if [[ ${tag} =~ ^[0-9]+$ ]];then
        if [[ "${tag}" -lt "${MAX_PIPELINE_ID}" ]]; then
          echo ${i}
          link="${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories/${repo}/tags/${tag}"
          arr+=($link)
        fi
      fi

    done
  done
}

delete_images () {
  for i in ${arr[*]}; do
#    echo ${i}
    DELETE=$(curl -s --request DELETE --header "PRIVATE-TOKEN: ${CI_JOB_TOKEN}" "${i}")
    if [[ ${DELETE} == "200" ]]; then
      echo "Image ${i} was deleted"
    else
      echo "Error code ${DELETE}"
    fi
  done
}

arr=()
GITLAB_URL="https://gitlab.example.com"
GROUP=$1
MAX_PIPELINE_ID=$2

### Get options
while getopts "h" options ;
do
  case $options in
  h)
    echo_help
    exit 0
  ;;
  esac
OPTS="$OPTS$options"
done

if [[ ${MAX_PIPELINE_ID} == '' ]]; then
  MAX_PIPELINE_ID=1000000000
fi

echo "Max Pipeline id: ${MAX_PIPELINE_ID}"

if [ -z "${CI_JOB_TOKEN}" ]; then
    echo "ERROR: please export our gitlab CI_JOB_TOKEN before start me"
    exit 1
fi

TOP=$(git rev-parse --show-toplevel)
PROJECT_NAME=${TOP##*/}

if [ -z "${GROUP}" ]; then
    PROJECT=$(curl -s -H "Private-Token: ${CI_JOB_TOKEN}" -H 'Content-Type: application/json' -L "${GITLAB_URL}/api/v4/search?scope=projects&search=${PROJECT_NAME}")
    PROJECT_ID=$(echo ${PROJECT} | jq '.[] | .id')
    if [ -z "${PROJECT_ID}" ]; then
        echo "Error: project '${PROJECT_NAME}' not found"
        exit 2
    fi
else
    PROJECT=$(curl -s -H "Private-Token: ${CI_JOB_TOKEN}" -H 'Content-Type: application/json' -L "${GITLAB_URL}/api/v4/projects/${GROUP}%2F${PROJECT_NAME}")
    RET=$(echo "${PROJECT}" | ( grep -i 'not found' || true ))
    if [ ! -z "$RET" ]; then
        echo "Project: ${GROUP}/${PROJECT_NAME} not found"
        exit 3
    fi
    PROJECT_ID=$(echo ${PROJECT} | jq '.id')
fi

if ! [[ ${PROJECT_ID} =~ ^[0-9]+$ ]]; then
    echo "Error: multiple matches found. Use: $0 GITLAB_PROJECT_GROUP"
    exit 4
fi

REGISTRY_REPOS=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories" | jq '.[] | .id')


get_images
echo "Delete this images? [y/n]:"
read ANSWER

if [[ ${ANSWER} == "y" ]]; then
  delete_images
else
  exit 0
fi
