#!/usr/bin/python3

"""
S3 Cloud Sender - Plugin to send data into S3 buckets
======================================================

This plugin lets you send local data into S3 buckets. It is based on the S3CloudPublisher plugin by Tom Kralidis
and Tyson Kaufmann, found here: 
https://github.com/MetPX/sr3-examples/blob/main/cloud-publisher-s3/config/sr3/plugins/s3CloudPublisher.py

This version is refactored into a Sender plugin (instead of Subscribe), and uses Sarracenia's normal config parser
and credentials.conf file, instead of environment variables. It supports posting the URL where the file was uploaded
to, allows not specifying a region in the config, etc.

The file to be uploaded must already exist on the local filesystem.


Configuration
--------------


credentials.conf:
^^^^^^^^^^^^^^^^^

::

    s3://access_key_id:secret_access_key@endpoint.example.com/
    s3://access_key_id:secret_access_key@None


sender config:
^^^^^^^^^^^^^^^^^

::

    # sendTo
    # Specify endpoint and credentials.
    # - If you don't have an Access Key ID and/or endpoint URL, use None.
    # - If you specify an endpoint URL, it will be prefixed with https:// when connecting.
    # - List of endpoints: https://docs.aws.amazon.com/general/latest/gr/s3.html#s3_region
    sendTo s3://access_key_id@endpoint.example.com/
    # No endpoint specified, boto3 will auto-select.
    sendTo s3://access_key_id@None/
    # No endpoint, and no Access Key ID, for public buckets
    sendTo s3://None@None/

    # directory
    # Where to send the files, like a normal sr3 sender.
    directory first-thing-is-bucket-name/anything_else_is_a_path
    # path is not mandatory
    directory just-a-bucket-name

    # post_urlType
    # Optional - sets the format of the posted URL. Can be https or s3_uri. If this post_urlType *and* post_baseUrl are
    #            both not set, s3_uri will be used.
    # Important: this will override any post_baseUrl setting. You can choose to not use this option and manually set
    #            post_baseUrl to https://BUCKET_NAME.s3.REGION.amazonaws.com/ or s3://
    # When using https, BUCKET_NAME and REGION will automatically be replaced with the correct bucket name and region.
    #
    # https:  baseUrl=https://BUCKET_NAME.s3.REGION.amazonaws.com/ relPath=path/to/object.file
    # s3_uri: baseUrl=s3://                                        relPath=bucketname/path/to/object.file
    post_urlType s3_uri

    # AWS_regionName
    # Optional - specify a region name
    AWS_regionName ca-central-1

    # AWS_sessionToken
    # Optional - set a session token to use with the Access Key ID and Secret Access Key
    AWS_sessionToken your_very_long_token........

---

Authors: Tom Kralidis <tomkralidis@gmail.com>, Tyson Kaufmann, Reid Sunderland

Copyright (c) 2021 Tom Kralidis

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""


import logging
import os
from sarracenia.credentials import Credential
from sarracenia.flowcb import FlowCB
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3CloudSender(FlowCB):
    """ Sender to S3 destination.
    """

    def __init__(self, options):
        """initialize"""
        
        super().__init__(options, logger)

        # Allow setting a logLevel *only* for this plugin in the config file:
        # set send.s3CloudSender.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        logger.debug("S3CloudSender starting up")

        # S3 sender specific config options
        self.o.add_option('AWS_regionName',   kind='str', default_value=None) # optional
        self.o.add_option('AWS_sessionToken', kind='str', default_value=None) # optional
        self.o.add_option("post_urlType",     kind='str', default_value=None) # optional, overrides post_baseUrl

        # post_urlType must be https or s3, and handle unknown cases
        if self.o.post_urlType and self.o.post_urlType not in ['https', 's3_uri']:
            logger.warning(f"Unknown post_urlType: {self.o.post_urlType}")
        elif self.o.post_urlType and self.o.post_urlType == 's3_uri':
            self.o.post_baseUrl = "s3://"
        elif self.o.post_urlType and self.o.post_urlType == 'https':
            # a sender can send into multiple different buckets, the region gets set when the file is sent
            self.o.post_baseUrl = "https://BUCKET_NAME.s3.REGION.amazonaws.com/"
        elif not self.o.post_urlType and not self.o.post_baseUrl:
            logger.info("post_urlType and post_baseUrl not set, using s3://")
            self.o.post_baseUrl = "s3://"
        else:
            logger.debug(f"Using post_baseUrl {self.o.post_baseUrl}")

        # sendTo destination in config file sets the URL and access key ID
        #  - Access Key and Secret Access Key should be defined in credentials.conf
        #  - Just in case the user wants to use sendTo s3://None:None@None or s3://None@None, we add them to the
        #    credentials DB here, so s3://None:None@None doesn't have to exist in credentials.conf
        cred_details = Credential(urlstr="s3://None:None@None")
        self.o.credentials.add("s3://None@None", details=cred_details)

        # Find credentials matching the sendTo URL
        ok, details = self.o.credentials.get(self.o.sendTo)

        if not ok:
            error_msg = f"Failed to find credentials for sendTo URL {self.o.sendTo}"
            logger.error(error_msg)
            raise Exception(error_msg)

        if details.url.scheme != 's3':
            logger.warning(f"Using credentials with scheme ({details.url.scheme}) that is not s3")

        netloc = details.url.netloc.rsplit(sep='@', maxsplit=1) # split on the rightmost @
        usr_pwd = netloc[0].split(':')

        # If any options are "None", make them None. This should allow creating a client using the default/auto settings.
        self.s3_url = "https://"+netloc[1] if not (type(netloc[1]) == str and netloc[1] == "None") else None
        self.access_key_id = usr_pwd[0] if not (type(usr_pwd[0]) == str and usr_pwd[0] == "None") else None
        self.secret_access_key = usr_pwd[1] if not (type(usr_pwd[1]) == str and usr_pwd[1] == "None") else None

        logger.info(f"Successfully loaded credentials for sendTo URL {self.o.sendTo}")

        self.s3_client = boto3.client('s3', endpoint_url=self.s3_url, aws_access_key_id=self.access_key_id, 
                                      aws_secret_access_key=self.secret_access_key,
                                      region_name=self.o.AWS_regionName, aws_session_token=self.o.AWS_sessionToken)

    def send(self, msg):

        logger.debug(f"Received msg: {msg}")
        logger.debug(f"Received msg: format={msg['_format']}, baseUrl={msg['baseUrl']}, " +
                     f"relPath={msg['relPath']}, new_dir={msg['new_dir']}, new_file={msg['new_file']}")

        # Bucket name and (optional remote path) come from the directory setting in the config
        # remote path should not start with /
        new_dir_parts = msg['new_dir'].strip('/').split('/')
        s3_bucket_name = new_dir_parts[0]
        if len(new_dir_parts) > 1: # new_dir (directory in config file) has more parts than just the bucket name
            remote_path = os.path.normpath(os.path.join(*new_dir_parts[1:], msg['new_file']))
        else:
            remote_path = msg['new_file']

        # Local file, from baseDir + relPath (relPath shouldn't start with a /)
        local_file = os.path.join(self.o.baseDir, msg['relPath'].lstrip('/'))
        if not os.path.isfile(local_file):
            logger.error(f"File does not exist: {local_file} (baseDir: {self.o.baseDir}, relPath: {msg['relPath']})")
            return False

        logger.debug(f"Going to upload local file: {local_file} to S3 bucket: {s3_bucket_name}, path: {remote_path}")

        try:
            self.s3_client.upload_file(local_file, s3_bucket_name, remote_path)
        except Exception as e:
            # The exception gives a nice explanation already
            logger.error(f"{e}")
            logger.debug("Exception details:", exc_info=True)
            return False
        
        logger.info(f"Sent {local_file} into S3 bucket: {s3_bucket_name}, path: {remote_path}")

        # Update the message
        msg['new_baseUrl'] = self.o.post_baseUrl

        if 'BUCKET_NAME' in msg['new_baseUrl']:
            msg['new_baseUrl'] = msg['new_baseUrl'].replace('BUCKET_NAME', s3_bucket_name)

        # Figure out the region when using https baseUrl
        if 'REGION' in msg['new_baseUrl']:
            try:
                resp = self.s3_client.head_bucket(Bucket=s3_bucket_name)
                region = resp['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']
                msg['new_baseUrl'] = msg['new_baseUrl'].replace('REGION', region)
            except Exception as e:
                logger.error("Couldn't determine region for HTTPS URL, setting baseUrl = s3://")
                logger.debug("Exception details", exc_info=True)
                msg['new_baseUrl'] = "s3://"

        # relPath depends on the type of URL posted
        if 's3://' in msg['new_baseUrl']:
            msg['new_relPath'] = s3_bucket_name + '/' + remote_path
        elif s3_bucket_name in msg['new_baseUrl']:
            msg['new_relPath'] = remote_path
        else:
            msg['new_baseUrl'] = 's3://'
            msg['new_relPath'] = remote_path
            logger.error(f"Couldn't determine baseUrl type for {msg['new_baseUrl']}, set to s3:// with relPath {msg['new_relPath']}")

        logger.debug(f"Modified msg: {msg}")

        return True

    def __repr__(self):
        return '<S3CloudSender>'

