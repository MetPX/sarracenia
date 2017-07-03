
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

 */


static int symlink_init_done = 0;
typedef int  (*symlink_fn) (const char*,const char*);
static symlink_fn symlink_fn_ptr = symlink;

int symlink(const char *target, const char* linkpath) 
{
  int status;

  if (!symlink_init_done) {
    symlink_fn_ptr = (symlink_fn) dlsym(RTLD_NEXT, "symlink");
    symlink_init_done = 1;
  }
  status = symlink_fn_ptr(target,linkpath);

  fprintf( stderr, "about to post symlink: %s\n", linkpath );
  if (!status) connect_and_post(linkpath);
  return(status);
}


static int link_init_done = 0;
typedef int  (*link_fn) (const char*,const char*);
static link_fn link_fn_ptr = link;

int link(const char *target, const char* linkpath) 
{
  int status;

  if (!link_init_done) {
    link_fn_ptr = (link_fn) dlsym(RTLD_NEXT, "link");
    link_init_done = 1;
  }
  status = link_fn_ptr(target,linkpath);

  if (!status) connect_and_post(linkpath);
  return(status);
}

static int unlinkat_init_done = 0;
typedef int  (*unlinkat_fn) (int dirfd, const char*, int flags);
static unlinkat_fn unlinkat_fn_ptr = unlinkat;

int unlinkat(int dirfd, const char *path, int flags) 
{
  int status;

  if (!unlinkat_init_done) {
    unlinkat_fn_ptr = (unlinkat_fn) dlsym(RTLD_NEXT, "unlinkat");
    unlinkat_init_done = 1;
  }
  status = unlinkat_fn_ptr(dirfd, path, flags);
  if (!status) connect_and_post(path);
  return(status);
}

static int unlink_init_done = 0;
typedef int  (*unlink_fn) (const char*);
static unlink_fn unlink_fn_ptr = unlink;

int unlink(const char *path) 
{
  int status;

  if (!unlink_init_done) 
  {
      unlink_fn_ptr = (unlink_fn) dlsym(RTLD_NEXT, "unlink");
      unlink_init_done = 1;
  }
  status = unlink_fn_ptr(path);
  if (!status) connect_and_post(path);
  return(status);
}


static int close_init_done = 0;
typedef int  (*close_fn) (int);
static close_fn close_fn_ptr = close;

int close(int fd) {

  int fdstat;
  char fdpath[32];
  char *real_fdpath = NULL;

  if (!close_init_done) {
    close_fn_ptr = (close_fn) dlsym(RTLD_NEXT, "close");
    close_init_done = 1;
  }
    
  // hack to prevent loops on close, when calling posting routines...
  // is there a better way? - PS.
  if ( getenv("SR_LD_USE_REAL_FN") != NULL )
      return close_fn_ptr(fd);

  fdstat = fcntl(fd, F_GETFL);

  if ( (fdstat & O_ACCMODE) == O_RDONLY )
      return close_fn_ptr(fd);
  
  real_fdpath = NULL;

  snprintf(fdpath, 32, "/proc/self/fd/%d", fd);
  real_fdpath = realpath(fdpath, NULL);

  // something like stdout, or stdin, no way to obtain file name...
  if (!real_fdpath) 
  {
       return(close_fn_ptr(fd));
  }

  putenv("SR_LD_USE_REAL_FN=True");

  connect_and_post(real_fdpath);
 
  fprintf( stderr, "back from connect_and_post %s\n", real_fdpath );
  unsetenv("SR_LD_USE_REAL_FN");
  free(real_fdpath);

  return(close_fn_ptr(fd));
}
