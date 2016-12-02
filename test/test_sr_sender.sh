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

#File to post
sender_file=sender_file.txt

#Files created by plugin scripts
on_msg_file="on_msg_file.txt"
on_post_file="on_post_file.txt"

cat << EOF > $file_origin/$sender_file
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
EOF

chmod 777 $file_origin/$sender_file

#Checks if the file exists in final destination using sr_sender, PASSED if exists, FAILED if not 
function check_sender {

	#TODO check contents of file using diff
        initial_dest=$file_origin/$sender_file
        final_dest=$file_destination/$sender_file

	if [ -f $final_dest ]; then
		diff $initial_dest $final_dest > /dev/null 2>&1
	else
		echo "FAILED... file not sent"
		return 1
	fi		

        if [ $? -eq 0 ]; then
                rm $final_dest
                return 0
        else
                echo "FAILED... difference in content"
                rm $file_destination/$sender_file
                return 1
        fi
}

#This test checks to see if sr_sender will send a file to a location
#when instead of specifying directory, the post_document_root, 
#post_exchange and post_broker are specified.
function test_post_doc {

        sr_sender --reset ./sender/test1.conf start > /dev/null 2>&1
	sleep 3
        sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file 			\
		-to test_cluster > /dev/null 2>&1		\
		/
	sleep 3

	check_sender
	RET=$?
	if [ $RET -eq 0 ]; then
		echo "PASSED"
	fi
	sr_sender ./sender/test1.conf stop > /dev/null 2>&1
	return $RET
}

#This test checks to see if sr_sender will properly disassemble a file
#into parts, send these parts to the specified destination, and
#reassemble them. The test is a pass if the contents of the sent file
#matches the content of the file in the original location. Part size
#in this case is 32 Bytes
function test_parts {

	sr_sender --reset ./sender/test2.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file 		\
		-to test_cluster > /dev/null 2>&1		\
		--parts i,32B					\
		/
        sleep 3

	check_sender
	RET=$?
	if [ $RET -eq 0 ]; then
		echo "PASSED"
	fi	
        sr_sender ./sender/test2.conf stop > /dev/null 2>&1
	return $RET
}

#Two methods are used here. The first method is to check and see if
#sr_sender sent the target file to the new destination. The second method is
#to check if the on_message plugin creates a file on its own (should run 
#once sr_sender receives the announcement)
function test_plugin_msg {

	#Using on_message script
	sr_sender --reset ./sender/test3.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file	 		\
		-to test_cluster  				\
		--flow "$file_destination" > /dev/null 2>&1	\
		/
	sleep 3

	script_file=$file_destination/$on_msg_file

	check_sender
	RET=$?

        if [ ! -f $script_file ]; then
                echo "FAILED... on_message plugin"
                RET=1
	else
		rm $script_file
        fi

	if [ $RET -eq 0 ]; then
		echo "PASSED"
	fi
	sr_sender ./sender/test3.conf stop > /dev/null 2>&1
	return $RET
}

#When using do_send, instead of sr_sender using its own sending mechanism, 
#you create your own in the plugin script. This test will check if the do_send
#plugin sent a copy of the original file to the destination.
function test_plugin_send {

	#Using do_send script
	sr_sender --reset ./sender/test4.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file 			\
		-to test_cluster > /dev/null 			\
		--flow "$file_destination" > /dev/null 2>&1	\
		/
	sleep 3

	check_sender
	RET=$?

	if [ $RET -eq 0 ]; then
		echo "PASSED"
	fi
	sr_sender ./sender/test4.conf stop > /dev/null 2>&1
	return $RET
}

#The on_post plugin posts the sent file to the exchange. For this to work, the 
#post_document_root, post_exchange and post_broker must be specified. The 
#purpose of this test is to check if the plugin runs after the file has been
#sent to its destination and announced to the post exchange.
function test_plugin_post {

	#Using on_post script
	sr_sender --reset ./sender/test5.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@$host/ 	\
		-u sftp://$sender@$host/ 			\
		-p $file_origin/$sender_file 			\
		-to test_cluster > /dev/null 2>&1		\
		--flow "$file_destination"     			\
		/
	sleep 3

        script_file=$file_destination/$on_post_file

	check_sender
	RET=$?

        if [ ! -f $script_file ]; then
                echo "FAILED... on_post plugin"
                RET=1
        else
                rm $script_file
        fi

	if [ $RET -eq 0 ]; then
		echo "PASSED"
	fi
	sr_sender ./sender/test5.conf stop > /dev/null 2>&1
	return $RET
}

RESULT=0
#Run tests
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
test_plugin_msg
if [ $? -eq 1 ]; then
        RESULT=1
fi
echo "Testing do_send plugin script..."
test_plugin_send
if [ $? -eq 1 ]; then
        RESULT=1
fi
echo "Testing on_post plugin script..."
test_plugin_post
if [ $? -eq 1 ]; then
        RESULT=1
fi

rm $file_origin/$sender_file
rm -r $file_origin

exit $RESULT 
