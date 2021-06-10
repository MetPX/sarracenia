# Flow Test Add sr3
# given a test vm, add v03 versions on top, to be able to test them.

# Install and configure dependencies
sudo apt -y install metpx-sr3c

# to be able to build v3 packages:
# assume on v03_wip branch... (git checkout v03_wip)
sudo apt -y install devscripts
# needs to be run from root dir of cloned rep.
sudo apt -y build-dep .
debuild -us -uc
sudo dpkg -i ../metpx-sr*.deb
#missing deps result...
sudo apt -y install -f 

