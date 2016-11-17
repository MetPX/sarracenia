#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):

		import subprocess

		final_dest = parent.msg.headers['flow']

		old_name = "%s/placeholder.txt" % final_dest
		new_name = "%s/sender_file.txt" % final_dest

		parent.logger.info("This on_post script is functional")

		subprocess.call(["mv", old_name, new_name])

		return True


configFile = ParseAndRetrieve(self)
self.on_post=configFile.perform
