#!/bin/bash

export SR_POST_CONFIG=""
export LD_PRELOAD=""

function application_dirs {
python3 << EOF
import appdirs

cachedir  = appdirs.user_cache_dir('sarra','science.gc.ca')
cachedir  = cachedir.replace(' ','\ ')
print('export CACHEDIR=%s'% cachedir)

confdir = appdirs.user_config_dir('sarra','science.gc.ca')
confdir = confdir.replace(' ','\ ')
print('export CONFDIR=%s'% confdir)

logdir  = appdirs.user_log_dir('sarra','science.gc.ca')
logdir  = logdir.replace(' ','\ ')
print('export LOGDIR=%s'% logdir)

EOF
}

eval `application_dirs`

tstdir="`pwd`"
httpdocroot=`cat $tstdir/.httpdocroot`


# function to see if same amount of files

function wait_dir_to_be_the_same {

       COUNT=`find "$httpdocroot"/cfr -type $1 -print | grep $2 | wc -l`
       echo "expecting " $COUNT
       sleep 5
       MCOUNT=`find "$httpdocroot"/cfile -type $1 -print | grep $2 | wc -l`
       while [ "${MCOUNT}" != "${COUNT}" ]; do
             sleep 5
             MCOUNT=`find "$httpdocroot"/cfile -type $1 -print | grep $2 | wc -l`
             echo "(${MCOUNT} expecting ${COUNT})"
       done
}

# sr_post initial start
# MIRROR TEST

sr_cpost stop veille_f34 > /dev/null 2>&1
sr_cpost cleanup veille_f34 > /dev/null 2>&1
rm "$LOGDIR"/sr_cpost_veille_f34*.log  2>&1
sr_cpost setup veille_f34 > /dev/null 2>&1

sr_subscribe stop cfile_f44 > /dev/null 2>&1
sr_subscribe cleanup cfile_f44 > /dev/null 2>&1
rm "$LOGDIR"/sr_subscribe_cfile_f44*.log  2>&1
sr_subscribe setup cfile_f44 > /dev/null 2>&1

# preventive cleanup (previous runs)

cd "$httpdocroot"/cfr
find . -type f -print | grep COPY | xargs -n1 rm 2> /dev/null
find . -type l -print | grep LINK | xargs -n1 rm 2> /dev/null
find . -type f -print | grep LINK | xargs -n1 rm 2> /dev/null
find . -type f -print | grep MOVE | xargs -n1 rm 2> /dev/null

cd "$httpdocroot"/cfile
find . -type f -print | grep COPY | xargs -n1 rm 2> /dev/null
find . -type l -print | grep LINK | xargs -n1 rm 2> /dev/null
find . -type f -print | grep LINK | xargs -n1 rm 2> /dev/null
find . -type f -print | grep MOVE | xargs -n1 rm 2> /dev/null

sr_cpost start veille_f34 > /dev/null 2>&1
sr_subscribe start cfile_f44 > /dev/null 2>&1

# copy 

echo "checking sr_cpost copy"
cd "$httpdocroot"/cfr
find . -type f -print                | xargs -iAAA cp AAA AAA.COPY
find . -type f -print | grep -v COPY | xargs -iAAA cp AAA AAA.COPY2
wait_dir_to_be_the_same f COPY
echo "success"

# move 

echo "checking sr_cpost move"
cd "$httpdocroot"/cfr
find . -type f -print | grep -v COPY | xargs -iAAA  mv AAA.COPY2 AAA.MOVE
wait_dir_to_be_the_same f MOVE
echo "success"

# softlink 

echo "checking sr_cpost softlink"
cd "$httpdocroot"/cfr
find . -type f -print | grep -v COPY | grep -v MOVE | xargs -iAAA  ln -s AAA AAA.SLINK
wait_dir_to_be_the_same l SLINK
echo "success"

# hardlink 

echo "checking sr_cpost hardlink"
cd "$httpdocroot"/cfr
find . -type f -print | grep -v COPY | grep -v MOVE | grep -v LINK | xargs -iAAA ln AAA AAA.HLINK
wait_dir_to_be_the_same f HLINK
echo "success"

# hardlink 

echo "checking sr_cpost remove"
cd "$httpdocroot"/cfr 
find . -type f -print | grep COPY | xargs -n1 rm
find . -type f -print | grep MOVE | xargs -n1 rm
find . -type f -print | grep LINK | xargs -n1 rm
find . -type l -print | grep LINK | xargs -n1 rm
wait_dir_to_be_the_same f \.
echo "success"
