#!/bin/bash -e

# Run script in git-repo folder
function echo_help() {
    echo -e "\nUsage for $0:\n
    $0 [ {GITLAB_GROUP} {MAX_PIPELINE_ID} ]

    GITLAB_GROUP..............Gitlab group of project
    \nKeys:
    -h                    Show this help.\n"
}

get_projects () {

  for i in $(seq 1 5);do
    projects=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/?per_page=100&page=${i}" | jq '.[].id')
    PROJECTS_IDS+="${projects} "
  done
    #echo $PROJECTS_IDS

    #for i in $PROJECTS_IDS; do
    #  echo $i
    #done

  }

get_images () {
  for PROJECT_ID in ${PROJECTS_IDS};do
    REGISTRY_REPOS=""
    PROJECT_REPO_SIZE=0
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
            info_tag=$(curl -s -H "Private-Token: $CI_JOB_TOKEN" -L "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}/registry/repositories/${repo}/tags/$tag")
            size=$(echo $info_tag | jq '.total_size')
            echo $size
            PROJECT_REPO_SIZE=$(( ${PROJECT_REPO_SIZE}+$size ))

          done
        done
      fi
    done
    echo -e "Total bytes: ${PROJECT_REPO_SIZE} \nTotal MB: $(( ${PROJECT_REPO_SIZE}/1000/1000 )) \nTotal GB: $(( ${PROJECT_REPO_SIZE}/1000/1000/1000 ))\n\n"
  done

}


GITLAB_URL="https://gitlab.example.com"
GROUP=$1
PROJECTS_IDS=""
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

get_projects
get_images
