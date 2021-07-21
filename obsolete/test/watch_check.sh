#!/bin/bash

export SR_POST_CONFIG=""
export LD_PRELOAD=""

if [[ ":$SARRA_LIB/../:" != *":$PYTHONPATH:"* ]]; then
    if [ "${PYTHONPATH:${#PYTHONPATH}-1}" == ":" ]; then
        export PYTHONPATH="$PYTHONPATH$SARRA_LIB/../"
    else 
        export PYTHONPATH="$PYTHONPATH:$SARRA_LIB/../"
    fi
fi

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
if [ ! "$SARRAC_LIB" ]; then
  sr_cpost stop veille_f34 > /dev/null 2>&1
  sr_cpost cleanup veille_f34 > /dev/null 2>&1
  rm "$LOGDIR"/sr_cpost_veille_f34*.log  2>&1
  sr_cpost setup veille_f34 > /dev/null 2>&1
else 
  "$SARRAC_LIB"/sr_cpost stop veille_f34 > /dev/null 2>&1
  "$SARRAC_LIB"/sr_cpost cleanup veille_f34 > /dev/null 2>&1
  rm "$LOGDIR"/sr_cpost_veille_f34*.log  2>&1
  "$SARRAC_LIB"/sr_cpost setup veille_f34 > /dev/null 2>&1
fi

if [ ! "$SARRA_LIB" ]; then
  sr_subscribe stop cfile_f44 > /dev/null 2>&1
  sr_subscribe cleanup cfile_f44 > /dev/null 2>&1
  rm "$LOGDIR"/sr_subscribe_cfile_f44*.log  2>&1
  sr_subscribe setup cfile_f44 > /dev/null 2>&1

else 
  "$SARRA_LIB"/sr_subscribe.py stop cfile_f44 > /dev/null 2>&1
  "$SARRA_LIB"/sr_subscribe.py cleanup cfile_f44 > /dev/null 2>&1
  rm "$LOGDIR"/sr_subscribe_cfile_f44*.log  2>&1
  "$SARRA_LIB"/sr_subscribe.py setup cfile_f44 > /dev/null 2>&1
fi


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

if [ ! "$SARRA_LIB" ]; then 
  sr_watch stop    ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  sr_watch cleanup ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  sr_watch setup   ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  sr_watch -debug start ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  sr_subscribe -debug start cfile_f44 > /dev/null 2>&1
else 
  "$SARRA_LIB"/sr_watch.py stop    ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  "$SARRA_LIB"/sr_watch.py cleanup ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  "$SARRA_LIB"/sr_watch.py setup   ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  "$SARRA_LIB"/sr_watch.py -debug start ${CONFDIR}/cpost/veille_f34.conf > /dev/null 2>&1
  "$SARRA_LIB"/sr_subscribe.py -debug start cfile_f44 > /dev/null 2>&1
fi

# copy 

echo "checking sr_watch copy"
cd "$httpdocroot"/cfr
find . -type f -print                | xargs -iAAA cp AAA AAA.COPY
find . -type f -print | grep -v COPY | xargs -iAAA cp AAA AAA.COPY2
wait_dir_to_be_the_same f COPY
echo "success"

# move 

echo "checking sr_watch move"
cd "$httpdocroot"/cfr
find . -type f -print | grep -v COPY | xargs -iAAA  mv AAA.COPY2 AAA.MOVE
wait_dir_to_be_the_same f MOVE
echo "success"

# softlink 

echo "checking sr_watch softlink"
cd "$httpdocroot"/cfr
find . -type f -print | grep -v COPY | grep -v MOVE | xargs -iAAA  ln -s AAA AAA.SLINK
wait_dir_to_be_the_same l SLINK
echo "success"

# hardlink 

echo "checking sr_watch hardlink"
cd "$httpdocroot"/cfr
find . -type f -print | grep -v COPY | grep -v MOVE | grep -v LINK | xargs -iAAA ln AAA AAA.HLINK
wait_dir_to_be_the_same f HLINK
echo "success"

# WhiteSpace in name

echo "checking sr_watch filename with space"
cd "$httpdocroot"/cfr
find . -type f -print | grep -v COPY | grep -v MOVE | grep -v LINK | xargs -iAAA cp AAA "AAA. SPACE test"
wait_dir_to_be_the_same f SPACE
echo "success"

# removal 

echo "checking sr_watch remove"
cd "$httpdocroot"/cfr 
find . -type f -print | grep COPY  | xargs -n1 rm
find . -type f -print | grep MOVE  | xargs -n1 rm
find . -type f -print | grep LINK  | xargs -n1 rm
find . -type l -print | grep LINK  | xargs -n1 rm
find . -type f -print | grep SPACE | sed 's/ /\\ /' | xargs -iAAA rm AAA
wait_dir_to_be_the_same f \.
echo "success"

# move directory

echo "checking sr_cpost move directory"
cd "$httpdocroot"/cfr
no=0
for d in `ls`; do
    if [ -d "$d" ]; then
       no=$((${no}+1))
       echo mv $d ${d}_${no}
       mv $d ${d}_${no}
    fi
done
wait_dir_to_be_the_same f \.
echo "success"
