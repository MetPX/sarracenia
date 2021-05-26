# Install sarracenia and download sr_insects repository
#
# Script should be called from root directory

sudo apt update
sudo apt install -y git python3-pip

export PATH=${PATH}:${HOME}/.local/bin
pip3 install -U pip
pip3 install -e .
git clone https://github.com/MetPX/sr_insects ${HOME}/sr_insects
