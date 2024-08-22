import copy
import pytest
from tests.conftest import *
#from unittest.mock import Mock

import os
from base64 import b64decode
#import urllib.request
import logging
import re

import sarracenia
import sarracenia.config
import sarracenia.config.credentials

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

     options = copy.deepcopy(sarracenia.config.default_config())
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
     assert try_pattern( options, message, "a_path/${DONT_TOUCH_THIS}something/else", r"a_path/\${DONT_TOUCH_THIS}something/else")
     assert try_pattern( options, message, "a_path/${1DONT_TOUCH_THIS}something/else", r"a_path/\${1DONT_TOUCH_THIS}something/else")
     assert try_pattern( options, message, "/apps/sarra/public_data/20231214/SSC-DATAINTERCHANGE/MSC-BULLETINS/${T1}${T2}/${CCCC}/17", 
                        r"/apps/sarra/public_data/20231214/SSC-DATAINTERCHANGE/MSC-BULLETINS/\${T1}\${T2}/\${CCCC}/17")
     assert try_pattern( options, message, "a_path/${1DONT_TOUCH_THIS}some/${%H}/thing/${STILL_DONT_CHANGE_ME}/${%Y}/hello", 
                        r"a_path/\${1DONT_TOUCH_THIS}some/[0-2][0-9]/thing/\${STILL_DONT_CHANGE_ME}/[0-9]{4}/hello")

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


def test_read_line_declare():

     options = copy.deepcopy(sarracenia.config.default_config())
     options.baseDir = '/data/whereIcameFrom'
     options.documentRoot = options.baseDir
     options.post_baseDir = '/data/whereIamGoingTo'
     options.varTimeOffset= 0
     num_subscribers = len(options.declared_users)
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "declare subscriber sub1" )
     new_num_subscribers = len(options.declared_users)
     logger.info( f"before declare: {num_subscribers}, after: {new_num_subscribers}" )
     assert( num_subscribers +1 ==  new_num_subscribers )
     assert( options.declared_users['sub1'] == 'subscriber' )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "declare env VAR99=hoho" )
     assert( options.env['VAR99'] == 'hoho' )

def test_read_line_flags():

     options = copy.deepcopy(sarracenia.config.default_config())

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "download off" )
     assert( options.download == False )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "download on" )
     assert( options.download == True )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "download False" )
     assert( options.download == False )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "download True" )
     assert( options.download == True )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "download no" )
     assert( options.download == False )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "download yes" )
     assert( options.download == True )

     assert( options.acceptSizeWrong == False )
     assert( options.acceptUnmatched == True )
     assert( options.sourceFromExchange == False )
     assert( options.sourceFromMessage == False )
     assert( options.sundew_compat_regex_first_match_is_zero == False )
     assert( options.topicCopy == False )

def test_read_line_counts():

     options = copy.deepcopy(sarracenia.config.default_config())

     # crasher input:
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch -1" )
     assert( options.batch == -1 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch 1" )
     assert( options.batch == 1 )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch 1kb" )
     assert( options.batch == 1024 )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch 1k" )
     assert( options.batch == 1000 )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch 1m" )
     assert( options.batch == 1000000 )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch 1mb" )
     assert( options.batch == 1024*1024 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch 134684" )
     assert( options.batch == 134684 )

     # count truncates floats... is this a good thing?
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "batch 1.9" )
     assert( options.batch == 1 )

def test_read_line_floats():

     options = copy.deepcopy(sarracenia.config.default_config())

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "messageRateMax 1.5mb" )
     assert( options.messageRateMax == 1572864 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "messageRateMax 0.5k" )
     assert( options.messageRateMax == 500 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "messageRateMax 0.5kb" )
     assert( options.messageRateMax == 512 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "messageRateMax 0.5b" )
     assert( options.messageRateMax == 0.5 )


def test_read_line_sets():

     options = copy.deepcopy(sarracenia.config.default_config())
     logger.info( f" {options.fileEvents=} " )

     assert( options.fileEvents == set( ['create', 'delete', 'link', 'mkdir', 'modify', 'rmdir' ] ) )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "fileEvents -rmdir" )
     logger.info( f" {options.fileEvents=} " )
     assert( options.fileEvents == set( ['create', 'delete', 'link', 'mkdir', 'modify' ] ) )

     #FIXME: must print an error message... how to test for that?
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "fileEvents moodify" )
     logger.info( f" {options.fileEvents=} " )
     assert( options.fileEvents == set( [ 'moodify' ] ) )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "fileEvents modify" )
     logger.info( f" {options.fileEvents=} " )
     assert( options.fileEvents == set( [ 'modify' ] ) )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "fileEvents +link" )
     logger.info( f" {options.fileEvents=} " )
     assert( options.fileEvents == set( [ 'link', 'modify' ] ) )


def test_read_line_perms():

     options = copy.deepcopy(sarracenia.config.default_config())
     logger.info( f" {options.permDefault=:o} " )


     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "permDefault 0755" )
     logger.info( f" {options.permDefault=:o} " )
     assert( options.permDefault == 0o755 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "permDefault 644" )
     logger.info( f" {options.permDefault=:o} " )
     assert( options.permDefault == 0o644 )


def test_read_line_duration():

     options = copy.deepcopy(sarracenia.config.default_config())
     logger.info( f" {options.sleep=} " )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "sleep 30" )
     logger.info( f" {options.sleep=} " )
     assert( options.sleep == 30 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "sleep 30m" )
     logger.info( f" {options.sleep=} " )
     assert( options.sleep == 30*60 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "sleep 3h" )
     logger.info( f" {options.sleep=} " )
     assert( options.sleep == 3*60*60 )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "sleep 2d" )
     logger.info( f" {options.sleep=} " )
     assert( options.sleep == 2*24*60*60 )


def test_read_line_add_option():

     options = copy.deepcopy(sarracenia.config.default_config())

     options.add_option( 'list_one', kind='list', default_value=['1','2'], all_values=['1','2','3','4'] )
     logger.info( f" {options.list_one=} " )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "list_one 3" )
     logger.info( f" {options.list_one=} " )
     assert( options.list_one == ['1','2','3']  )

     options.add_option( 'str_one', kind='str', default_value='one' )
     logger.info( f" {options.str_one=} " )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "str_one too" )
     logger.info( f" {options.str_one=} " )
     assert( options.str_one == 'too'  )

     options.add_option( 'set_one', kind='set', default_value=['1','2'], all_values=['1','2','3','4'] )
     logger.info( f" {options.set_one=} " )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "set_one +3" )
     logger.info( f" {options.set_one=} " )
     assert( options.set_one == set( ['1','2','3'] )  )

     options.add_option( 'count_one', kind='count', default_value=30 )
     logger.info( f" {options.count_one=} " )
     assert( options.count_one == 30  )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "count_one 60" )
     logger.info( f" {options.count_one=} " )
     assert( options.count_one == 60  )

     options.add_option( 'duration_one', kind='duration', default_value=30 )
     logger.info( f" {options.duration_one=} " )
     assert( options.duration_one == 30  )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "duration_one 60m" )
     logger.info( f" {options.duration_one=} " )
     assert( options.duration_one == 3600  )

     options.add_option( 'octal_one', kind='octal', default_value='644' )
     logger.info( f" {options.octal_one=:o} " )
     assert( options.octal_one == 0o644  )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "octal_one 755" )
     logger.info( f" {options.octal_one=:o} " )
     assert( options.octal_one == 0o755  )

     options.add_option( 'size_one', kind='size', default_value='644' )
     logger.info( f" {options.size_one=} " )
     assert( options.size_one == 644  )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "size_one 4kb" )
     logger.info( f" {options.size_one=} " )
     assert( options.size_one == 4096  )

     options.add_option( 'float_one', kind='float', default_value='3.4' )
     logger.info( f" {options.float_one=} " )
     assert( options.float_one == 3.4  )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "float_one 7.2" )
     logger.info( f" {options.float_one=} " )
     assert( options.float_one == 7.2  )

     options.add_option( 'flag_one', kind='flag', default_value=False )
     logger.info( f" {options.flag_one=} " )
     assert( options.flag_one == False  )
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "flag_one on" )
     logger.info( f" {options.flag_one=} " )
     assert( options.flag_one == True  )

def test_source_from_exchange():

     options = copy.deepcopy(sarracenia.config.default_config())

     # crasher input:
     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "declare source tsource" )
     assert( 'tsource' in options.declared_users )
     assert( options.declared_users['tsource'] == 'source' )

     options.parse_line( "subscribe", "ex1", "subscribe/ex1", 1, "exchange xs_tsource_favourite" )
     
     assert( options.exchange == 'xs_tsource_favourite' )

     source = options.get_source_from_exchange(options.exchange)
     assert( source == 'tsource' )

def test_subscription():

     o = copy.deepcopy(sarracenia.config.default_config())

     o.component = 'subscribe'
     o.config = 'ex1'
     o.action = 'start'
     o.no = 1
     before_add=len(o.credentials.credentials)
     o.credentials.add( 'amqp://lapinferoce:etpoilu@localhost' )
     o.credentials.add( 'amqp://capelli:tropcuit@localhost' )
     o.parse_line( o.component, o.config, "subscribe/ex1", 1, "broker amqp://lapinferoce@localhost" )
     o.parse_line( o.component, o.config, "subscribe/ex1", 2, "exchange hoho1" )

     assert( o.exchange == "hoho1" )

     o.parse_line( o.component, o.config, "subscribe/ex1", 3, "subtopic hoho.#" )
     o.parse_line( o.component, o.config, "subscribe/ex1", 3, "subtopic lala.hoho.#" )
     
     assert( hasattr(o,'subscriptions')  )
     assert( len(o.subscriptions)==1 )
     #assert( len(o.subscriptions[0]['bindings'] == 2 )

     o.parse_line( o.component, o.config, "subscribe/ex1", 2, "exchange xpublic" )
     o.parse_line( o.component, o.config, "subscribe/ex1", 3, "subtopic #" )

     assert( len(o.subscriptions)==1 )

     o.parse_line( o.component, o.config, "subscribe/ex1", 1, "broker amqp://capelli@localhost" )
     o.parse_line( o.component, o.config, "subscribe/ex1", 2, "queue myfavouriteQ" )
     o.parse_line( o.component, o.config, "subscribe/ex1", 2, "topicPrefix v02.post" )
     o.parse_line( o.component, o.config, "subscribe/ex1", 3, "subtopic #" )
            
     assert( len(o.subscriptions)==2 )

     logger.info( f" {o.subscriptions=} " )

def test_broker_finalize():

     options = copy.deepcopy(sarracenia.config.default_config())
     options.component = 'subscribe'
     options.config = 'ex1'
     options.action = 'start'

     before_add=len(options.credentials.credentials)

     options.credentials.add( 'amqp://bunnypeer:passthepoi@localhost' )

     after_add=len(options.credentials.credentials)

     assert( before_add + 1 == after_add )

     options.parse_line( options.component, options.config, "subscribe/ex1", 1, "broker amqp://bunnypeer@localhost" )
     options.parse_line( options.component, options.config, "subscribe/ex1", 1, "post_broker amqp://bunnypeer@localhost" )

     assert( options.broker.url.username == 'bunnypeer' )
     assert( options.broker.url.password == 'passthepoi' )
     assert( options.broker.url.username == 'bunnypeer' )
     assert( options.broker.url.password == 'passthepoi' )

     assert( options.exchange == None )
     assert( not hasattr(options,'post_exchange') )
     assert( not hasattr(options,'retry_ttl') )

     options.parse_line( options.component, options.config, "subscribe/ex1", 1, "directory ~/ex1" )
     options.parse_line( options.component, options.config, "subscribe/ex1", 1, "no 1" )
     
     assert( len(options.bindings) == 0 )
     assert( options.directory == '~/ex1' )
     assert( not hasattr( options, 'queue_filename' )  )
     assert( options.queueName == None  )

     options.finalize()

     assert( hasattr(options,'retry_ttl') )
     assert( hasattr( options, 'queue_filename' )  )
     assert( hasattr( options, 'queueName' )  )
     assert( type(options.queueName) == str )
     assert( options.queueName.startswith('q_bunnypeer.subscribe.ex1')  )
     assert( options.directory == os.path.expanduser( '~/ex1' ) )
     assert( len(options.bindings) == 1 )
     assert( options.exchange == 'xs_bunnypeer' )
     assert( options.post_exchange == [ 'xs_bunnypeer' ] )
     assert( hasattr(options,'nodupe_ttl') )
     assert( hasattr(options,'metricsFilename') )
     assert( hasattr(options,'pid_filename') )
     assert( hasattr(options,'retry_path') )
     assert( hasattr(options,'novipFilename') )
     assert( hasattr(options,'bindings') )
