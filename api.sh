#!/bin/bash
set -e
source /etc/container_environment.sh

API_PORT=${API_PORT:-8888}

exec uvicorn api:app --host 0.0.0.0 --port "${API_PORT}" --app-dir /app
