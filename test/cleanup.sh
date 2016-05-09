
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

if [ -f .httpdocroot ]; then
   echo " you may want to rm -rf `cat .httpdocroot` "
fi

remove_if_present=".httpserverpid aaa.conf bbb.inc checksum_AHAH.py sr_http.test.anonymous"

rm -f ${remove_if_present}

sr stop

adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; }; ' ~/.config/sarra/credentials.conf`"

queues_to_delete="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues | awk ' ( NR > 1 ) { print $1; }; '`"


rm ~/.config/sarra/sarra/t_prime_dd.conf
rm ~/.config/sarra/subscribe/t_sub.conf

for q in $queues_to_delete; do
    rabbitmqadmin -H localhost -u bunnymaster -p "${adminpw}" delete queue name=$q
done
 
