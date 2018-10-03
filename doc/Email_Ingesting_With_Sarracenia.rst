=======================================
Email Ingesting with Sarracenia
=======================================

Email is an easy way to route data between servers. Using the Post Office Protocol (POP3) and
Internet Message Access Protocol (IMAP), email files can be disseminated through Sarracenia 
by extending the polling anddownloading functions.

.. contents::

Polling
-------
Extending Polling Protocols
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Out of the box, Sarracenia supports polling destinations with HTTP/HTTPS and SFTP/FTP protocols. Other
protocols can be supported by creating a *do_poll* plugin, with the new protocol registered at the 
bottom of the plugin file in the form of a **registered_as** plugin::

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
retrieving it with POP3 it will be marked as read, and it won't be picked up on further polls. Python's
*poplib* offers further options like deleting the file after it's been read, but IMAP offers more mail
management options like moving between folders and generating more complex queries. IMAP also allows
more than one client to connect to a mailbox at the same time, and supports tracking message flags like
whether the message is read/unread, replied to/not yet replied to, or deleted/still in the inbox. The 
example polling plugin,
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

	FIXME: run this and include output

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

	FIXME: run this and include output

Use Case
--------
The email ingest plugins were developed for the short burst data use case, where information would 
arrive in message attachments. Previously the emails were downloaded with a fetchmail script, and a 
cronjob would run every once in a while to detect and decode new files and their email attachments, 
to be used for further data processing. Sarracenia now takes care of all the steps of data routing, 
and allows this process to be more parallelizable.
