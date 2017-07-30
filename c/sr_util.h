
#ifndef SR_UTIL_H
#define SR_UTIL_H

#include <time.h>
#include <openssl/sha.h>

#define SR_TIMESTRLEN (19)
#define SR_SUMSTRLEN  (2 * SHA512_DIGEST_LENGTH + 3 )

 /* 
   return a correct sumstring (assume it is big enough)  as per sr_post(7)
   algo = 
     '0' - no checksum, value is random. -> now same as N.
     'd' - md5sum of block.
     'n' - md5sum of filename (fn).
     'L' - now sha512 sum of link value.
     'N' - md5sum of filename (fn) + partstr.
     'R' - no checksum, value is random. -> now same as N.
     's' - sha512 sum of block.

   block starts at block_size * block_num, and ends 

   same storage is re-used on repeated calls, so best to strdup soon after return.

  */

int get_sumstrlen( char algo );

char *set_sumstr( char algo, const char* fn, const char* partstr, char *linkstr,
          unsigned long block_size, unsigned long block_count, unsigned long block_rem, unsigned long block_num
     );

char *sr_hash2sumstr( unsigned char *h, int l );

char *sr_time2str( struct timespec *tin );
struct timespec *sr_str2time( char *s ); 


#endif
