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

import boto3

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

        self.__init()
    
    ##  --------------------- PRIVATE METHODS ---------------------

    # init
    def __init(self):
        Transfer.init(self)

        logger.debug("sr_s3 __init")
        self.connected = False
        self.client = boto3.client('s3')
        self.details = None
        self.seek = True

        self.bucket = 's3transfer'
        self.cwd = ''

        self.entries = {}

    ##  ---------------------- PUBLIC METHODS ---------------------
    def registered_as():
        return ['s3']
    
    def cd(self, path):
        logger.debug("sr_s3 cd %s" % path)
        self.cwd = os.path.dirname(path)
        self.path = path
    
    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0, exactLength=False):
        logger.debug("get %s %s %d" % (remote_file, local_file, local_offset))
        logger.debug("sr_s3 self.path %s" % self.path)

        # open local file
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo
        if self.sumalgo: self.sumalgo.set_path(remote_file)

        # download
        self.write_chunk_init(dst)

        self.client.download_file(Bucket=self.bucket, Key=remote_file, Filename=local_file, Callback=self.write_chunk)

        rw_length = self.write_chunk_end()

        # close
        self.local_write_close(dst)

        return rw_length
    
    def put(self,
            msg,
            local_file,
            remote_file,
            local_offset=0,
            remote_offset=0,
            length=0):
        logger.debug("sr_s3 put %s %s" % (local_file, remote_file))

        # open
        src = self.local_read_open(local_file, local_offset)

        # upload
        self.client.upload_file( Filename=local_file, Bucket=self.bucket, Key=remote_file, Callback=self.write_chunk)

        rw_length = self.write_chunk_end()

        # close
        self.local_read_close(src)

        return rw_length

    def ls(self):
        logger.debug("sr_s3 ls")

        self.entries = {}

        #objects = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=self.cwd)

        paginator = self.client.get_paginator('list_objects_v2')
        page_iterator  = paginator.paginate(Bucket=self.bucket, Prefix=self.path)

        for page in page_iterator:
            for obj in page['Contents']:
                self.entries += obj['Key'].replace(self.path, "")

        return self.entries
    
        # delete
    def delete(self, path):
        logger.debug("sr_s3 delete %s" % path)
        # if delete does not work (file not found) run pwd to see if connection is ok
        self.client.delete_object(Bucket=self.bucket, Key=path)


    def rename(self, remote_old, remote_new):
        self.client.copy_object(Bucket=self.bucket, CopySource=remote_old, Key=remote_new)
        self.client.delete_object(Bucket=self.bucket, Key=remote_old)
    
    # rmdir
    def rmdir(self, path):
        logger.debug("sr_s3 rmdir %s" % path)
        paginator = self.client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=path + "/")

        delete_us = dict(Objects=[])
        for item in pages.search('Contents'):
            delete_us['Objects'].append(dict(Key=item['Key']))

            # flush once aws limit reached
            if len(delete_us['Objects']) >= 1000:
                self.client.delete_objects(Bucket=self.bucket, Delete=delete_us)
                delete_us = dict(Objects=[])

        # flush rest
        if len(delete_us['Objects']):
            self.client.delete_objects(Bucket=self.bucket, Delete=delete_us)