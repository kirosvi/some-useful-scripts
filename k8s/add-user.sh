#!/bin/bash -e

if [[ -z "$1" ]] ;then
  echo "usage: $0 <username>"
  exit 1
fi

trap 'rm -f ca.crt' EXIT

user=$1

kubectl create serviceaccount ${user} || true
secret=$(kubectl get serviceaccount ${user} -o json | jq -r .secrets[].name)

kubectl get secret ${secret} -o json | jq -r '.data["ca.crt"]' | base64 -d > ca.crt
user_token=$(kubectl get secret ${secret} -o json | jq -r '.data["token"]' | base64 -d)

c=`kubectl config current-context`

cluster_name=`kubectl config get-contexts $c | awk '{print $3}' | tail -n 1`

endpoint=`kubectl config view -o jsonpath="{.clusters[?(@.name == \"${cluster_name}\")].cluster.server}"`

# Set up the config
touch k8s-${user}-conf
export KUBECONFIG=k8s-${user}-conf

kubectl config set-cluster ${cluster_name} \
    --embed-certs=true \
    --server=${endpoint} \
    --certificate-authority=./ca.crt

kubectl config set-credentials ${user}-${cluster_name#cluster-} --token=${user_token}
kubectl config set-context ${user}-${cluster_name#cluster-} \
    --cluster=${cluster_name} \
    --user=${user}-${cluster_name#cluster-}
kubectl config use-context ${user}-${cluster_name#cluster-}

echo "export KUBECONFIG=k8s-${user}-conf"

