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
 
    Add ``callback authenticate.nasa_earthdata``, in your subscribe, sarra or other download config.  

    Add ``https://username:password@urs.earthdata.nasa.gov/`` to your ``credentials.conf`` file.  
    
    Optional: set ``acceptSizeWrong True`` in the sarra/subscribe config to suppress the WARNING message
     about a file being downloaded with no length given.

    Enable debug logging for this plugin only: ``set authenticate.nasa_earthdata.logLevel debug``

    For examples, see https://github.com/MetPX/sarracenia/tree/stable/sarracenia/examples/subscribe files
    named ``*nasa_earthdata*.conf``. 

Change log:
-----------

    - 2023-10-10: first attempt at this plugin. The old v2 code re-implemented downloading, using a session with
      stored cookies. This should be better, because it uses the native sr3 download code.
    - 2024-05-09: refactoring, to be able to be easily called from poll plugins, and elsewhere.
    - 2024-07-23: fix renewal bug. Refactor to use get_token and BearerToken parent class.
                  Need to check if today >= expiry date, not just ==. Use datetime class for comparisons.
"""

from sarracenia.flowcb.authenticate import BearerToken
import datetime
import logging
import requests

logger = logging.getLogger(__name__)

class Nasa_earthdata(BearerToken):
    def __init__(self, options):
        super().__init__(options, logger)
        logger.debug("plugin: NASA_Earthdata __init__")

        self.o.add_option('earthdataUrl', kind='str', default_value='https://urs.earthdata.nasa.gov')

        if self.o.earthdataUrl[-1] == '/':
            self.o.earthdataUrl = self.o.earthdataUrl.strip('/')

        self._token = None
        # self._token_expires = None 
        self.__token_expires = None # stored as a datetime object 

        # end __init__
    
    @property
    def _token_expires(self):
        return self.__token_expires
    
    @_token_expires.setter
    def _token_expires(self, new_value):
        """ date string format from NASA is MM/DD/YYYY :-(
        """
        if type(new_value) == str:
            self.__token_expires = datetime.datetime.strptime(new_value, "%m/%d/%Y")
        else:
            self.__token_expires = new_value
    
    def _token_expiry_str(self):
        if type(self._token_expires) == datetime.datetime:
            return self._token_expires.strftime("%Y-%m-%d")
        else:
            return None

    def get_token(self):
        """ Return the bearer token, or None in case of an error.

            This plugin stores the bearer token internally in self._token. If set and not expired, this will
            return the value from self._token. Otherwise, we request a token from NASA's API. The API will either
            return an existing token if the account has one, or will create a new token if it doesn't. 
        """
        # NASA doesn't specify what time the token expires on the expiry date. It seems to expire at 23:59:59 on the
        # expiry date or 00:00:00 the next day. If today >= expiry date, then try to get a new token every time this
        # runs. If it's not expired yet, we'll get the same token from the API and can try to check again on the next
        # run. If it is expired, we should get a brand new token.
        today = datetime.datetime.utcnow()
        try:
            if self._token_expires and today >= self._token_expires:
                logger.info(f"the token ending with ...{self._token[-5:]} " + 
                            f"is expired or expires today (expiry date: {self._token_expiry_str()})")
                self._token = None
                self._token_expires = None
            elif self._token_expires:
                logger.debug(f"token is not expired. today = {today.strftime('%Y-%m-%d')}, " + 
                            f"token expires on {self._token_expiry_str()}")
            else:
                logger.debug("no token yet")
        except Exception as e:
            logger.error(f"token expiry check failed {e}")
            logger.debug("exception details", exc_info=True)
            self._token = None
            self._token_expires = None

        # Get a token from the NASA API, if there isn't one already
        if not self._token:
            # Try to get a new token
            if not self.get_earthdata_token():
                logger.error(f"Failed to retrieve bearer token from {self.o.earthdataUrl}")
        
        return self._token


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
            self._token_expires = resp_j['expiration_date']
            logger.info(f"Successfully created new token! Token ends with ..." + 
                        f"{self._token[-5:]} and expires on {self._token_expiry_str()}")
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
                logger.error(f"Failed to login to NASA Earthdata ({self.o.earthdataUrl})." + 
                             f" Code: {resp.status_code} Info: {resp.text} Username: {username}")
                return False 
            
            # If we got 200, we either have an empty response (user has 0 tokens), or we have a token
            resp_j = resp.json()
            # logger.debug(f"Here's the response: {resp_j}, {len(resp_j)}")

            if len(resp_j) >= 1: 
                self._token = resp_j[0]['access_token']
                self._token_expires = resp_j[0]['expiration_date']
                logger.info(f"There is/are {len(resp_j)} token(s) in {username}'s Earthdata account. Using the " +
                            f"token that ends with ...{self._token[-5:]} and expires on {self._token_expiry_str()}")
                return True
            # Valid response, but no tokens in the account. Need to create one.
            else:
                logger.info(f"There are {len(resp_j)} tokens in {username}'s Earthdata account. A new token will be created.")
                return self.create_earthdata_token(auth)
            
        except Exception as e:
            logger.error(f"Failed to login to NASA Earthdata. {e}")
            logger.debug("details:", exc_info=True)
            return False

        
