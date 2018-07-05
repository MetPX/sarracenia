#!/usr/bin/python3

"""
Fetches emails from a server using the specified protocol,
either pop3 or imap. If poll_ingest_use_ssl is equal to 
True, then it connects to the server using SSL (really TLS, 
with the most secure settings on by default)
Compatible with Python 2.7+.

poll_ingest: a sample do_poll option for sr_poll.
             connects to an email server with the provided
             credentials and posts all new messages.

usage:
        in an sr_poll configuration file:

        poll_ingest_protocol pop3|imap
        poll_ingest_use_ssl True|False 
        poll_ingest_server server 
        poll_ingest_username username
        poll_ingest_password password
        poll_ingest_port port

        IMAP over SSL uses 993, POP3 over SSL uses 995
        IMAP unsecured uses 143, POP3 unsecured uses 110

        No defaults, everything must be specified

"""

import poplib, imaplib, datetime, logging

class Fetcher(object):

        def __init__(self, parent):
                parent.declare_option( 'poll_ingest_username' )
                parent.declare_option( 'poll_ingest_password' )
                parent.declare_option( 'poll_ingest_server' )
                parent.declare_option( 'poll_ingest_port' )
                parent.declare_option( 'poll_ingest_protocol' )
                parent.declare_option( 'poll_ingest_use_ssl' )

        def perform(self, parent):
                import poplib, imaplib, datetime, logging

                # get values from sr_poll config
                logger = parent.logger
                # could also do one long 'not hasattr', but not very readable
                try:
                        odir            = parent.currentDir
                        user            = parent.poll_ingest_username[0]
                        password        = parent.poll_ingest_password[0]
                        server          = parent.poll_ingest_server[0]
                        port            = int(parent.poll_ingest_port[0])
                        protocol        = parent.poll_ingest_protocol[0]
                        ssl             = parent.poll_ingest_use_ssl[0]
                except Exception as e:
                        logger.error("Incorrect usage: {}".format(e))
                        return

                if odir[-1] != '/':
                        odir += '/'
                protocol = protocol.lower()
                ssl = ssl.lower()                

                if protocol == "imap":
                        if ssl == "true":
                                try:
                                        mailman = imaplib.IMAP4_SSL(server, port=port)
                                        mailman.login(user, password)
                                except imaplib.IMAP4.error as e:
                                        logger.error("Imaplib connection error: {}".format(e))
                                        return

                        elif ssl == "false":
                                try:
                                        mailman = imaplib.IMAP4(server, port=port)
                                        mailman.login(user, password)
                                except imaplib.IMAP4.error as e:
                                        logger.error("Imaplib connection error: {}".format(e))
                                        return

                        else: 
                                logger.error("poll_ingest_use_ssl must be one of 'True' or 'False'.")
                                return

                        # only retrieves unread mail from inbox, change these values as to your preference
                        mailman.select(mailbox='INBOX')
                        resp, data = mailman.search(None, '(UNSEEN)')
                        for index in data[0].split():
                                r, d = mailman.fetch(index, '(RFC822)')
                                msg = d[0][1].decode("utf-8", "ignore") + "\n"
                                ofile = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%f")
 
                                try:
                                        with open(odir + ofile, 'w') as f:
                                                f.write(msg)
                                        logger.info("Msg received: {}".format(odir + ofile))

                                except IOError as e:
                                        logger.error("Error writing to file: {}".format(e))
                                        return

                        mailman.close()
                        mailman.logout()

                elif protocol == "pop3":
                        if ssl == "true":
                                try:
                                        mailman = poplib.POP3_SSL(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                except poplib.error_proto as e:
                                        logger.error("Poplib connection error: {}".format(e))
                                        return

                        elif ssl == "false":
                                try:
                                        mailman = poplib.POP3(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                except poplib.error_proto as e:
                                        logger.error("Poplib connection error: {}".format(e))
                                        return
                        else:
                                logger.error("poll_ingest_use_ssl must be one of 'True' or 'False'.")
                                return

                        # only retrieves msgs that haven't triggered internal pop3 'read' flag
                        numMsgs = len(mailman.list()[1])
                        for index in range(numMsgs):
                                msg=""
                                for line in mailman.retr(index+1)[1]:
                                        msg += line.decode("utf-8", "ignore") + "\n"
                                ofile = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%f")

                                try:
                                        with open(odir + ofile, 'w') as f:
                                                f.write(msg)
                                        logger.info("Msg received: {}".format(odir + ofile))

                                except IOError as e:
                                        logger.error("Error writing to file: {}".format(e))
                                        return

                        mailman.quit()

                else:
                        logger.error("poll_ingest_protocol must be one of 'imap' or 'pop3'.")
                        return

fetcher = Fetcher(self)
self.do_poll = fetcher.perform
