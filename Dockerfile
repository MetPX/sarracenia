FROM ubuntu:latest

MAINTAINER "Peter.Silva@ssc-spc.gc.ca"

ENV TZ="Etc/UTC" \
    DEBIAN_FRONTEND="noninteractive" \
    BUILD_PACKAGES="build-essential" 

# deps copied from setup.py requires= ...  

RUN apt-get update ; apt-get install -y python3-appdirs python3-dateparser python3-watchdog python3-netifaces python3-humanize python3-jsonpickle python3-paramiko python3-psutil python3-amqp python3-pip

# need version >= 1.5.1 to get MQTT v5 support, not in repos of 20.04 ... so get from pip.
RUN pip3 install paho-mqtt

WORKDIR /src

COPY . /src

RUN python3 setup.py install

