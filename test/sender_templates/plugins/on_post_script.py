#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):

		import subprocess

		path = parent.msg.headers["flow"]

		on_post_file = "%s/on_post_file.txt" %(path)

		subprocess.call(["touch", on_post_file])

		return True


configFile = ParseAndRetrieve(self)
self.on_post=configFile.perform
