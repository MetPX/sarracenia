#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):

		import subprocess

		old_name = "/home/pfd/.cache/tmp/sr_sarra/placeholder.txt"
		new_name = "/home/pfd/.cache/tmp/sr_sarra/sender_file.txt"

		parent.logger.info("This on_post script is functional")

		subprocess.call(["mv", old_name, new_name])

		return True


configFile = ParseAndRetrieve(self)
self.on_post=configFile.perform
