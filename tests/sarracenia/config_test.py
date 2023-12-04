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
     assert try_pattern(  options, message, "/pub/DATASETS/NOAA/G02158/unmasked/${%Y}/${%m}_${%b}", \
            "/pub/DATASETS/NOAA/G02158/unmasked" + '/[0-9]{4}/[0-9]{2}_[A-Z]{1}[a-z]{2}' )
     assert try_pattern(  options, message, "${PBD}/${%Y}/${SOURCE}/AIRNOW/CSV/BCMOE/${%H}/",  \
             options.post_baseDir + '/[0-9]{4}/'+ message['source'] +'/AIRNOW/CSV/BCMOE/[0-9]{2}/' )

     options.sundew_compat_regex_first_match_is_zero = True
     options.post_baseDir = '/apps/sarra/public_data'
     input_path='sftp://sarra@server//var/opt/CampbellSci/LoggerNet/data/WQL/WQL_final_storage_1.dat'
     accept_regex= r'.*.data.(.*)/.*'
     logger.info( f"path matched: {input_path} against: {accept_regex}" )
     message['_matches'] = re.match( accept_regex, input_path )
     assert( try_pattern( options, message, "${PBD}/${YYYYMMDD}/${SOURCE}/loggernet/${0}/", 
         "/apps/sarra/public_data/[0-9]{8}/WhereDataComesFrom/loggernet/WQL" ) )

     logger.info( "Next is an error message generated because the fourth group does not exist. Expected result is that the ${4} is not replaced." )
     options.sundew_compat_regex_first_match_is_zero = False
     message['_matches'] = re.match( r'.*.data.(.*)/.*_([0-9])\.', input_path )
     assert( try_pattern( options, message, "${PBD}/${YYYYMMDD}/${SOURCE}/loggernet/${1}${4}",
         r"/apps/sarra/public_data/[0-9]{8}/WhereDataComesFrom/loggernet/WQL\$\{4\}" ) )

     
     options.sundew_compat_regex_first_match_is_zero = True
     input_path= r'https://hpfx.collab.science.gc.ca/20231127/WXO-DD/meteocode/que/cmml/TRANSMIT.FPCN71.11.27.1000Z.xml'
     accept_regex= r'.*/WXO-DD/meteocode/(atl|ont|pnr|pyr|que)/.*/TRANSMIT\.FP([A-Z][A-Z]).*([0-2][0-9][0-6][0-9]Z).*'
     logger.info( f"path matched: {input_path} against: {accept_regex}" )
     message['_matches'] = re.match( accept_regex, input_path )
     print( f" matched: {message['_matches']} ")

     assert( try_pattern( options, message, '/tmp/meteocode/${2}/${0}/${1}' , r'/tmp/meteocode/1000Z/que/CN' ))

     options.sundew_compat_regex_first_match_is_zero = False
     assert( try_pattern( options, message, '/tmp/meteocode/${3}/${1}/${2}' , r'/tmp/meteocode/1000Z/que/CN' ))

     options.sundew_compat_regex_first_match_is_zero = True
     assert( try_pattern( options, None, '${PBD}/${%Y%m%d}' , r'/apps/sarra/public_data/[0-9]{8}' ))



     # to get stuff to print out, make it fail.
     #assert False 
     
