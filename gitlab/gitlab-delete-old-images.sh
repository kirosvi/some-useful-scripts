#!/bin/bash -e

# Run script in git-repo folder
function echo_help() {
    echo -e "\nUsage for $0:\n
    $0 [ {GITLAB_GROUP} {MAX_PIPELINE_ID} ]

    GITLAB_GROUP..............Gitlab group of project
    DAYS_BEFORE_TODAY...........All images for this days befor today will be saved in registry
    \nKeys:
    -h                    Show this help.\n"
}

get_projects () {

  for i in $(seq 1 5);do
    projects=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/?per_page=100&page=${i}" | jq '.[].id')
    PROJECTS_IDS+="${projects} "
  done

  }

function is_delete () {
  # Return "1" if variable 'NOT IN LIST' and "0" if variable 'IN LIST'

  delete_image=1
  image=$1

  for i in ${tags_exclude[@]}; do
    if [ "$i" == "$image" ]; then
      delete_image=0
      break
    fi
  done
  echo $delete_image

  }

get_images () {
    REGISTRY_REPOS=""
    echo "Project ID: $(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}" | jq '.name')"
    for i in $(seq 1 5);do
      repos=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories?per_page=100&page=${i}" | jq '.[].id')
      #echo $repos
        if [ ! -z "$repos" ]; then
          REGISTRY_REPOS+="${repos} "
        fi
    done
    echo "Registry repos: $REGISTRY_REPOS"
    for repo in $REGISTRY_REPOS; do
      if [ ! -z "$repo" ]; then
        echo "Repo id: ${repo}"
        for i in $(seq 1 100);do
          REPO_TAGS=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories/${repo}/tags?per_page=100&page=${i}" | jq '.[] | .name')
          tags=$( echo $REPO_TAGS | tr " " "\n" | sed 's/"//g')
          for tag in ${tags}; do
            DELETE_IMAGE=$( is_delete ${tag} )
            if [ ${DELETE_IMAGE} == "1" ]; then
            info_tag=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories/${repo}/tags/$tag")
            cr_date=$(echo $info_tag | jq ' .created_at')
            date=$(echo $cr_date | sed 's/\..*//;s/"//g' )
            if [[ "$OSTYPE" == "darwin"* ]]; then
              unixdate=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$date" "+%s")
            else
              unixdate=$(date -d "$date" "+%s")
            fi
            #echo $unixdate
              if [ $unixdate -le $STAMP ];then
                  link="${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories/${repo}/tags/${tag}"
                  echo $link
                  arr_old_images+=($link)
              fi

            fi
          done
        done
      fi
    done

}

delete_images () {

  for i in ${arr_old_images[*]}; do
    DELETE=$(curl -s --request DELETE --header "PRIVATE-TOKEN: ${CI_JOB_TOKEN}" "${i}")
    if [[ ${DELETE} == "200" ]]; then
      echo "Image ${i} was deleted"
    else
      echo "Error code ${DELETE}"
    fi
  done

}


arr_old_images=()
GITLAB_URL="https://gitlab.example.com"
GROUP=$1
TOTAL_SIZE=0
tags_exclude=(master latest)
if [[ "$OSTYPE" == "darwin"* ]]; then
    STAMP=$(date -v-$2d +%s)
    echo $STAMP
  else
    STAMP=$(date --date="$2 day ago" +%s)
fi
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
get_images

echo -e "\n\nOld images:"
for i in ${arr_old_images[*]}; do
  echo $i
done
echo "Delete this images? [y/n]:"
read ANSWER

if [[ ${ANSWER} == "y" ]]; then
  delete_images
else
  exit 0
fi
