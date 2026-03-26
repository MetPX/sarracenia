
import copy
import json
import os
import sarracenia

import logging

logger = logging.getLogger(__name__)


class Publisher(dict):

    def __init__(self, options ):

        if not hasattr(options,'post_broker'): 
            logger.error("missing publisher post_broker")
            return

        if not hasattr(options.post_broker, 'url'): 
            logger.error("post_broker: {options.post_broker} does not resolve, missing credentials?")
            return

        if not options.post_broker.url:
            logger.error("malformed publisher post_broker: {str(post_broker)}")
            return

        self['broker'] = copy.deepcopy(options.post_broker)

<<<<<<< HEAD
        exchange_root = None
        if hasattr(options,'post_exchange'):
            if  options.post_exchange != 'default':
                exchange_root = options.post_exchange
            else:
                exchange_root = 'xs_%s' % options.post_broker.url.username
=======
        exchange_root = getattr(options,'post_exchange', 'default' if self['broker'].url.scheme.lower().startswith('amqp') else None )

        if exchange_root == "default":
            if not hasattr(self['broker'].url,'username') or ( self['broker'].url.username == 'anonymous' ):
                exchange_root = 'xpublic'
            else:
                exchange_root = f'xs_{self["broker"].url.username}'
>>>>>>> issue1572_pas1

        already_a_list = hasattr(options,'post_exchange') and type(options.post_exchange) == list
        #logger.debug( f" {exchange_root=}  {already_a_list=} " )

        if exchange_root:
            if already_a_list:
                self['exchange'] = options.post_exchange
            else:
               if hasattr(options, 'post_exchangeSuffix'):
<<<<<<< HEAD
                   exchange_root += '_%s' % options.post_exchangeSuffix
=======
                   exchange_root += f'_{options.post_exchangeSuffix}'
>>>>>>> issue1572_pas1

               if hasattr(options, 'post_exchangeSplit') and options.post_exchangeSplit > 1:
                   l = []
                   for i in range(0, int(options.post_exchangeSplit)):
                       y = f"{exchange_root}{i:02d}"
                       l.append(y)
                   self['exchange'] = l
               else:
                   self['exchange'] = [ exchange_root ]

            if 'exchange' not in self:
                logger.error("malformed publisher, missing (post_)exchange")
                return

        # else, *exchange* will not be present...

        if hasattr(options,'tlsRigour') :
            self['tlsRigour'] = options.tlsRigour
    
        if hasattr(options,'post_format') :
            self['format'] = options.post_format
        elif hasattr(options,'post_topicPrefix') and options.post_topicPrefix[0] in [ 'v02', 'v03' ]:
            self['format'] = options.post_topicPrefix[0]
        else:
            self['format'] = 'v03'

        if hasattr(options,'post_topicPrefix') and options.post_topicPrefix:
            self['topicPrefix'] = options.post_topicPrefix
        elif hasattr(options, 'topicPrefix') and options.topicPrefix:
            self['topicPrefix'] = options.topicPrefix
        else:
            self['topicPrefix'] = []

        for a in [ 'baseDir', 'baseUrl', 'exchangeSplit', 'topicPrefix' ]:
            aa = "post_"+a
            if hasattr(options, aa):
                self[a] = getattr(options,aa)

        if (not 'baseUrl' in self or not self['baseUrl']) and hasattr(options,'pollUrl') and options.pollUrl:
            self['baseUrl'] = options.pollUrl

        if not 'baseDir' in self or not self['baseDir']:
            if self['baseUrl'] and ( self['baseUrl'][0:5] in [ 'file:' ] ):
                self['baseDir'] = self['baseUrl'][5:]
            elif self['baseUrl'] and ( self['baseUrl'][0:5] in [ 'sftp:' ] ):
                u =  sarracenia.baseUrlParse(self['baseUrl'])
                self['baseDir'] = u.path


        for a in [ 'auto_delete', 'durable', 'exchangeDeclare', 'messageAgeMax', 
                  'messageDebugDump', 'persistent', 'timeout' ]:
            if hasattr(options, a):
                self[a] = getattr(options,a)
        #logger.debug( f" {self} " )

    def __eq__(self,other):

        if 'broker' in self and 'broker' in other :
            if ( str(self['broker']) != str(other['broker']) ):
                return False
        elif ('broker' in self) or ('broker' in other):
            return False
         
        if 'exchange' in self and 'exchange' in other:
            if ( self['exchange'] != other['exchange'] ):
                return False
        elif ('exchange' in self) or ('exchange' in other):
                return False

        if 'topicPrefix' in self and 'topicPrefix' in other:
            if ( self['topicPrefix'] != other['topicPrefix'] ):
                return False
        elif ('topicPrefix' in self) or ('topicPrefix' in other):
            return False

        if 'format' in self and 'format' in other:
            if ( self['format'] != other['format'] ):
                return False
        elif ('format' in self) or ('format' in other):
            return False

        return True

class Publishers(list):
    # list of publishers

    def add(self, new_publisher):

        found=False
        if not new_publisher:
            return

        for s in self:
            if ( s == new_publisher ):
                found=True

        if not found:
            self.append(new_publisher)
