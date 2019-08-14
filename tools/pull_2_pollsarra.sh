#!/bin/bash

# SPECIFIC FOR DDSR.CMC.EC.GC.CA
# just make sure the resulting poll/sarra config
# corresponds to your site

conf=`echo $1| sed 's/^.*\///' | sed 's/.conf//' | sed 's/pull.//' | sed 's/-/_/g'`

mkdir poll

POLL="poll/${conf}.conf"

vi -c '1,/^type/-1w!./doc' -c q  $1
cat ./doc > $POLL

cat >> $POLL << EOF

# on doit avoir le vip de ddsr.cmc.ec.gc.ca

#vip 142.135.12.146
post_broker amqp://feeder@localhost/

# post_broker is DDSR spread the poll messages
# post_broker is localhost and all products are processed locally

#post_broker amqp://SOURCE@ddsr.cmc.ec.gc.ca/
#post_broker amqp://SOURCE@localhost/
post_exchange xs_SOURCE

# options

EOF

echo sleep `cat $1 | grep ^pull_sleep | awk '{print $2}' 2> /dev/null` >> $POLL
echo timeout `cat $1 | grep ^timeout_get | awk '{print $2}' 2> /dev/null` >> $POLL

cat >> $POLL << EOF2

# to useless... left for backward compat

to DDSR.CMC,DDI.CMC,CMC,SCIENCE,EDM

# destination

EOF2

protocol=`cat $1| grep '^protocol'    | awk '{print $2}' 2>/dev/null`
pro_host=`cat $1| grep '^host'        | awk '{print $2}' 2>/dev/null`
pro_port=`cat $1| grep '^port'        | awk '{print $2}' 2>/dev/null`
pro_user=`cat $1| grep '^user'        | awk '{print $2}' 2>/dev/null`
pro_pass=`cat $1| grep '^password'    | awk '{print $2}' 2>/dev/null`
pro_mode=`cat $1| grep '^ftp_mode'    | awk '{print $2}' 2>/dev/null`
pro_keyf=`cat $1| grep '^ssh_keyfile' | awk '{print $2}' 2>/dev/null`
pro_bina=`cat $1| grep '^binary'      | awk '{print $2}' 2>/dev/null`

credline="${protocol}://${pro_user}"
destination=$credline

if [[ ! -z "$pro_pass" ]]; then
   credline="$credline:$pro_pass"
fi

credline="$credline@$pro_host"
destination="$destination@$pro_host"

if [[ ! -z "$pro_port" ]]; then
   credline="$credline:$pro_port"
   destination="$destination:$pro_port"
fi

if [[ "$protocol" == "sftp" ]]; then
   if [[ ! -z "$pro_keyf" ]]; then
      credline="$credline ssh_keyfile=$pro_keyf"
   fi
fi

if [[ "$protocol" == "ftp" ]]; then
   if [[ ! -z "$pro_mode" ]]; then
      if   [[ "$pro_mode" == "active" ]]; then
              credline="$credline active,"
      elif [[ "$pro_mode" == "passive" ]]; then
              credline="$credline passive,"
      fi
   fi
   if [[ ! -z "$pro_bina" ]]; then
      if   [[ "$pro_bina" == "True" ]]; then
              credline="$credline binary"
      elif [[ "$pro_mode" == "False" ]]; then
              credline="$credline ascii"
      fi
   fi
fi

credline=`echo $credline | sed 's/,$//'`

echo $credline > ./credentials

echo "destination $destination"           >> $POLL
echo                                      >> $POLL
echo "# where to get the products"        >> $POLL

vi -c '/^extension/+1,$w!./dir' -c q $1
cat ./dir | sed 's/\/\//\//g' | sed 's/\/$//' >> $POLL

cat >> $POLL << EOF3

# ==============================l
# could change get for accept in sr_poll

EOF3

cat $1 | grep -v ^#  >> $POLL

#========= now sarra =============

mkdir sarra
SARRA="sarra/get_${conf}.conf"

cat ./doc > $SARRA
rm ./doc

cat >> $SARRA << EOF4

# source

instances 1

# broker is DDSR the poll messages were spreaded
# broker is localhost and all products are processed locally

#broker amqp://feeder@ddsr.cmc.ec.gc.ca/
broker amqp://feeder@localhost/
exchange   xs_SOURCE

# listen to spread the poll messages

prefetch  10
queue_name q_feeder.\${PROGRAM}.\${CONFIG}.SHARED
queue_name q_feeder.\${PROGRAM}.\${CONFIG}.\${HOSTNAME}

source_from_exchange True
accept_unmatch       False

# what to do with product

mirror        False
preserve_time False

EOF4

echo '# MG CHECK DELETE' >> $SARRA
echo '#delete' `cat $1 | grep ^delete | awk '{print $2}' 2> /dev/null` >> $SARRA
echo delete False >> $SARRA

extension=`grep extension $1 | awk '{print $2}' 2>/dev/null`

cat >> $SARRA << EOF5

# extension

header sundew_extension=$extension

EOF5


cat >> $SARRA << EOF5
# directories

directory \${PBD}/\${YYYYMMDD}/\${SOURCE}/--\${0}-- to be determined ----

EOF5

cat ./dir | grep directory | sed 's/\/\//\//g' \
          | sed 's/directory */accept .*/'     \
          | sed 's/$/.*/' >> $SARRA
rm ./dir

cat >> $SARRA << EOF6

# destination

post_broker   amqp://feeder@localhost/
post_exchange xpublic
post_base_url http://\${HOSTNAME}
post_base_dir /apps/sarra/public_data

# FOR VERIFICATION THE OPTIONS OF SUNDEW

EOF6

cat $1 | grep -v ^#  >> $SARRA
