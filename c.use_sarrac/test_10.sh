
if [ ! "${SR_POST_CONFIG}" ]; then

cat > ./TOTO <<EOF
SXCN03 CWEG 272000
SXCN40 KWAL 271835
SXCN40 KWAL 271836
======
SXCN40 KWAL 271837
SXCN40 KWAL 271838
SXUS22 KWNB 271800 RRX
SXUS23 KWNB 272000 RRP
SZAU01 AMMC 272012
SZIO01 AMMC 272012
SZPA01 AMMC 272012
SZPS01 AMMC 272012
XOCA52 KWBC 272012
XOCA52 KWBC 272012
XOCA52 KWBC 272012
EOF
   export SR_POST_CONFIG=`pwd`/test_post.conf
   export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0
   exec $0
fi

cat ./TOTO |  sed -n -e '/FPCN20/,/======/p
/FPCN21/,/======/p
/FPCN22/,/======/p
/FPCN23/,/======/p
/FPCN24/,/======/p
/FPCN25/,/======/p
/SXCN40/,/======/p
/SXCN26/,/======/p
/SXCN23/,/======/p
/SXCN3 /,/======/p
/SXCN03/,/======/p
/SXCN4 /,/======/p
/SXCN04/,/======/p
/SXCN6 /,/======/p
/SXCN06/,/======/p' >> ./tutu
