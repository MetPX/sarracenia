
import copy
import json
import os

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

        if hasattr(options,'post_exchange'):
            exchange_root = options.post_exchange
        else:
            exchange_root = 'xs_%s' % options.post_broker.url.username

        already_a_list = hasattr(options,'post_exchange') and type(options.post_exchange) == list
        #logger.debug( f" {exchange_root=}  {already_a_list=} " )

        if already_a_list:
            self['exchange'] = options.post_exchange
        else:
           if hasattr(options, 'post_exchangeSuffix'):
               exchange_root += '_%s' % options.post_exchangeSuffix

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

        for a in [ 'auto_delete', 'durable', 'exchangeDeclare', 'exchangeSplit', 'messageAgeMax', 
                  'messageDebugDump', 'persistent', 'timeout' ]:
            if hasattr(options, a):
                self[a] = getattr(options,a)
        #logger.debug( f" {self} " )


class Publishers(list):
    # list of publishers

    def add(self, new_publisher):

        found=False
        if not new_publisher:
            return

        for s in self:
            #logger.debug( f" {s=}  vs. {new_publisher=} ")
            #logger.debug( f" {str(s['broker'])=}  vs. {str(new_publisher['broker'])=} ")
            if s == {}:
                continue

            if ( str(s['broker']) == str(new_publisher['broker']) ) and \
               ( s['exchange'] == new_publisher['exchange'] ):
                found=True

        if not found:
            self.append(new_publisher)
