#!/bin/ksh

#This self test script is a work in progress and will be improved

file_origin=/tmp/sr_sarra
file_destination=/tmp/sr_sarra/incoming_files

#For the use of test 4 and 5 only
#doc_root=/tmp
#initial_path=sr_sarra

if [ ! -d $file_origin ]; then
	mkdir $file_origin
fi

if [ ! -d $file_destination ]; then
	mkdir $file_destination
fi


sender=pfd
host=localhost

#Exchanges and credentials
exchange=tsender_src
credentials=TestSENDer

#Files to use
sender_file=sender_file.txt
placeholder=placeholder.txt

cat << EOF > $file_origin/$sender_file
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
EOF

cat << EOF > $file_origin/$placeholder
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
EOF


cp ./templates/sender/test1.conf $file_origin/sender_test1.conf
cp ./templates/sender/test2.conf $file_origin/sender_test2.conf
cp ./templates/sender/test3.conf $file_origin/sender_test3.conf
cp ./templates/sender/test4.conf $file_origin/sender_test4.conf
cp ./templates/sender/test5.conf $file_origin/sender_test5.conf

chmod 777 $file_origin/$sender_file
chmod 777 $file_origin/$placeholder

#Checks if the file exists in final destination using sender, PASSED if exists, FAILED if not 
function check_destination {

	#TODO check contents of file using diff
        initial_dest=$file_origin/$sender_file
        final_dest=$file_destination/$sender_file

        diff $initial_dest $final_dest >/dev/null 2>&1
        if [ $? -eq 0 ]; then
                echo "PASSED"
                rm $file_destination/$sender_file
		return 0
        else
                echo "FAILED"
		return 1
        fi
}

#This test checks to see if sr_sender will send a file to a location
#when instead of specifying directory, the post_document_root, 
#post_exchange and post_broker are specified.
function test_post_doc {

        sr_sender --reset $file_origin/sender_test1.conf start > /dev/null 2>&1
	sleep 3
        sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file 			\
		-to test_cluster > /dev/null 2>&1		\
		/
	sleep 3
	check_destination "1"
	RET=$?
	sr_sender $file_origin/sender_test1.conf stop > /dev/null 2>&1
	return $RET
}

#This test checks to see if sr_sender will properly disassemble a file
#into parts, send these parts to the specified destination, and
#reassemble them. The test is a pass if the contents of the sent file
#matches the content of the file in the original location. Part size
#in this case is 32 Bytes
function test_parts {

	sr_sender --reset $file_origin/sender_test2.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file 		\
		-to test_cluster > /dev/null 2>&1		\
		--parts i,32B					\
		/
        sleep 3
	check_destination "2"
	RET=$?	
        sr_sender $file_origin/sender_test2.conf stop > /dev/null 2>&1
	return $RET
}

#This test checks to see if the plugin scripts work properly when using
#sr_sender. The plugin scripts will move or manipulate files and the
#self test will check if the sent file will match the file in the original
#location.
function test_plugins {

	#Using on_message script
	sr_sender --reset $file_origin/sender_test${1}.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file 		\
		-to test_cluster  				\
		--flow "$file_destination" > /dev/null 2>&1		\
		/
	sleep 3
	check_destination "${1}"
	RET=$?
	sr_sender $file_origin/sender_test${1}.conf stop > /dev/null 2>&1
	return $RET
}

#function test4 {
#
#	echo "Testing do_send plugin"
#	#Using do_send script
#	sr_sender --reset $file_origin/sender_test4.conf start > /dev/null 2>&1
#	sleep 3
#	sr_post -b amqp://$exchange:$credentials@$host/ 	\
#		-u sftp://$sender@$host/ 			\
#		-p $file_origin/$sender_file 		\
#		-to test_cluster > /dev/null 			\
#		--flow "$file_destination" > /dev/null 2>&1			\
#		/
#	sleep 3
#	check_destination "4"
#	RET=$?
#	sr_sender $file_origin/sender_test4.conf stop > /dev/null 2>&1
#	return $RET
#}
#
#function test5 {
#
#	echo "Testing on_post plugin"
#	#Using on_post script
#	sr_sender --reset $file_origin/sender_test5.conf start > /dev/null 2>&1
#	sleep 3
#	sr_post -b amqp://$exchange:$credentials@$host/ 	\
#		-u sftp://$sender@$host/ 			\
#		-p $file_origin/$placeholder 			\
#		-to test_cluster > /dev/null 2>&1		\
#		--flow "$file_destination"     			\
#		/
#	sleep 3
#	check_destination "5"
#	RET=$?
#	sr_sender $file_origin/sender_test5.conf stop > /dev/null 2>&1
#	return $RET
#}

RESULT=0
# Run tests
echo "Sending file by using post_document_root instead of directory..."
test_post_doc
if [ $? -eq 1 ]; then
	RESULT=1
fi
echo "Sending file by parts to destination and reassembling file..."
test_parts
if [ $? -eq 1 ]; then
        RESULT=1
fi
echo "Testing on_message plugin script..."
test_plugins "3"
if [ $? -eq 1 ]; then
        RESULT=1
fi
echo "Testing do_send plugin script..."
test_plugins "4"
if [ $? -eq 1 ]; then
        RESULT=1
fi
echo "Testing on_post plugin script..."
test_plugins "5"
if [ $? -eq 1 ]; then
        RESULT=1
fi

rm $file_origin/$placeholder
rm $file_origin/$sender_file
rm -r $file_origin

exit $RESULT 
