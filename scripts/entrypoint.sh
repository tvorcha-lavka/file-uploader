#!/bin/bash

source /scripts/logging.sh

BASE_FLAGS=(
  "--pool=gevent"
  "--concurrency=10"
  "--queues=${QUEUE}"
  "--max-tasks-per-child=50"
  "--hostname=file-uploader@%h"
  "--loglevel=info"
  "--without-mingle"
  "--without-gossip"
)

start() {
  if [[ "$ENV_STATE" == "production" || "$ENV_STATE" == "staging" ]]; then
    log_message INFO "Starting upload queue in ${GREEN}$ENV_STATE mode${NO_COLOR}..."
  else
    log_message WARNING "Starting upload queue in ${YELLOW}development mode${NO_COLOR}..."
  fi
  celery -A main worker "${BASE_FLAGS[@]}"
}

start
