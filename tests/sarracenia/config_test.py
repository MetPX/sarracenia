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

def try_pattern( options, message, pattern, goodre ):
    """
       given a pattern, call variable expansion, and confirm it matches the resulting regex.

    """
    result = options.variableExpansion( pattern, message );
    logger.debug( f"input: {pattern} result: {result}" )
    good = re.compile( goodre )
    return good.match(result)

def test_variableExpansion():

     options = sarracenia.config.default_config()
     options.baseDir = '/data/whereIcameFrom'
     options.documentRoot = options.baseDir
     options.post_baseDir = '/data/whereIamGoingTo'
     options.varTimeOffset= 0

     message = sarracenia.Message()
     message['source'] = 'WhereDataComesFrom'
     message['baseUrl'] = 'https://localhost/smorgasbord'

     assert try_pattern(  options, message, "${PDR}/${%Y%m%d}/",  options.post_baseDir + '/[0-9]{8}/' )
     assert try_pattern(  options, message, "${PBD}/${%Y%m%d}/",  options.post_baseDir + '/[0-9]{8}/' )
     assert try_pattern(  options, message, "${PBD}/${SOURCE}/${%Y%m%d}/boughsOfHolly",  options.post_baseDir + '/' + message['source'] + '/[0-9]{8}/boughsOfHolly' )
     assert try_pattern(  options, message, "${PBD}/${BUPL}/${%Y%m%d}/falala",  options.post_baseDir + '/smorgasbord/[0-9]{8}/falala' )
     assert try_pattern(  options, message, "${PBD}/${BUPL}/${%Y%m%d}/",  options.post_baseDir + '/smorgasbord/[0-9]{8}/' )
     assert try_pattern(  options, message, "${PBD}/${%Y%m%d}/${SOURCE}/AIRNOW/CSV/BCMOE/${%H}/",  \
             options.post_baseDir + '/[0-9]{8}/'+ message['source'] +'/AIRNOW/CSV/BCMOE/[0-9]{2}/' )
     assert try_pattern(  options, message, "${PBD}/${%Y%m%d}/${SOURCE}/AIRNOW/CSV/BCMOE/${%o-4h%H}/",  \
             options.post_baseDir + '/[0-9]{8}/'+ message['source'] +'/AIRNOW/CSV/BCMOE/[0-9]{2}/' )


     # to get stuff to print out, make it fail.
     #assert False 
