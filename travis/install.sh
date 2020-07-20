# Install sarracenia and download sr_insects repository
#
# Script should be called from root directory

sudo apt -y install git devscripts debhelper dh-python python3-setuptools python3-docutils python3-amqp python3-appdirs python3-humanize python3-psutil python3-watchdog
debuild -us -uc
sudo dpkg -i ../metpx-sarracenia*.deb
git clone https://github.com/MetPX/sr_insects ${HOME}/sr_insects
