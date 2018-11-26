#!/usr/bin/python3

"""
Decodes the attachment of an email in MIME 1.0 format, saves it as the attachment filename. 
If no attachment is detected, it'll save the body/to/from headers in a file with the subject/timestamp. 
Works assuming the attachment have been properly formatted (e.g. 'Content-Disposition: attachment')
and standard content transfer encodings are used. 

Usage:
on_file file_email_decode
"""

import email

class Decoder(object): 

	def __init__(self,parent):
		parent.logger.debug("file_email_decode initialized")

	def perform(self,parent):
		import email

		logger = parent.logger
		fichier = parent.msg.new_file
		idir = parent.currentDir
		odir = parent.post_base_dir
		if odir[-1] != '/': odir += '/'
		if idir[-1] != '/': idir += '/'
		try: 
			with open(idir+fichier,'r') as f:
				emailmsg = email.message_from_file(f)
		except:
			logger.error("file_email_decode could not open file: %s" % idir+fichier)
			return

		try:
			if emailmsg.is_multipart() and len(emailmsg.get_payload()) == 2:
				attachment = emailmsg.get_payload()[1]
				data       = attachment.get_payload(decode=True)
				for part in emailmsg.walk():
					content_disposition = part.get('Content-Disposition',None)
					if content_disposition:
						dispositions = content_disposition.strip().split(";")
						for param in dispositions[1:]:
							name,value = param.split("=")
							name = name.lower().strip()
							if name == "filename":
								fname = value.strip('"') 
								with open(odir+fname, 'w') as f:
									f.write(data)
									logger.info("file_email_decode attachment has been decoded: %s" % odir+fname)
			else:
			# take the first section marked text/plain and that isn't encoded
				msgsubject = emailmsg['subject']
				msgto      = emailmsg['to']
				msgfrom    = emailmsg['from']
	
				for part in emailmsg.get_payload():
					if 'multipart/alternative' in part['Content-Type'] or 'text/plain' in part['Content-Type']:
						if part.get_payload():
							msgbody = part.get_payload()[0].as_string().split('\n',2)[2]
							fname = msgsubject.strip()+datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%f")
							with open(odir+fname,'w') as f:
								f.write("From: %s\n"    % msgfrom)
								f.write("To: %s\n"      % msgto)
								f.write("Subject: %s\n" % msgsubject)
								f.write(msgbody)
							logger.info("file_email_decode msg body written to file: %s" % odir+fname)
							return
		except:
			logger.error("file_email_decode cannot decipher file")
			return
decoder = Decoder(self)
self.on_file = decoder.perform
