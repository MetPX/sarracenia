#!/usr/bin/python3

"""
Authentication for new BC Trans API
=====================================================================================

Description

    The BC Trans data provider is migrating to a public API. We used to have sarracenia polls fetching from their HTTP site. This has since been discontinued.
    The API works by
    1. Providing the client secret to the endpoint server.
    2. The server responds with an access token.
    3. Pass the access token to https://sawsx-services-dev-api-gov-bc-ca.test.api.gov.bc.ca/api/v1/motisite/report7100/al/X to get last X hours of data from provider.

    The access token has a life span of 5 minutes. You can also generate however many access tokens you'd like given you have access to the client_secret and client_id.
    As of now, the only data that can be fetched is 3 hours worth of past data.
    The pollUrl should remain the same , unless other timestamps are specified in the future.

    This plugin uses the BearerToken authentication class entry points.

Documentation available from the Government of BC website
    API tutorial (with examples) : https://developer.gov.bc.ca/docs/default/component/aps-infra-platform-docs/tutorials/quick-start/
    Developer portal : https://api.gov.bc.ca/devportal/api-directory


Configurable Options:
----------------------

``tokenEndpoint_baseUrl`` URL:
^^^^^^^^^^^^^^^^^^^^^^^^

    URL where to fetch the access token.

``tokenEndpoint_path`` URL:
^^^^^^^^^^^^^^^^^^^^^^^^

    Path where to fetch the access token. To use in combination with token_Endpoint_baseUrl


*Potential Room For Improvement*:
----------------------------------

    - Download from multiple different hour marks?

How to set up your flow config:
--------------------------------

    Use ``callback authenticate.bc_trans``, and read about the config options above.

    For example, see https://github.com/MetPX/sarracenia/tree/development/sarracenia/examples/flow files named ``*bc_trans*.conf``.

Change log:
-----------
    - 2024-08-06: Inception of authenticate plugin.
"""


import sarracenia
from sarracenia.flowcb.authenticate import BearerToken
import logging
import requests

logger = logging.getLogger(__name__)

class Bc_trans(BearerToken):
    def __init__(self, options):
        super().__init__(options, logger)
        
        # Allow setting a logLevel *only* for this plugin in the config file:
        # set accept.auth_eumetsat.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        # For additional options (defined by user)
        self.o.add_option('tokenEndpoint_baseUrl', 'str', 'https://loginproxy.gov.bc.ca/') # required
        self.o.add_option('tokenEndpoint_path', 'str', 'auth/realms/apigw/protocol/openid-connect/token') # required

        # Set initial values
        self._bearer_token = None

        # Make sure values already exist
        if not self.o.tokenEndpoint_baseUrl or not self.o.tokenEndpoint_path:
            logger.error(f"tokenEndpoint_baseUrl and tokenEndpoint_path is a required option.")
            sys.exit(1)

        # Get credentials from credentials.conf.
        # In this case the client ID is the traditional url username and the client secret is the traditional password
        # This avoids creating new fields in the credentials class
        if self.o.tokenEndpoint_baseUrl and self.o.tokenEndpoint_path:
            ok, self.details = sarracenia.config.Config.credentials.get(
                self.o.tokenEndpoint_baseUrl + self.o.tokenEndpoint_path)

        self.client_id = self.details.url.username
        self.client_secret = self.details.url.password
        self.grant_type = 'client_credentials'

        # end __init__


    def get_token(self):
        """
        Fetches the bearer token from the token endpoint. Uses the parent class entry point.
        NOTE : Multiple bearer tokens can be fetched at the same time.
        NOTE : The bearer token has a lifespan of 5 minutes.
        """
        try:
            logger.info("Requesting a new bearer token")

            response = requests.post(self.o.tokenEndpoint_baseUrl + self.o.tokenEndpoint_path,\
                data={'grant_type': f'{self.grant_type}'},\
                auth=(self.client_id, self.client_secret))

            # Get response information
            response_status = response.status_code
            response_text = response.text

            if response_status == 200:
                self._bearer_token = response.json()["access_token"]
            else:
                logger.error( f"Request status received: {response_status}. Response message: {response_text}" )
                self._bearer_token = None

        except Exception as e:
            logger.debug("Exception details:", exc_info=True)
        
        return self._bearer_token
