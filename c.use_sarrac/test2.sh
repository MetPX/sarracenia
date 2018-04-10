
mkdir -p pathreal/toto 2> /dev/null
ln -s pathreal pathsym 2> /dev/null

if [ ! "${SR_POST_CONFIG}" ]; then
   export SR_POST_CONFIG=`pwd`/test_post.conf
   export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0
   exec $0
fi

cat > pathsym/toto/myfile << EOF
a
b
c
d
EOF

rm  pathsym/toto/myfile
