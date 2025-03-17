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

import urllib.parse

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

        if hasattr(self.o, 'tlsRigour'):
            self.o.tlsRigour = self.o.tlsRigour.lower()
            if self.o.tlsRigour == 'lax':
                self.connection_verify = False
            else:
                self.connection_verify = True

        # The default INFO level for this logger is quite verbose, we might want to reduce it some day
        # logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel('WARNING')

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
        self.container_url = None
        self.credentials = None
        self.account = None
        self.key = None

        self.path = ""
        self.cwd = ""

        self.entries = {}

        self._Metadata_Key = 'sarracenia_v3'

    def __credentials(self) -> bool:
        # logger.debug("%s" % self.sendTo)
        
        sendTo = self.sendTo.lower().replace("azure://", "https://").replace("azblob://", "https://")

        try:
            ok, details = self.o.credentials.get(self.sendTo)
            url = None
            if details:
                url = details.url

                self.account = url.username if url.username != '' else None

                if url.password is not None and url.password != '':
                    self.key = urllib.parse.unquote_plus(url.password)
                else:
                    self.key = None

                if url.password is not None and url.password in sendTo:
                    sendTo = sendTo.replace(':'+ url.password, '')
                
                if url.username is not None and url.username in sendTo:
                    sendTo = sendTo.replace(url.username + '@', '')
    
            self.container_url = sendTo

            if details and hasattr(details, 'azure_credentials') and details.azure_credentials is not None:
                self.credentials = details.azure_credentials
                logger.debug("azure_credentials= is set, it will override any "+
                             "username/password (account name/key) in the URL")
                return True
            elif self.account and self.key:
                self.credentials = { "account_name": self.account,
                                     "account_key":  self.key,
                                   }
                return True
            else:
                # assuming this is ok, for anonymous access
                self.credentials = None
                logger.debug(f"no credential for {self.sendTo}")
                return True

        except Exception as e:
            logger.error(f"sr_azure/credentials: unable to get credentials for {self.sendTo} ({e})")
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
            # logger.debug(f"connecting to {self.container_url} with credential {self.credentials}")
            self.client = ContainerClient.from_container_url(container_url=self.container_url,
                                                             credential=self.credentials,
                                                             connection_timeout=self.o.timeout,
                                                             read_timeout=self.o.timeout,
                                                             retry_total=self.o.attempts,
                                                             connection_verify=self.connection_verify,
                                                             user_agent=self.__user_agent
                                                             )
            info = self.client.get_account_information()
            self.connected = True
            logger.debug(f"Connected to {self.container_url}; sku:{info['sku_name']}, kind:{info['account_kind']}")
            return True

        except azure.core.exceptions.ClientAuthenticationError as e:
            logger.error(f"Unable to establish connection, {e}")
        except Exception as e:
            logger.error(f"Something else happened: {e}", exc_info=True)
            
        return False

    def delete(self, path):
        logger.debug(f"deleting {path}")
        self.client.delete_blob(path.lstrip('/'))

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
          data = blob.download_blob()
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

        blobs = self.client.walk_blobs(name_starts_with=self.path)

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
        # logger.debug(f"uploading {local_file} to {remote_file}")

        file_key = self.path + remote_file
        logger.debug(f"{local_file} to {self.container_url}/{file_key}")
        # logger.debug(f"msg={msg}")

        md = {}
        if 'identity' in msg:
            md['identity'] = msg['identity']
        if 'mtime' in msg:
            md['mtime'] = msg['mtime']

        metadata = { self._Metadata_Key: json.dumps(md) }

        # upload
        try:
            with open(local_file, 'rb') as data:
                new_file = self.client.upload_blob(name=file_key, data=data, metadata=metadata)
            #self.client.upload_file( Filename=local_file, Bucket=self.bucket, Key=file_key, Config=self.s3_transfer_config, ExtraArgs=extra_args)

            write_size = new_file.get_blob_properties().size
            logger.debug(f'uploaded {local_file} to {self.container_url}/{file_key}')
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
        b_new.start_copy_from_url(from_url)
        self.client.delete_blob(remote_old.lstrip('/'))
    
    def rmdir(self, path):
        blobList=[*self.client.list_blobs(name_starts_with=path)]
        
        logger.debug(f"deleting {len(blobList)} blobs under {path}")
        while len(blobList) > 0:
            first256 = blobList[0:255]
            self.client.delete_blobs(*first256, delete_snapshots='include')     # delete_blobs() is faster!
            logger.debug("deleted " + str(len(first256)) + " of " + str(len(blobList)) + " blobs")
            del blobList[0:255]

    def umask(self):
        logger.debug("umask")
        return
