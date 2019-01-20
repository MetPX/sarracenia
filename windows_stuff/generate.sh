#!/bin/bash

# Remove last build
rm -rf build

# Windows specific pkgs
mkdir pynsist_pkgs
cd pynsist_pkgs/

# Ensure that pip3 is always used to download-only windows whls
pip3 download paramiko --only-binary=:all: --platform win_amd64
pip3 download metpx-sarracenia --only-binary=:all: --platform win_amd64
pip3 download amqplib --only-binary=:all: --platform win_amd64
pip3 download appdirs --only-binary=:all: --platform win_amd64
pip3 download watchdog --only-binary=:all: --platform win_amd64
pip3 download netifaces --only-binary=:all: --platform win_amd64
pip3 download humanize --only-binary=:all: --platform win_amd64
pip3 download psutil --only-binary=:all: --platform win_amd64

cd ..

# NSIS packaging
pynsist installer.cfg
rm -rf pynsist_pkgs

