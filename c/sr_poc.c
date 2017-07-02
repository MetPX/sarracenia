
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <limits.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <sys/time.h>
#include <math.h>
#include <stdarg.h>

#include "sr_context.h"

/*
 preload proof of concept from Alain St-Denis...
 with mods to work with sr_context

 missing:
     symlink
     link
     unlink...

 */



static int init_done = 0;
typedef int  (*close_fn) (int);
static close_fn close_fn_ptr = close;

int close(int fd) {

  int fdstat;
  char fdpath[32];
  char *real_fdpath = NULL;


  if (!init_done) {
    close_fn_ptr = (close_fn) dlsym(RTLD_NEXT, "close");
    init_done = 1;
  }
    
  // hack to prevent loops on close, when calling posting routines...
  // is there a better way? - PS.
  if ( getenv("SR_LD_USE_REAL_CLOSE") != NULL ) {
    return close_fn_ptr(fd);
  }

  fdstat = fcntl(fd, F_GETFL);

  if ( (fdstat & O_ACCMODE) == O_RDONLY ) { 
    return close_fn_ptr(fd);
  }
  real_fdpath = NULL;

  snprintf(fdpath, 32, "/proc/self/fd/%d", fd);
  real_fdpath = realpath(fdpath, NULL);

  putenv("SR_LD_USE_REAL_CLOSE=True");

  connect_and_post(real_fdpath);

  unsetenv("SR_LD_USE_REAL_CLOSE");
  free(real_fdpath);

  return(close_fn_ptr(fd));
}
