FROM ubuntu:bionic

RUN apt-get update
RUN apt-get install -y --no-install-recommends ca-certificates wget

WORKDIR /build
RUN wget -O buildroot.tar.gz https://buildroot.org/downloads/buildroot-2018.02.3.tar.gz
RUN tar xzvf -C ./buildroot buildroot.tar.gz
