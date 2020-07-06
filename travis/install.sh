# Install sarracenia and download sr_insects repository
#
# Script should be called from root directory

sudo apt -y install git python3-pip
pip3 install -U pip
pip3 install -e .
git clone https://github.com/MetPX/sr_insects ${HOME}/sr_insects
