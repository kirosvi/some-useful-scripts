#!/usr/bin/env bash
if [[ -z "${1}" || -z "${2}" ]]; then
    echo "Usage: ${0} USER_NAME ACCESS_TOKEN"
    exit 1
fi
REGISTRY="https://gitlab.example.com:4567/v2/"

echo "{"auths":{"${REGISTRY}":{"username":"${1}","password":"${2}","email":"${1}@example.com"}}}" | base64
