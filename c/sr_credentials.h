
#ifndef SR_CREDENTIALS_H
#define SR_CREDENTIALS_H 1

char *sr_credentials_fetch( char *s ) ;
  /* search for the first credential that matches the search spec given.
   */
void sr_credentials_init() ;
 /* initally read in the credentials, so they can be retrieved by fetch
  */

#endif
