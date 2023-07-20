#!/usr/bin/python3

"""

This downloader corresponds to the poll.mail class.
Fetches emails from a server using the specified protocol,
either pop3 or imap. The imaplib/poplib implementations in
Python use the most secure SSL settings by default: 
PROTOCOL_TLS, OP_NO_SSLv2, and OP_NO_SSLv3.
Compatible with Python 2.7+.

download_email_ingest: a sample do_download option for sr_subscribe.
                        connects to an email server with the provided
                        credentials and posts all new messages.

usage:
        in an sr_subscribe configuration file:

        destination [imap|imaps|pop|pops]://[user[:password]@]host[:port]/
        do_download download_email_ingest

        IMAP over SSL uses 993, POP3 over SSL uses 995
        IMAP unsecured uses 143, POP3 unsecured uses 110

        Full credentials must be in credentials.conf.
        If port is not specified it'll default to the ones above based on protocol/ssl setting.

"""

import poplib, imaplib, datetime, logging, email, urllib

import sarracenia
from sarracenia.flowcb import FlowCB
import sarracenia.identity


logger = logging.getLogger(__name__)

class Mail_ingest(FlowCB):

        def download(self, msg) -> bool:

                #ok, details = self.o.credentials.get(parent.msg.notice.split()[1])
                ok, details = self.o.credentials.get(msg.baseUrl)
                if ok: 
                        setting         = details.url
                        user            = setting.username
                        user = urllib.parse.unquote(user)
                        password        = setting.password
                        password = urllib.parse.unquote(password)
                        server          = setting.hostname
                        protocol        = setting.scheme.lower() 
                        port            = setting.port
                else:
                        logger.error("download_email_ingest: destination has invalid credentials: %s" % msg['baseUrl'])
                        return False

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
                                        logger.error("download_email_ingest imaplib connection error: {}".format(e))
                                        return False

                        elif protocol == "imap":
                                try:
                                        mailman = imaplib.IMAP4(server, port=port)
                                        mailman.login(user, password)
                                except imaplib.IMAP4.error as e:
                                        logger.error("download_email_ingest imaplib connection error: {}".format(e))
                                        return False
                        else: return False

                        mailman.select(mailbox='INBOX')
                        resp, data = mailman.search(None, 'ALL')
                        for index in data[0].split():
                                r, d = mailman.fetch(index, '(RFC822)')
                                msg = d[0][1].decode("utf-8", "ignore") + "\n"
                                logger.info("download_email_ingest downloaded file: %s" % msg['new_dir']+'/'+msg['new_file'])
                                with open(msg['new_dir']+'/'+msg['new_file'], 'w') as f:
                                       f.write(msg)
                                       f.close()
                                if self.o.delete :
                                       mailman.store(index, '+FLAGS', '\\Deleted')

                        mailman.expunge()
                        mailman.close()
                        mailman.logout()
                        return True
                        
                elif "pop" in protocol:
                        if protocol == "pops":
                                try:
                                        mailman = poplib.POP3_SSL(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                except poplib.error_proto as e:
                                        logger.error("download_email_ingest pop3 connection error: {}".format(e))
                                        return False

                        elif protocol == "pop":
                                try:
                                        mailman = poplib.POP3(server, port=port)
                                        mailman.user(user)
                                        mailman.pass_(password)
                                except poplib.error_proto as e:
                                        logger.error("download_email_ingest pop3 connection error: {}".format(e))
                                        return False
                        else: return False
                        # only retrieves msgs that haven't triggered internal pop3 'read' flag
                        numMsgs = len(mailman.list()[1])
                        found = False
                        for index in range(numMsgs):

                                # read the email message
                                email_message=""
                                for line in mailman.retr(index+1)[1]:
                                        email_message += line.decode("utf-8", "ignore") + "\n"
                                msgid = email.message_from_string(email_message).get('Message-ID').strip('<>')

                                # if it worked, write it locally, update message as needed.
                                if msgid == msg['new_file']:                                        
                                    logger.info("download_email_ingest downloaded file: %s" % msg['new_dir']+'/'+msg['new_file'])
                                    
                                    sumalgo = sarracenia.identity.Identity.factory(self.o.identity_method)
                                    sumalgo.set_path(path)
                                    with open(msg['new_dir']+'/'+msg['new_file'], 'w') as f:
                                        sumalgo.update(email_message)
                                        f.write(email_message)
                                        f.close()
                                
                                    message['size'] = len(bytes(email_message,'utf8'))
                                    message['identity'] = { 'method': self.o.identity_method, 'value': sumalgo.value }
                                    if self.o.delete :
                                        mailman.dele(index+1)
                                    found=True
                                    break

                        if not found:
                           logger.error('message not found on server, giving up')

                        mailman.quit()
                        #v2 parent.msg.set_parts()-> sr3? msg.updatePaths( self.o, msg['new_dir'], msg['new_file'] )
                        return True

                else:
                        logger.error("download_email_ingest destination protocol must be one of 'imap/imaps' or 'pop/pops'.")
                        return False
