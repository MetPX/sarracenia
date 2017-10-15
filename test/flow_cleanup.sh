#!/bin/bash

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


sr stop


echo "cleanup trivial http server... "
if [ -f .httpserverpid ]; then
   httpserverpid="`cat .httpserverpid`"
   if [ "`ps ax | awk ' $1 == '${httpserverpid}' { print $1; }; '`" ]; then
       kill $httpserverpid
       echo "web server stopped."
   else
       echo "no web server found running"
   fi
fi

echo "cleanup trivial ftp server... "
if [ -f .ftpserverpid ]; then
   ftpserverpid="`cat .ftpserverpid`"
   if [ "`ps ax | awk ' $1 == '${ftpserverpid}' { print $1; }; '`" ]; then
       kill $ftpserverpid
       echo "ftp server stopped."
   else
       echo "no ftp server found running"
   fi
fi

remove_if_present=".ftpserverpid .httpserverpid aaa.conf bbb.inc checksum_AHAH.py sr_http.test.anonymous"

rm -f ${remove_if_present}

C_ALSO="`which sr_cpost`"


adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; exit; }; ' "$CONFDIR"/credentials.conf`"

queues_to_delete="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues | awk ' ( NR > 1 ) { print $1; }; '`"


for q in $queues_to_delete; do
    rabbitmqadmin -H localhost -u bunnymaster -p "${adminpw}" delete queue name=$q
done

exchanges_to_delete="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list exchanges | awk ' ( $1 ~ /x.*/ ) { print $1; }; '`"
for exchange in $exchanges_to_delete ; do 
   echo "deleting $exchange"
   rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv delete exchange name=${exchange} 
done

 
templates="`ls flow_templates/*/*.py flow_templates/*/*.conf flow_templates/*/*.inc`"
c_templates="`ls cflow_templates/*/*.conf cflow_templates/*/*.inc`"

if [ "$C_ALSO" ]; then
  templates="$templates $c_templates"
fi

state_files=""

for cf in ${templates}; do
    echo "removing $cf"
    newcf="`echo $cf | sed 's+.*flow_templates\/++'`"
    rm "$CONFDIR"/${newcf}
    sd="`echo $newcf | sed 's+.conf$++'`"
    state_files="${state_files} $CACHEDIR/${sd}"
done

#for cf in "$CONFDIR"/shovel/rr*.conf  ; do
#    rm ${cf}
#done


httpdr=""
if [ -f .httpdocroot ]; then
   httpdr="`cat .httpdocroot`"
fi

echo " you may want to rm -rf $httpdr $LOGDIR/* $CACHEDIR/watch/*/* ${state_files} "

