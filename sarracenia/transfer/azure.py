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

from azure.storage.blob import ContainerClient
import azure.core.exceptions

logger = logging.getLogger(__name__)

class Azure(Transfer):
    """
    Azure Storage Account blob storage  ( https://azure.microsoft.com/en-us/products/storage/blobs ) 


    built with: 
        Azure SKDs blob client (https://learn.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob?view=azure-python)
    """

    #  ----------------------- MAGIC METHODS ----------------------
    #region Magic
    def __init__(self, proto, options):

        super().__init__(proto, options)

        logger.debug("sr_azure __init__")

        self.__user_agent = 'Sarracenia/' + sarracenia.__version__

        self.__init()
    

    ##  --------------------- PRIVATE METHODS ---------------------
    #region Private
    def __init(self):
        Transfer.init(self)

        logger.debug("sr_azure __init")
        self.connected = False
        self.client = None
        self.details = None
        self.seek = True
        self.sendTo = None

        self.account = None
        self.container = None
        self.credentials = None

        self.path = ""
        self.cwd = ""

        self.entries = {}

        self._Metadata_Key = 'sarracenia_v3'

    def __credentials(self) -> bool:
        logger.debug("%s" % self.sendTo)

        try:
            ok, details = self.o.credentials.get(self.sendTo)

            self.account = details.url.hostname
            self.container = details.url.path.lstrip('/')
            self.container_url = f"https://{self.account}.blob.core.windows.net/{self.container}"

            if hasattr(details, 'azure_credentials'):
                self.credentials = details.azure_credentials

            return True

        except:
            logger.error("sr_azure/credentials: unable to get credentials for %s" % self.sendTo)
            logger.debug('Exception details: ', exc_info=True)

        return False
    

    ##  ---------------------- PUBLIC METHODS ---------------------
    #region Public
    def cd(self, path):
        logger.debug(f"changing into {path}")
        self.cwd = os.path.dirname(path)
        self.path = path.strip('/') + "/"
        self.path = self.path.lstrip('/')


    def cd_forced(self, path):
        logger.debug(f"forcing into  {path}")
        self.cd(path)

    def check_is_connected(self) -> bool:
        logger.debug("sr_azure check_is_connected")

        if not self.connected:
            return False

        if self.sendTo != self.o.sendTo:
            self.close()
            return False

        return True

    def chmod(self, perms):
        logger.debug(f"would change perms to {perms} if it was implemented")
        return
        
    def close(self):
        logger.debug("closing down connection")
        self.connected = False
        self.client = None
        self.sendTo = None
        return

    def connect(self) -> bool:
        logger.debug("creating azure blob client")

        self.sendTo = self.o.sendTo

        if not self.__credentials():
            logger.error(f"Unable to get credentials")
            return False

        try:
            self.client = ContainerClient.from_container_url(container_url=self.container_url, 
                                                            credential=self.credentials, connection_timeout=5, read_timeout=5, retry_total=1)
            info = self.client.get_account_information(user_agent=self.__user_agent)
            self.connected = True
            logger.debug(f"Connected to container {self.container} in account {self.account} ({self.container_url}); sku:{info['sku_name']}, kind:{info['account_kind']}")
            return True

        except azure.core.exceptions.ClientAuthenticationError as e:
            logger.error(f"Unable to establish connection, {e}")
        except Exception as e:
            logger.error(f"Something else happened: {e}", exc_info=True)
            
        return False

    def delete(self, path):
        logger.debug(f"deleting {path}")
        self.client.delete_blob(path.lstrip('/'), user_agent=self.__user_agent)

    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0, exactLength=False) -> int:
        
        logger.debug(f"downloading {remote_file} into {self.path}")

        file_key = self.path + remote_file
        logger.debug(f"get https://{self.container_url}/{file_key} to {local_file}")

        blob = self.client.get_blob_client(file_key)

        with open(local_file, 'wb') as file:
          data = blob.download_blob(user_agent=self.__user_agent)
          file.write(data.readall())

        rw_length = os.stat(local_file).st_size

        return rw_length
    
    def gethttpsUrl(self, path):
        return self.container_url + '/' + path

    
    def getcwd(self):
        if self.client:
            return self.cwd
        else:
            return None

    def ls(self):
        logger.debug(f"ls-ing items at {self.container_url}/{self.path}")

        self.entries = {}

        blobs = self.client.walk_blobs(name_starts_with=self.path, user_agent=self.__user_agent)

        for b in blobs:
            # files
            if not hasattr(b, 'prefix'):
                filename = b.name.replace(self.path, '', 1)
                if filename == "":
                    continue
                
                entry = paramiko.SFTPAttributes()

                entry.sr_httpsUrl = self.container_url + '/' + self.path + filename

                if self._Metadata_Key in b.metadata:
                    sr_metadata = json.loads(b.metadata[self._Metadata_Key])
                    entry.sr_mtime = sr_metadata['mtime']
                    entry.sr_identity = sr_metadata['identity']
                
                if hasattr(b, 'last_modified'):
                    t = b.last_modified.timestamp()
                    entry.st_atime = t
                    entry.st_mtime = t
                if hasattr(b, 'size'):
                    entry.st_size = b.size
                    
                entry.st_mode = 0o644

                self.entries[filename] = entry

            # folders
            else:
                logger.debug(f"Found folder {b.name}")

                filename = b.name.replace(self.path, '', 1).rstrip("/")
                if filename == "":
                    continue

                entry = paramiko.SFTPAttributes()
                entry.st_mode = 0o755 | stat.S_IFDIR
    
                self.entries[filename] = entry

        logger.debug(f"self.entries={self.entries}")
        return self.entries
    
    def mkdir(self, remote_dir):
        logger.debug(f"would mkdir {remote_dir} inside {self.path}, if it was supported")
        return

    def put(self,
            msg,
            local_file,
            remote_file,
            local_offset=0,
            remote_offset=0,
            length=0) -> int:
        logger.debug(f"uploading {local_file} to {remote_file}")

        file_key = self.path + remote_file
        logger.debug(f"put {local_file} to http://{self.container_url}/{file_key}")
        logger.debug(f"msg={msg}")

        metadata = {
                self._Metadata_Key: json.dumps({
                        'identity': msg['identity'],
                        'mtime': msg['mtime'],
                    })
            }

        # upload
        try:
            with open(local_file, 'rb') as data:
                new_file = self.client.upload_blob(name=file_key, data=data, metadata=metadata, user_agent=self.__user_agent)
            #self.client.upload_file( Filename=local_file, Bucket=self.bucket, Key=file_key, Config=self.s3_transfer_config, ExtraArgs=extra_args)

            write_size = new_file.get_blob_properties(user_agent=self.__user_agent).size
            return write_size
        except Exception as e:
            logger.error(f"Something went wrong with the upload: {e}", exc_info=True)
            return -1

    def registered_as() -> list:
        return ['azure', 'azblob']
    
    def rename(self, remote_old, remote_new):
        remote_new = remote_new.lstrip('/')
        b_new = self.client.get_blob_client(remote_new)

        from_url = self.container_url + "/" + remote_old + "?" + self.credentials

        logger.debug(f"remote_old={remote_old}; from_url={self.container_url}/{remote_old}; remote_new={remote_new}")
        b_new.start_copy_from_url(from_url, user_agent=self.__user_agent)
        self.client.delete_blob(remote_old.lstrip('/'), user_agent=self.__user_agent)
    
    def rmdir(self, path):
        blobList=[*self.client.list_blobs(name_starts_with=path, user_agent=self.__user_agent)]
        
        logger.debug(f"deleting {len(blobList)} blobs under {path}")
        while len(blobList) > 0:
            first256 = blobList[0:255]
            self.client.delete_blobs(*first256, delete_snapshots='include', user_agent=self.__user_agent)     # delete_blobs() is faster!
            logger.debug("deleted " + str(len(first256)) + " of " + str(len(blobList)) + " blobs")
            del blobList[0:255]

    def umask(self):
        logger.debug("umask")
        return
