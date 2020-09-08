#!/usr/bin/python3
"""

 Useful only for debugging.

 print a the entire message and all configuration and fields 


"""

import os, stat, time


class Transformer(object):

    import calendar

    def __init__(self, parent):

        parent.logger.info("PARENT = \n")
        parent.logger.info(vars(parent))

        pass

    def on_message(self, parent):

        parent.logger.info("message = \n")
        parent.logger.info(vars(parent.msg))

        return True


transformer = Transformer(self)
self.on_message = transformer.on_message
