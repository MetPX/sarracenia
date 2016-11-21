#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):
		import subprocess

		parent.logger.info("Copying " + parent.local_file + " to destination")
		subprocess.call(["cp", parent.local_path, "/home/pfd/.cache/tmp/sr_sarra/sender_file.txt"] )

		return True


configFile = ParseAndRetrieve(self)
self.do_send=configFile.perform
