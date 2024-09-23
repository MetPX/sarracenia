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
import paramiko
import stat
import json

from sarracenia.transfer import Transfer

import boto3, botocore
from boto3.s3.transfer import TransferConfig

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

        self.s3_transfer_config = TransferConfig()
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
        self.sendTo = None

        self.bucket = None
        self.client_args = {}

        self.path = ""
        self.cwd = ""

        self.entries = {}

        self._Metadata_Key = 'sarracenia_v3'

    def __credentials(self) -> bool:
        logger.debug("%s" % self.sendTo)

        try:
            ok, details = self.o.credentials.get(self.sendTo)
            if details:
                url = details.url

            self.bucket = details.url.hostname

            if url.username != '':
                self.client_args['aws_access_key_id'] = url.username
            if url.password != '':
                self.client_args['aws_secret_access_key'] = url.password
            if hasattr(details, 's3_session_token'):
                self.client_args['aws_session_token'] = details.s3_session_token
            if hasattr(details, 's3_endpoint'):
                self.client_args['endpoint_url'] = details.s3_endpoint

            return True

        except:
            logger.error("sr_s3/credentials: unable to get credentials for %s" % self.sendTo)
            logger.debug('Exception details: ', exc_info=True)

        return False
    

    ##  ---------------------- PUBLIC METHODS ---------------------

    def cd(self, path):
        logger.debug("sr_s3 cd %s" % path)
        self.cwd = os.path.dirname(path)
        self.path = path.strip('/') + "/"

    def cd_forced(self, path):
        logger.debug("sr_s3 cd %s" % path)
        self.cwd = os.path.dirname(path)
        self.path = path.strip('/') + "/"

    def check_is_connected(self) -> bool:
        logger.debug("sr_s3 check_is_connected")

        if not self.connected:
            return False

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
        self.sendTo = None
        return

    def connect(self) -> bool:
        logger.debug("creating boto3 client")

        self.sendTo = self.o.sendTo

        self.__credentials()

        try:
            self.client = boto3.client('s3', config=self.s3_client_config, **self.client_args)
            buckets = self.client.list_buckets()
            if self.bucket in [b['Name'] for b in buckets['Buckets']]:
                self.connected = True
                logger.debug(f"Connected to bucket {self.bucket} in {self.client.get_bucket_location(Bucket=self.bucket)['LocationConstraint']}")
                return True
            else:
                logger.error(f"Can't find bucket called {self.bucket}")

        except botocore.exceptions.ClientError as e:
            logger.error(f"unable to establish boto3 connection: {e}")
        except botocore.exceptions.NoCredentialsError as e:
            logger.error(f"unable to establish boto3 connection, no credentials: {e}")
        except Exception as e:
            logger.error(f"Something else happened: {e}", exc_info=True)
            
        return False

    def delete(self, path):
        logger.debug("deleting %s" % path)
        self.client.delete_object(Bucket=self.bucket, Key=path)

    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0, exactLength=False) -> int:
        
        logger.debug("sr_s3 get; self.path %s" % self.path)

        file_key = self.path + remote_file
        logger.debug(f"get s3://{self.bucket}/{file_key} to {local_file}")

        self.client.download_file(Bucket=self.bucket, Key=file_key, Filename=local_file, Config=self.s3_transfer_config)

        rw_length = os.stat(local_file).st_size

        return rw_length

    def getcwd(self):
        if self.client:
            return self.cwd
        else:
            return None
    
    def ls(self):
        logger.debug(f"ls-ing items in {self.bucket}/{self.path}")

        self.entries = {}

        paginator = self.client.get_paginator('list_objects_v2')
        page_iterator  = paginator.paginate(Bucket=self.bucket, Prefix=self.path, Delimiter='/')

        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    filename = obj['Key'].replace(self.path, '', 1)
                    if filename == "":
                        continue
                    
                    entry = paramiko.SFTPAttributes()

                    obj_metadata = self.client.head_object(Bucket=self.bucket, Key=obj['Key'])['Metadata']

                    if self._Metadata_Key in obj_metadata:
                        sr_metadata = json.loads(obj_metadata[self._Metadata_Key])
                        entry.sr_mtime = sr_metadata['mtime']
                        entry.sr_identity = sr_metadata['identity']
                    
                    if 'LastModified' in obj:
                        t = obj["LastModified"].timestamp()
                        entry.st_atime = t
                        entry.st_mtime = t
                    if 'Size' in obj:
                        entry.st_size = obj['Size']
                        
                    
                    entry.st_mode = 0o644

                    self.entries[filename] = entry

            if 'CommonPrefixes' in page:
                for prefix in page['CommonPrefixes']:
                    logger.debug(f"Found folder {prefix['Prefix']}")

                    filename = prefix['Prefix'].replace(self.path, '', 1).rstrip("/")
                    if filename == "":
                        continue

                    entry = paramiko.SFTPAttributes()
                    entry.st_mode = 0o755 | stat.S_IFDIR
        
                    self.entries[filename] = entry

        logger.debug(f"self.entries={self.entries}")
        return self.entries
    
    def mkdir(self, remote_dir):
        logger.debug(f"mkdir {remote_dir}; {self.path}")
        return

    def put(self,
            msg,
            local_file,
            remote_file,
            local_offset=0,
            remote_offset=0,
            length=0) -> int:
        logger.debug("sr_s3 put; %s %s" % (local_file, remote_file))

        file_key = self.path + remote_file
        logger.debug(f"put {local_file} to s3://{self.bucket}/{file_key}")
        logger.debug(f"msg={msg}")

        extra_args = {
            'Metadata': {
                self._Metadata_Key: json.dumps({
                        'identity': msg['identity'],
                        'mtime': msg['mtime'],
                    })
            }
        }

        # upload
        try:
            self.client.upload_file( Filename=local_file, Bucket=self.bucket, Key=file_key, Config=self.s3_transfer_config, ExtraArgs=extra_args)

            write_size = self.client.get_object_attributes(Bucket=self.bucket, Key=file_key, ObjectAttributes=['ObjectSize'])['ObjectSize']
            return write_size
        except Exception as e:
            logger.error(f"Something went wrong with the upload: {e}", exc_info=True)
            return -1

    def registered_as() -> list:
        return ['s3']
    
    def rename(self, remote_old, remote_new):
        logger.debug(f"remote_old={remote_old}; remote_new={remote_new}")
        self.client.copy_object(Bucket=self.bucket, CopySource=self.bucket + "/" + remote_old, Key=remote_new)
        self.client.delete_object(Bucket=self.bucket, Key=remote_old)
    
    def rmdir(self, path):
        logger.debug("%s" % path)
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
        logger.debug("umask")
        return
