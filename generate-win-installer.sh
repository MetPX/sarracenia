#!/bin/bash
set -e

# Windows specific pkgs
rm -rf pynsist_pkgs
mkdir pynsist_pkgs
cd pynsist_pkgs/

# Ensure to download only windows binaries
pip3 download amqp --only-binary=:all: --platform win_amd64
pip3 download appdirs --only-binary=:all: --platform win_amd64
#pip3 download netifaces --only-binary=:all: --platform win_amd64
pip3 download netifaces-w38 --only-binary=:all: --platform win_amd64
pip3 download pika --only-binary=:all: --platform win_amd64
pip3 download psutil --only-binary=:all: --platform win_amd64
pip3 download paramiko --only-binary=:all: --platform win_amd64

# weirdly... pip install fails for this one, so fetch an arch neutral one.
pip3 wheel paho-mqtt 

# No binary available, thats why they are not fetched by pip (to be tested later) 
#pip3 download humanize --only-binary=:all: --platform win_amd64
#pip3 download pycparser --only-binary=:all: --platform win_amd64
#pip3 download pathtools --only-binary=:all: --platform win_amd64
#pip3 download watchdog --only-binary=:all: --platform win_amd64

cd ..

# Remove last build
rm -rf dist
rm -rf build
python3 setup.py bdist_wheel

if [ "$1" ]; then
    PYVERSION=$1
else
    PYVERSION="`python3 -V| awk '{ print $2; }'`"
fi
VERSION=`grep __version__ sarracenia/__init__.py | cut -c15- | sed -e 's/"//g'`

sed 's/__version__/'$VERSION'/; s/__pyversion__/'$PYVERSION'/;' <win_installer.cfg.tem >win_installer.cfg
# NSIS packaging
pynsist win_installer.cfg

