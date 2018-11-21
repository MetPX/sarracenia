#!/usr/bin/python3

"""

Overwrites the sum header of the incoming message with 'a,<randint>', where randint is a 4 digit random
number between 0 and 9999.

To be used in conjunction with the checksum_a plugin, in the DMS use case.

"""

import logging,random

class SumWriter(object):

	def __init__(self, parent):
		parent.logger.debug("msg_overwrite_sum initialized")

	def on_message(self, parent):
		import logging,random

		logger = parent.logger

		parent.msg.headers['sum'] = 'a,%.4d' % random.randint(0,9999)
		parent.logger.debug("msg_overwrite_sum overwrote the msg sum to be: %s" % parent.msg.headers['sum'])
		return True

swriter = SumWriter(self)
self.on_message = swriter.on_message
