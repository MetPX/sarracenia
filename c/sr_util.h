
#ifndef SR_UTIL_H
#define SR_UTIL_H

#include <time.h>
#include <openssl/sha.h>

#define SR_TIMESTRLEN (19)
#define SR_SUMSTRLEN  (2 * SHA512_DIGEST_LENGTH + 3 )


char *sr_hash2sumstr( unsigned char *h, int l );

char *sr_time2str( struct timespec *tin );
struct timespec *sr_str2time( char *s ); 


#endif
