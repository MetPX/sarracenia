"""

Description
	Posts any new emails from an email server, connected to using
	the specified protocol, either pop3 or imap. The imaplib/poplib
	implementations in Python use the most secure SSL settings by
	default: PROTOCOL_TLS, OP_NO_SSLv2, and OP_NO_SSLv3.

	connects to an email server with the provided
	credentials and posts all new messages by their msg ID.

Options

	poll_mail_filename_option
		Select filename type based on what the email returns.
		`subject` -> Use the subject in the destination filename
		`msgid` -> Use the msgid in the destination filename

Usage

    In ``credentials.conf``
        [imap|imaps|pop|pops]://[user[:password]@]host[:port]/
        IMAP over SSL uses 993, POP3 over SSL uses 995
        IMAP unsecured uses 143, POP3 unsecured uses 110
        Full credentials must be in credentials.conf.
        If port is not specified it'll default to the ones above based on protocol/ssl setting.

    In a configuration file
        callback poll.mail

        This posts what messages are available. A separate component is needed to
        download the message, which would need:

             callback download.mail_ingest

        to process these posts.

"""

import datetime
import email
import imaplib
import logging
import poplib
import sarracenia
from sarracenia.flowcb import FlowCB

from urllib.parse import unquote

logger = logging.getLogger(__name__)


class Mail(FlowCB):
    def __init__(self, options):

        super().__init__(options,logger)
        logger.info("init")

        self.o.add_option('poll_mail_filename_option', kind='str', default_value='subject')

    def attribute_filename(self, msg):
        # Attribute filename based on specified option
        if self.o.poll_mail_filename_option == 'msgid':
            return email.message_from_string(msg).get('Message-ID').strip('<>')
        else:
            msg_subject = email.message_from_string(msg).get('Subject')
            return msg_subject + datetime.datetime.now().strftime('%Y%m%d_%H%M%s_%f')


    def poll(self) -> list:

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
            logger.warning(f"{setting} {user} {password} {server} {protocol} {port}")
        else:
            logger.error("pollUrl: invalid credentials")
            return []

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
                        f"imaplib connection error: {e}")
                    return []

            elif protocol == "imap":
                try:
                    mailman = imaplib.IMAP4(server, port=port)
                    mailman.login(user, password)
                except imaplib.IMAP4.error as e:
                    logger.error(
                        f"imaplib connection error: {e}")
                    return []
            else:
                logger.error(f"unknown protocol: {protocol}")
                return []
            # only retrieves unread mail from inbox, change these values as to your preference
            mailman.select(mailbox='INBOX')
            resp, data = mailman.search(None, '(UNSEEN)')
            # self.metrics['transferRxBytes'] += len(data)
            for index in data[0].split():
                r, d = mailman.fetch(index, '(RFC822)')
                msg = d[0][1].decode("utf-8", "ignore") + "\n"

                msg_filename = self.attribute_filename(msg)
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
                    logger.debug("connection started")
                except poplib.error_proto as e:
                    logger.error(
                        f"pop3 connection error: {e}")
                    return []

            elif protocol == "pop":
                try:
                    mailman = poplib.POP3(server, port=port)
                    mailman.user(user)
                    mailman.pass_(password)
                except poplib.error_proto as e:
                    logger.error(
                        f"pop3 connection error: {e}")
                    return []
            else:
                return []
            # only retrieves msgs that haven't triggered internal pop3 'read' flag
            numMsgs = len(mailman.list()[1])
            for index in range(numMsgs):
                msg = ""
                for line in mailman.retr(index + 1)[1]:
                    # self.metrics['transferRxBytes'] += len(line)
                    msg += line.decode("utf-8", "ignore") + "\n"
                msg_filename = self.attribute_filename(msg)
                m = sarracenia.Message.fromFileInfo(msg_filename, self.o)
                gathered_messages.append(m)

            mailman.quit()

        else:
            logger.error(
                "pollUrl protocol must be one of 'imap/imaps' or 'pop/pops'."
            )
        return gathered_messages
