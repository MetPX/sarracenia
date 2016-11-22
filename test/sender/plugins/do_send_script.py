#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):
		import subprocess

		final_dest = parent.msg.headers['flow']

		subprocess.call(["cp", parent.local_path, "%s/sender_file.txt" % final_dest] )

		return True


configFile = ParseAndRetrieve(self)
self.do_send=configFile.perform
