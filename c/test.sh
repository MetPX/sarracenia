export SR_POST_CONFIG=`pwd`/test_post.conf
export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0

set -x
python pyiotest
cp libsrshim.c ~/test/hoho_my_darling.txt
touch hihi
ln -s hoho haha
mv haha hihi
rm hihi
