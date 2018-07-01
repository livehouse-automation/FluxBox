#!/bin/bash
docker build -t fluxbox-os-build .
docker run \
	--name fluxbox-os-build \
	--rm \
	-it \
	-v /home/mikenye/odroid/ubuntu-18.04-4.14-minimal-odroid-xu4-20180531.img.xz:/imagefiles/original.img.xz:ro \
	fluxbox-os-build
