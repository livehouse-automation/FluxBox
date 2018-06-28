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
  -v /storage/influxdb/data:/var/lib/influxdb \
  influxdb:latest

# recreate grafana container
docker run \
  -d \
  --rm \
  --name grafana \
  -p 3000:3000 \
  -v /storage/grafana/data:/var/lib/grafana \
  livehouseautomation/veraflux-grafana:latest

