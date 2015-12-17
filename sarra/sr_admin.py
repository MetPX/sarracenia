#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_admin.py : python3 program allowing users setup (account, exchange... etc)
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 15 09:23:14 EST 2015
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#

import os,socket,sys,time

try :    
         from sr_rabbit       import *
         from sr_config       import *
except : 
         from sarra.sr_rabbit import *
         from sarra.sr_config import *

class sr_admin(sr_config):

    def __init__(self,config=None,args=None):
        sr_config.__init__(self,config,args)
        del self.logger

        LOG_FORMAT  = ('[%(levelname)s] %(message)s')
        logging.basicConfig(format=LOG_FORMAT)
        self.logger = logging.RootLogger(logging.INFO)
        self.logger.setLevel(logging.INFO)
        self.defaults()
        self.general()

    def rabbitmqadmin(self,options):
        try :
                 (status, answer) = exec_rabbitmqadmin(self.admin,options)
                 if status != 0 or answer == None or len(answer) == 0 or 'error' in answer :
                    #print("Error could not execute this:")
                    #print("rabbimtqadmin "+ options)
                    return []

                 if answer == None or len(answer) == 0 : return []

                 lst = eval(answer)
                 return lst

        except :
                (stype, svalue, tb) = sys.exc_info()
                print("Error  Type: %s, Value: %s,  ..." % (stype, svalue))
                print("Error with :  rabbimtqadmin "+ options)
        return []

    def verify(self,verbose=True):

        self.error   = 0
        self.warning = 0

        # make sure admin exists

        admin_ok     = False

        if self.admin :
           if verbose : print("\nadmin %s"   % self.admin.geturl())
        else:
           print("\nError: No admin user set ")
           print("Error: In default.conf use : manager amqp://mgr_user@..")
           print("                             admin username")
           print("       In credentials.conf : admin and manager must be defined")
           self.error += 1

        if self.admin :
           lst = self.rabbitmqadmin("list users name")
           if lst != [] :
              if verbose : print("**** admin account verified *****")
           else:
              print("ERROR: admin %s"   % self.admin.geturl())
              print("       **** account not working on broker ****")
              self.error += 1
        
        if self.manager :
           if verbose : print("\nmanager %s" % self.manager.geturl())
        else:
           print("\nmanager ... ")
           print("Error: No manager set ")
           print("Error: In default.conf use : manager amqp://usern@...")
           print("                             admin username")
           print("       In credentials.conf : admin and manager must be defined")
           self.error += 1

        if self.users :
           if verbose : print("\nusers.conf")
           for u in self.users :
                if verbose : print("user %10s  roles %s" % (u,self.users[u]))
        else :
           print("\nusers.conf")
           print("Error: Users should be defined in users.conf")
           print("       Used by sr_admin to create user, set permissions and declare exchanges")
           print("       Used by sr_log2source to post products log into the sources'exchange")
           print("       Used by sr_police.py ... FIX ME ... TO BE DETERMINED.")
           self.error += 1

        if self.cluster :
           if verbose : print("\ncluster %s"   % self.cluster)
        else :
           print("\ncluster")
           print("Error: The cluster name must be set in default.conf")
           print("       AMQP message headers target one or a list of clusters")
           print("       If not set, no message can be processed.")
           self.error += 1

        if self.cluster_aliases != [] :
           if verbose : print("\ncluster_aliases %s"   % self.cluster_aliases)
        else :
           if verbose : print("\ncluster_aliases")
           if verbose : print("Warning: The option cluster_aliases is not mandatory")
           if verbose : print("         It can be set in default.conf")
           if verbose : print("         It should be used when this cluster can be named in different ways. Ex.:")
           # FIX ME : better example
           if verbose : print("         cluster ddi")
           if verbose : print("         cluster_aliases ddi1.cmc,ddi2.cmc")
           self.warning += 1

        if self.gateway_for != [] :
           if verbose : print("\ngateway_for %s" % self.gateway_for)
        else :
           if verbose : print("\ngateway_for")
           if verbose : print("Warning: The option gateway_for is not mandatory")
           if verbose : print("         It can be set in default.conf")
           if verbose : print("         Use this option if this cluster is a hop to other pumps.")
           if verbose : print("         Declare the pumps using their cluster names like this:")
           if verbose : print("         gateway_for ddi.edm,ddi1.edm,ddi2.edm")
           # FIX ME : better example
           if verbose : print("         cluster ddi")
           if verbose : print("         cluster_aliases ddi.cmc,ddi.edm")
           self.warning += 1

        if verbose : print("\nlog2clusters.conf")
        if self.log_clusters != {} :
           for  i in self.log_clusters :
                cluster,broker,exchange = self.log_clusters[i]
                if verbose : print("name %s  url %s exchange %s" %
                                              (cluster,broker.geturl(),exchange))
        else :
           if verbose : print("Warning: log2clusters.conf is not mandatory")
           if verbose : print("         Use this file if this cluster is a hop to other pumps'log.")
           if verbose : print("         Logs going back to clusters may need to go through this cluster ")
           if verbose : print("         You would set to target a cluster like this (one per line):")
           # FIX ME : better example
           if verbose : print("         #cluster_name url exchange")
           if verbose : print("         ddi.edm amqp://mgr_user@ddi.edm.ec.gc.ca xlog")
           self.warning += 1

        if self.error != 0 : sys.exit(self.error)

# ===================================
# MAIN
# ===================================

def main():

    adm = sr_admin(None,None)

    adm.verify(True)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

