#!/bin/bash

# Get FluxBox stuff
mkdir /src
cd /src
git clone -b develop https://github.com/livehouse-automation/FluxBox.git
# TODO ^^^^ remove develop branch when ready

# alias for running commands in the image
alias run_in_image='proot -q qemu-arm -r /imageroot'

# Sort out dns in container for this process
echo nameserver 8.8.8.8 > /imageroot/etc/resolv.conf
echo nameserver 8.8.4.4 >> /imageroot/etc/resolv.conf


# refresh apt inside image
run_in_image apt-get update -y

# upgrade anything that needs it
run_in_image apt-get upgrade -y

# various prerequisites
run_in_image apt-get install -y curl net-tools

# Hard Drive Disk Parking Safely
# https://wiki.odroid.com/odroid-xu4/troubleshooting/shutdown_script
run_in_image apt-get install -y hdparm
run_in_image curl -fsSL https://dn.odroid.com/5422/script/odroid.shutdown -o /lib/systemd/system-shutdown/odroid.shutdown
run_in_image chown root:root /lib/systemd/system-shutdown/odroid.shutdown
run_in_image chmod 0755 /lib/systemd/system-shutdown/odroid.shutdown

# Install NTP
run_in_image apt-get install -y ntp

# Install docker
run_in_image apt-get install -y dmsetup
run_in_image curl -fsSL get.docker.com | bash
run_in_image docker run --rm hello-world

# Create livehouse network
run_in_image docker network create livehouse

# Pull livehouse images
run_in_image docker pull influxdb:latest
run_in_image docker pull livehouseautomation/veraflux-grafana:latest

# Install telegraf for monitoring underlying system
run_in_image curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
run_in_image source /etc/lsb-release
run_in_image echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
run_in_image apt-get update -y
run_in_image apt-get install -y telegraf

# Copy scripts
run_in_image mkdir -p /opt/livehouse/
cp -v /src/FluxBox/start_containers/start_containers.sh /imageroot/opt/livehouse/
cp -v /src/FluxBox/startup_config/startup_config.py /imageroot/opt/livehouse/
cp -v /src/FluxBox/startup_config/config.ini /imageroot/media/boot/

