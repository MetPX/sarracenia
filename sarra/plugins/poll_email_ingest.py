#!/usr/bin/python3

"""
Posts any new emails from an email server, connected to using 
the specified protocol, either pop3 or imap. The imaplib/poplib 
implementations in Python use the most secure SSL settings by 
default: PROTOCOL_TLS, OP_NO_SSLv2, and OP_NO_SSLv3.
Compatible with Python 2.7+.

poll_email_ingest: a sample do_poll option for sr_poll.
             connects to an email server with the provided
             credentials and posts all new messages by their msg ID.

usage:
        in an sr_poll configuration file:

        destination [imap|imaps|pop|pops]://[user[:password]@]host[:port]/

        IMAP over SSL uses 993, POP3 over SSL uses 995
        IMAP unsecured uses 143, POP3 unsecured uses 110

        Full credentials must be in credentials.conf.
        If port is not specified it'll default to the ones above based on protocol/ssl setting.

"""

import poplib, imaplib, datetime, logging, email
try: from sr_credentials import *
except: from sarra.sr_credentials import *

class Fetcher(object):

        def __init__(self, parent):
                parent.logger.info("poll_email_ingest init")

        def do_poll(self, parent):
                import poplib, imaplib, datetime, logging, email

                logger = parent.logger
                logger.debug("poll_email_ingest do_poll")
            
                ok, details = parent.credentials.get(parent.destination)
                if ok: 
                        setting         = details.url
                        user            = setting.username
                        password        = setting.password
                        server          = setting.hostname
                        protocol        = setting.scheme.lower() 
                        port            = setting.port
                        logger.debug("poll_email_ingest destination valid")
                else:
                        logger.error("poll_email_ingest destination: invalid credentials")
                        return

                if not port:
                        if protocol == "imaps":
                                port = 993
                        elif protocol == "pops":
                                port = 995
                        elif protocol == "imap":
                                port = 143
                        else:
                                port = 110

                if "imap" in protocol:
                        if protocol == "imaps":
                                try:
                                        mailman = imaplib.IMAP4_SSL(server, port=port)
                                        mailman.login(user, password)
                                except imaplib.IMAP4.error as e:
                                        logger.error("poll_email_ingest imaplib connection error: {}".format(e))
                                        return

                        elif protocol == "imap":
                                try:
                                        mailman = imaplib.IMAP4(server, port=port)
                                        mailman.login(user, password)
                                except imaplib.IMAP4.error as e:
                                        logger.error("poll_email_ingest imaplib connection error: {}".format(e))
                                        return
                        else: return
                        # only retrieves unread mail from inbox, change these values as to your preference
                        mailman.select(mailbox='INBOX')
                        resp, data = mailman.search(None, '(UNSEEN)')
                        for index in data[0].split():
                                r, d = mailman.fetch(index, '(RFC822)')
                                msg = d[0][1].decode("utf-8", "ignore") + "\n"
                                msg_subject = email.message_from_string(msg).get('Subject')
                                msg_filename = msg_subject + datetime.datetime.now().strftime('%Y%m%d_%H%M%s_%f')

                                parent.msg.new_baseurl = parent.destination
                                parent.to_clusters = 'ALL'
                                parent.msg.new_file = msg_filename
                                parent.msg.sumflg = 'z'
                                parent.msg.sumstr = 'z,d'
                                parent.post(parent.exchange,parent.msg.new_baseurl,parent.msg.new_file,parent.to_clusters,parent.msg.partstr,parent.msg.sumstr)

                        mailman.close()
                        mailman.logout()
                        
                elif "pop" in protocol:
                        if protocol == "pops":
                                try:
                                        mailman = poplib.POP3_SSL(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                        logger.debug("poll_email_ingest connection started")
                                except poplib.error_proto as e:
                                        logger.error("poll_email_ingest pop3 connection error: {}".format(e))
                                        return

                        elif protocol == "pop":
                                try:
                                        mailman = poplib.POP3(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                except poplib.error_proto as e:
                                        logger.error("poll_email_ingest pop3 connection error: {}".format(e))
                                        return
                        else: return
                        # only retrieves msgs that haven't triggered internal pop3 'read' flag
                        numMsgs = len(mailman.list()[1])
                        for index in range(numMsgs):
                                msg=""
                                for line in mailman.retr(index+1)[1]:
                                        msg += line.decode("utf-8", "ignore") + "\n"
                                msg_subject = email.message_from_string(msg).get('Subject')
                                msg_filename = msg_subject + datetime.datetime.now().strftime('%Y%m%d_%H%M%s_%f')
                                parent.msg.new_baseurl = parent.destination
                                parent.msg.new_file = msg_filename
                                parent.to_clusters = 'ALL'
                                parent.msg.sumflg = 'z'
                                parent.msg.partstr = '1,1,1,0,0'
                                parent.msg.sumstr = 'z,d'
                                parent.post(parent.exchange,parent.msg.new_baseurl,parent.msg.new_file,parent.to_clusters,parent.msg.partstr,parent.msg.sumstr)

                        mailman.quit()

                else:
                        logger.error("poll_email_ingest destination protocol must be one of 'imap/imaps' or 'pop/pops'.")
                        return

def registered_as(self):
        return ['imap','imaps','pop','pops']

fetcher = Fetcher(self)
self.do_poll = fetcher.do_poll
