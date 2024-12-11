"""
Email Sender
============

``sarracenia.flowcb.send.email.Email`` is an sr3 sender plugin. It will send the *contents* of a 
file in the *body* of an email to the configured recipient(s).

The email subject will be the name of the file being sent.

Usage:
^^^^^^

    1. In the config file, include the following line: ::

        callback send.email

    And define the email server ::

        sendTo

    2. Define the email server (required) using the ``sendTo`` option, and the sender's email address (optional)
       in the config file: ::

        sendTo      smtp://email.relay.server.ca

        email_from  santa@canada.ca

        # or, with a "human readable" sender name:

        email_from  Santa Claus <santa@canada.ca>
    
    3. Configure recipients using accept statements. You must have at least one recipient per accept statement.
       Multiple recipients can be specified by separating each address by a comma. ::
    
        accept .*AACN27.* test@example.com
        accept .*SXCN.*   user1@example.com, user2@example.com
        accept .*CACN.* DESTFN=A_CACN_Bulletin  me@ssc-spc.gc.ca,you@ssc-spc.gc.ca,someone@ssc-spc.gc.ca

To change the filename that is sent in the subject, you can use the filename option, a renamer plugin or
DESTFN/DESTFNSCRIPT on a per-accept basis. The ``email_subject_prepend`` option can be used to add text before
the filename in the email subject. For example: ::

    email_subject_prepend  Sent by Sarracenia: 

Future Improvement Ideas:
  - SMTP on different ports and with authentication
  - Attach the file instead of putting the contents in the body (useful for binary files)
    
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
        self.o.add_option('email_from',            'str', default_value='')
        self.o.add_option('email_subject_prepend', 'str', default_value='')

        # Parse accept/reject mask arguments into email recipient lists
        try:
            for mask in self.o.masks:
                # mask[4] == True if accept, False if reject, only need to parse for accept
                if len(mask[-1]) > 0 and mask[4]:
                    # logger.debug(f"mask args before parse: {mask[-1]}")
                    arg_string = ''.join(mask[-1]).replace(' ', '').strip()
                    recipients = arg_string.split(',')
                    mask[-1].clear()
                    for recipient in recipients:
                        if '@' not in recipient:
                            logger.error(f"Invalid email recipient: {recipient} for accept {mask[0]}")
                        else:
                            mask[-1].append(recipient)
                    # logger.debug(f"mask args after parse: {mask[-1]}")
                elif mask[4]:
                    logger.warning(f"No email recipients defined for accept {mask[0]}")
        except Exception as e:
            logger.critical(f"Failed to parse recipients from mask: {mask}")
            raise e

        # Server must be defined
        if not self.o.sendTo or len(self.o.sendTo) == 0:
            raise Exception("No email server (sendTo) is defined in the config!")
        # sendTo --> email_server
        self.email_server = self.o.sendTo.strip('/')
        if '//' in self.email_server:
            self.email_server = self.email_server[self.email_server.find('//') + 2 :]
        logger.debug(f"Using email server: {self.email_server} (sendTo was: {self.o.sendTo})")

        # Add trailing space to email_subject_prepend
        if len(self.o.email_subject_prepend) > 0:
            self.o.email_subject_prepend += ' '
            
    def after_work(self, worklist):
        """ This plugin can also be used in a sarra/subscriber, mostly for testing purposes.
        """
        if self.o.component != 'sender':
            for msg in worklist.ok:
                actual_baseDir = self.o.baseDir
                actual_relPath = msg['relPath']
                msg['relPath'] = os.path.join(msg['new_dir'], msg['new_file'])
                self.o.baseDir = msg['new_dir']

                self.send(msg)

                self.o.baseDir = actual_baseDir
                msg['relPath'] = actual_relPath

    def send(self, msg):
        """ Send an email to each recipient defined in the config file for a particular accept statement.
            The file contents are sent in the body of the email. The subject is the filename.
        """
        
        if not msg['relPath'].startswith(self.o.baseDir): 
            ipath = os.path.normpath(f"{self.o.baseDir}/{msg['relPath']}")
        else:
            ipath = os.path.normpath(f"{msg['relPath']}")

        if '_mask_index' not in msg:
            logger.error("Recipients unknown, can't email file {ipath}")
            # negative return == permanent failure, don't retry
            return -1
        
        # Get list of recipients for this message, from the mask that matched the filename/path
        recipients = self.o.masks[msg['_mask_index']][-1]

        # Prepare the email message
        emsg = EmailMessage()
        try:
            with open(ipath) as fp:
                emsg.set_content(fp.read())
        except Exception as e:
            logger.error(f"Failed to read {ipath}, can't send to {recipients}")
            # No retry if the file doesn't exist
            return -1
        
        emsg['Subject'] = self.o.email_subject_prepend + msg['new_file']

        # if not set in the config, just don't set From, the From address will usually be derived from the hostname
        if self.o.email_from and len(self.o.email_from) > 0:
            emsg['From'] = self.o.email_from
        
        # if sending to any one recipient fails, we will return False, triggering a retry.
        all_ok = True
        for recipient in recipients:
            if '@' not in recipient:
                logger.error(f"Cannot send {ipath} to recipient {recipient}. Email address is invalid!")
                continue

            try:
                logstr = f"file {ipath} to {recipient} with subject {emsg['Subject']}"
                logger.debug(f'sending {logstr} from {self.o.email_from} using server {self.email_server}')

                if 'To' in emsg:
                    del emsg['To']
                emsg['To'] = recipient
                logger.debug(emsg)

                s = smtplib.SMTP(self.email_server)
                s.send_message(emsg)
                s.quit()

                logger.info(f'Sent file {logstr}')

            except Exception as e:
                logger.error(f'failed to send {logstr} from {self.o.email_from} using server {self.email_server}' 
                             + f' because {e}')
                logger.debug('Exception details:', exc_info=True)
                all_ok = False

        return all_ok
