#!/usr/bin/env bash

cd /app
yc config profile create sa-profile
yc config set service-account-key config/key.json
yc config set cloud-id ${YC_CLOUD_ID}
yc config set folder-id ${YC_FODER_ID}

exec /app/sync.py
