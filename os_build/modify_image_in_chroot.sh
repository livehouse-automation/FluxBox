#!/bin/bash -x

# Set up proc within chroot jail
mount -t proc proc /proc

# Sort out dns in container for this process
cp -v /etc/resolv.conf /etc/resolv.conf.original
echo nameserver 8.8.8.8 > /etc/resolv.conf
echo nameserver 8.8.4.4 >> /etc/resolv.conf

# update apt repo
apt-get update

# upgrade anything that needs it
apt-get upgrade -y

# install prerequisites
apt-get install -y git-sh

# various prerequisites
apt-get install -y curl net-tools

# Get FluxBox stuff
mkdir /src
cd /src
git clone -b develop https://github.com/livehouse-automation/FluxBox.git
# TODO ^^^^ remove develop branch when ready

# Hard Drive Disk Parking Safely
# https://wiki.odroid.com/odroid-xu4/troubleshooting/shutdown_script
apt-get install -y hdparm
curl -fsSL https://dn.odroid.com/5422/script/odroid.shutdown -o /lib/systemd/system-shutdown/odroid.shutdown
chown root:root /lib/systemd/system-shutdown/odroid.shutdown
chmod 0755 /lib/systemd/system-shutdown/odroid.shutdown

# Install NTP
apt-get install -y ntp ntpdate

# Install docker
curl -fsSL get.docker.com -o /tmp/get-docker.sh
bash -x /tmp/get-docker.sh

# Install telegraf for monitoring underlying system
curl -sL https://repos.influxdata.com/influxdb.key | apt-key add -
source /etc/lsb-release
echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | tee /etc/apt/sources.list.d/influxdb.list
apt-get update
apt-get install -y telegraf

cat << EOF > /etc/telegraf/telegraf.d/influxdb_output.conf
[[outputs.influxdb]]
  urls = ["udp://127.0.0.1:8086"]
  database = "livehousebrick"
EOF

# Copy scripts
mkdir -p /opt/livehouse/scripts
cp -v /src/FluxBox/start_containers/start_containers.sh /opt/livehouse/scripts
cp -v /src/FluxBox/startup_config/startup_config.py /opt/livehouse/scripts
cp -v /src/FluxBox/startup_config/config.ini /media/boot/

# Setup startup script
cp -v /etc/rc.local /etc/rc.local.original
grep -v 'exit 0' /etc/rc.local.original > /etc/rc.local
cat << EOF >> /etc/rc.local

# Apply config from SD card boot partition /config.ini and log to /config.log
python3 /opt/livehouse/scripts/startup_config.py

# Pull latest docker containers and start them
bash /opt/livehouse/scripts/start_containers.sh &>> /var/log/start_containers.log

exit 0
EOF

# create /etc/profile.d/influx.sh
cat << EOF > /etc/profile.d/livehouse_aliases.sh
#!/bin/bash
alias influx='docker exec -it influxdb influx'
alias influxdb_backup='docker exec -it influxdb influxd backup -database vera -portable /backup/vera-`date +%Y%m%d%H%M%S`'
EOF

# setup logrotate for docker
cat << EOF > /etc/logrotate.d/docker-logs
/var/lib/docker/containers/*/*.log {
  rotate 7
  daily
  compress
  size=1M
  missingok
  delaycompress
  copytruncate
}
EOF

# setup logrotate for start-containers log
cat << EOF > /etc/logrotate.d/start-containers
/var/log/start_containers.log {
  rotate 7
  daily
  compress
  size=1M
  missingok
  delaycompress
  copytruncate
}
EOF

# FINAL STUFF

# revert resolv.conf
mv -v /etc/resolv.conf.original /etc/resolv.conf

# clean apt
rm -rf /var/lib/apt/lists/*

# unmount /proc
mount -t proc proc /proc

# jump out of chroot
exit