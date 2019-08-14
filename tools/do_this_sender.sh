#!/bin/bash

p=$1

echo
echo $p

RDM=$RANDOM

SENDER=''
echo     > /tmp/$RDM
echo $p >> /tmp/$RDM
echo    >> /tmp/$RDM

grep delivered ~/convert/log/sundew/*/*${p}*.log* | awk '{print $7}' | sed 's/^.*\///' | sed 's/:2019080.......$//' | sed 's/:$//' > /tmp/delivered

echo NB_OF_DELIVERED_PER_DAY=`cat /tmp/delivered | wc -l` >> /tmp/$RDM
echo

# make a working directory for that sender

pdir=`echo $p | sed 's/-/_/g' | tr '[a-z]' '[A-Z]'`
mkdir $pdir
cd $pdir

# make sender directory

mkdir  sender

# place sender config

cp ~/convert/config/sundew/etc/tx/${p}.conf sender

# place two levels of include (should be enough)

IC1=`cat sender/${p}.conf | grep '^include' | awk '{print $2}'`
IC2=''

if [[ ! -z "$IC1" ]]; then
   for INC in $IC1; do
       cp ~/convert/config/sundew/etc/tx/$INC sender
       IC=`cat sender/$INC | grep '^include' | awk '{print $2}'`
       if [[ ! -z "$IC" ]]; then
          IC2=$IC2' '$IC
       fi
   done
fi

if [[ ! -z "$IC2" ]]; then
   for INC in $IC2; do
       cp ~/convert/config/sundew/etc/tx/$INC sender
   done
fi

# scripts to plugins

SC=`cat sender/* | grep '\.py$' | grep -v '^#' | sed 's/^.*=//' | sed 's/^.* //'| sort -u`

if [[ ! -z "$SC" ]]; then
   mkdir plugins

   for SCR in $SC; do
       cp ~/convert/config/sundew/etc/scripts/$SCR plugins
   done
fi

# files implied

echo
echo "FILES IMPLIED"
cd sender
ls *
cd ..
if [[ -d plugins ]]; then
   cd plugins
   ls *
   cd ..
fi
echo

# Now try to change accept/reject and add subtopic

echo "finding subtopic ..."
echo "routing a day of ddsr products to pxSender $p"
echo

~/convert/tools/sundew_routing_2_sarra_subtopic.py \
  ~/convert/config/sundew/etc/*Routing.conf \
  ~/convert/data/ddsr.20190804 `pwd`/sender/${p}.conf | tee -a /tmp/$RDM

mv /tmp/$RDM INFO_$p

# run the pxsender_2_sarra.sh script

~/convert/tools/pxsender_2_sarra.sh `pwd`/sender/${p}

