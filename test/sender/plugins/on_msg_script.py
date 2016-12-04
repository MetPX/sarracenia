#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):

		import subprocess

		path = parent.msg.headers["flow"]

		on_msg_file = "%s/on_msg_file.txt" %(path)

		subprocess.call(["touch", on_msg_file])

		return True


configFile = ParseAndRetrieve(self)
self.on_message=configFile.perform
