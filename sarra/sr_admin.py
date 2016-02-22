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

    def verify_pump(self):

        error   = 0
        warning = 0

        # verify admin user exists

        if not self.admin :
           self.logger.error("No admin user set ")
           self.logger.error("In default.conf use : feeder amqp://fdr_user@..")
           self.logger.error("                      admin username")
           self.logger.error("In credentials.conf : admin and feeder must be defined")
           error += 1

        # verify admin user works
        else:
           self.logger.info("admin %s"   % self.admin.geturl())
           lst = self.rabbitmqadmin("list users name")
           if lst != [] :
              self.logger.info("**** admin account verified *****")
           else:
              self.logger.error("admin %s"   % self.admin.geturl())
              self.logger.error("**** account not working on broker ****")
              error += 1
        
        # verify feeder exists
        # (was kept manager in code but feeder or manager in config file)
        if self.manager :
           self.logger.info("\nfeeder %s" % self.manager.geturl())
        else:
           self.logger.error("\nfeeder ... ")
           self.logger.error("No feeder set ")
           self.logger.error("Error: In default.conf use : feeder amqp://f_usern@...")
           self.logger.error("                             admin  a_username")
           self.logger.error("       In credentials.conf : admin and feeder must be defined")
           error += 1

        # verify if some users were defined
        if self.users :
           self.logger.info("\nusers.conf")
           for u in self.users :
               self.logger.info("user %15s  roles %s" % (u,self.users[u]))
        else :
           self.logger.error("Users should be defined in users.conf")
           self.logger.info("After having declared users and roles in users.conf")
           self.logger.info("use: sr_audit --users foreground")
           self.logger.info("it creates users, set their permissions and declare their exchanges")
           self.logger.info("source users are also used in sr_log2source to make products log available to them")
           error += 1

        # verify if the pump have a cluster name set
        if self.cluster :
           self.logger.info("\ncluster %s"   % self.cluster)
        else :
           self.logger.error("\ncluster")
           self.logger.error("The cluster name must be set in default.conf")
           self.logger.error("AMQP message headers target one or a list of clusters")
           self.logger.error("If not set, no message can be processed.")
           error += 1

        if self.cluster_aliases != [] :
           self.logger.info("\ncluster_aliases %s"   % self.cluster_aliases)
        else :
           self.logger.warning("\ncluster_aliases")
           self.logger.warning("The option cluster_aliases is not mandatory")
           self.logger.warning("It can be set in default.conf")
           self.logger.warning("It should be used when this cluster can be named in different ways. Ex.:")
           self.logger.warning("   cluster ddi")
           self.logger.warning("   cluster_aliases ddi1.cmc,ddi2.cmc")
           warning += 1

        if self.gateway_for != [] :
           self.logger.info("\ngateway_for %s" % self.gateway_for)
        else :
           self.logger.warning("\ngateway_for")
           self.logger.warning("The option gateway_for is not mandatory")
           self.logger.warning("It can be set in default.conf")
           self.logger.warning("Use this option if this pump is a hop to other pumps for messages")
           self.logger.warning("Declare the pumps using their cluster names like this:")
           self.logger.warning("gateway_for ddi.edm,ddi1.edm,ddi2.edm")
           warning += 1

        if self.log_clusters != {} :
           self.logger/info("\nlog2clusters.conf")
           for  i in self.log_clusters :
                cluster,broker,exchange = self.log_clusters[i]
                self.logger.info("name %s  url %s exchange %s" % (cluster,broker.geturl(),exchange))
        else :
           self.logger.info("log2clusters.conf is not mandatory")
           self.logger.info("Use this file if this cluster is a hop to other pumps'log.")
           self.logger.info("Logs going back to clusters may need to go through this cluster ")
           self.logger.info("You would set to target a cluster like this (one per line):\n")
           self.logger.info("#cluster_name url                                exchange")
           self.logger.info("ddi.edm       amqp://mgr_user@ddi.edm.ec.gc.ca   xlog")
           warning += 1

        self.logger.info(" %d error(s) and %d warning(s)" % (error,warning))

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

