"""
    sarracenia.flowcb.send.email.Email is an sr3 sender plugin. Once a file is 
    posted, the plugin matches the topic(what the filename begins with) to the
    file name and sends the appropriate emails.

    Usage:
      1. Need the following variables in an sr_sender config defined: file_email_to, file_email_relay
         Optionally, you can also provide a sender name/email as file_email_form:

            file_email_to AACN27 muhammad.taseer@canada.ca, test@test.com
            file_email_relay email.relay.server.ca
            file_email_from santa@canada.ca

      2. In the config file, include the following line:

            callback send.email

      3. sr_sender foreground emails.conf

    Original Author: Wahaj Taseer - June, 2019
"""

from email.message import EmailMessage
import logging
import os.path
import re
from sarracenia.flowcb import FlowCB
import smtplib

logger = logging.getLogger(__name__)


class Email(FlowCB):
    def __init__(self, options):

        super().__init__(options,logger)
        self.o.add_option('file_email_command', 'str', '/usr/bin/mail')
        self.o.add_option('file_email_to', 'list')
        self.o.add_option('file_email_from', 'str')
        self.o.add_option('file_email_relay', 'str')

    def send(self, msg):

        # have a list of email destinations...
        logger.debug("email: %s" % self.o.file_email_to)
        ipath = os.path.normpath(msg['relPath'])

        # loop over all the variables from config file, if files match, send via email
        for header in self.o.file_email_to:
            file_type, emails = header.split(' ', 1)
            emails = [x.strip(' ') for x in emails.split(',')]

            # check if the file arrived matches any email rules
            if re.search('^' + file_type + '.*', msg['new_file']):

                for recipient in emails:
                    logger.debug('sending file %s to %s' % (ipath, recipient))

                    with open(ipath) as fp:
                        emsg = EmailMessage()
                        emsg.set_content(fp.read())

                    try:
                        sender = self.o.file_email_from
                        if not sender:
                            sender = 'sarracenia-emailer'
                    except AttributeError:
                        sender = 'sarracenia-emailer'

                    logger.debug("Using sender email: " + sender)

                    emsg['Subject'] = msg['new_file']
                    emsg['From'] = sender
                    emsg['To'] = recipient

                    try:
                        email_relay = self.o.file_email_relay
                        if not email_relay:
                            raise AttributeError()
                    except AttributeError:
                        logger.error(
                            'file_email_relay config NOT defined, please define an SMTP (relay) server'
                        )

                    logger.debug("Using email relay server: " + email_relay)
                    s = smtplib.SMTP(email_relay)
                    s.send_message(emsg)
                    s.quit()

                    logger.info('sent file %s to %s' % (ipath, recipient))

        return True
