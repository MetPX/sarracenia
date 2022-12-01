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

        pollUrl [imap|imaps|pop|pops]://[user[:password]@]host[:port]/

        IMAP over SSL uses 993, POP3 over SSL uses 995
        IMAP unsecured uses 143, POP3 unsecured uses 110

        Full credentials must be in credentials.conf.
        If port is not specified it'll default to the ones above based on protocol/ssl setting.

"""

import datetime
import email
import imaplib
import logging
import poplib
import sarracenia
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Mail(FlowCB):
    def __init__(self, options):

        self.o = options
        logger.info("poll_email_ingest init")

    def poll(self):

        logger.debug("start")

        ok, details = self.o.credentials.get(self.o.pollUrl)
        if ok:
            setting = details.url
            user = setting.username
            password = setting.password
            server = setting.hostname
            protocol = setting.scheme.lower()
            port = setting.port
            logger.debug("pollUrl valid")
        else:
            logger.error("pollUrl: invalid credentials")
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

        gathered_messages = []
        if "imap" in protocol:
            if protocol == "imaps":
                try:
                    mailman = imaplib.IMAP4_SSL(server, port=port)
                    mailman.login(user, password)
                except imaplib.IMAP4.error as e:
                    logger.error(
                        "poll_email_ingest imaplib connection error: {}".
                        format(e))
                    return

            elif protocol == "imap":
                try:
                    mailman = imaplib.IMAP4(server, port=port)
                    mailman.login(user, password)
                except imaplib.IMAP4.error as e:
                    logger.error(
                        "poll_email_ingest imaplib connection error: {}".
                        format(e))
                    return
            else:
                return
            # only retrieves unread mail from inbox, change these values as to your preference
            mailman.select(mailbox='INBOX')
            resp, data = mailman.search(None, '(UNSEEN)')
            for index in data[0].split():
                r, d = mailman.fetch(index, '(RFC822)')
                msg = d[0][1].decode("utf-8", "ignore") + "\n"
                msg_subject = email.message_from_string(msg).get('Subject')
                msg_filename = msg_subject + datetime.datetime.now().strftime(
                    '%Y%m%d_%H%M%s_%f')
                m = sarracenia.Message.fromFileInfo(msg_filename, self.o)
                gathered_messages.append(m)

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
                    logger.error(
                        "poll_email_ingest pop3 connection error: {}".format(
                            e))
                    return

            elif protocol == "pop":
                try:
                    mailman = poplib.POP3(server, port=port)
                    mailman.user(user)
                    mailman.pass_(password)
                except poplib.error_proto as e:
                    logger.error(
                        "poll_email_ingest pop3 connection error: {}".format(
                            e))
                    return
            else:
                return
            # only retrieves msgs that haven't triggered internal pop3 'read' flag
            numMsgs = len(mailman.list()[1])
            for index in range(numMsgs):
                msg = ""
                for line in mailman.retr(index + 1)[1]:
                    msg += line.decode("utf-8", "ignore") + "\n"
                msg_subject = email.message_from_string(msg).get('Subject')
                msg_filename = msg_subject + datetime.datetime.now().strftime(
                    '%Y%m%d_%H%M%s_%f')
                m = sarracenia.Message.fromFileInfo(msg_filename, self.o)
                gathered_messages.append(m)

            mailman.quit()

        else:
            logger.error(
                "poll_email_ingest pollUrl protocol must be one of 'imap/imaps' or 'pop/pops'."
            )
        return gathered_messages
