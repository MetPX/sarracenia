#!/usr/bin/python3

"""
   Override message header for products that are posted.

   This can be useful or necessary when re-distributing beyond the original intended
   destinations.
   
  for example company A delivers to their own DMZ server.  ACME is a client of them,
  and so subscribes to the ADMZ server, but the to_cluster=ADMZ, when ACME downloads, they
  need to override the destination to specify the distribution within ACME.

  post_override to_clusters ACME

"""

import os,stat,time

class Override(object): 


    def __init__(self,parent):
          parent.logger.info('post_override settings: %s' % parent.post_override )
          pass
          
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        if type(parent.post_override) is list:
           for o in parent.post_override:
               ( osetting, ovalue ) = o.split()
               parent.logger.info('post_override applying: header:%s value:%s' %  \
                     ( osetting, ovalue ) )
               msg.headers[ osetting ] = ovalue
        else:
           ( osetting, ovalue ) = parent.post_override.split()
           msg.headers[ osetting ] = ovalue
           
        return True

override = Override(self)
self.on_post = override.perform
