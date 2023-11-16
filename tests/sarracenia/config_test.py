import pytest
#from unittest.mock import Mock

import os
from base64 import b64decode
#import urllib.request
import logging
import re

import sarracenia
import sarracenia.config

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


logger = logging.getLogger('sarracenia.config')
logger.setLevel('DEBUG')

def test_variableExpansion():

     options = sarracenia.config.default_config()
     options.baseDir = '/data/whereIcameFrom'
     options.documentRoot = options.baseDir
     options.post_baseDir = '/data/whereIamGoingTo'
     options.varTimeOffset= 0

     message = sarracenia.Message()
     message['source'] = 'WhereDataComesFrom'
     message['baseUrl'] = 'https://localhost/smorgasbord'

     result = options.variableExpansion( "${PDR}/${%Y%m%d}/", message );
     logger.debug( f"result: {result}" )
     good = re.compile( options.post_baseDir + '/[0-9]{8}/' )
     assert good.match(result)

     result = options.variableExpansion( "${PBD}/${%Y%m%d}/", message );
     logger.debug( f"result: {result}" )
     good = re.compile( options.post_baseDir + '/[0-9]{8}/' )
     assert good.match(result)

     result = options.variableExpansion( "${PBD}/${SOURCE}/${%Y%m%d}/boughsOfHolly", message );
     logger.debug( f"result: {result}" )
     good = re.compile( options.post_baseDir + '/' + message['source'] + '/[0-9]{8}/boughsOfHolly' )
     assert good.match(result)

     result = options.variableExpansion( "${PBD}/${BUPL}/${%Y%m%d}/falala", message );
     logger.debug( f"result: {result}" )
     good = re.compile( options.post_baseDir + '/smorgasbord/[0-9]{8}/falala' )
     assert good.match(result)

     result = options.variableExpansion( "${PBD}/${BUPL}/${%Y%m%d}/", message );
     logger.debug( f"result: {result}" )
     good = re.compile( options.post_baseDir + '/smorgasbord/[0-9]{8}/' )
     assert good.match(result)

     assert False 
     
     
