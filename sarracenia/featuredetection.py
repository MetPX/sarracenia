#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
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

"""
  Extra Feature Scanning and Enablement.

  checking for extra dependencies, not "hard" dependencies ("requires")
  listed as features in setup.py and omitted entirely from debian packaging.
  this allows installation with fewer dependencies ahead of time, and then
  provide some messaging to users when they "need" an optional dependency.
 
  optional features can be enabled using pip install metpx-sr3[extra]
  where extra is one of the features listed below. Alternatively,
  one can just install the modules that are needed and the functionality
  will be enabled after a component restart.
  
  amqp - ability to communicate with AMQP (rabbitmq) brokers
  mqtt - ability to communicate with MQTT brokers
  filetypes - ability to
  ftppoll - ability to poll FTP servers
  vip  - enable vip (Virtual IP) settings to implement singleton processing
         for high availability support.
  watch - monitor files or directories for changes.

"""

import logging
import sys

logger = logging.getLogger(__name__)

features = { 
    'amqp' : { 'modules_needed': [ 'amqp' ], 'present': False, 
            'lament' : 'cannot connect to rabbitmq brokers', 
            'rejoice' : 'can connect to rabbitmq brokers' },
    'azurestorage' : { 'modules_needed': [ 'azure-storage-blob' ], 'present': False, 
            'lament' : 'cannot connect natively to Azure Stoarge accounts', 
            'rejoice' : 'can connect natively to Azure Stoarge accounts' },
   'appdirs' : { 'modules_needed': [ 'appdirs' ], 'present': False, 
           'lament' : 'assume linux file placement under home dir', 
           'rejoice': 'place configuration and state files appropriately for platform (windows/mac/linux)', },
   'filetypes' : { 'modules_needed': ['magic'], 'present': False, 
           'lament': '(pip package python-magic, on windows python-magic-bin) will not be able to set content headers' ,
           'rejoice': 'able to set content headers' },
   'ftppoll' : { 'modules_needed': ['dateparser', 'pytz'], 'present': False, 
       'lament' : 'not able to poll with ftp' ,
       'rejoice' : 'able to poll with ftp' },
   'humanize' : { 'modules_needed': ['humanize', 'humanfriendly' ], 'present': False, 
           'lament': 'humans will have to read larger, uglier numbers',
           'rejoice': 'humans numbers that are easier to read.' },
   'jsonlogs' : { 'modules_needed': ['pythonjsonlogger' ], 'present': False, 
           'lament': 'only have raw text logs',
           'rejoice': 'can write json logs, in addition to text ones.' },
   'mqtt' : { 'modules_needed': ['paho.mqtt.client'], 'present': False, 
           'lament': 'cannot connect to mqtt brokers (need >= 2.1.0)' ,
           'rejoice': 'can connect to mqtt brokers' },
   'process' : { 'modules_needed': ['psutil'], 'present': False,
        'lament': 'cannot monitor running processes, sr3 CLI basically does not work.',
        'rejoice': 'can monitor, start, stop processes:  Sr3 CLI should basically work' },
   'reassembly' :  { 'modules_needed': [ 'flufl.lock' ], 'Needed': True,
        'lament' : 'need to lock block segmented files to put them back together',
        'rejoice' : 'can reassemble block segmented files transferred' },
   'redis' : { 'modules_needed': [ 'redis', 'redis_lock' ],
        'lament': 'cannot use redis implementations of retry and nodupe',
        'rejoice': 'can use redis implementations of retry and nodupe'
        },
   'retry': { 'modules_needed': ['jsonpickle'], 'present': False,
           'lament': 'unable to use local queues on the side (disk or redis) to retry messages later',
           'rejoice': 'can write messages to local queues to retry failed publishes/sends/downloads'},
    's3' : { 'modules_needed': [ 'boto3' ], 'present': False, 
        'lament' : 'cannot connect natively to S3-compatible locations (AWS S3, Minio, etc..)', 
        'rejoice': 'able to connect natively to S3-compatible locations (AWS S3, Minio, etc..)', },
   'sftp' : { 'modules_needed': [ 'paramiko' ],
        'lament': 'cannot use or access sftp/ssh based services',
        'rejoice': 'can use sftp or ssh based services'
        },
   'vip'  : { 'modules_needed': ['netifaces'] , 'present': False, 
           'lament': 'will not be able to use the vip option for high availability clustering' ,
           'rejoice': 'able to use the vip option for high availability clustering' },
   'watch'  : { 'modules_needed': ['watchdog'] , 'present': False, 
           'lament': 'cannot watch directories' ,
           'rejoice': 'watch directories' },
   'xattr'  : { 'modules_needed': ['xattr'] , 'present': False, 
           'lament': 'unable to store additional file metadata in extended attributes' ,
           'rejoice': 'will store file metadata in extended attributes' }
}

if sys.platform == 'win32':
    features['ctypes'] = { 'modules_needed':['ctypes'], 'present':False, 
           'lament': 'unable to store additional file metadata in extended attributes' ,
           'rejoice': 'will store file metadata in extended attributes' }
   
for x in features:
   
   features[x]['present']=True
   for y in  features[x]['modules_needed']:
       try:
           # used to use importlib, but that only tested if the module itself was installed.
           # https://github.com/MetPX/sarracenia/issues/753
           # It turns out that import can fail because of transitive deps, a package is installed,
           # but something that it depends on is missing, so it's clearer to just try an import.

           exec( f"import {y}" )
           logger.debug( f'found feature {y}, which should help to enable {x}')
       except:
           logger.debug( f"extra feature {x} needs missing module {y}. Disabled" ) 
           features[x]['present']=False


if features['filetypes']['present']:
    import magic
    if not hasattr(magic,'from_file'):
        features['filetypes']['present'] = False
        logger.debug( f'redhat magic bindings not supported.')

if features['mqtt']['present']:
    import paho.mqtt
    if not paho.mqtt.__version__ >= '2.1.0' :
        features['mqtt']['present'] = False
        logger.debug( f'paho-mqtt minimum version needed is 2.1.0')


