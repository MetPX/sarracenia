#!/usr/bin/python3
"""

Sends metareas Enhanced Group Call (EGC) command to a specified email given an MSC bulletin file. 
Parses the filename to determine what kind of EGC info to send.

Usage:
	In an sr_subscribe config:

	on_file file_mail_metareas.py
	file_mail_metareas_user <user_emails>
	file_mail_metareas_telnet telnet://user@host

	where <user_emails> is the space-separated email list where the EGC command is being sent.
	The email will also contain the telnet credentials to send the egc. The file_mail_metareas_telnet
	must contain the user and host in the above format, where the password is taken from your 
	~/.config/sarra/credentials.conf file, where it must follow the format: 
	telnet://user:password@host

The EGC code (i.e: egc ocean,c1,c2,c3,c4,c5) in the subject field to represent the following:

	Ocean Region: Western Atlantic = 0, Eastern Atlantic = 1, Pacific = 2
	Priority code (safety priority) C1 = 1,
	Service code (METAREAS marine forecast or warning) C2 = 31,
	Address code (service area) C3 = 17 (Metarea XVII) or 18 (Metarea XVIII),
	Broadcast repetition code C4 = 11 (once on receipt and repeat 6 minutes later),
	Presentation code (7-bit ASCII) C5 = 00

(Refer to "Stratos EGC Fleetnet User Guide" for more information)

"""

import logging, subprocess, sys, os, os.path, string
from stat import ST_SIZE


class MetMailer(object):
    def __init__(self, parent):
        parent.declare_option('file_mail_metareas_user')
        parent.declare_option('file_mail_metareas_telnet')
        parent.logger.debug("file_mail_metareas init")

    def on_file(self, parent):
        import logging, subprocess, sys, os, os.path, string
        from stat import ST_SIZE

        logger = parent.logger
        useremails = parent.file_mail_metareas_user

        ipath = parent.msg.new_relpath
        subp = parent.msg.new_file.split('_')

        # Grabs credentials from credentials.conf that were given in a config option
        ok, details = parent.credentials.get(
            parent.file_mail_metareas_telnet[0])
        if ok:
            setting = details.url
            user = setting.username
            password = setting.password
            server = setting.hostname
            logger.debug("file_mail_metareas telnet scheme valid")
        else:
            user = ""
            password = ""
            server = ""
            logger.debug(
                "file_mail_metareas telnet scheme invalid, not being sent in email"
            )

        tlx = "al: " + server if server else ""
        usr = "Userid: " + user if user else ""
        pw = "Password: " + password if password else ""

        fil = "/tmp/metareas.tmp"

        cmd = (
            "echo {1} > {0} ; echo {2} >> {0} ; echo {3} >> {0} ; echo >> {0} ; cat {4} >> {0}"
            .format(fil, tlx, usr, pw, ipath))

        try:
            resp = subprocess.run([cmd],
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            if resp.returncode != 0 and len(resp.stderr) != 0:
                logger.error(
                    "file_mail_metareas: could not set username, password and bulletin \
					content in temporary file %s" % fil)
                return False
        except:
            return False

        # Set ECG codes for METAREAS regions 17 and 18
        egc_XVII_1 = '2,1,4,66n171w11053,1,0'
        egc_XVII_2 = '2,1,4,66n171w11053,11,0'

        egc_XVIII_1 = '0,1,4,66n122w11074,1,0'
        egc_XVIII_2 = '0,1,4,66n122w11074,11,0'

        egc = ""

        ############## METAREA region XVII South of 75N

        # Merged FQ CWAO product replaces the FW CWNT and FI CWIS  -  July 15, 2013
        # New EGC code Nov. 07 FQCN02 CWAO -  egc 0,1,4,66n171w11057,1,0
        if subp[0] == 'FQCN02' and subp[1] == 'CWAO':
            egc = "0,1,4,66n171w11057,1,0"
        if subp[0] == 'FICN02' and subp[1] == 'CWIS':
            egc = "0,1,4,66n171w11057,1,0"

        # The following bulletins are normally sent to SafetyNet by Coast Guard.
        # During the off season, however, we send the weekly "data not available" message...
        # Merged FQ CWAO product replaces the FW CWNT and FI CWIS  -  July 15, 2013
        if subp[0] == 'FQCN01' and subp[1] == 'CWAO': egc = egc_XVII_1
        if subp[0] == 'FICN01' and subp[1] == 'CWIS': egc = egc_XVII_1

        #    Alaska bulletins  (Commented PAFG bulletins were asked to be removed by Tom King July 22 2010)
        #    Jun.19th 2013:  Tom King asked to add FZAK61_PAFG
        # New EGC code Nov. 07 FZAK61 PAFG -  egc 0,1,4,66n171w11034,1,0
        if subp[0] == 'FZAK61' and subp[1] == 'PAFG':
            egc = "0,1,4,66n171w11034,1,0"
        if subp[0] == 'FZAK69' and subp[1] == 'PAFG':
            egc = "0,1,4,66n171w11034,1,0"

        #    The following is a Marine Weather Statement and a Warning, so the repetition code is different

        ############## METAREA region XVIII South of 75N

        # Merged FQ CWAO product replaces the FW CWNT and FI CWIS  -  July 15, 2013
        if subp[0] == 'FQCN04' and subp[1] == 'CWAO':
            egc = "0,1,4,66n126w11078,1,0"
        if subp[0] == 'FICN04' and subp[1] == 'CWIS':
            egc = "0,1,4,66n126w11078,1,0"

        if subp[0] == 'FICN07' and subp[1] == 'CWIS':
            egc = "0,1,4,66n080w11032,1,0"

        # The following bulletins are normally sent to SafetyNet by Coast Guard.
        # During the off season, however, we send the weekly "data not available" message...
        # Merged FQ CWAO product replaces the FW CWNT and FI CWIS  -  July 15, 2013
        if subp[0] == 'FQCN03' and subp[1] == 'CWAO': egc = egc_XVIII_1
        if subp[0] == 'FICN03' and subp[1] == 'CWIS': egc = egc_XVIII_1

        if subp[0] == 'FQCN05' and subp[1] == 'CWAO':
            egc = "0,1,4,50n098w18030,1,0"
        if subp[0] == 'FICN05' and subp[1] == 'CWIS':
            egc = "0,1,4,50n098w18030,1,0"

        #    Denmark bulletins...
        if subp[0] == 'FBGL50' and subp[1] == 'EKMI': egc = egc_XVIII_1

        #    The FBDN51_EKMI is apparently a Warning (??), so the repetition code is different
        if subp[0] == 'FBDN51' and subp[1] == 'EKMI':
            egc = "0,1,4,66n080w11032,1,0"

        if not egc:
            logger.error("file_mail_metareas: EGC code not defined for %s %s. Email not sent." % \
             (subp[0] ,subp[1]))
            return False

        # for FQ of CWAO if 'PAN PAN' in message than increase priority
        if subp[0][:2] == 'FQ' and subp[1] == 'CWAO':
            with open(ipath, 'r') as f:
                data = f.read()
            if 'PAN PAN' in data:
                egc = egc.replace(',1,4', ',2,4')

        try:
            fsize = os.stat(fil)[ST_SIZE]
        except:
            fsize = 0

        for useremail in useremails:
            cmd = 'cat {0} | mail -s "egc {1}" {2}'.format(fil, egc, useremail)
            try:
                resp = subprocess.run([cmd],
                                      shell=True,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                if resp.returncode != 0 and len(resp.stderr) != 0:
                    logger.error(
                        "file_mail_metareas: could not set username, password and bulletin \
						content in temporary file %s" % fil)
                    return False
            except:
                return False
            logger.info("file_mail_metareas (%i Bytes) File %s mailed to %s" %
                        (fsize, ipath, useremail))

        try:
            os.remove(fil)
        except:
            pass
        return True


metmailer = MetMailer(self)
self.on_file = metmailer.on_file
