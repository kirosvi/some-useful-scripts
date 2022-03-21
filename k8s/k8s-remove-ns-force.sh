#!/bin/bash

NS=$1

kubectl get ns $NS -o json \
    | tr -d "\n" | sed "s/\"finalizers\": \[[^]]\+\]/\"finalizers\": []/" \
    | kubectl replace --raw /api/v1/namespaces/${NS}/finalize -f -

