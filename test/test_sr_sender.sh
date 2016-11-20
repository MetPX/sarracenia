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

#cd $file_origin

sender=pfd
#recipient=pfd

#Exchanges and credentials
exchange=tsender_src
credentials=TestSENDer

cat << EOF > $file_origin/sender_file.txt
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
EOF

cat << EOF > $file_origin/placeholder.txt
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
EOF


cp ./test_sr_sender_configs/test1.conf $file_origin/sender_test1.conf
cp ./test_sr_sender_configs/test2.conf $file_origin/sender_test2.conf
cp ./test_sr_sender_configs/test3.conf $file_origin/sender_test3.conf
cp ./test_sr_sender_configs/test4a.conf $file_origin/sender_test4a.conf
cp ./test_sr_sender_configs/test4b.conf $file_origin/sender_test4b.conf
cp ./test_sr_sender_configs/test4c.conf $file_origin/sender_test4c.conf
cp ./test_sr_sender_configs/test5.conf $file_origin/sender_test5.conf

chmod 777 $file_origin/sender_file.txt
chmod 777 $file_origin/placeholder.txt

#Checks if the file exists in final destination using sender, PASSED if exists, FAILED if not 
function check_destination {

	#TODO check contents of file using diff
        initial_dest=$file_origin/sender_file.txt
        final_dest=$file_destination/sender_file.txt

        diff $initial_dest $final_dest >/dev/null 2>&1
        if [ $? -eq 0 ]; then
                echo "TEST $1 PASSED"
                rm $file_destination/sender_file.txt
        else
                echo "TEST $1 FAILED"
                #sr_sender $file_origin/sender_test${1}.conf stop > /dev/null 2>&1
                #exit 1
        fi
}

#Protocol Tests (sftp and http)
#function test1 {
#	
#	echo "Running Self Test 1 for sr_sender:"
#	#Starting sftp test
#	sr_sender --reset $file_origin/sender_test1.conf start > /dev/null 2>&1 
#	sleep 3
#	sr_post -b amqp://$exchange:$credentials@localhost/ 	\
#		-u sftp://$sender@localhost/ 		    	\
#		-dr $doc_root 					\
#		-p $initial_path/sender_file.txt 		\
#		-to test_cluster > /dev/null 2>&1 		\
#		/
#	sleep 3
#	check_destination "1a"
#	sleep 3
#
#	#Starting http test
#	sr_post -b amqp://$exchange:$credentials@localhost/ 	\
#		-u http://localhost/ 				\
#		-dr $doc_root 					\
#		-p $initial_path/sender_file.txt 		\
#		-to test_cluster > /dev/null 2>&1		\
#		/
#	sleep 3
#	check_destination "1b"
#	sr_sender $file_origin/sender_test1.conf stop > /dev/null 2>&1
#	echo "Self Test 1 Completed"
#}

#This test checks to see if sr_sender will send a file to a location 
#with post_document_root specified rather than directory.
function test2 {

	echo "Running test by specifying post document root (Test #2)"
        sr_sender --reset $file_origin/sender_test2.conf start > /dev/null 2>&1
	sleep 3
        sr_post -b amqp://$exchange:$credentials@localhost/ 	\
		-u sftp://$sender@localhost/ 			\
		-p $file_origin/sender_file.txt 			\
		-to test_cluster > /dev/null 2>&1		\
		/
	sleep 3
	check_destination "2"
	sr_sender $file_origin/sender_test2.conf stop > /dev/null 2>&1
	echo "Self Test 2 Completed"
}

#This test checks to see if sr_sender will properly disassemble a file
#into parts, send these parts to the specified destination, and
#reassemble them. The test is a pass if the contents of the sent file
#matches the content of the file in the original location. Part size
#in this case is 32 Bytes
function test3 {

	echo "Running test by sending a file in parts (Test #3)"
	sr_sender --reset $file_origin/sender_test3.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@localhost/ 	\
		-u sftp://$sender@localhost/ 			\
		-p $file_origin/sender_file.txt 		\
		-to test_cluster > /dev/null 2>&1		\
		--parts i,32B					\
		/
        sleep 3
	check_destination "3"	
        sr_sender $file_origin/sender_test3.conf stop > /dev/null 2>&1
	echo "Self Test 3 Completed"
}

#This test checks to see if the plugin scripts work properly when using
#sr_sender. The plugin scripts will move or manipulate files and the
#self test will check if the sent file will match the file in the original
#location.
function test4 {

	echo "Running test by using the on_message plugin (Test #4a)"
	#Using on_message script
	sr_sender --reset $file_origin/sender_test4a.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@localhost/ 	\
		-u sftp://$sender@localhost/ 			\
		-p $file_origin/sender_file.txt 		\
		-to test_cluster  				\
		--flow "$file_destination" > /dev/null 2>&1		\
		/
	sleep 3
	check_destination "4a"
	sr_sender $file_origin/sender_test4a.conf stop > /dev/null 2>&1

	echo "Running test by using the do_send plugin (Test #4b)"
	#Using do_send script
	sr_sender --reset $file_origin/sender_test4b.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@localhost/ 	\
		-u sftp://$sender@localhost/ 			\
		-p $file_origin/sender_file.txt 		\
		-to test_cluster > /dev/null 2>&1		\
		--flow "$file_destination"			\
		/
	sleep 3
	check_destination "4b"
	sr_sender $file_origin/sender_test4b.conf stop > /dev/null 2>&1

#currently work in progress
	echo "Running test by using the on_post plugin (Test #4c)"
	#Using on_post script
	sr_sender --reset $file_origin/sender_test4c.conf start > /dev/null 2>&1
	sleep 3
	sr_post -b amqp://$exchange:$credentials@localhost/ 	\
		-u sftp://$sender@localhost/ 			\
		-p $file_origin/placeholder.txt 		\
		-to test_cluster > /dev/null 2>&1		\
		--flow "$file_destination"     			\
		/
	sleep 3
	check_destination "4c"
	sr_sender $file_origin/sender_test4c.conf stop > /dev/null 2>&1
	echo "Self Test 4 Completed"
}

# Run tests
#test1
test2
test3
test4

rm $file_origin/placeholder.txt
rm $file_origin/sender_file.txt
rm -r $file_origin 
