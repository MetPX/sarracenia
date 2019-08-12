#!/bin/bash

p=$1

echo $p

SOURCE=''
echo > /tmp/aaa
echo $p >> /tmp/aaa

echo >> /tmp/aaa
INGESTED=`grep Ingested ~/convert/log/pxatx/*${p}*.log*| head -n10 | tail -n1| sed 's/^.*\///' | sed 's/:20190520......$//'`
echo INGESTED=$INGESTED >> /tmp/aaa
echo NB_OF_INGESTION_PER_DAY=`grep Ingested ~/convert/log/pxatx/*${p}*.log*| wc -l` >> /tmp/aaa
echo >> /tmp/aaa

SOURCE_REF=`grep $p ~/convert/log/pxatx/*ddsr*| grep delivered | tail -n1 | sed 's/^.*http/http/' | sed 's/:20190520.*$//'`
echo SOURCE_REF=$SOURCE_REF >> /tmp/aaa
SOURCE=`echo $SOURCE_REF | sed 's/^.*[ \/]20190520\///' | sed 's/\/.*$//'`
echo SOURCE=$SOURCE >> /tmp/aaa
echo >> /tmp/aaa

echo FX= >> /tmp/aaa
grep $INGESTED ~/convert/log/pxatx/fx*.log*| sed 's/:.*$//' | sort -u | sed 's/.*\///' >> /tmp/aaa
echo >> /tmp/aaa

echo TX= >> /tmp/aaa
grep $INGESTED ~/convert/log/pxatx/tx*.log*| sed 's/:.*$//' | sort -u | sed 's/.*\///' >> /tmp/aaa
echo >> /tmp/aaa

echo PXATX_SARRA >> /tmp/aaa
echo SR_SENDER= >> /tmp/aaa
grep $INGESTED ~/convert/log/sr_pxatx/sr_sender*| sed 's/:.*$//' | sort -u | sed 's/.*\///' >> /tmp/aaa
echo >> /tmp/aaa

ISHORT=`echo $INGESTED| sed 's/:/#/' | sed 's/^.*#//'`
echo PRESENT_IN_SARRA_CONFIG= >> /tmp/aaa
grep -His -C3 $ISHORT ~/convert/config/sarra/sender/* >> /tmp/aaa
echo >> /tmp/aaa

pdir=`echo $p | sed 's/^pull.//' | sed 's/-/_/g' | tr '[a-z]' '[A-Z]'`
mkdir $pdir
cd $pdir

cp /tmp/aaa INFO_$p
cp ~/convert/config/pxatx/etc/rx/*${p}*.conf .
~/convert/tools/pull_2_pollsarra.sh *${p}*.conf

