

if [ ! "${SR_POST_CONFIG}" ]; then
   export SR_POST_CONFIG=`pwd`/test_post.conf
   export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0
   exec $0
fi

set -x

echo "FIXME: KNOWN ISSUE redirection close does not get posted!"
bash -c 'echo "hoho" >>~/test/hoho'

truncate --size=2 ~/test/hoho

/usr/bin/python2.7 pyiotest
grep lovely pyiotest
cp libsrshim.c ~/test/hoho_my_darling.txt
touch hihi
ln -s hoho haha
mv haha hihi
ln hihi hoohoo
mv ~/test/hoho_my_darling.txt ~/test/hoho2.log
rm hihi

rm ~/test/hoho2.log
mkdir dirone
echo "fileone" >>dirone/fileone
mkdir dirone/dirtwo
echo "filetwo" >>dirone/dirtwo/filetwo
mv dirone dirthree
rm -rf dirthree
rm hoho hoohoo
