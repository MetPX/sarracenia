#!/bin/ksh

#This self test script is a work in progress and will be improved

mkdir /tmp/sr_sarra
cd /tmp/sr_sarra

sender=pfd
recipient=pfd

#Exchanges and credentials
exchange=tsender_src
credentials=TestSENDer

test_root=/tmp/sr_sarra

cat << EOF > ${test_root}/sender_file.txt
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
EOF

cat << EOF > ${test_root}/placeholder.txt
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
EOF


cp ~/src/metpx-git/sarracenia/test/templates/sender/test1.conf /tmp/sr_sarra/sender_test1.conf
cp ~/src/metpx-git/sarracenia/test/templates/sender/test2.conf /tmp/sr_sarra/sender_test2.conf
cp ~/src/metpx-git/sarracenia/test/templates/sender/test3.conf /tmp/sr_sarra/sender_test3.conf
cp ~/src/metpx-git/sarracenia/test/templates/sender/test4a.conf /tmp/sr_sarra/sender_test4a.conf
cp ~/src/metpx-git/sarracenia/test/templates/sender/test4b.conf /tmp/sr_sarra/sender_test4b.conf
cp ~/src/metpx-git/sarracenia/test/templates/sender/test4c.conf /tmp/sr_sarra/sender_test4c.conf
cp ~/src/metpx-git/sarracenia/test/templates/sender/test5.conf /tmp/sr_sarra/sender_test5.conf

chmod 777 /tmp/sr_sarra/sender_file.txt
chmod 777 /tmp/sr_sarra/placeholder.txt

#Checks if the file exists in final destination using sender, PASSED if exists, FAILED if not 
function check_destination {

	#TODO check contents of file using diff
        if [ -f /home/$recipient/.cache/tmp/sr_sarra/sender_file.txt ]; then
                echo "TEST $1 PASSED"
                rm /home/$recipient/.cache/tmp/sr_sarra/sender_file.txt
        else
                echo "TEST $1 FAILED"
                sr_sender /tmp/sr_sarra/sender_test${1}.conf stop > /dev/null 2>&1
                exit 1
        fi

}

#Protocol Tests (sftp and http)
function test1 {
	
	sr_sender --reset /tmp/sr_sarra/sender_test1.conf start > /dev/null 2>&1 

	sleep 3

	sr_post -b amqp://$exchange:$credentials@localhost/ -u sftp://$sender@localhost/ -dr /tmp -p sr_sarra/sender_file.txt -to test_cluster > /dev/null 2>&1
	
	sleep 3

	check_destination "1a"

	sleep 3

	sr_post -b amqp://$exchange:$credentials@localhost/ -u http://localhost/ -dr /tmp -p sr_sarra/sender_file.txt -to test_cluster > /dev/null 2>&1

	sleep 3

	check_destination "1b"
	
	sr_sender /tmp/sr_sarra/sender_test1.conf stop > /dev/null 2>&1

}

#Testing config without using document_root
function test2 {
	
        sr_sender --reset /tmp/sr_sarra/sender_test2.conf start > /dev/null 2>&1

	sleep 3

        sr_post -b amqp://$exchange:$credentials@localhost/ -u sftp://$sender@localhost/ -p /tmp/sr_sarra/sender_file.txt -to test_cluster > /dev/null 2>&1

	sleep 3

	check_destination "2"

	sr_sender /tmp/sr_sarra/sender_test2.conf stop > /dev/null 2>&1

}

#Testing config without using post_document_root
function test3 {

	sr_sender --reset /tmp/sr_sarra/sender_test3.conf start > /dev/null 2>&1
	
	sleep 3

	sr_post -b amqp://$exchange:$credentials@localhost/ -u sftp://$sender@localhost/ -p /tmp/sr_sarra/sender_file.txt -to test_cluster > /dev/null 2>&1

        sleep 3

	check_destination "3"	

        sr_sender /tmp/sr_sarra/sender_test3.conf stop > /dev/null 2>&1

}

#Testing config files with plugin scripts do_send, on_message and on_post
function test4 {

	sr_sender --reset /tmp/sr_sarra/sender_test4a.conf start > /dev/null 2>&1

	sleep 3

	sr_post -b amqp://$exchange:$credentials@localhost/ -u sftp://$sender@localhost/ -dr /tmp -p sr_sarra/placeholder.txt -to test_cluster > /dev/null 2>&1

	sleep 3

	check_destination "4a"

	sr_sender /tmp/sr_sarra/sender_test4a.conf stop > /dev/null 2>&1

	sr_sender --reset /tmp/sr_sarra/sender_test4b.conf start > /dev/null 2>&1

	sleep 3

	sr_post -b amqp://$exchange:$credentials@localhost/ -u sftp://$sender@localhost/ -dr /tmp -p sr_sarra/sender_file.txt -to test_cluster > /dev/null 2>&1

	sleep 3

	check_destination "4b"

	sr_sender /tmp/sr_sarra/sender_test4b.conf stop > /dev/null 2>&1

	sr_sender --reset /tmp/sr_sarra/sender_test4c.conf start > /dev/null 2>&1

	sleep 3

	sr_post -b amqp://$exchange:$credentials@localhost/ -u sftp://$sender@localhost/ -dr /tmp -p sr_sarra/placeholder.txt -to test_cluster > /dev/null 2>&1

	sleep 3

	check_destination "4c"

	sr_sender /tmp/sr_sarra/sender_test4c.conf stop > /dev/null 2>&1
}

#Testing config by specifying the directory (for recipient) followed by, accept .*
function test5 {

	sr_sender --reset /tmp/sr_sarra/sender_test5.conf start > /dev/null 2>&1

	sleep 3

	sr_post -b amqp://$exchange:$credentials@localhost/ -u sftp://$sender@localhost/ -dr /tmp -p sr_sarra/sender_file.txt -to test_cluster > /dev/null 2>&1

	sleep 3

	check_destination "5"

	sr_sender /tmp/sr_sarra/sender_test5.conf stop > /dev/null 2>&1
}

# Run tests
echo "Running Self Test 1 for sr_sender:"
test1
echo "Self Test 1 Completed"
echo "Running Self Test 2 for sr_sender:"
test2
echo "Self Test 2 Completed"
echo "Running Self Test 3 for sr_sender:"
test3
echo "Self Test 3 Completed"
echo "Running Self Test 4 for sr_sender:"
test4
echo "Self Test 4 Completed"
echo "Running Self Test 5 for sr_sender:"
test5
echo "Self Test 5 Completed"

rm /tmp/sr_sarra/placeholder.txt
rm /tmp/sr_sarra/sender_file.txt 
