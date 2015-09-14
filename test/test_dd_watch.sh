#!/bin/ksh

cat << EOF > toto
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
7 123456789abcde
8 123456789abcde
9 123456789abcde
a 123456789abcde
b 123456789abcde
c 123456789abcde
d 123456789abcde
e 123456789abcde

EOF

echo dd_watch -u file:${PWD}/
echo touch ./toto

../sara/dd_watch.py -u file:${PWD}/ &
PID=$!
sleep 2
touch ./toto
sleep 2
kill -9 $PID

echo

echo dd_watch -u file:${PWD}/ -e IN_CLOSE_WRITE
echo rm ./toto

../sara/dd_watch.py -u file:${PWD}/ -e IN_CLOSE_WRITE &
PID=$!
sleep 2
touch ./toto
sleep 2
kill -9 $PID

echo



echo dd_watch -u file:${PWD}/
echo rm ./toto

cp toto toto2
../sara/dd_watch.py -u file:${PWD}/ &
PID=$!
sleep 2
rm ./toto
sleep 2
kill -9 $PID

echo

echo dd_watch -u file:${PWD}/ -e IN_DELETE
echo rm ./toto

mv toto2 toto
../sara/dd_watch.py -u file:${PWD}/ -e IN_DELETE &
PID=$!
sleep 2
rm ./toto
sleep 2
kill -9 $PID

echo


