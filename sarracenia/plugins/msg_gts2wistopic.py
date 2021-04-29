#!/usr/bin/python3

"""
  the default on_msg handler for sr_log.
  prints a simple notice.


  msg.topic=v03.post.20200314T22.GTS.KWBC.HG, msg.newname=HGIE98_KWBC_141800_d65a0c90023a6e0e78889a87c425057c.grib

"""

class msg_GTS2WISTopic(object): 

    def __init__(self,parent):

        import GTStoWIS2

        parent.topic_builder=GTStoWIS2.GTStoWIS2()
        parent.logger.debug("msg_log initialized")

          
    def on_message(self,parent):

        msg=parent.msg
        tpfx=msg.topic.split('.')

        # YYYYMMDDTHHMM
        # 0123245678901
        td=tpfx[2]+"T"+msg.pubtime[8:10]
        t='.'.join(tpfx[0:2])+'.'+td
        #parent.logger.info(" tpfxs %s pubtime=%s " % ( tpfx, msg.pubtime ) )

        #parent.logger.info( "before: msg.topic=%s, msg.newname=%s, msg.new_dir=%s t=%s" % ( msg.topic, msg.new_file, msg.new_dir, t) )
        try: 
            d = parent.topic_builder.mapAHLtoTopic(msg.new_file)
            #parent.logger.info(" remove %s from %s " % ( os.path.dirname(msg.relpath), msg.new_dir ) )
            shorter=  msg.new_dir.replace( os.path.dirname(msg.relpath), '',1 )
            #parent.logger.info(" result %s" % ( shorter ) )
            msg.new_dir += os.sep + td + os.sep + "WIS" + os.sep + d
            t += '.' + d.replace('/','.')
            msg.topic=t
        except Exception as ex:
            parent.logger.error( "topic_builder", exc_info=True )
            return False
 
        #parent.logger.info( "after: topic=%s newdir=%s" % ( msg.topic, msg.new_dir) )
        
        
        return True

msg_gts2wistopic = msg_GTS2WISTopic(self)

self.on_message = msg_gts2wistopic.on_message

