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
 
    Add ``callback authenticate.copernicus``, in your subscribe, sarra or other download config.  

    Add ``https://username:password@identity.dataspace.copernicus.eu/`` to your ``credentials.conf`` file (or whatever
    URL matches your ``openidConnectUrl``).

    NOTE: When downloading large files on a slow connection, it is possible for the access token to expire during a
    batch download. Setting ``batch 1`` or ``batch n`` (where n*(download time per file) < 10 minutes) in your
    download config will help prevent this.

Change log:
-----------

    - 2023-12-27: first attempt at this plugin.
    - 2024-07-23: refactor to use BearerToken parent class. after_accept is inherited from BearerToken.
"""

from sarracenia.flowcb.authenticate import BearerToken
import datetime
import logging
import requests

logger = logging.getLogger(__name__)

class Copernicus(BearerToken):
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

    def get_token(self, retry=False):
        """ Returns a bearer token, or None
        """
        r = None
        now = datetime.datetime.utcnow()
        if not self._token or self._token_expires <= now:
            self._token = None

            # Use username and password when refresh token is not available or expired
            if not self._refresh or self._refresh_expires <= now:
                logger.info("Requesting a new token using username/password")
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
                logger.info("Requesting a new access token using refresh_token")
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
                # set tokens to expire sooner than they actually do, to reduce likelihood of it expiring between
                # when after_accept runs and when download runs.
                self._token_expires = now + datetime.timedelta(seconds=j['expires_in'], minutes=-2)
                self._refresh = j['refresh_token']
                self._refresh_expires = now + datetime.timedelta(seconds=j['refresh_expires_in'], minutes=-5)
                logger.info("Success! Access token created.")
                logger.debug(j)
            except Exception as e:
                logger.error(f"Access token creation failed. {e}")
                logger.debug("Details:", exc_info=True)
                if r:
                    logger.debug(f"response: {r.json()}")
                self._token = None
                self._token_expires = now
                self._refresh = None
                self._refresh_expires = now
                if retry:
                    return None
                else:
                    # do 1 retry
                    return self.get_token(retry=True)
        
        return self._token
