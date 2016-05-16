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
# sr_audit.py : python3 program checking for bad exchange, queues... etc
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Feb  2 09:33:02 EST 2016
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
         from sr_rabbit          import *
         from sr_instances       import *
except : 
         from sarra.sr_rabbit    import *
         from sarra.sr_instances import *

class sr_audit(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

    def add_exchange(self,e):
        self.logger.info("adding exchange '%s'" % e)
        dummy = self.rabbitmqadmin("declare exchange name='%s' type=topic auto_delete=false durable=true"%e)

    def add_user(self,u,role):
        self.logger.info("adding user %s" % u)

        if role == 'admin' :
           dummy = self.rabbitmqadmin("declare user name='%s' password= tags=administrator"%u)
        else:
           dummy = self.rabbitmqadmin("declare user name='%s' password= tags="%u)

        # admin and feeder gets the same permissions

        if role in ['admin,','feeder','manager']:
           c="configure='.*'"
           w="write='.*'"
           r="read='.*'"
           self.logger.info("permission user '%s' role %s  %s %s %s " % (u,'feeder',c,w,r))
           dummy = self.rabbitmqadmin("declare permission vhost=/ user='%s' %s %s %s"%(u,c,w,r))
           return

        # source

        if role == 'source':
           c="configure='^q_%s.*'"%u
           w="write='^q_%s.*|^xs_%s$'"%(u,u)
           r="read='^q_%s.*|^xs_%s$|^xl_%s$|^xpublic$'"%(u,u,u)
           self.logger.info("permission user '%s' role %s  %s %s %s " % (u,'source',c,w,r))
           dummy = self.rabbitmqadmin("declare permission vhost=/ user='%s' %s %s %s"%(u,c,w,r))
           return

        # PS asked not to implement this (Fri Mar  4 2016)
        # anonymous was special at a certain time ... historical reasons
        # anonymous should only be a subscribe... but it is a special case...
        # to work with old versions of subscribe : queue cmc* and configure permission on xpublic
        # this anonymous code will be deprecated at a certain point...

        #if u == 'anonymous' :
        #   c="configure='^q_%s.*|xpublic|^cmc.*$'"%u
        #   w="write='^q_%s.*|^xs_%s$|xlog|^cmc.*$'"%(u,u)
        #   r="read='^q_%s.*|^xl_%s$|xpublic|^cmc.*$'"%(u,u)
        #   self.logger.info("permission user %s role %s  %s %s %s " % (u,'source',c,w,r))
        #   dummy = self.rabbitmqadmin("declare permission vhost=/ user=%s %s %s %s"%(u,c,w,r))
        #   return

        # subscribe

        if role == 'subscribe':
           c="configure='^q_%s.*'"%u
           w="write='^q_%s.*|^xs_%s$'"%(u,u)
           r="read='^q_%s.*|^xpublic$'"%u
           self.logger.info("permission user '%s' role %s  %s %s %s " % (u,'source',c,w,r))
           dummy = self.rabbitmqadmin("declare permission vhost=/ user='%s' %s %s %s"%(u,c,w,r))
           return

    def check(self):
        self.logger.debug("sr_audit check")

        # only one audit around
        self.nbr_instances = 1

        # audit must be user  admin
        if not hasattr(self,'admin'):
           self.logger.error("admin user not set... sr_audit stop")
           sys.exit(1)

        # get other admins  users

        picked      = []
        self.admins = []
        self.logger.debug("users = %s" % self.users)
        for user in self.users :
            roles = self.users[user]
            if 'admin' in roles :
               self.admins.append(user)
               picked.append(user)

        # get feeder users

        self.feeders = []
        for user in self.users :
            roles = self.users[user]
            if 'feeder' in roles or 'manager' in roles and not user in picked :
               self.feeders.append(user)
               picked.append(user)

        # get source users

        self.sources = []
        for user in self.users :
            roles = self.users[user]
            if 'source' in roles and not user in picked :
               self.sources.append(user)
               picked.append(user)

        # get subscribe users

        self.subscribes = []

        for user in self.users :
            roles = self.users[user]
            if 'subscribe' in roles and not user in picked :
               self.subscribes.append(user)
               picked.append(user)

        # invalid roles left...
        for user in self.users :
            roles = self.users[user]
            if not user in picked :
                self.logger.error("unknown role '%s' for user '%s' " % (roles,user) )





    def delete_exchange(self,e):
        self.logger.info("deleting exchange %s" % e)
        dummy = self.rabbitmqadmin("delete exchange name=%s"%e)

    def delete_queue(self,q):
        self.logger.info("deleting queue %s" % q)
        dummy = self.rabbitmqadmin("delete queue name=%s"%q)

    def delete_user(self,u):
        self.logger.info("deleting user %s" % u)
        dummy = self.rabbitmqadmin("delete user name='%s'"%u)

    def overwrite_defaults(self):
        self.logger.debug("sr_audit overwrite_defaults")
        self.sleep = 60

    def rabbitmqadmin(self,options):
        try :
                 (status, answer) = exec_rabbitmqadmin(self.admin,options,self.logger)
                 if status != 0 or answer == None or len(answer) == 0 or 'error' in answer :
                    self.logger.error("rabbitmqadmin invocation failed")
                    return []

                 if answer == None or len(answer) == 0 : return []

                 lst = []
                 try    : lst = eval(answer)
                 except : pass

                 return lst

        except :
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                self.logger.error("rabbimtqadmin "+ options)
        return []

    def verify_exchanges(self):
        self.logger.debug("sr_audit verify_exchanges")

        # get exchanges name (a list of dictionnaries)

        lst_dict = self.rabbitmqadmin("list exchanges name")

        # loop build list of exchanges of interest
        # empty or rabbitmq-server defaults 'amq.' are taken off

        exchange_rab = ['amq.direct','amq.fanout','amq.headers','amq.match', \
                        'amq.rabbitmq.log','amq.rabbitmq.trace','amq.topic'  ]

        exchange_lst = []
        for edict in lst_dict :
            exchange = edict['name']
            if exchange == '' : continue
            # if you want sr_audit to get rid of rabbitmq-server amq.* default exchanges
            # just comment this next line
            if exchange in exchange_rab : continue
            exchange_lst.append(exchange)

        # mandatory xlog,xpublic

        for e in ['xlog','xpublic','xwinnow'] :
            if e in exchange_lst :
               exchange_lst.remove(e)
               continue
            self.add_exchange(e)

        # all sources should have: xs_ and xl_"user"

        for u in self.sources :
            e = 'xs_' + u
            if e in exchange_lst :
               exchange_lst.remove(e)
            else:
               self.add_exchange(e)

            e = 'xl_' + u
            if e in exchange_lst :
               exchange_lst.remove(e)
               continue
            self.add_exchange(e)

        # all sources and subscribes should have: xs_"user"

        for u in self.subscribes :
            e = 'xs_' + u
            if e in exchange_lst :
               exchange_lst.remove(e)
               continue
            self.add_exchange(e)

        # delete leftovers
        # MG : Peter specified that we may need other exchanges to work with 
        #      Such an exchange would be created manually and would start with 'x'
        #
        #      So  get rid of all exceeding 'xl_' 'xs_' exchanges as deprecated
        #      and get rid of all exchanges that do not start with 'x'
        for e in exchange_lst :

            # deprecated exchanges  (from deleted users?)
            if 'xs_' in e or 'xl_' in e :
               self.logger.warning("deprecated exchange %s" % e)
               self.delete_exchange(e)

            # weird exchange... not starting with 'x'
            elif e[0] != 'x' :
               self.logger.warning("unnecessary exchange %s" % e)
               self.delete_exchange(e)

            # leading 'x' exchanges that might be there for a reason
            # leave but notify ...
            else:
               self.logger.info("noticed exchange %s leaving alone." % e)

    def verify_users(self):
        self.logger.debug("sr_audit verify_users")

        # get users name (a list of dictionnaries)

        lst_dict = self.rabbitmqadmin("list users name")

        user_lst = []
        for edict in lst_dict :
            user = edict['name']
            if user == '' : continue
            user_lst.append(user)

        self.logger.debug("user_lst = %s" % user_lst)

        # admins

        for u in self.admins :
            if u in user_lst :
               user_lst.remove(u)
               continue
            self.add_user(u,'admin')

        # feeders

        for u in self.feeders:
            if u in user_lst :
               user_lst.remove(u)
               continue
            self.add_user(u,'feeder')

        # sources

        for u in self.sources :
            if u in user_lst :
               user_lst.remove(u)
               continue
            self.add_user(u,'source')

        # subscribes

        for u in self.subscribes:
            if u in user_lst :
               user_lst.remove(u)
               continue
            self.add_user(u,'subscribe')

        # delete leftovers
        for u in user_lst :
            self.logger.warning("unnecessary user %s" % u)
            self.delete_user(u)

    def verify_queues(self):
        self.logger.debug("sr_audit verify_queues")

        lst_dict = self.rabbitmqadmin("list queues name messages state")
        self.logger.debug("lst_dict = %s" % lst_dict)

        for edict in lst_dict :
            # skip empty name
            q = edict['name']
            if q == '' : continue
            # get queue size
            try    : qsize = int(edict['messages'])
            except : qsize = -1
            # skip running queue
            try    : s = edict['state']
            except : s= ''
            if s == 'running' :
               self.logger.debug("running queue %s (%d) discarded" % (q,qsize))
               continue
            self.logger.debug("verifying queue %s (%d)" % (q,qsize))

            # queue bigger than max_queue_size are deleted right away
            if qsize >= self.max_queue_size :
               self.logger.debug("queue too big %s (%d)" % (q,qsize))
               self.delete_queue(q)
               continue

            # queue name starting with cmc are tolerated for now
            # FIX ME, when sarra really well implemented/used delete cmc queue

            lq = len(q)
            if lq > 3 and q[:3] == 'cmc' :
               self.logger.debug("cmc queue tolerated %s " % q)
               continue

            # at this point any queue that does not start with sarra's default is deleted
            # so any queue should start with q_"username".

            if lq < 2 or q[:2] != 'q_'  :
               self.logger.debug("queue with invalid name %s " % q)
               self.delete_queue(q)
               continue

            # extract username from queuename... 

            if self.users_flag :
               parts = q.split('.')
               username = parts[0][2:]

               # verify all valid usernames
               if username in self.admins                   or \
                  username in self.feeders                  or \
                  username in self.sources                  or \
                  username in self.subscribes:
                  self.logger.debug("queue ok, recognized username %s " % username)
                  continue

               # queue of with invalid or obsolete username
               self.logger.debug("queue with invalid username %s " % q)
               self.delete_queue(q)


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
           lst = self.rabbitmqadmin("list users name")
           if lst != [] :
              self.logger.info("**** admin account verified *****")
              self.logger.info("admin %s"   % self.admin.geturl())
           else:
              self.logger.error("**** account not working on broker ****")
              self.logger.error("admin %s"   % self.admin.geturl())
              error += 1
        
        # verify feeder exists
        # (was kept manager in code but feeder or manager in config file)
        if self.manager :
           self.logger.info("**** feeder account defined *****")
           self.logger.info("feeder %s" % self.manager.geturl())
        else:
           self.logger.error("feeder ... ")
           self.logger.error("No feeder set ")
           self.logger.error("Error: In default.conf use : feeder amqp://f_usern@...")
           self.logger.error("                             admin  a_username")
           self.logger.error("       In credentials.conf : admin and feeder must be defined")
           error += 1

        # verify if some users were defined
        if len(self.users) > 0 :
           self.logger.info("**** users defined *****")
           for u in self.users :
               self.logger.info("user %15s  roles %s" % (u,self.users[u]))
        else :
           self.logger.error("**** users.conf file not present *****")
           self.logger.error("Users should be defined in users.conf, ex.:")
           self.logger.error("root         admin")
           self.logger.error("feeder       feeder")
           self.logger.error("nws-internet source")
           self.logger.error("anonymous    subscribe")
           self.logger.error("After having declared users and roles in users.conf")
           self.logger.error("use: sr_audit --users foreground")
           self.logger.error("it creates users, set their permissions and declare their exchanges")
           self.logger.error("source users are also used in sr_log2source to make products log available to them")
           error += 1

        # verify if the pump have a cluster name set
        if self.cluster :
           self.logger.info("**** cluster (pump name) defined *****")
           self.logger.info("cluster %s"   % self.cluster)
        else :
           self.logger.error("**** cluster (pump name) undefined *****")
           self.logger.error("cluster clustername")
           self.logger.error("The cluster name must be set in default.conf")
           self.logger.error("AMQP message headers target one or a list of clusters")
           self.logger.error("If not set, no message can be processed.")
           error += 1

        if self.cluster_aliases != [] :
           self.logger.info("**** cluster_aliases declared *****")
           self.logger.info("cluster_aliases %s"   % self.cluster_aliases)
        else :
           self.logger.warning("**** cluster_aliases undefined but not mandatory *****")
           self.logger.warning("cluster_aliases clusteralias1,clusteralias2,...")
           self.logger.warning("It can be set in default.conf")
           self.logger.warning("It should be used when the cluster can be named in different ways. Ex.:")
           self.logger.warning("   cluster ddi")
           self.logger.warning("   cluster_aliases DDIDOR,ddi1.cmc,ddi2.cmc")
           warning += 1

        if self.gateway_for != [] :
           self.logger.info("**** gateway_for declared *****")
           self.logger.info("gateway_for %s" % self.gateway_for)
        else :
           self.logger.warning("**** gateway_for undeclared but not mandatory *****")
           self.logger.warning("gateway_for clustername1,clustername2,...")
           self.logger.warning("It can be set in default.conf")
           self.logger.warning("Use this option if this pump is a hop to other pumps for messages")
           self.logger.warning("Declare the pumps using their cluster names like this:")
           self.logger.warning("   gateway_for ddi.edm,ddi1.edm,ddi2.edm")
           warning += 1

        if self.log_clusters != {} :
           self.logger.info("**** log2clusters.conf file present *****")
           self.logger.info("log2clusters.conf")
           for  i in self.log_clusters :
                cluster,broker,exchange = self.log_clusters[i]
                self.logger.info("name %s  url %s exchange %s" % (cluster,broker.geturl(),exchange))
        else :
           self.logger.warning("**** log2clusters.conf file not present but not mandatory *****")
           self.logger.warning("Use this file if this cluster is a hop to other pumps'log.")
           self.logger.warning("Logs going back to clusters may need to go through this cluster ")
           self.logger.warning("You would set to target a cluster like this (one per line):")
           self.logger.warning("    #cluster_name url                                exchange")
           self.logger.warning("    ddi.edm       amqp://mgr_user@ddi.edm.ec.gc.ca   xlog")
           warning += 1

        self.logger.info(" %d error(s) and %d warning(s)" % (error,warning))

    def run(self):
        self.logger.info("sr_audit run")

        # loop : audit should never stop working   ;-)

        while True  :
              try   :
                      self.logger.info("sr_audit waking up")
                      self.configure()
                      self.verify_queues()
                      if self.users_flag : self.verify_users()
                      if self.users_flag : self.verify_exchanges()
                      if self.pump_flag  : self.verify_pump()
              except:
                      (stype, svalue, tb) = sys.exc_info()
                      self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))

              if self.users_flag or self.pump_flag :
                  return
              else :
                  self.logger.info("audit is sleeping %d seconds " % self.sleep)
                  time.sleep(self.sleep)

    def reload(self):
        self.logger.info("%s reload" % self.program_name)
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.logger.info("%s start" % self.program_name)
        self.run()

    def stop(self):
        self.logger.info("%s stop" % self.program_name)
        self.close()
        os._exit(0)
                 
# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None

    if len(sys.argv) > 1 :
       action = sys.argv[-1]
       args   = sys.argv[1:-1]

    if len(sys.argv) > 2 : 
       config    = sys.argv[-2]
       cfg       = sr_config()
       cfg.defaults()
       cfg.general()
       ok,config = cfg.config_path('audit',config,mandatory=False)
       if ok     : args = sys.argv[1:-2]
       if not ok : config = None

    audit = sr_audit(config,args)

    if   action == 'foreground' : audit.foreground_parent()
    elif action == 'reload'     : audit.reload_parent()
    elif action == 'restart'    : audit.restart_parent()
    elif action == 'start'      : audit.start_parent()
    elif action == 'stop'       : audit.stop_parent()
    elif action == 'status'     : audit.status_parent()
    else :
           audit.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
