#!/bin/bash

# create network
docker network create livehouse

# pull latest container images
docker pull influxdb:latest
docker pull telegraf:latest
docker pull livehouseautomation/veraflux-grafana:latest

# stop running containers
docker stop influxdb
docker stop telegraf
docker stop grafana

# recreate influxdb container
docker run \
  -d \
  --rm \
  --name influxdb \
  --network livehouse \
  -v /storage/influxdb/data:/var/lib/influxdb \
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

