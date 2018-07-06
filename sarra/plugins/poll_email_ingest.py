#!/usr/bin/python3

"""
Fetches emails from a server using the specified protocol,
either pop3 or imap. The imaplib/poplib implementations in
Python use the most secure SSL settings by default: 
PROTOCOL_TLS, OP_NO_SSLv2, and OP_NO_SSLv3.
Compatible with Python 2.7+.

poll_email_ingest: a sample do_poll option for sr_poll.
             connects to an email server with the provided
             credentials and posts all new messages.

usage:
        in an sr_poll configuration file:

        poll_email_ingest_setting [imap|pop]://[user[:password]@]host[:port]/
        poll_email_ingest_use_ssl True|False

        IMAP over SSL uses 993, POP3 over SSL uses 995
        IMAP unsecured uses 143, POP3 unsecured uses 110

        poll_email_ingest_use_ssl defaults to True.
        Full credentials must be in credentials.conf.
        If port is not specified it'll default to the ones above based on protocol/ssl setting.

"""

import poplib, imaplib, datetime, logging
try: from sr_credentials import *
except: from sarra.sr_credentials import *

class Fetcher(object):

        def __init__(self, parent):
                parent.declare_option( 'poll_email_ingest_setting' )
                parent.declare_option( 'poll_email_ingest_use_ssl' )

        def perform(self, parent):
                import poplib, imaplib, datetime, logging
                logger = parent.logger
                odir = parent.currentDir

                if not hasattr(parent, 'poll_email_ingest_setting'): return
                ssl = "true" if not hasattr(parent, 'poll_email_ingest_use_ssl') else parent.poll_email_ingest_use_ssl[0].lower()
            
                ok, details = parent.credentials.get(parent.poll_email_ingest_setting[0])
                if ok: 
                        setting         = details.url
                        user            = setting.username
                        password        = setting.password
                        server          = setting.hostname
                        protocol        = setting.scheme.lower() 
                        port            = setting.port
                else:
                        logger.error("Invalid credentials")
                        return

                if odir[-1] != '/':
                        odir += '/'

                if not port:
                        if ssl == "true" and protocol == "imap":
                                port = 993
                        elif ssl == "true" and protocol == "pop":
                                port = 995
                        elif ssl == "false" and protocol == "imap":
                                port = 143
                        else:
                                port = 110

                if protocol == "imap":
                        if ssl == "true":
                                try:
                                        mailman = imaplib.IMAP4_SSL(server, port=port)
                                        mailman.login(user, password)
                                except imaplib.IMAP4.error as e:
                                        logger.error("Imaplib connection error: {}".format(e))
                                        return

                        else:
                                try:
                                        mailman = imaplib.IMAP4(server, port=port)
                                        mailman.login(user, password)
                                except imaplib.IMAP4.error as e:
                                        logger.error("Imaplib connection error: {}".format(e))
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

                elif protocol == "pop":
                        if ssl == "true":
                                try:
                                        mailman = poplib.POP3_SSL(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                except poplib.error_proto as e:
                                        logger.error("Poplib connection error: {}".format(e))
                                        return

                        else:
                                try:
                                        mailman = poplib.POP3(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                except poplib.error_proto as e:
                                        logger.error("Poplib connection error: {}".format(e))
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
                        logger.error("poll_email_ingest_setting proto must be one of 'imap' or 'pop'.")
                        return

fetcher = Fetcher(self)
self.do_poll = fetcher.perform
