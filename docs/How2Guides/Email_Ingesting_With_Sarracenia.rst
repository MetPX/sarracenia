=======================================
Email Ingesting with Sarracenia
=======================================

Email is an easy way to route data between servers. Using the Post Office Protocol (POP3) and
Internet Message Access Protocol (IMAP), email files can be disseminated through Sarracenia 
by extending the polling and downloading functions.

.. contents::

Polling
-------
Extending Polling Protocols
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Out of the box, Sarracenia supports polling destinations with HTTP/HTTPS and SFTP/FTP protocols. Other
protocols can be supported by creating a *do_poll* plugin, with the new protocol registered at the 
bottom of the plugin file in the form of a **registered_as** function::

	def registered_as(self):
		return ['pop','pops','imap','imaps']

Now when the sr_poll instance is started up with this plugin, it would confirm the destination is
valid if the scheme is any one of the protocols returned by **registered_as**, and perform the
polling as outlined in the *do_poll* plugin. 

Implementing POP/IMAP
~~~~~~~~~~~~~~~~~~~~~
With Python's *poplib* and *imaplib* modules, the destination can be parsed and the email server
connected to as per the scheme specified. Sarracenia can extract the credentials from the destination
through its built-in classes, so no passwords need to be stored in the config file to connect. POP3
uses an internal read-flag to determine if a message has been seen or not. If a message is unread, after
retrieving it with POP3 it will be marked as read, and it won't be picked up on further polls. 
POP3 offers further options like deleting the file after it's been read, but IMAP offers more mail
management options like moving between folders and generating more complex queries. IMAP also allows
more than one client to connect to a mailbox at the same time, and supports tracking message flags like
whether the message is read/unread, replied to/not yet replied to, or deleted/still in the inbox. The 
example polling plugin
`poll_email_ingest.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_email_ingest.py>`_
only retrieves unread email in the inbox and marks them as unread after retrieving them, in both the 
POP and IMAP versions. This setting can be easily changed as per the end user's intentions. If there
are any new messages from the last time a POP/IMAP client had connected, it will then advertise the file 
based on the subject and a timestamp, where an sr_subscribe instance can receive the posted message,
connect individually to the server, and download the message to output into a file locally. A sample
configuration has been included under **examples** as `pollingest.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollingest.conf>`_. Once you edit/supply the environment variables required for the 
config to work, open a new terminal and run::

	[aspymap:~]$ sr_poll foreground pollingest.conf

If the credentials have been included correctly, and all the variables were set, the output should look 
something like this::

	[aspymap:~/sarra_test_output]$ sr_poll foreground pollingest.conf 
	2018-10-03 15:24:58,611 [INFO] poll_email_ingest init
	2018-10-03 15:24:58,617 [INFO] sr_poll pollingest startup
	2018-10-03 15:24:58,617 [INFO] log settings start for sr_poll (version: 2.18.07b3):
	2018-10-03 15:24:58,617 [INFO]  inflight=unspecified events=create|delete|link|modify use_pika=False
	2018-10-03 15:24:58,617 [INFO]  suppress_duplicates=1200 retry_mode=True retry_ttl=Nonems
	2018-10-03 15:24:58,617 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-10-03 15:24:58,617 [INFO]  heartbeat=300 default_mode=400 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-10-03 15:24:58,617 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-10-03 15:24:58,617 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report_back=True
	2018-10-03 15:24:58,617 [INFO]  post_base_dir=None post_base_url=pops://dfsghfgsdfg24@hotmail.com@outlook.office365.com:995/ sum=z,d blocksize=209715200 
	2018-10-03 15:24:58,617 [INFO]  Plugins configured:
	2018-10-03 15:24:58,617 [INFO]          on_line: Line_Mode 
	2018-10-03 15:24:58,617 [INFO]          on_html_page: Html_parser 
	2018-10-03 15:24:58,617 [INFO]          do_poll: Fetcher 
	2018-10-03 15:24:58,617 [INFO]          on_message: 
	2018-10-03 15:24:58,617 [INFO]          on_part: 
	2018-10-03 15:24:58,618 [INFO]          on_file: File_Log 
	2018-10-03 15:24:58,618 [INFO]          on_post: Post_Log 
	2018-10-03 15:24:58,618 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse 
	2018-10-03 15:24:58,618 [INFO]          on_report: 
	2018-10-03 15:24:58,618 [INFO]          on_start: 
	2018-10-03 15:24:58,618 [INFO]          on_stop: 
	2018-10-03 15:24:58,618 [INFO] log_settings end.
	2018-10-03 15:24:58,621 [INFO] Output AMQP broker(localhost) user(tsource) vhost(/)
	2018-10-03 15:24:58,621 [INFO] Output AMQP exchange(xs_tsource)
	2018-10-03 15:24:58,621 [INFO] declaring exchange xs_tsource (tsource@localhost)
	2018-10-03 15:24:59,452 [INFO] post_log notice=20181003192459.452392 pops://dfsghfgsdfg24@hotmail.com@outlook.office365.com:995/ sarra%20demo20181003_15241538594699_452125 headers={'parts': '1,1,1,0,0', 'sum': 'z,d', 'from_cluster': 'localhost', 'to_clusters': 'ALL'}
	^C2018-10-03 15:25:00,355 [INFO] signal stop (SIGINT)
	2018-10-03 15:25:00,355 [INFO] sr_poll stop

Downloading
-----------
The email messages, once retrieved, are formatted in raw Multipurpose Internet Mail Extensions (MIME) 1.0 format,
as indicated in the first header of the file. The metadata of the email is conveyed in a series of headers, one 
per line, in name:value format. This can be parsed for attachments, message bodies, encoding methods, etc. A
*do_download* plugin can implement the retrieval of the message to output to a file by registering the 
protocol in a separate module, as in the *do_poll* plugin. Once a message is received with the user/host 
advertised, it can then connect to the mail server using the destination and the credentials as specified
in ~/.config/sarra/credentials.conf and retrieve the message locally. An example of a plugin that does this
can be found under **plugins** as `download_email_ingest.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_email_ingest.py>`_. 

Decoding Contents
~~~~~~~~~~~~~~~~~
Once the email message is downloaded, an *on_file* plugin can parse the MIME formatted file and extract the attachment, usually denoted by the Content-Disposition header, or the message body/subject/address fields, to be saved as a
new file for further data refining. An example of a plugin that does this can be found under **plugins** as 
`file_email_decode.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/file_email_decode.py>`_.
A sample configuration incorporating this type of file processing is included under **examples** as 
`downloademail.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/downloademail.conf>`_.
Once the environment variables have been provided and the rabbitmq server is set up correctly, open a new 
terminal and run::

	[aspymap~]$ sr_subscribe foreground downloademail.conf

If everything was supplied correctly, the output should look something like this::

	[aspymap:~/sarra_output_test]$ sr_subscribe foreground downloademail.conf 
	2018-10-03 15:24:57,153 [INFO] download_email_ingest init
	2018-10-03 15:24:57,159 [INFO] sr_subscribe downloademail start
	2018-10-03 15:24:57,159 [INFO] log settings start for sr_subscribe (version: 2.18.07b3):
	2018-10-03 15:24:57,159 [INFO]  inflight=.tmp events=create|delete|link|modify use_pika=False
	2018-10-03 15:24:57,159 [INFO]  suppress_duplicates=False retry_mode=True retry_ttl=300000ms
	2018-10-03 15:24:57,159 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-10-03 15:24:57,159 [INFO]  heartbeat=300 default_mode=000 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-10-03 15:24:57,159 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-10-03 15:24:57,159 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report_back=True
	2018-10-03 15:24:57,159 [INFO]  Plugins configured:
	2018-10-03 15:24:57,159 [INFO]          do_download: Fetcher 
	2018-10-03 15:24:57,159 [INFO]          do_get     : 
	2018-10-03 15:24:57,159 [INFO]          on_message: 
	2018-10-03 15:24:57,159 [INFO]          on_part: 
	2018-10-03 15:24:57,159 [INFO]          on_file: File_Log Decoder 
	2018-10-03 15:24:57,159 [INFO]          on_post: Post_Log 
	2018-10-03 15:24:57,159 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse RETRY 
	2018-10-03 15:24:57,159 [INFO]          on_report: 
	2018-10-03 15:24:57,159 [INFO]          on_start: 
	2018-10-03 15:24:57,159 [INFO]          on_stop: 
	2018-10-03 15:24:57,159 [INFO] log_settings end.
	2018-10-03 15:24:57,159 [INFO] sr_subscribe run
	2018-10-03 15:24:57,160 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
	2018-10-03 15:24:57,164 [INFO] Binding queue q_tsource.sr_subscribe.downloademail.64168876.31529683 with key v02.post.# from exchange xs_tsource on broker amqp://tsource@localhost/
	2018-10-03 15:24:57,166 [INFO] reading from to tsource@localhost, exchange: xs_tsource
	2018-10-03 15:24:57,167 [INFO] report_back to tsource@localhost, exchange: xs_tsource
	2018-10-03 15:24:57,167 [INFO] sr_retry on_heartbeat
	2018-10-03 15:24:57,172 [INFO] No retry in list
	2018-10-03 15:24:57,173 [INFO] sr_retry on_heartbeat elapse 0.006333
	2018-10-03 15:25:00,497 [INFO] download_email_ingest downloaded file: /home/ib/dads/map/.cache/sarra/sarra_doc_test/sarra demo20181003_15241538594699_452125
	2018-10-03 15:25:00,500 [INFO] file_log downloaded to: /home/ib/dads/map/.cache/sarra/sarra_doc_test/sarra demo20181003_15241538594699_452125
	^C2018-10-03 15:25:03,675 [INFO] signal stop (SIGINT)
	2018-10-03 15:25:03,675 [INFO] sr_subscribe stop


Use Case
--------
The email ingest plugins were developed for the short burst data use case, where information would 
arrive in message attachments. Previously the emails were downloaded with a fetchmail script, and a 
cronjob would run every once in a while to detect and decode new files and their email attachments, 
to be used for further data processing. Sarracenia now takes care of all the steps of data routing, 
and allows this process to be more parallelizable.
