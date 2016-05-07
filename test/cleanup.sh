
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
