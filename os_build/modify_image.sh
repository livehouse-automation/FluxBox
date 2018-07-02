#!/bin/bash

# Get FluxBox stuff
mkdir /src
cd /src
git clone -b develop https://github.com/livehouse-automation/FluxBox.git
# TODO ^^^^ remove develop branch when ready

# alias for running commands in the image
alias run_in_image='proot -q qemu-arm -0 -r /imageroot'


#### CODE BELOW SHOULD BE RUN IN IMAGE


# Sort out dns in container for this process
echo nameserver 8.8.8.8 > /etc/resolv.conf
echo nameserver 8.8.4.4 >> /etc/resolv.conf

# fix issue with apt
#mv -v /imageroot/etc/passwd /imageroot/etc/passwd.original
#grep -v "^_apt" /imageroot/etc/passwd.original > /imageroot/etc/passwd

# refresh apt inside image
apt-get update -y

# upgrade anything that needs it
apt-get upgrade -y

# various prerequisites
apt-get install -y curl net-tools

# Hard Drive Disk Parking Safely
# https://wiki.odroid.com/odroid-xu4/troubleshooting/shutdown_script
apt-get install -y hdparm
curl -fsSL https://dn.odroid.com/5422/script/odroid.shutdown -o /lib/systemd/system-shutdown/odroid.shutdown
chown root:root /lib/systemd/system-shutdown/odroid.shutdown
chmod 0755 /lib/systemd/system-shutdown/odroid.shutdown

# Install NTP
apt-get install -y ntp

# Install docker
apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository \
   "deb [arch=armhf] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
apt-get update
apt-get install docker-ce

# Create livehouse network
docker network create livehouse

# Pull livehouse images
docker pull influxdb:latest
docker pull livehouseautomation/veraflux-grafana:latest

# Install telegraf for monitoring underlying system
curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/lsb-release
echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
apt-get update -y
apt-get install -y telegraf

# Copy scripts
mkdir -p /opt/livehouse/
cp -v /src/FluxBox/start_containers/start_containers.sh /imageroot/opt/livehouse/
cp -v /src/FluxBox/startup_config/startup_config.py /imageroot/opt/livehouse/
cp -v /src/FluxBox/startup_config/config.ini /imageroot/media/boot/

