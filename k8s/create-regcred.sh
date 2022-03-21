#!/bin/bash

kubectl create secret docker-registry \
    regcred \
    --docker-server="gitlab.domain.ru:4567" \
    --docker-username="gitlab-deploy-token" \
    --docker-password="*************" \
    --docker-email="email@domain.ru"

