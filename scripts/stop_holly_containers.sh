#!/bin/bash

# Find all running containers with names starting with 'holly-container'
containers=$(docker ps --format "{{.ID}} {{.Names}}" | awk '$2 ~ /^holly-container/ {print $1}')

# Stop matching containers
for container in $containers; do
  echo "Stopping container named 'holly-container*': $container"
  docker ps -a | grep $container
  docker stop "$container"
done

# Find all containers (running or stopped) with names starting with 'holly-container'
all_matching=$(docker ps -a --format "{{.ID}} {{.Names}}" | awk '$2 ~ /^holly-container/ {print $1}')
for container in $all_matching; do
  echo "Removing container named 'holly-container*': $container"
  docker rm "$container"
done

