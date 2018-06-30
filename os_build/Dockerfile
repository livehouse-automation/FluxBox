FROM ubuntu:bionic

RUN apt-get update
RUN apt-get install -y --no-install-recommends ca-certificates wget

WORKDIR /build
RUN wget https://buildroot.org/downloads/buildroot-2018.02.3.tar.gz -O buildroot.tar.gz
RUN tar xzvf buildroot.tar.gz -C ./buildroot
