#!/usr/bin/python3

"""
Plugin to authenticate with the EUMETSAT API
============================================================

This plugin enables authentication for URLs posted by the ``eumetsat.py`` poll plugin.

Uses the EUMETSAT Data Store APIs https://eumetsatspace.atlassian.net/wiki/spaces/DSDS/pages/315818088/Using+the+APIs

Requires that a consumer_key and consumer_secret are stored in the credentials.conf file, instead of the username and
password. To get the key and secret, log in here: https://data.eumetsat.int/search with a username and password.
Then click on your username/the person icon at the top right. Click API Key. You can get the key and secret from
this page. Create a new entry in credentials.conf with https://<consumer_key>:<consumer_secret>@api.eumetsat.int/
  
Configurable Options:
----------------------

``apiTokenUrl``:
^^^^^^^^^^^^^^^^^^^^

    Default is ``https://api.eumetsat.int/token``.

How to set up your download config:
------------------------------------
 
    Add ``callback authenticate.eumetsat``, in your subscribe, sarra or other download config.  

    Add ``https://<consumer_key>:<consumer_secret>@api.eumetsat.int/`` to your ``credentials.conf`` file.


Change log:
-----------

    - 2024-01: split into a separate, after_accept plugin instead of download.
    - 2024-07-23: refactor to use BearerToken parent class. after_accept is inherited from BearerToken.
"""

from sarracenia.flowcb.authenticate import BearerToken
import datetime
import logging
import requests

logger = logging.getLogger(__name__)

class Eumetsat(BearerToken):
    def __init__(self, options):
        super().__init__(options, logger)
        
        # Allow setting a logLevel *only* for this plugin in the config file:
        # set accept.auth_eumetsat.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        self.o.add_option('apiTokenUrl', kind='str', default_value='https://api.eumetsat.int/token')

        self._api_token = None 
        self._token_expiry_time = None
        # end __init__

    def get_token(self):
        """Given a consumer_key and consumer_secret, gets and returns an API token. 

        Code taken from https://gitlab.eumetsat.int/eumetlab/data-services/authorisation_functions/-/blob/master/authorisation_functions.py
        See API documentation here: https://eumetsatspace.atlassian.net/wiki/spaces/DSDS/pages/316014673/API+Authentication
        """
        now = datetime.datetime.utcnow()
        # Only request a token if there's no cached token, or it's expired
        if not self._api_token or not self._token_expiry_time or now >= self._token_expiry_time:
            try: 
                # Credentials - use consumer_key and consumer_secret to generate an API token
                ok, details = self.o.credentials.get(self.o.apiTokenUrl)
                if not ok:
                    logger.error(f"credential lookup for {self.o.apiTokenUrl} failed")
                    self._token_expiry_time = now
                    self._api_token = None
                    
                creds = details.url
                consumer_key = creds.username
                consumer_secret = creds.password
                response = requests.post(self.o.apiTokenUrl,
                    auth=requests.auth.HTTPBasicAuth(consumer_key, consumer_secret),
                    data = {'grant_type': 'client_credentials'},
                    headers = {"Content-Type" : "application/x-www-form-urlencoded"}
                )
                response_j = response.json()
                self._token_expiry_time = now + datetime.timedelta(seconds=response_j['expires_in'])
                self._api_token = response_j['access_token']
                
            except Exception as e:
                logger.error("Failed to get token")
                logger.debug("Exception details", exc_info=True)
                self._token_expiry_time = now
                self._api_token = None
        
        return self._api_token