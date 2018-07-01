#!/bin/bash
docker build -t fluxbox-os-build .
docker run \
	--name fluxbox-os-build \
	--rm \
	-it \
	-v /home/mikenye/odroid/root:/imageroot \
	fluxbox-os-build
