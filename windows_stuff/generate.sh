#!/bin/bash

# Remove last build
rm -rf build

# Windows specific pkgs
mkdir pynsist_pkgs
cd pynsist_pkgs/

# Ensure that pip3 is always used to download-only windows whls
pip3 download pika --only-binary=:all: --platform win_amd64
pip3 download netifaces --only-binary=:all: --platform win_amd64
pip3 download psutil --only-binary=:all: --platform win_amd64
pip3 download paramiko --only-binary=:all: --platform win_amd64

cd ../..

python setup.py bdist_wheel

cd windows_stuff

# NSIS packaging
pynsist installer.cfg
rm -rf pynsist_pkgs

