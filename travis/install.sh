# Install sarracenia and download sr_insects repository
#
# Script should be called from root directory

debuild -us -uc
sudo dpkg -i ../metpx-sarracenia*.deb
git clone https://github.com/MetPX/sr_insects ${HOME}/sr_insects
