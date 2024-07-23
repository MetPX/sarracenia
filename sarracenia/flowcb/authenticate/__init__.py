"""
sarracenia.flowcb.authenticate plugins deal with implementing custom authentication
for various data sources.

This currently supports various ways of dynamically generating and using 
bearer tokens, for authenticating with HTTP(S) sources.

Work in progress. See https://github.com/MetPX/sarracenia/issues/565
"""
import sarracenia
import logging

logger = logging.getLogger(__name__)

class BearerToken(sarracenia.flowcb.FlowCB):
    """ BearerToken class implements an after_accept method that is common
    to authentication plugins that provide bearer tokens. 

    A plugin author just needs to create a subclass of BearerToken and
    implement the get_token() method. The after_accept method defined here
    will handle loading the token into Sarracenia's credentials database.

    The get_token() method should return the bearer token as a string,
    or None in case it failed to get a token.

    """

    def __init__(self, options):
        super().__init__(options, logger)

    def after_accept(self, worklist):
        """ Adds a bearer token to Sarracenia's in memory credentials DB for the message's baseUrl. This will allow
            the file to be downloaded with Sarracenia's default HTTPS transfer class using the bearer token.
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
        """ To be implemented by plugin authors.
        """
        logger.error("BearerToken class get_token not implemented.")
        return None
