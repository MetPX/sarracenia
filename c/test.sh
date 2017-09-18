export SR_POST_CONFIG="post"
export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0

set -x
cp libsrshim.c ~/test/hoho_my_darling.txt
touch hihi
ln -s hoho haha
rm haha hihi

