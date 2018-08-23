#!/usr/bin/python3

"""

File_Assemble: This plugin is used by sr_watch. Gets triggered by on_post when a file arrives
				It checks the file name then finds all the other part files in the directory,
				if all are present and it hasn't already been assembled, then it calls sr_assemble 

Usage: in an sr_watch configuration file, you need:
		broker <ampq://user@server>
		post_exchange: <exchange>
		path <path of directory to watch>
		post_base_url file:/ 
		on_post /path-to-plugin/file_assemble.py
		accept .Part
		suppress_duplicates on -- doesn't seem to disable the cache

"""

class File_Assemble(object):

	def __init__(self, parent):
		parent.logger.debug("Assembler initialized")
		parent.suppress_posting_partial_assembled_file = True # referenced in sr_post:post_file

	def perform(self, parent):
		try: 
			import sr_assemble as sr_assemble
			import sr_file as sr_file
		except: 
			import sarra.sr_assemble as sr_assemble
			import sarra.sr_file as sr_file

		# Check if part file arrived
		file_info = parent.msg.new_file.rsplit('.', 6)
		if len(file_info) != 7:
			parent.logger.warning('%s: Not a part file, ignoring...' % parent.msg.new_file)
			return False

		parent.msg.target_file = file_info[0]

		try:
			if not ('parent.msg.target_relpath' in vars()):
				target_relpath = parent.msg.relpath.rsplit('/', 1)[0]+'/'+parent.msg.target_file
				parent.msg.target_relpath = target_relpath
			if not ('parent.msg.new_baseurl' in vars()):
				parent.msg.new_baseurl = parent.msg.baseurl
		except:
			parent.logger.warning('Unable to set msg.target_relpath or msg.new_baseurl: %s' %parent.msg.target_file)

		# call reassemble method in sr_file to do the rest of the work
		finished =  sr_file.file_reassemble(parent)

		return finished



file_assemble = File_Assemble(self)
self.on_part = file_assemble.perform
