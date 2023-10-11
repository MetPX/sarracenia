#!/usr/bin/python3

"""
Plugin to download from NASA using an Earthdata account
========================================================

This plugin enables authentication for URLs posted by the ``poll_NASA_CMR.py`` plugin, and other NASA data
sources that are compatible with bearer tokens that come from https://urs.earthdata.nasa.gov.

This plugin is required because it's not possible to use a username and password to authenticate with the URL
to be downloaded. Either you need to use a bearer token, or login to https://urs.earthdata.nasa.gov and download
your file using the authenticated session, which has cookies to track your login. 

Sarracenia supports bearer token authentication, so the default downloading code can be used. But, NASA bearer
tokens expire after 90 days. This plugin handles dynamically creating and retrieving the bearer tokens from the
https://urs.earthdata.nasa.gov API.

For every message processed by this plugin, it will add a credential with a valid bearer token matching the message's
baseUrl to Sarracenia's in-memory credential database.

  
Configurable Options:
----------------------

``earthdataUrl``:
^^^^^^^^^^^^^^^^^^^^

    Default is ``https://urs.earthdata.nasa.gov``. If you want to override it, you can specify the
    ``earthdataUrl https://your-endpoint.example.com`` option.

How to set up your download config:
--------------------------------
 
    Add ``callback accept.auth_NASA_Earthdata``, in your subscribe, sarra or other download config.  

    Add ``https://username:password@urs.earthdata.nasa.gov/`` to your ``credentials.conf`` file.  
    
    Optional: set ``acceptSizeWrong True`` in the sarra/subscribe config to suppress the WARNING message
     about a file being downloaded with no length given.

    For examples, see https://github.com/MetPX/sarracenia/tree/main/sarracenia/examples/subscribe files
    named ``*nasa_earthdata*.conf``. 

Change log:
-----------

    - 2023-10-10: first attempt at this plugin. The old v2 code re-implemented downloading, using a session with
      stored cookies. This should be better, because it uses the native sr3 download code.
"""

import sarracenia
import datetime
import logging
import requests

logger = logging.getLogger(__name__)

class Auth_nasa_earthdata(sarracenia.flowcb.FlowCB):
    def __init__(self, options):
        super().__init__(options, logger)
        
        # Allow setting a logLevel *only* for this plugin in the config file:
        # set accept.auth_NASA_Earthdata.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        logger.debug("plugin: Download_NASA_Earthdata __init__")

        self.o.add_option('earthdataUrl', kind='str', default_value='https://urs.earthdata.nasa.gov')

        if self.o.earthdataUrl[-1] == '/':
            self.o.earthdataUrl = self.o.earthdataUrl.strip('/')

        self._token = None
        self._token_expires = None # format MM/DD/YYYY, e.g. 12/25/2023

        # end __init__

    def after_accept(self, worklist):
        """ Doesn't actually do any downloading. First, get or create a bearer token from
            https://urs.earthdata.nasa.gov by logging in with the username and password from credentials.conf.
            Then adds the bearer token to Sarracenia's credentials DB for the message's baseUrl. This will allow
            the file to be downloaded from msg['baseUrl']+msg['relPath'] using the bearer token.
        """

        # It's not clear what time the token expires on the expiry date. If today = expiry date, then try to get a
        # token every time this runs. If it's not expired yet, we'll get the same token from the API and can try 
        # to check again on the next run. If it is expired, we should get a brand new token.
        today = datetime.datetime.utcnow().strftime("%m/%d/%Y")
        if self._token_expires and today == self._token_expires:
            logger.info("the token ending with ...{self._token[-5:]} expires today ({self._token_expires})")
            self._token = None
            self._token_expires = None

        # Get a token from the NASA API, if there isn't one already
        if not self._token:
            # Try to get a new token
            if not self.get_earthdata_token():
                logger.error(f"Failed to retrieve Bearer token from {self.o.earthdataUrl}. " + 
                             f"Can't download {msg['baseUrl']}{msg['relPath']}")

        for msg in worklist.incoming:
            
            # If the credential already exists and the bearer_token matches, don't need to do anything
            ok, details = self.o.credentials.get(msg['baseUrl'])
            token_already_in_creds = False
            try: 
                token_already_in_creds = (ok and details.bearer_token == self._token)
                if token_already_in_creds:
                    logger.debug(f"Token for {msg['baseUrl']} already in credentials database")
            except:
                token_already_in_creds = False

            if not token_already_in_creds:
                logger.info(f"Token for {msg['baseUrl']} not in credentials database. Adding it!")
                # Add the new bearer token to the internal credentials db. If the credential is already in the db, it will
                # be replaced which is desirable.
                cred = sarracenia.credentials.Credential(urlstr=msg['baseUrl'])
                cred.bearer_token = self._token
                self.o.credentials.add(msg['baseUrl'], details=cred)


    def create_earthdata_token(self, auth: requests.auth.HTTPBasicAuth) -> bool:
        """ Create a new Earthdata token.
        """
        self._token = None
        self._token_expires = None

        try:
            # Create a new token
            resp = requests.post(self.o.earthdataUrl + "/api/users/token", auth=auth)
            if resp.status_code != 200:
                logger.error(f"Failed to create a new token! Code: {resp.status_code} Info: {resp.text}")
                return False
            
            # If we got 200, success!
            resp_j = resp.json()
            # logger.debug(f"Here's the response: {resp_j}")

            self._token = resp_j['access_token']
            self._token_expiry = resp_j['expiration_date']
            logger.info(f"Successfully created new token! " + 
                        f"Token ends with ...{self._token[-5:]} and expires on {self._token_expiry}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create a new token! {e}")
            logger.debug("details:", exc_info=True)
            return False

    def get_earthdata_token(self) -> bool:
        """ Try to retrieve a token from the Earthdata account. If there is no token, it will create a new one.
        https://urs.earthdata.nasa.gov/documentation/for_users/user_token
        """
        self._token = None
        self._token_expires = None

        # From config file
        endpoint = self.o.earthdataUrl

        # Credentials - from Earthdata endpoint URL
        ok, details = self.o.credentials.get(endpoint)
        if not ok:
            logger.error(f"credential lookup failed for {endpoint}. Check your credentials.conf file!")
            return False
        creds = details.url
        username = creds.username
        password = creds.password

        auth = requests.auth.HTTPBasicAuth(username, password)

        try:
            # Try to get an existing token
            resp = requests.get(self.o.earthdataUrl + "/api/users/tokens", auth=auth)
            if resp.status_code != 200:
                logger.error(f"Failed to login to NASA Earthdata. Code: {resp.status_code} Info: {resp.text}")
                return False
            
            # If we got 200, we either have an empty response (user has 0 tokens), or we have a token
            resp_j = resp.json()
            # logger.debug(f"Here's the response: {resp_j}, {len(resp_j)}")

            if len(resp_j) >= 1: 
                self._token = resp_j[0]['access_token']
                self._token_expiry = resp_j[0]['expiration_date']
                logger.info(f"There is/are {len(resp_j)} token(s) in {username}'s Earthdata account. " + 
                            f"Using the token that ends with ...{self._token[-5:]} and expires on {self._token_expiry}")
                return True
            # Valid response, but no tokens in the account. Need to create one.
            else:
                logger.info(f"There are {len(resp_j)} tokens in {username}'s Earthdata account. A new token will be created.")
                return self.create_earthdata_token(auth)
            
        except Exception as e:
            logger.error(f"Failed to login to NASA Earthdata. {e}")
            logger.debug("details:", exc_info=True)
            return False

        