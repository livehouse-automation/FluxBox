FROM ubuntu:bionic

RUN apt-get update
RUN apt-get install -y --no-install-recommends ca-certificates wget

WORKDIR /build
RUN wget -O buildroot.tar.gz https://buildroot.org/downloads/buildroot-2018.02.3.tar.gz
RUN mkdir -p /build/buildroot
RUN tar xzvf --strip-components=1 --directory /build/buildroot buildroot.tar.gz
