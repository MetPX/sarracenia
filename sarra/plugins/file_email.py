#!/usr/bin/python3

"""
    File_Email: sr_sender plugin. Once a file is posted, the plugin matches the
    topic(what the filename begins with) to the file name and sends the appropriate emails.

    Usage:
      1. Need the following in an sr_sender config: file_email_to TOPIC email1,email2,...
        ex. file_email_to AACN27 muhammad.taseer@canada.ca
        ex. file_email_to SR muhammad.taseer@canada.ca,test@test.com
      2. sr_sender foreground emails.conf

      Rules for TOPIC:
        - Treated as a regular expression, so avoid using symbols.
        - TOPIC will be matched from the beginning of the file name and the rest is ignored
        - For reference: https://docs.python.org/3/library/re.html

    Last modified: Wahaj Taseer - June, 2019
"""


class File_Email(object):

    def __init__(self, parent):
        parent.declare_option('file_email_command')
        parent.declare_option('file_email_to')
        self.registered_list = ['ftp', 'ftps', 'sftp']

    def registered_as(self):
        return self.registered_list

    def on_start(self, parent):
        if not hasattr(parent, 'file_email_command'):
                 parent.file_mail_command = ['/usr/bin/mail']

    def do_send(self, parent):
      
        import os.path
        import re

        # have a list of email destinations...
        parent.logger.debug("email: %s" % parent.file_email_to)
        ipath = os.path.normpath(parent.msg.relpath)

        # loop over all the variables from config file, if files match, send via email
        for header in parent.file_email_to:
            topic, emails = header.split(' ', 1)
            emails = [x.strip(' ') for x in emails.split(',')]

            # check if the file arrived matches any email rules
            if re.search('^' + topic + '.*', parent.new_file):

                import smtplib
                from email.message import EmailMessage

                for recipient in emails:
                    parent.logger.debug('sending bulletin %s to %s' % (ipath, recipient))

                    with open(ipath) as fp:
                        emsg = EmailMessage()
                        emsg.set_content(fp.read())

                    emsg['Subject'] = parent.new_file
                    emsg['From'] = 'sarra-emailer@canada.ca'
                    emsg['To'] = recipient

                    s = smtplib.SMTP('smtp.cmc.ec.gc.ca')
                    s.send_message(emsg)
                    s.quit()

                    parent.logger.info('sent bulletin %s to %s' % (ipath, recipient))

        return True


file_email = File_Email(self)
self.do_send = file_email.do_send



