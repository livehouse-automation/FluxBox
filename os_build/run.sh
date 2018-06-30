#!/bin/bash
docker build -t fluxbox-os-build .
docker run --name fluxbox-os-build --rm -it fluxbox-os-build
