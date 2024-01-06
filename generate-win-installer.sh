#/bin/bash

# so... if you invoke this without arguments it often fails with:
#
# Downloading embeddable Python build...
#Getting https://www.python.org/ftp/python/3.10.12/python-3.10.12-embed-amd64.zip
#Traceback (most recent call last):
#  File "/home/peter/.local/bin/pynsist", line 8, in <module>
#    sys.exit(main())
#  File "/home/peter/.local/lib/python3.10/site-packages/nsist/__init__.py", line 533, in main
#    ec = InstallerBuilder(**args).run(makensis=(not options.no_makensis))
#  File "/home/peter/.local/lib/python3.10/site-packages/nsist/__init__.py", line 475, in run
#    self.fetch_python_embeddable()
#  File "/home/peter/.local/lib/python3.10/site-packages/nsist/__init__.py", line 205, in fetch_python_embeddable
#    download(url, cache_file)
#  File "/home/peter/.local/lib/python3.10/site-packages/nsist/util.py", line 22, in download
#    r.raise_for_status()
#  File "/home/peter/.local/lib/python3.10/site-packages/requests/models.py", line 1021, in raise_for_status
#    raise HTTPError(http_error_msg, response=self)
#requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://www.python.org/ftp/python/3.10.12/python-3.10.12-embed-amd64.zip
#
#
#  you need to visit https://www.python.org/downloads/windows/
#
#  And look for the minor version that they announce has the AMD64 embedded package...
#
#  hunting for python 3.10, we see it is 3.10.9 that is blessed, so call the thing with that version:
#
#  ./generate_win_installer 3.10.9
#
#  and it should find it.
#

set -e

# Windows specific pkgs
rm -rf pynsist_pkgs
mkdir pynsist_pkgs
cd pynsist_pkgs/

# Ensure to download only windows binaries
pip3 download amqp --only-binary=:all: --platform win_amd64
pip3 download appdirs --only-binary=:all: --platform win_amd64
pip3 download dateparser --only-binary=:all: --platform win_amd64
pip3 download humanfriendly --only-binary=:all: --platform win_amd64
pip3 download humanize --only-binary=:all: --platform win_amd64
pip3 download jsonpickle --only-binary=:all: --platform win_amd64

# these are often missing... means vip will be disabled.
#pip3 download netifaces --only-binary=:all: --platform win_amd64
#pip3 download netifaces-w39 --only-binary=:all: --platform win_amd64

# not used anymore.
#pip3 download pika --only-binary=:all: --platform win_amd64

pip3 download psutil --only-binary=:all: --platform win_amd64
pip3 download paramiko --only-binary=:all: --platform win_amd64
pip3 download regex --only-binary=:all: --platform win_amd64
pip3 download python-dateutil --only-binary=:all: --platform win_amd64
pip3 download pytz --only-binary=:all: --platform win_amd64
#pip3 download tzlocal --only-binary=:all: --platform win_amd64

# weirdly... pip install fails for this one, so fetch an arch neutral one.
pip3 wheel paho-mqtt 

# No binary available, thats why they are not fetched by pip (to be tested later) 
# look in win_installer.cfg.tem fo additional deps.
#pip3 download pycparser --only-binary=:all: --platform win_amd64
#pip3 download pathtools --only-binary=:all: --platform win_amd64
pip3 download watchdog --only-binary=:all: --platform win_amd64
pip3 download python-magic-bin --only-binary=:all: --platform win_amd64

cd ..

# Remove last build
rm -rf dist
rm -rf build
python3 -m build

if [ "$1" ]; then
    PYVERSION=$1
else
    PYVERSION="`python3 -V| awk '{ print $2; }'`"
fi
VERSION=`grep __version__ sarracenia/_version.py | cut -c15- | sed -e 's/"//g'`

sed 's/__version__/'$VERSION'/; s/__pyversion__/'$PYVERSION'/;' <win_installer.cfg.tem >win_installer.cfg
# NSIS packaging
pynsist win_installer.cfg

