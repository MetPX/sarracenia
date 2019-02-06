#!/bin/bash


# Windows specific pkgs
rm -rf pynsist_pkgs
mkdir pynsist_pkgs
cd pynsist_pkgs/

# Ensure to download only windows binaries
pip download amqp --only-binary=:all: --platform win_amd64
pip download appdirs --only-binary=:all: --platform win_amd64
pip download netifaces --only-binary=:all: --platform win_amd64
pip download pika --only-binary=:all: --platform win_amd64
pip download psutil --only-binary=:all: --platform win_amd64
pip download paramiko --only-binary=:all: --platform win_amd64

# No binary available, thats why they are not fetched by pip (to be tested later) 
#pip3 download humanize --only-binary=:all: --platform win_amd64
#pip3 download pycparser --only-binary=:all: --platform win_amd64
#pip3 download pathtools --only-binary=:all: --platform win_amd64
#pip3 download watchdog --only-binary=:all: --platform win_amd64

cd ..

# Remove last build
rm -rf dist
rm -rf build
python setup.py bdist_wheel

# NSIS packaging
pynsist win_installer.cfg

