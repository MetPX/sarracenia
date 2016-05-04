#../sarra/bi../sarra/sh

# credential requirements to run this self test
# access to 
#
#../sarra/sr_consumer.py
#    amqp../sarra//anonymous:anonymous@ddi.cmc.ec.gc.c../sarra/
#
#../sarra/sr_poster.py
#    amqp../sarra//guest:guest@localhos../sarra/"
#
#../sarra/sr_http.py
#    amqp../sarra//anonymous:anonymous@ddi.cmc.ec.gc.c../sarra/
#
#../sarra/sr_ftp.py
#    in credentials.conf :  declare valid ftp../sarra//...@localhos../sarra/
#
#../sarra/sr_sftp.py
#    in credentials.conf :  declare valid sftp../sarra//...@localhos../sarra/
#
#../sarra/sr_2xlog.py
#    credentials.conf    :  declare valid amqp../sarra//ddi2.edm.ec.gc.c../sarra/
#
#../sarra/sr_log2clusters.py
#    credentials.conf    :  declare valid amqp../sarra//ddi1.edm.ec.gc.c../sarra/
#                           declare valid amqp../sarra//ddi1.cmc.ec.gc.c../sarra/
#../sarra/sr_log2source.py
#    credentials.conf    :  declare valid amqp../sarra//ddi1.cmc.ec.gc.c../sarra/

# once we are sure we can read credentials and configurations, we
# can set up more elaborate tests.

echo 'sr_credentials' 
../sarra/sr_credentials.py TEST
echo $?
echo 'sr_config' 
touch aaa
../sarra/sr_config.py aaa start
rm aaa
echo $?

echo 'sr_consumer' 
echo 'reading 100 messages, this may take a while the first time... a little patience.'
echo "on subsequent passes, messages are likely to be queues"
../sarra/sr_consumer.py TEST
echo $?



echo 'sr_poster' 
../sarra/sr_poster.py TEST
echo $?
echo 'sr_file' 
../sarra/sr_file.py TEST
echo $?
echo 'sr_http' 
../sarra/sr_http.py TEST
echo $?
echo 'sr_ftp' 
../sarra/sr_ftp.py TEST
echo $?
echo 'sr_sftp' 
../sarra/sr_sftp.py TEST
echo $?
echo 'sr_2xlog' 
../sarra/sr_2xlog.py TEST
echo $?
echo 'sr_log2clusters' 
../sarra/sr_log2clusters.py TEST
echo $?
echo 'sr_log2source' 
../sarra/sr_log2source.py TEST
echo $?
echo 'sr_subscribe' 
../sarra/sr_subscribe.py TEST
echo $?
echo 'sr_instances' 
../sarra/sr_instances.py --instances 10 start
sleep 3
echo $?
../sarra/sr_instances.py --instances 10 status
echo $?
../sarra/sr_instances.py --instances 10 stop
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

