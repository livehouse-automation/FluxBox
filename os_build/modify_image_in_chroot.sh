#!/bin/bash -x

# Set up proc within chroot jail
mount -t proc proc /proc

# Sort out dns in container for this process
cp -v /etc/resolv.conf /etc/resolv.conf.original
echo nameserver 8.8.8.8 > /etc/resolv.conf
echo nameserver 8.8.4.4 >> /etc/resolv.conf

# set default hostname
echo "livehousebrick" > /etc/hostname

# update apt repo
apt-get update -y

# remove network manager
apt-get purge -y network-manager network-manager-gnome network-manager-pptp

# remove modem manager
apt-get purge -y modemmanager

# remove other unneeded packages
apt-get purge -y adwaita-icon-theme
apt-get purge -y colord colord-data
apt-get purge -y crda
apt-get purge -y dbus-x11
apt-get purge -y fontconfig fontconfig-config fonts-dejavu-core
apt-get purge -y gnome-keyring
apt-get purge -y gsettings-desktop-schemas
apt-get purge -y gtk-update-icon-cache
apt-get purge -y hicolor-icon-theme
apt-get purge -y indicator-application
apt-get purge -y iw
apt-get purge -y netplan.io
apt-get purge -y networkd-dispatcher
apt-get purge -y notification-daemon
apt-get purge -y policykit-1-gnome
apt-get purge -y powermgmt-base
apt-get purge -y ppp
apt-get purge -y pptp-linux
apt-get purge -y ubuntu-advantage-tools
apt-get purge -y ubuntu-keyring
apt-get purge -y wireless-tools
apt-get purge -y wpasupplicant
apt-get purge -y x11-common
apt-get purge -y xauth
apt-get purge -y xkb-data
apt-get purge -y `dpkg --list | grep "^rc" | tr -s " " | cut -d " " -f 2`
apt-get autoremove -y

# upgrade everything remaining
apt-get upgrade -y

# install ifupdown
apt-get install -y ifupdown

# install lldpd
apt-get install -y lldpd

# install prerequisites
apt-get install -y git-sh

# various prerequisites
apt-get install -y curl net-tools

# Get FluxBox stuff
mkdir -p /opt/livehouse/
cd /opt/livehouse/
git clone -b develop https://github.com/livehouse-automation/FluxBox.git
cp -v ./FluxBox/livehouse_early_boot/config.ini /media/boot/
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

# Apply config from SD card boot partition /config.ini and log to /config.log


# Setup startup script
cp -v /etc/rc.local /etc/rc.local.original
grep -v 'exit 0' /etc/rc.local.original > /etc/rc.local
cat << EOF >> /etc/rc.local

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

# disable IPv6
touch /etc/sysctl.d/90-disable-ipv6.conf
cat << EOF > /etc/sysctl.d/90-disable-ipv6.conf
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF

# configure lldpd
cat << EOF > /etc/lldpd.d/10-livehouse.conf
configure system description 'LiveHouse Brick'
configure lldp portidsubtype ifname
EOF
cat << EOF > /etc/default/lldpd
# Uncomment to start SNMP subagent and enable CDP, SONMP and EDP protocol
DAEMON_ARGS="-x -c -s -e"
EOF

# truncate dhcp lease files
for filename in /var/lib/dhcp/dhclient.*; do
  truncate -s 0 $filename
done

# prepare networking
mkdir -p /etc/network/interfaces.d
cat << EOF > /etc/network/interfaces
source-directory /etc/network/interfaces.d
auto lo
iface lo inet loopback
EOF
cat << EOF > /etc/network/interfaces.d/eth0
auto eth0
iface eth0 inet dhcp
EOF

# change boot.ini
# store original boot.ini
mv /media/boot/boot.ini /media/boot/boot.ini.original
# write new boot.ini, cutting out stuff we don't need, changing default runlevel to 3
cat << EOF > /media/boot/boot.ini
ODROIDXU-UBOOT-CONFIG

# U-Boot Parameters
setenv initrd_high "0xffffffff"
setenv fdt_high "0xffffffff"

# DRAM Frequency
# Sets the LPDDR3 memory frequency
# Supported values: 933 825 728 633 (MHZ)
setenv ddr_freq 825

# External watchdog board enable
setenv external_watchdog "false"
# debounce time set to 3 ~ 10 sec, default 3 sec
setenv external_watchdog_debounce "3"

#------------------------------------------------------------------------------------------------------
# Basic Ubuntu Setup
# --------------------------------
setenv bootrootfs "console=ttySAC2,115200n8 root=UUID=e139ce78-9841-40fe-8823-96a304a09859 rootwait ro fsck.repair=yes net.ifnames=0"

# Load kernel, initrd and dtb in that sequence
fatload mmc 0:1 0x40008000 zImage
fatload mmc 0:1 0x42000000 uInitrd

setenv fdtloaded "false"
if test "x${board_name}" = "x"; then setenv board_name "xu4"; fi
if test "${board_name}" = "xu4"; then fatload mmc 0:1 0x44000000 exynos5422-odroidxu4.dtb; setenv fdtloaded "true"; fi
if test "${fdtloaded}" = "false"; then fatload mmc 0:1 0x44000000 exynos5422-odroidxu4.dtb; setenv fdtloaded "true"; fi

fdt addr 0x44000000

# final boot args
setenv bootargs "${bootrootfs} ${external_watchdog}"

# set DDR frequency
dmc ${ddr_freq}

# change default runlevel
setenv bootargs ${bootargs} 3

# display bootargs
echo "Boot args:"
echo ${bootargs}

# Boot the board
bootz 0x40008000 0x42000000 0x44000000
EOF

# change boot orders
#mv -v S11bootmisc.sh S12bootmisc.sh
#mv -v S10mountnfs-bootclean.sh S11mountnfs-bootclean.sh
#mv -v S09mountnfs.sh S10mountnfs.sh
#mv -v S09mountall-bootclean.sh S10mountall-bootclean.sh 
#mv -v S08networking S09networking


# FINAL STUFF

# revert resolv.conf
mv -v /etc/resolv.conf.original /etc/resolv.conf

# clean apt
rm -rf /var/lib/apt/lists/*

# unmount /proc
mount -t proc proc /proc

# jump out of chroot
exit