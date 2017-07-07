#!/bin/bash

function application_dirs {
python3 << EOF
import appdirs
print('export CONFDIR=%s'%appdirs.user_config_dir('sarra','science.gc.ca'))
print('export LOGDIR=%s'%appdirs.user_log_dir('sarra','science.gc.ca'))
print('export CACHEDIR=%s'%appdirs.user_cache_dir('sarra','science.gc.ca'))
EOF
}

eval `application_dirs`

echo $CACHEDIR
echo $CONFDIR
echo $LOGDIR



sr stop


echo "cleanup"
if [ -f .httpserverpid ]; then
   httpserverpid="`cat .httpserverpid`"
   if [ "`ps ax | awk ' $1 == '${httpserverpid}' { print $1; }; '`" ]; then
       kill $httpserverpid
       echo "web server stopped."
   else
       echo "no web server found running"
   fi
fi

remove_if_present=".httpserverpid aaa.conf bbb.inc checksum_AHAH.py sr_http.test.anonymous"

rm -f ${remove_if_present}


adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; exit; }; ' $CONFDIR/credentials.conf`"

queues_to_delete="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues | awk ' ( NR > 1 ) { print $1; }; '`"


for q in $queues_to_delete; do
    rabbitmqadmin -H localhost -u bunnymaster -p "${adminpw}" delete queue name=$q
done
 
templates="`cd flow_templates; ls */*.py */*.conf */*.inc`"
for cf in ${templates}; do
    echo "removing $cf"
    rm $CONFDIR/${cf}
done

#for cf in $CONFDIR/shovel/rr*.conf  ; do
#    rm ${cf}
#done


if [ -f .httpdocroot ]; then
   echo " you may want to rm -rf `cat .httpdocroot` "
fi

echo " you may want to rm -rf "$LOGDIR"/* "$CACHEDIR"/watch/*/* "

