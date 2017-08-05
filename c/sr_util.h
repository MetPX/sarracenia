
#ifndef SR_UTIL_H
#define SR_UTIL_H

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>


#include <time.h>
#include <openssl/sha.h>

// message > log_level will be printed.
extern int log_level ;

// log message severities.
#define LOG_DEBUG     (1)
#define LOG_INFO      (2)
#define LOG_WARNING   (4)
#define LOG_ERROR     (8)
#define LOG_CRITICAL (16)

void log_msg(const int prio, const char *format, ...);

void log_setup(const char *logfname, mode_t mode, int severity);
// set up logging to the named file, suppressing messages of lower severity 

void log_cleanup();

void daemonize();
// executed to go from a management instance to a daemon working instance.

#define SR_TIMESTRLEN (19)

// Assumed longest possible hash. typeprefix + SHA512_DIGEST 
#define SR_SUMHASHLEN (SHA512_DIGEST_LENGTH+1)

// SUMSTR is the printable-string representation of the hash, each digit decodes to two characters for hexadecimal digits.
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

int get_sumhashlen( char algo );
 /* return the length of the hash buffer (which includes the 1 char prefix for the type.
  */

char *set_sumstr( char algo, const char* fn, const char* partstr, char *linkstr,
          unsigned long block_size, unsigned long block_count, unsigned long block_rem, unsigned long block_num
     );

unsigned char *sr_sumstr2hash( const char *s );

char *sr_hash2sumstr( const unsigned char *h );

char *sr_time2str( struct timespec *tin );
struct timespec *sr_str2time( char *s ); 


#endif
