#!/bin/bash

# create network
docker network create livehouse

# pull latest container images
docker pull influxdb:latest
docker pull livehouseautomation/veraflux-grafana:latest

# stop running containers
docker container rename influxdb influxdb_old
docker container rename grafana grafana_old
docker stop influxdb
docker stop grafana

# recreate influxdb container
docker run \
  -d \
  --rm \
  --name influxdb \
  --network livehouse \
  -p 8086:8086 \
  -p 8083:8083 \
  -p 2003:2003 \
  -p 25826:25826 \
  -e INFLUXDB_DATA_WAL_FSYNC_DELAY=1s \
  -e INFLUXDB_DATA_MAX_CONCURRENT_COMPACTIONS=1 \
  -e INFLUXDB_COORDINATOR_QUERY_TIMEOUT=60s \
  -e INFLUXDB_COORDINATOR_LOG_QUERIES_AFTER=30s \
  -e INFLUXDB_RETENTION_CHECK_INTERVAL=3600m0s \
  -v /storage/influxdb/data:/var/lib/influxdb \
  -v /storage/influxdb/backup:/backup \
  influxdb:latest

# recreate grafana container
mkdir -p /storage/grafana/data
chown -R 472:472 /storage/grafana
docker run \
  -d \
  --rm \
  --name grafana \
  --network livehouse \
  -p 3000:3000 \
  -v /storage/grafana/data:/var/lib/grafana \
  livehouseautomation/veraflux-grafana:latest

