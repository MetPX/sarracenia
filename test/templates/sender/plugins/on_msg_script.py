#!/usr/bin/python3

class ParseAndRetrieve(object):

	def __init__(self, parent):
		pass
		
	def perform(self, parent):

		import subprocess

		doc_root = parent.msg.headers['flow']		

		old_name = "%s/placeholder.txt" % doc_root
		temp_name = "%s/temp.txt" % doc_root
		new_name = "%s/sender_file.txt" % doc_root

		subprocess.call(["cp", old_name, temp_name])
		subprocess.call(["mv", temp_name, new_name])

		return True


configFile = ParseAndRetrieve(self)
self.on_message=configFile.perform
