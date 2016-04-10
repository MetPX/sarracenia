#!/bin/sh

# credential requirements to run this self test
# access to 
#
#./sr_consumer.py
#    amqp://anonymous:anonymous@ddi.cmc.ec.gc.ca/
#
#./sr_poster.py
#    amqp://guest:guest@localhost/"
#
#./sr_http.py
#    amqp://anonymous:anonymous@ddi.cmc.ec.gc.ca/
#
#./sr_ftp.py
#    in credentials.conf :  declare valid ftp://...@localhost/
#
#./sr_sftp.py
#    in credentials.conf :  declare valid sftp://...@localhost/
#
#./sr_2xlog.py
#    credentials.conf    :  declare valid amqp://ddi2.edm.ec.gc.ca/
#
#./sr_log2clusters.py
#    credentials.conf    :  declare valid amqp://ddi1.edm.ec.gc.ca/
#                           declare valid amqp://ddi1.cmc.ec.gc.ca/
#./sr_log2source.py
#    credentials.conf    :  declare valid amqp://ddi1.cmc.ec.gc.ca/

echo 'sr_credentials' 
./sr_credentials.py TEST
echo $?
echo 'sr_config' 
touch aaa
./sr_config.py aaa start
rm aaa
echo $?
echo 'sr_consumer' 
./sr_consumer.py TEST
echo $?
echo 'sr_poster' 
./sr_poster.py TEST
echo $?
echo 'sr_file' 
./sr_file.py TEST
echo $?
echo 'sr_http' 
./sr_http.py TEST
echo $?
echo 'sr_ftp' 
./sr_ftp.py TEST
echo $?
echo 'sr_sftp' 
./sr_sftp.py TEST
echo $?
echo 'sr_2xlog' 
./sr_2xlog.py TEST
echo $?
echo 'sr_log2clusters' 
./sr_log2clusters.py TEST
echo $?
echo 'sr_log2source' 
./sr_log2source.py TEST
echo $?
echo 'sr_subscribe' 
./sr_subscribe.py TEST
echo $?
echo 'sr_instances' 
./sr_instances.py --instances 10 start
sleep 3
echo $?
./sr_instances.py --instances 10 status
echo $?
./sr_instances.py --instances 10 stop
echo $?

# Self test yet to be developed
# sr.py
# sr_amqp.py
# sr_log.py
# sr_message.py
# sr_poll.py
# sr_post.py
# sr_rabbit.py
# sr_sarra.py
# sr_sender.py
# sr_util.py
# sr_watch.py
# sr_winnow.py
