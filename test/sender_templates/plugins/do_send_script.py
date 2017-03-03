#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):
		import subprocess

		orig_file = parent.local_path

		new_path = parent.msg.headers["flow"]
		destination = new_path + "/" + parent.local_file

		subprocess.call(["cp", orig_file, destination])

		return True

configFile = ParseAndRetrieve(self)
self.do_send=configFile.perform
