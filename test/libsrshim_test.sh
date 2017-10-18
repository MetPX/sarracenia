#!/bin/bash

tstdir="`pwd`"
httpdocroot=`cat $tstdir/.httpdocroot`
cd

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

# function to see if same amount of files

function wait_dir_to_be_the_same {

       COUNT=`find "$httpdocroot"/cfr -type f -print | wc -l`
       COUNT2=`find "$httpdocroot"/cfr -type l -print | wc -l`
       TCOUNT=$(($COUNT+$COUNT2))
       sleep 5
       MCOUNT=`find "$httpdocroot"/cfile -type f -print | wc -l`
       MCOUNT2=`find "$httpdocroot"/cfile -type l -print | wc -l`
       TMCOUNT=$(($MCOUNT+$MCOUNT2))
       while [ "${TMCOUNT}" != "${TCOUNT}" ]; do
             sleep 5
             MCOUNT=`find "$httpdocroot"/cfile -type f -print | wc -l`
             MCOUNT2=`find "$httpdocroot"/cfile -type l -print | wc -l`
             TMCOUNT=$(($MCOUNT+$MCOUNT2))
             echo "(${TMCOUNT} expecting ${TCOUNT})"
       done
}

# sr_subscribe initial start (no sr_cpost)

sr_cpost stop veille_f34 > /dev/null 2>&1
rm "$LOGDIR"/sr_cpost_veille_f34*.log > /dev/null

sr_subscribe stop cfile_f44 > /dev/null 2>&1
rm "$LOGDIR"/sr_subscribe_cfile_f44*.log > /dev/null

# preventive cleanup (previous runs)

find "$httpdocroot"/cfr -type f -print | grep COPY | xargs -n1 rm 2> /dev/null
find "$httpdocroot"/cfr -type l -print | grep LINK | xargs -n1 rm 2> /dev/null
find "$httpdocroot"/cfr -type f -print | grep LINK | xargs -n1 rm 2> /dev/null
find "$httpdocroot"/cfr -type f -print | grep MOVE | xargs -n1 rm 2> /dev/null

find "$httpdocroot"/cfile -type f -print | grep COPY | xargs -n1 rm 2> /dev/null
find "$httpdocroot"/cfile -type l -print | grep LINK | xargs -n1 rm 2> /dev/null
find "$httpdocroot"/cfile -type f -print | grep LINK | xargs -n1 rm 2> /dev/null
find "$httpdocroot"/cfile -type f -print | grep MOVE | xargs -n1 rm 2> /dev/null

sr_subscribe start cfile_f44 > /dev/null 2>&1

# setting up libsrshim

export SR_POST_CONFIG="${CONFDIR}/cpost/veille_f34.conf"
export LD_PRELOAD=${tstdir}/../c/libsrshim.so.1.0.0
rm /tmp/libsrshim.log.tmp 2> /dev/null

# copy 

echo "checking libsrshim copy"
find "$httpdocroot"/cfr -type f -print                | xargs -iAAA cp AAA AAA.COPY  >> /tmp/libsrshim.log.tmp 2>&1
find "$httpdocroot"/cfr -type f -print | grep -v COPY | xargs -iAAA cp AAA AAA.COPY2 >> /tmp/libsrshim.log.tmp 2>&1
wait_dir_to_be_the_same copy
echo "success"

# move 

echo "checking libsrshim move"
find "$httpdocroot"/cfr -type f -print | grep -v COPY | xargs -iAAA  mv AAA.COPY2 AAA.MOVE  >> /tmp/libsrshim.log.tmp 2>&1
wait_dir_to_be_the_same move
echo "success"

# softlink 

echo "checking libsrshim softlink"
find "$httpdocroot"/cfr -type f -print | grep -v COPY | grep -v MOVE | xargs -iAAA  ln -s AAA AAA.SLINK >> /tmp/libsrshim.log.tmp 2>&1
wait_dir_to_be_the_same softlink
echo "success"

# hardlink 

echo "checking libsrshim hardlink"
find "$httpdocroot"/cfr -type f -print | grep -v COPY | grep -v MOVE | grep -v LINK | xargs -iAAA ln AAA AAA.HLINK >> /tmp/libsrshim.log.tmp 2>&1
wait_dir_to_be_the_same hardlink
echo "success"

# hardlink 

echo "checking libsrshim remove"
find "$httpdocroot"/cfr -type f -print | grep COPY | xargs -n1 rm >> /tmp/libsrshim.log.tmp 2>&1
find "$httpdocroot"/cfr -type f -print | grep MOVE | xargs -n1 rm >> /tmp/libsrshim.log.tmp 2>&1
find "$httpdocroot"/cfr -type f -print | grep LINK | xargs -n1 rm >> /tmp/libsrshim.log.tmp 2>&1
find "$httpdocroot"/cfr -type l -print | grep LINK | xargs -n1 rm >> /tmp/libsrshim.log.tmp 2>&1
wait_dir_to_be_the_same remove
echo "success"
