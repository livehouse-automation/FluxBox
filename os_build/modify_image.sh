#!/bin/bash -x

IMAGEFILE="./ubuntu-18.04-4.14-minimal-odroid-xu4-20180531.img"

#get image
#wget http://path/to/image

# backup image
cp -v $IMAGEFILE $IMAGEFILE.original

# extract image
#xz -d $IMAGEFILE

# setup loopback
LOOPBACKDEV=`losetup -P --show -f $IMAGEFILE`
# GRAB OUTPUT AS THIS IS LOOPBACK

# mount image
mkdir ./imagerootfs
mount ${LOOPBACKDEV}p2 ./imagerootfs
mount ${LOOPBACKDEV}p1 ./imagerootfs/media/boot

# copy script to run inside chroot
cp -v ./modify_image_in_chroot.sh ./imagerootfs/tmp/

# chroot into image and run script
chroot ./imagerootfs /tmp/modify_image_in_chroot.sh

# CLEAN UP 

# remove temp stuff
rm -r ./imagerootfs/src
rm -r ./imagerootfs/tmp/*

# remove bash history
rm ./imagerootfs/root/bash_history
touch ./imagerootfs/root/bash_history
chmod 0600 ./imagerootfs/root/bash_history
chown 0 ./imagerootfs/root/bash_history
chgrp 0 ./imagerootfs/root/bash_history

# truncate logs
truncate -s 0 ./imagerootfs/var/log/alternatives.log 
truncate -s 0 ./imagerootfs/var/log/auth.log 
truncate -s 0 ./imagerootfs/var/log/dmesg
truncate -s 0 ./imagerootfs/var/log/dpkg.log 
truncate -s 0 ./imagerootfs/var/log/faillog 
truncate -s 0 ./imagerootfs/var/log/fontconfig.log 
truncate -s 0 ./imagerootfs/var/log/kern.log 
truncate -s 0 ./imagerootfs/var/log/lastlog 
truncate -s 0 ./imagerootfs/var/log/syslog 
truncate -s 0 ./imagerootfs/var/log/tallylog 
truncate -s 0 ./imagerootfs/var/log/wtmp
truncate -s 0 ./imagerootfs/var/log/apt/history.log
truncate -s 0 ./imagerootfs/var/log/apt/term.log
truncate -s 0 ./imagerootfs/var/log/unattended-upgrades/unattended-upgrades-dpkg.log
truncate -s 0 ./imagerootfs/var/log/unattended-upgrades/unattended-upgrades.log

# Unmount image
umount ./imagerootfs/media/boot
umount ./imagerootfs
rmdir ./imagerootfs

# Clean up loopback
losetup -v -d ${LOOPBACKDEV}

# Rename
mv -v $IMAGEFILE livehouseautomation-$IMAGEFILE

# Compress image
xz -vzT4 livehouseautomation-$IMAGEFILE
