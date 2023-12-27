#!/usr/bin/python3

"""
Plugin to download from the Copernicus Data Space Ecosystem
============================================================

This plugin enables authentication for URLs posted by the ``odata.py`` plugin, and other Copernicus data
sources that use bearer tokens. It may also work with other OpenID Connect-based systems.

For every message processed by this plugin, it will add a credential with a valid bearer token matching the message's
baseUrl to Sarracenia's in-memory credential database.

Register for an account here: https://documentation.dataspace.copernicus.eu/Registration.html

This code is based on https://documentation.dataspace.copernicus.eu/APIs/Token.html#by-python-script.

  
Configurable Options:
----------------------

``openidConnectUrl``:
^^^^^^^^^^^^^^^^^^^^

    Default is ``https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token``. If you
    want to override it, you can specify the ``openidConnectUrl https://your-endpoint.example.com`` option.

``clientId``:
^^^^^^^^^^^^^

    Passed to the API. Default is ``cdse-public``.

``grantType``:
^^^^^^^^^^^^^^

    Passed to the API. Default is ``password``.

How to set up your download config:
------------------------------------
 
    Add ``callback accept.auth_copernicus``, in your subscribe, sarra or other download config.  

    Add ``https://username:password@identity.dataspace.copernicus.eu/`` to your ``credentials.conf`` file (or whatever
    URL matches your ``openidConnectUrl``). Most usernames are email addresses - you will need to use ``%40`` instead
    of the ``@`` symbol in the username.

Change log:
-----------

    - 2023-12-27: first attempt at this plugin.
"""

import sarracenia
import datetime
import logging
import requests

logger = logging.getLogger(__name__)

class Auth_copernicus(sarracenia.flowcb.FlowCB):
    def __init__(self, options):
        super().__init__(options, logger)
        
        # Allow setting a logLevel *only* for this plugin in the config file:
        # set accept.auth_copernicus.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        self.o.add_option('openidConnectUrl', kind='str', 
            default_value='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token')
        self.o.add_option('clientId', kind='str', default_value='cdse-public')
        self.o.add_option('grantType', kind='str', default_value='password')

        self._token = None
        self._token_expires = None # format MM/DD/YYYY, e.g. 12/25/2023

        # end __init__

    def after_accept(self, worklist):
        """ Doesn't actually do any downloading. Get/create a bearer token by logging in with the username and 
            password from credentials.conf. Then adds the bearer token to Sarracenia's credentials DB for the 
            message's baseUrl. This will allow the file to be downloaded from msg['baseUrl']+msg['relPath'] 
            using the bearer token.
        """
        for msg in worklist.incoming:
            token = self.get_token()
            
            # If the credential already exists and the bearer_token matches, don't need to do anything
            ok, details = self.o.credentials.get(msg['baseUrl'])
            token_already_in_creds = False
            try: 
                token_already_in_creds = (ok and details.bearer_token == token)
                if token_already_in_creds:
                    logger.debug(f"Token for {msg['baseUrl']} already in credentials database")
            except:
                token_already_in_creds = False

            if not token_already_in_creds:
                logger.info(f"Token for {msg['baseUrl']} not in credentials database. Adding it!")
                # Add the new bearer token to the internal credentials db. If the credential is already in the db, it will
                # be replaced which is desirable.
                cred = sarracenia.credentials.Credential(urlstr=msg['baseUrl'])
                cred.bearer_token = token
                self.o.credentials.add(msg['baseUrl'], details=cred)

    def get_token(self):
        """ Returns a token, or None
        """
        if not self._token:
            logger.debug("Requesting a token")

            # Credentials - from Earthdata endpoint URL
            ok, details = self.o.credentials.get(self.o.openidConnectUrl)
            creds = details.url
            username = creds.username
            password = creds.password
            if not ok or not username or not password:
                # logger.debug(f"{ok}, {username}, {password}")
                logger.error(f"credential lookup failed for {self.o.openidConnectUrl}. Check credentials.conf!")
                return None

            data = {
                "client_id": self.o.clientId,
                "username": username,
                "password": password,
                "grant_type": self.o.grantType,
            }
            try:
                r = requests.post(self.o.openidConnectUrl, data=data)
                r.raise_for_status()
                j = r.json()
                self._token = j["access_token"]
                logger.info("Success! Access token created.")
                logger.debug(j)
            except Exception as e:
                logger.error(f"Access token creation failed. Reponse from the server was: {r.json()}")
                return None
        
        return self._token
