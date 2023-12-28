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

According to this, each token is valid for 10 minutes: https://documentation.dataspace.copernicus.eu/FAQ.html#apis
  
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
        self._token_expires = datetime.datetime.utcnow()
        self._refresh = None
        self._refresh_expires = self._token_expires
        # end __init__

    def after_accept(self, worklist):
        """ Doesn't actually do any downloading. Get/create a bearer token by logging in with the username and 
            password from credentials.conf. Then adds the bearer token to Sarracenia's credentials DB for the 
            message's baseUrl. This will allow the file to be downloaded from msg['baseUrl']+msg['relPath'] 
            using the bearer token.
        """
        for msg in worklist.incoming:
            token = self.get_token()
            
            if not token:
                logger.error("Failed to get token!")
                continue

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
        now = datetime.datetime.utcnow()
        if not self._token or self._token_expires <= now:
            logger.info(f"Requesting a new token. Expired? {self._token_expires <= now}")

            # Use username and password when refresh token is not available or expired
            if not self._refresh or self._refresh_expires <= now:
                logger.info("Using username/password")
                # Credentials
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
            else:
                logger.info("Using refresh_token")
                data = {
                    "client_id": self.o.clientId,
                    "refresh_token": self._refresh,
                    "grant_type": "refresh_token",
                }

            try:
                r = requests.post(self.o.openidConnectUrl, data=data)
                r.raise_for_status()
                j = r.json()
                self._token = j['access_token']
                self._token_expires = now + datetime.timedelta(seconds=j['expires_in'])
                self._refresh = j['refresh_token']
                self._refresh_expires = now + datetime.timedelta(seconds=j['refresh_expires_in'])
                logger.info("Success! Access token created.")
                logger.debug(j)
            except Exception as e:
                logger.error(f"Access token creation failed. Reponse from the server was: {r.json()}")
                self._token = None
                self._token_expires = now
                self._refresh = None
                self._refresh_expires = now
                return None
        
        return self._token


#'expires_in': 600, 'refresh_expires_in': 3600, 'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJhZmFlZTU2Zi1iNWZiLTRiMzMtODRlYS0zMWY2NzMyMzNhNzgifQ.eyJleHAiOjE3MDM3ODA2ODIsImlhdCI6MTcwMzc3NzA4MiwianRpIjoiMjg1Y2NiNzEtMWNkYS00YTk1LWJjN2UtYmVlODgzNjRmNDg4IiwiaXNzIjoiaHR0cHM6Ly9pZGVudGl0eS5kYXRhc3BhY2UuY29wZXJuaWN1cy5ldS9hdXRoL3JlYWxtcy9DRFNFIiwiYXVkIjoiaHR0cHM6Ly9pZGVudGl0eS5kYXRhc3BhY2UuY29wZXJuaWN1cy5ldS9hdXRoL3JlYWxtcy9DRFNFIiwic3ViIjoiNGY5ODIwMGYtYzM3Ny00YWU3LTgyMTQtZTE5NTdjZDhjY2Q5IiwidHlwIjoiUmVmcmVzaCIsImF6cCI6ImNkc2UtcHVibGljIiwic2Vzc2lvbl9zdGF0ZSI6IjhkYjdjM2JlLWQxNzItNDI4OS1hYTU3LTk5MWVmNWY4ZmUwNCIsInNjb3BlIjoiQVVESUVOQ0VfUFVCTElDIG9wZW5pZCBlbWFpbCBwcm9maWxlIG9uZGVtYW5kX3Byb2Nlc3NpbmcgdXNlci1jb250ZXh0Iiwic2lkIjoiOGRiN2MzYmUtZDE3Mi00Mjg5LWFhNTctOTkxZWY1ZjhmZTA0In0.rBMOTKRq497G6_L_DQ-7SpvYWDMi1BXWcxm7uFdL2KY', 'token_type': 'Bearer', 'not-before-policy': 0, 'session_state': '8db7c3be-d172-4289-aa57-991ef5f8fe04', 'scope': 'AUDIENCE_PUBLIC openid email profile ondemand_processing user-context'}