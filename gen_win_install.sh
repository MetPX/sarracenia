#!/bin/bash


# Windows specific pkgs
rm -rf pynsist_pkgs
mkdir pynsist_pkgs
cd pynsist_pkgs/

# Ensure that pip3 is always used to download-only windows whls
pip3 download pika --only-binary=:all: --platform win_amd64
pip3 download netifaces --only-binary=:all: --platform win_amd64
pip3 download psutil --only-binary=:all: --platform win_amd64
pip3 download paramiko --only-binary=:all: --platform win_amd64
cd ..

# Remove last build
rm -rf dist
rm -rf build
python setup.py bdist_wheel

# NSIS packaging
pynsist win_installer.cfg

