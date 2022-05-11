# Flow Test Add sr3
# given a test vm, add v03 versions on top, to be able to test them.

# Install and configure dependencies
sudo apt -y install metpx-sr3c

# recommends don't seem to be showing up... FIXM.. should be a way to explicitly install recommends.
sudo apt -y install wget ncftp

# to be able to build v3 packages:
# assume on v03_wip branch... (git checkout v03_wip)
sudo apt -y install devscripts
# needs to be run from root dir of cloned rep.
sudo apt -y build-dep .

# 18.04 paho-mqtt  library is too old, need >=1.5

sudo apt remove python3-paho-mqtt
sudo apt install python3-pip
sudo pip3 install paho-mqtt
debuild -us -uc
sudo dpkg -i ../metpx-sr*.deb
#missing deps result...
sudo apt -y install -f 
