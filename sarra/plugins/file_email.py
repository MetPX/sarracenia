#!/usr/bin/python3

"""
    File_Email: sr_subscribe plugin. Once a file is downloaded, the plugin matches the
    topic(what the filename begins with) to the file name and sends the appropriate emails.

    Usage:
      1. Need the following in a subscriber plugin: file_email_to TOPIC email1,email2,...
        ex. file_email_to AACN27 muhammad.taseer@canada.ca
        ex. file_email_to SR muhammad.taseer@canada.ca,test@test.com
      2. sr_subscribe emails.conf foreground

    Todo:
      * Change plugin to be an sr_sender plugin using do_send/so_put?

    Last modified: Wahaj Taseer - June, 2019
"""


class File_Email(object):

    def __init__(self, parent):
        parent.declare_option('file_email_command')
        parent.declare_option('file_email_to')

    def on_start(self, parent):
        if not hasattr(parent, 'file_email_command'):
                 parent.file_mail_command = ['/usr/bin/mail']


    def on_file(self, parent):
      
        import os.path, re, subprocess

        # have a list of email destinations...
        parent.logger.debug("email: %s" % parent.file_email_to)
        ipath = os.path.normpath(parent.msg.new_dir + '/' + parent.msg.new_file)
        parent.logger.info("file_email downloaded to: %s" % ipath)

        # loop over all the variables from config file, if files match, send via email
        for header in parent.file_email_to:
            topic, emails = header.split(' ', 1)
            emails = [x.strip(' ') for x in emails.split(',')]

            # check if the file arrived matches any email rules
            if re.search('^' + topic + '.*', parent.new_file):
                for recipient in emails:
                    parent.logger.debug('sending file %s to %s' % (ipath, recipient))
                    cmd = 'mail -s ' + parent.new_file + ' ' + recipient
                    file_to_send = open(ipath)
                    try:
                        subprocess.run(cmd.split(), stdin=file_to_send, stdout=subprocess.PIPE)
                    except subprocess.CalledProcessError as e:
                        parent.logger.error('Could not mail %s to %s' % (parent.new_file, recipient))
                        parent.logger.error(e.stderr)

                    file_to_send.close()
                    parent.logger.info('email %s sent to %s' % (topic, recipient))

        return True

file_email = File_Email(self)
self.on_file = file_email.on_file



