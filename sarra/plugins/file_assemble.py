#!/usr/bin/python3

"""

File_Assemble:

Usage:

"""

class File_Assemble(object):

	def __init__(self, parent):
		parent.logger.debug("Assembler initialized")

	def perform(self, parent):
		try: import sr_assemble as sr_assemble
		except: import sarra.sr_assemble as sr_assemble

		parent.logger.info('Downloading in parts: %s' % (not parent.inplace))
		if parent.inplace: # test
			return False

		# Needs assembling
		parent.logger.info("FILE_ASSEMBLE file part downloaded to: %s/%s" % ( parent.msg.new_dir, parent.msg.new_file) )
		file_info = parent.msg.new_file.rsplit('.', 6)
		#...


		assembler=sr_assemble.sr_assemble()
		#assembler.__do_assemble__(parent.msg.new_dir+'/'+parent.msg.new_file)
		assembler.__do_assemble__()



file_assemble = File_Assemble(self)
self.on_post = file_assemble.perform
