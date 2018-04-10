#!/usr/bin/python3

"""
  on_heartbeat handler that runs a check on all queues
  This plugin was designed to be used under sr_audit only

"""

class Hb_Police_Queues(object): 

    def __init__(self,parent):
        parent.logger.debug( "hb_police_queues initialized" )
          
    def perform(self,parent):
        parent.logger.info( "hb_police_queues launched" )

        try   :
                # establish an amqp connection using admin

                parent.amqp_connect()

                # could not connect ?

                if not parent.amqp_isconnected():
                   parent.logger.error("no connection to broker with admin %s" % parent.admin.geturl())
                   parent.amqp_close()
                   return

                # verify overall queues
                parent.verify_queues()

                # close connection
                parent.amqp_close()

        except:
                (stype, svalue, tb) = sys.exc_info()
                parent.logger.error("hb_police_queues Type: %s, Value: %s,  ..." % (stype, svalue))

        return True

hb_police_queues = Hb_Police_Queues(self)
self.on_heartbeat = hb_police_queues.perform
