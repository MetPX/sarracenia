export SR_POST_CONFIG=`pwd`/test_post.conf
export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0

#echo "ldd /usr/bin/python"
#ldd /usr/bin/python2.7

#export LD_DEBUG=bindings

export SRSHIMDEBUG=lala
set -x
/usr/bin/python2.7 pyiotest
cp libsrshim.c ~/test/hoho_my_darling.txt
touch hihi
ln -s hoho haha
mv haha hihi
rm hihi
