#!/usr/bin/python3

"""
   Overwrite to_cluster definition for products that are posted.
   This can be useful or necessary when re-distributing beyond the original intended
   destinations.
   
  for example company A delivers to their own DMZ server.  ACME is a client of them,
  and so subscribes to the ADMZ server, but the to_cluster=ADMZ, when ACME downloads, they
  need to override the destination to specify the distribution within ACME.

"""

import os,stat,time

class Transformer(object): 


    def __init__(self,parent):
          pass
          
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        msg.headers['to_clusters']  = "ACME" 

        return True

transformer = Transformer(self)
self.on_post = transformer.perform

