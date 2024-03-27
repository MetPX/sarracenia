# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2021
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

import logging
import os
import sarracenia
import sys

from sarracenia.transfer import Transfer
from sarracenia.transfer import alarm_cancel, alarm_set, alarm_raise

import boto3, botocore

logger = logging.getLogger(__name__)


class S3(Transfer):
    """
    Simple Storage Service (S3)  ( https://en.wikipedia.org/wiki/Amazon_S3 ) 


    built with: 
        boto3's S3 client (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
    """

    #  ----------------------- MAGIC METHODS ----------------------

    def __init__(self, proto, options):

        super().__init__(proto, options)

        logger.debug("sr_s3 __init__")

        self.s3_client_config = botocore.config.Config(
                user_agent_extra= 'Sarracenia/' + sarracenia.__version__
            )

        self.s3_transfer_config = boto3.s3.transfer.S3TransferConfig()
        if hasattr(self.o, 'byteRateMax'):
            self.s3_transfer_config.max_bandwidth = self.o.byteRateMax


        self.__init()
    

    ##  --------------------- PRIVATE METHODS ---------------------
        
    def __init(self):
        Transfer.init(self)

        logger.debug("sr_s3 __init")
        self.connected = False
        self.client = None
        self.details = None
        self.seek = True

        self.bucket = None
        self.client_args = {}

        self.cwd = ''

        self.entries = {}

    def __credentials(self):
        logger.debug("sr_s3 __credentials %s" % self.sendTo)

        try:
            ok, details = self.o.credentials.get(self.sendTo)
            if details: url = details.url

            if url.username != '':
                self.client_args['aws_access_key_id'] = url.username
            if url.password != '':
                self.client_args['aws_secret_access_key'] = url.password
            if hasattr(details, 's3_session_token'):
                self.client_args['aws_session_token'] = details.s3_session_token
            if hasattr(details, 's3_endpoint'):
                self.client_args['endpoint'] = details.s3_endpoint

            return True

        except:
            logger.error("sr_s3/credentials: unable to get credentials for %s" % self.sendTo)
            logger.debug('Exception details: ', exc_info=True)

        return False
    

    ##  ---------------------- PUBLIC METHODS ---------------------

    def cd(self, path):
        logger.debug("sr_s3 cd %s" % path)
        self.cwd = os.path.dirname(path)
        self.path = path

    def check_is_connected(self):
        logger.debug("sr_s3 check_is_connected")

        if not self.connected : return False

        if self.sendTo != self.o.sendTo:
            self.close()
            return False

        return True

    def chmod(self, perms):
        logger.debug(f"sr_s3 chmod {perms}")
        return
        
    def close(self):
        logger.debug("sr_s3 close")
        self.connected = False
        self.client = None
        return

    def connect(self):
        logger.debug("sr_s3 connect %s" % self.o.sendTo)

        self.__credentials()

        self.client = boto3.client('s3', Config=self.s3_client_config, **self.client_args)
        self.connected = True

        return True
        
    def delete(self, path):
        logger.debug("sr_s3 delete %s" % path)
        # if delete does not work (file not found) run pwd to see if connection is ok
        self.client.delete_object(Bucket=self.bucket, Key=path)

    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0, exactLength=False):
        logger.debug("sr_s3 get; self.path %s" % self.path)
        logger.debug("get %s %s %d" % (remote_file, local_file, local_offset))


        # open local file
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo
        if self.sumalgo: self.sumalgo.set_path(remote_file)

        # download
        self.write_chunk_init(dst)

        self.client.download_file(Bucket=self.bucket, Key=remote_file, Filename=local_file, Callback=self.write_chunk, Config=self.s3_transfer_config)

        rw_length = self.write_chunk_end()

        # close
        self.local_write_close(dst)

        return rw_length
    
    def getAccelerated (self, msg, remote_file, local_file, length=0 ):
        return self.get(msg, remote_file, local_file, 0, 0, length, False)
    
    def ls(self):
        logger.debug("sr_s3 ls")

        self.entries = {}

        paginator = self.client.get_paginator('list_objects_v2')
        page_iterator  = paginator.paginate(Bucket=self.bucket, Prefix=self.path)

        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    self.entries += obj['Key'].replace(self.path, "")

        return self.entries
    
    def put(self,
            msg,
            local_file,
            remote_file,
            local_offset=0,
            remote_offset=0,
            length=0):
        logger.debug("sr_s3 put; %s %s" % (local_file, remote_file))

        # open
        src = self.local_read_open(local_file, local_offset)

        # upload
        self.client.upload_file( Filename=local_file, Bucket=self.bucket, Key=remote_file, Callback=self.write_chunk, Config=self.s3_transfer_config)

        rw_length = self.write_chunk_end()

        # close
        self.local_read_close(src)

        return rw_length

    def putAccelerated (self, msg, remote_file, local_file, length=0 ):
        return self.put(msg,local_file, remote_file, 0, 0, length)

    def registered_as():
        return ['s3']
    
    def rename(self, remote_old, remote_new):
        self.client.copy_object(Bucket=self.bucket, CopySource=remote_old, Key=remote_new)
        self.client.delete_object(Bucket=self.bucket, Key=remote_old)
    
    def rmdir(self, path):
        logger.debug("sr_s3 rmdir %s" % path)
        paginator = self.client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=path + "/")

        delete_us = dict(Objects=[])
        for item in pages.search('Contents'):
            delete_us['Objects'].append(dict(Key=item['Key']))

            # flush once aws limit reached
            if len(delete_us['Objects']) >= 500:
                self.client.delete_objects(Bucket=self.bucket, Delete=delete_us)
                delete_us = dict(Objects=[])

        # flush rest
        if len(delete_us['Objects']):
            self.client.delete_objects(Bucket=self.bucket, Delete=delete_us)

    def umask(self):
        logger.debug("sr_s3 umask")
        return