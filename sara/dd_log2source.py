#!/usr/bin/python3

import amqplib.client_0_8 as amqp
import logging,logging.handlers
import getopt, os, sys, time

try :    from dd_amqp      import *
except : from sara.dd_amqp import *

# ==========
# MAIN
# ==========

def help():
    print("Usage: %s [-h] [-l logdir] host user password")

def main():

    # default options

    ldir     = None
    host     = 'localhost'
    user     = 'guest'
    password = 'guest'

    # options from arguments

    try:
           opts, args = getopt.getopt(sys.argv[1:],'hl:',['help','log-dir='])
    except getopt.GetoptError as err:    
           help()
           sys.exit(2)                    
    
    #validate options
    if opts == [] and args == []:
      help()  
      sys.exit(2)

    for o, a in opts:
        if o in ('-h','--help'):
           help()
           sys.exit(0)
        elif o in ('-l','--log-dir'):
           ldir = a       
           if not os.path.exists(ldir) :
              print("Error 2: specified logging directory does not exist.")
              help()
              sys.exit(3)
        
    #validate arguments
    if len(args) == 2:
       user   = args[0]
       passwd = args[1]

    if len(args) == 3:
       host   = args[0]
       user   = args[1]
       passwd = args[2]

    if len(args) == 1 or len(args) > 3:
      help()  
      sys.exit(4)

    # logging to stdout
    LOG_FORMAT = ('%(asctime)s [%(levelname)s] %(message)s')

    if ldir == None :
       logger = logging.getLogger(__name__)
       logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    # user wants to logging in a directory/file
    else :
       lfn    = "dd_log2source.log"
       lfile  = ldir + os.sep + lfn

       # Standard error is redirected in the log
       sys.stderr = open(lfile, 'a')

       # python logging
       logger = None
       fmt    = logging.Formatter( LOG_FORMAT )
       hdlr   = logging.handlers.TimedRotatingFileHandler(lfile, when='midnight', interval=1, backupCount=5) 
       hdlr.setFormatter(fmt)
       logger = logging.getLogger(lfn)
       logger.setLevel(logging.INFO)
       logger.addHandler(hdlr)

    # =========================
    # consuming log part
    # =========================

    # consuming connection

    hc_con = HostConnect( host, None, user, passwd, ssl = False, logger = logger, loop=True)
    hc_con.connect()

    # will use log exchange
    e  = Exchange(hc_con,'log')
    e.build()

    # will use a log queue
    q  = Queue(hc_con,'cmc.dd_log2source')
    q.add_binding('log','v01.log.#')
    q.build()

    
    # will consume from that queue
    c = Consumer(hc_con)
    c.build()


    # =========================
    # publishing part
    # =========================

    hc_pub = hc_con

    # will publish 

    p = Publisher(hc_pub)
    p.build()

    # loop on all logs entries

    while True :

          try  :
                 msg = c.consume(q.qname)
                 if msg == None : continue

                 body   = msg.body
                 parts  = body.split()
                 md5sum = parts[0]

                 hdr = msg.properties['application_headers']
                 key = msg.delivery_info['routing_key']
                 fn  = hdr['filename']

                 parts = key.split('.')
                 exchange_name = 'sx_' + parts[3]

                 logger.info(" exchange_name = %s" % exchange_name)
                 logger.info(" key  = %s" % key)
                 logger.info(" body = %s" % body)
                 p.publish(exchange_name,key,body + ' x',fn)
                 c.ack(msg)

          except :
                 (type, value, tb) = sys.exc_info()
                 logger.error("Type: %s, Value: %s,  ..." % (type, value))

    hc_con.close()
    hc_pub.close()

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
