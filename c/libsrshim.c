
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <limits.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <sys/time.h>
#include <sys/types.h>
#include <math.h>
#include <stdarg.h>

#include "sr_post.h"

/*
 libsrshim - intercepts calls to libc and kernel to post files for broker.

 FIXME:  1024, and PATH_MAX, should likely be replaced by code that mallocs properly.

 set following variables to non-empty strings to activate.

 SR_SHIMDEBUG - when set, debug output triggerred.

 SRSHIMMV - trigger new form of MV posting.

 FIXME:
     sigh.... redirection... the final frontier...

    rmdir(2)
      - directory must be empty, so rmdir has no effect (only deal with files.)
        hmm... do we need to start dealing with directories?
        result: even with delete active, empty directories likely.

    sendfile64(2)
    truncate64(2)
      - ordinary calls are dealt with... dunno that we need a separate 64 variety.

 */
static struct sr_context *sr_c = NULL;
static struct sr_config_t sr_cfg; 


void srshim_initialize(const char* progname) 
{

  static int config_read = 0;
  char *setstr;

  if (sr_c) return;

  setstr = getenv( "SR_POST_CONFIG" ) ;
  if ( setstr != NULL )
  { 
     if ( config_read == 0 ) 
     {
       sr_config_init(&sr_cfg,progname);
       config_read = sr_config_read(&sr_cfg,setstr,1,1);
       if (!config_read) return;
     }
     if ( !sr_config_finalize( &sr_cfg, 0 )) return;

     sr_c = sr_context_init_config(&sr_cfg);
     sr_c = sr_context_connect( sr_c );

  } 
}


void srshim_realpost(const char *path) 
/*
  post using initialize sr_ context.

 */
{
  struct sr_mask_t *mask; 
  struct stat sb;
  int statres;
  char *s;
  char rn[PATH_MAX+1];
  char fn[PATH_MAX+1];
  char fnreal[PATH_MAX+1];

  if (!path || !sr_c) return;
  //log_msg( LOG_INFO, "ICI1 PATH %s\n", path);
 
  statres = lstat( path, &sb ) ;

  strcpy( fn, path );

  if (sr_cfg.realpath || sr_cfg.realpath_filter)
  {
      if (!statres) 
      {
          /* realpath of a link might result in a file or directory
             the stat must be reassigned
           */
          realpath( path, fnreal );
          statres = lstat( fnreal, &sb ) ;
      } else {
          /* If the stat failed, assume ENOENT (normal for removal or move), do realpath the directory containing the entry.
             then add the filename onto the that.
           */
          strcpy( rn, path );
          s=rindex( rn, '/' );
          *s='\0';
          s++;
          if ( realpath( rn, fnreal ) )
          {
              strcat( fnreal, "/" );
              strcat( fnreal, s );
          } else {
              strcpy( fnreal, path );
          }
      }
  }

  if ( sr_cfg.realpath ) strcpy( fn, fnreal );

  if ( sr_cfg.realpath_filter) {
     //log_msg( LOG_INFO, "ICI2 FNREAL %s\n", fnreal);
     mask = isMatchingPattern(&sr_cfg, fnreal);
  } else {
     mask = isMatchingPattern(&sr_cfg, fn);
  }

  if ( (mask && !(mask->accepting)) || (!mask && !(sr_cfg.accept_unmatched)) )
  { //reject.
      log_msg( LOG_INFO, "mask: %p, mask->accepting=%d accept_unmatched=%d\n", 
            mask, mask->accepting, sr_cfg.accept_unmatched );
      if (sr_cfg.debug) log_msg( LOG_DEBUG, "sr_%s rejected 2: %s\n", sr_cfg.progname, fn );
      return;
  }

  if ( statres )  {
      sr_post( sr_c, fn, NULL );
      return;
  }

  /* if it is a link, sr_post uses the path of the link...  */

  if (S_ISLNK(sb.st_mode))  {
      strcpy( fn, path );
  }

  sr_post( sr_c, fn, &sb );

}


static int in_librshim_already_dammit = 0;

int shimpost( const char *path, int status )
{
    char *cwd=NULL;
    char *real_path=NULL;

    //log_msg( LOG_INFO, "ICI0 PATH %s\n", path);

    if (in_librshim_already_dammit) return(status);

    in_librshim_already_dammit=1;
    if (!status) 
    {
       srshim_initialize( "post" );
       if (path[0] == '/' )
       {
          if (getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG absolute shimpost %s\n", path );
          srshim_realpost( path );
       } else {
          cwd = get_current_dir_name();
          real_path = (char*)malloc( strlen(cwd) + strlen(path) + 3 );
          //getwd(real_path);
          strcpy(real_path,cwd);
          strcat(real_path,"/");
          strcat(real_path,path);
          if (getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG relative shimpost %s\n", real_path );
          srshim_realpost( real_path );
          free(real_path);
          free(cwd);
       }
    }
    in_librshim_already_dammit=0;

    return(status);
}


static int truncate_init_done = 0;
typedef int  (*truncate_fn) (const char*,off_t length);
static truncate_fn truncate_fn_ptr = truncate;

int truncate(const char *path, off_t length) 
{
    int status;

    if (!truncate_init_done) {
        truncate_fn_ptr = (truncate_fn) dlsym(RTLD_NEXT, "truncate");
        truncate_init_done = 1;
    }
    status = truncate_fn_ptr(path,length);
    if ( !strncmp(path,"/dev/", 5) ) return(status);
    if ( !strncmp(path,"/proc/", 6) ) return(status);

    return(shimpost(path, status));

}




static int symlink_init_done = 0;
typedef int  (*symlink_fn) (const char*,const char*);
static symlink_fn symlink_fn_ptr = symlink;

int symlink(const char *target, const char* linkpath) 
{
    int status;

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG symlink %s %s\n", target, linkpath );
    if (!symlink_init_done) {
        symlink_fn_ptr = (symlink_fn) dlsym(RTLD_NEXT, "symlink");
        symlink_init_done = 1;
    }
    status = symlink_fn_ptr(target,linkpath);
    if ( !strncmp(linkpath,"/dev/", 5) ) return(status);
    if ( !strncmp(linkpath,"/proc/", 6) ) return(status);

    return(shimpost(linkpath, status));
}



static int unlinkat_init_done = 0;
typedef int  (*unlinkat_fn) (int dirfd, const char*, int flags);
static unlinkat_fn unlinkat_fn_ptr = unlinkat;

int unlinkat(int dirfd, const char *path, int flags) 
{
    int status;
    char fdpath[PATH_MAX+1];
    char real_path[PATH_MAX+1];
    char *real_return;

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG unlinkat %s dirfd=%d\n", path, dirfd );
    if (!unlinkat_init_done) {
        unlinkat_fn_ptr = (unlinkat_fn) dlsym(RTLD_NEXT, "unlinkat");
        unlinkat_init_done = 1;
    }

    status = unlinkat_fn_ptr(dirfd, path, flags);

    if ( dirfd == AT_FDCWD ) 
       return(shimpost(path,status));
    
    snprintf( fdpath, 32, "/proc/self/fd/%d", dirfd );
    real_return = realpath(fdpath, real_path);
    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG unlinkat relative directory %s real_return=%p\n", fdpath, real_return );
    strcat(real_path,"/");
    strcat(real_path,path);
    if (!real_return) return(status);

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG unlinkat realpath %s\n", real_path );

    return(shimpost(real_path,status));
}

static int unlink_init_done = 0;
typedef int  (*unlink_fn) (const char*);
static unlink_fn unlink_fn_ptr = unlink;

int unlink(const char *path) 
{
    int status;

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG unlink %s\n", path );
    if (!unlink_init_done) 
    {
        unlink_fn_ptr = (unlink_fn) dlsym(RTLD_NEXT, "unlink");
        unlink_init_done = 1;
    }
    status = unlink_fn_ptr(path);
    if ( !strncmp(path,"/dev/", 5) ) return(status);

    return(shimpost(path,status));
}


static int link_init_done = 0;
typedef int  (*link_fn) (const char*,const char*);
static link_fn link_fn_ptr = link;

static int linkat_init_done = 0;
typedef int  (*linkat_fn) (int, const char*, int, const char *, int flags);
static linkat_fn linkat_fn_ptr = linkat;

static int renameat_init_done = 0;
typedef int  (*renameat_fn) (int, const char*, int, const char*);
static renameat_fn renameat_fn_ptr = NULL;

static int renameat2_init_done = 0;
typedef int  (*renameat2_fn) (int, const char*, int, const char*, unsigned int);
static renameat2_fn renameat2_fn_ptr = NULL;

int renameorlink(int olddirfd, const char *oldpath, int newdirfd, const char *newpath, int flags, int link)
/*
  The real implementation of all renames.
 */
{
    int status;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;
    char oreal_path[PATH_MAX+1];
    char *oreal_return;

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG renameorlink %s %s\n", oldpath, newpath );

    if (!renameat2_init_done) 
    {
        renameat2_fn_ptr = (renameat2_fn) dlsym(RTLD_NEXT, "renameat2");
        renameat2_init_done = 1;
    }
    if (!renameat_init_done) 
    {
        renameat_fn_ptr = (renameat_fn) dlsym(RTLD_NEXT, "renameat");
        renameat_init_done = 1;
    }

    if (!link_init_done) {
        link_fn_ptr = (link_fn) dlsym(RTLD_NEXT, "link");
        link_init_done = 1;
    }

    if (!linkat_init_done) {
        linkat_fn_ptr = (linkat_fn) dlsym(RTLD_NEXT, "linkat");
        linkat_init_done = 1;
    }

    if (link)
    {
       if (linkat_fn_ptr) 
          status = linkat_fn_ptr(olddirfd, oldpath, newdirfd, newpath, flags);
       else if (link_fn_ptr && !flags )
          status = link_fn_ptr(oldpath, newpath);
       else {
          log_msg( LOG_ERROR, "SR_SHIMDEBUG renameorlink could not identify real entry point for link\n" );
       }
    } else {
       if (renameat2_fn_ptr) 
          status = renameat2_fn_ptr(olddirfd, oldpath, newdirfd, newpath, flags);
       else if (renameat_fn_ptr && !flags )
          status = renameat_fn_ptr(olddirfd, oldpath, newdirfd, newpath);
       else {
          log_msg( LOG_ERROR, "SR_SHIMDEBUG renameorlink could not identify real entry point for renameat\n" );
          return(-1);
       }
    }

    if (status) 
    {
         if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG renameorlink %s %s failed, no post\n", oldpath, newpath );
         return(status);
    }

    srshim_initialize("post");

    if (!sr_c) return(status);

    if ( olddirfd == AT_FDCWD ) 
    {
       strcpy(oreal_path,oldpath);
    } else {
       snprintf( fdpath, 32, "/proc/self/fd/%d", olddirfd );
       oreal_return = realpath(fdpath, oreal_path);
       if (oreal_return) 
       {
         log_msg( LOG_WARNING, "srshim renameorlink could not obtain real_path for olddirfd=%s failed, no post\n", fdpath );
         return(status);
       }
       strcat( oreal_path, "/" );
       strcat( oreal_path, oldpath );
    }

    if ( newdirfd == AT_FDCWD ) 
    {
       strcpy(real_path,newpath);
    } else {
       snprintf( fdpath, 32, "/proc/self/fd/%d", newdirfd );
       real_return = realpath(fdpath, real_path);
       if (real_return) 
       {
         log_msg( LOG_WARNING, "srshim renameorlink could not obtain real_path for newdir=%s failed, no post\n", fdpath );
         return(status);
       }
       strcat( real_path, "/" );
       strcat( real_path, newpath );
    }
    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG renameorlink sr_c=%p, oreal_path=%s, real_path=%s\n", 
            sr_c, oreal_path, real_path );

    sr_post_rename( sr_c, oreal_path, real_path );

    return(status);

}

static int dup2_init_done = 0;
typedef int (*dup2_fn) ( int, int  );
static dup2_fn dup2_fn_ptr = dup2;

int dup2(int oldfd, int newfd )
{   
    int  fdstat;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;
    int  fd_dup;
    int  status;
    
    if (!dup2_init_done) {
        dup2_fn_ptr = (dup2_fn) dlsym(RTLD_NEXT, "dup2");
        dup2_init_done = 1;
        if (getenv("SR_POST_READS"))
           srshim_initialize( "post" );
    }
    
    fdstat = fcntl(newfd, F_GETFL);

    if ( ((fdstat & O_ACCMODE) == O_RDONLY ) && ( !sr_c || !( SR_READ & sr_c->cfg->events ) ) )
           return dup2_fn_ptr(oldfd, newfd);

    snprintf(fdpath, 32, "/proc/self/fd/%d", newfd);
    real_return = realpath(fdpath, real_path);

    status = 0;
    fd_dup = dup2_fn_ptr (oldfd, newfd);
    if (fd_dup == -1) status = fd_dup;

    if (!real_return) return(status);

    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG dup2 %s\n", real_path );

    status = shimpost(real_path, status) ;

    return fd_dup;
}

static int dup3_init_done = 0;
typedef int (*dup3_fn) ( int, int, int );
static dup3_fn dup3_fn_ptr = dup3;

int dup3(int oldfd, int newfd, int flags )
{   
    int  fdstat;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;
    int  fd_dup;
    int  status;
    
    if (!dup3_init_done) {
        dup3_fn_ptr = (dup3_fn) dlsym(RTLD_NEXT, "dup3");
        dup3_init_done = 1;
        if (getenv("SR_POST_READS"))
           srshim_initialize( "post" );
    }
    
    fdstat = fcntl(newfd, F_GETFL);

    if ( ((fdstat & O_ACCMODE) == O_RDONLY ) && ( !sr_c || !( SR_READ & sr_c->cfg->events ) ) )
           return dup2_fn_ptr(oldfd, newfd);

    snprintf(fdpath, 32, "/proc/self/fd/%d", newfd);
    real_return = realpath(fdpath, real_path);

    status = 0;
    fd_dup = dup3_fn_ptr (oldfd, newfd, flags);
    if (fd_dup == -1) status = fd_dup;

    if (!real_return) return(status);

    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG dup3 %s\n", real_path );

    status = shimpost(real_path, status) ;

    return fd_dup;
}


int link(const char *target, const char* linkpath) 
{
    if (getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG link %s %s\n", target, linkpath );
    return( renameorlink(AT_FDCWD, target, AT_FDCWD, linkpath, 0, 1 ));
}

int linkat(int olddirfd, const char *oldpath, int newdirfd, const char *newpath, int flags) 
{
    if ( getenv("SR_SHIMDEBUG")) 
         fprintf( stderr, "SR_SHIMDEBUG linkat olddirfd=%d, oldname=%s newdirfd=%d newname=%s flags=%d\n", 
            olddirfd, oldpath, newdirfd, newpath, flags );
    return( renameorlink(olddirfd, oldpath, newdirfd, newpath, flags, 1 ));
}

int rename(const char *oldpath, const char *newpath)
{
    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG rename %s %s\n", oldpath, newpath );

    return( renameorlink(AT_FDCWD, oldpath, AT_FDCWD, newpath, 0, 0 ));
}

int renameat(int olddirfd, const char *oldpath, int newdirfd, const char *newpath)
{
    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG renameat %s %s\n", oldpath, newpath );

    return( renameorlink(olddirfd, oldpath, newdirfd, newpath, 0, 0 ));
}

int renameat2(int olddirfd, const char *oldpath, int newdirfd, const char *newpath, unsigned int flags)
{
    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG renameat2 %s %s\n", oldpath, newpath );

    return( renameorlink(olddirfd, oldpath, newdirfd, newpath, flags, 0 ));
}



static int sendfile_init_done = 0;
typedef ssize_t  (*sendfile_fn) (int, int, off_t *, size_t);
static sendfile_fn sendfile_fn_ptr = NULL;

ssize_t sendfile(int out_fd, int in_fd, off_t *offset, size_t count)
{
    ssize_t status;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;

    if (!sendfile_init_done) 
    {
        sendfile_fn_ptr = (sendfile_fn) dlsym(RTLD_NEXT, "sendfile");
        sendfile_init_done = 1;
    }
    status = sendfile_fn_ptr( out_fd, in_fd, offset, count );

    snprintf( fdpath, 32, "/proc/self/fd/%d", out_fd );
    real_return = realpath(fdpath, real_path);

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG sendfile to %s\n", real_path );

    if (!real_return) return(status);
    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    return(shimpost(real_path,status));
}



static int copy_file_range_init_done = 0;
typedef int  (*copy_file_range_fn) (int, loff_t *, int, loff_t *, size_t, unsigned int);
static copy_file_range_fn copy_file_range_fn_ptr = NULL;

int copy_file_range(int fd_in, loff_t *off_in, int fd_out, loff_t *off_out, size_t len, unsigned int flags)
{
    int status;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;

    if (!copy_file_range_init_done) 
    {
        copy_file_range_fn_ptr = (copy_file_range_fn) dlsym(RTLD_NEXT, "copy_file_range");
        copy_file_range_init_done = 1;
    }
    status = copy_file_range_fn_ptr( fd_in, off_in, fd_out, off_out, len, flags );

    snprintf( fdpath, 32, "/proc/self/fd/%d", fd_out );
    real_return = realpath(fdpath, real_path);

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG copy_file_range to %s\n", real_path );

    if (!real_return) return(status);
    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    return(shimpost(real_path,status));
}



static int close_init_done = 0;
typedef int  (*close_fn) (int);
static close_fn close_fn_ptr = close;

int close(int fd) 
{

    int fdstat;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;
    int status;

    if (!close_init_done) {
        close_fn_ptr = (close_fn) dlsym(RTLD_NEXT, "close");
        close_init_done = 1;
        if (getenv("SR_POST_READS"))
           srshim_initialize( "post" );
    }
    
    fdstat = fcntl(fd, F_GETFL);

    if ( ((fdstat & O_ACCMODE) == O_RDONLY ) && ( !sr_c || !( SR_READ & sr_c->cfg->events ) ) )
           return close_fn_ptr(fd);
  
    snprintf(fdpath, 32, "/proc/self/fd/%d", fd);
    real_return = realpath(fdpath, real_path);

    if (!getenv("SR_POST_READS"))
       srshim_initialize( "post" );

    status = close_fn_ptr(fd);

    if (!real_return) return(status);

    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG close %s\n", real_path );

    return shimpost(real_path, status) ;
}


static int fclose_init_done = 0;
typedef int  (*fclose_fn) (FILE *);
static fclose_fn fclose_fn_ptr = fclose;

int fclose(FILE *f) 
{

    int fd;
    int fdstat;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;
    int status;

    if (!fclose_init_done) {
        fclose_fn_ptr = (fclose_fn) dlsym(RTLD_NEXT, "fclose");
        fclose_init_done = 1;
        if (getenv("SR_POST_READS"))
           srshim_initialize( "post" );
    }
    fd = fileno(f);
 
    fdstat = fcntl(fd, F_GETFL);

    if ( ((fdstat & O_ACCMODE) == O_RDONLY ) && ( !sr_c || !( SR_READ & sr_c->cfg->events ) ) )
           return fclose_fn_ptr(f);
  
    snprintf(fdpath, 32, "/proc/self/fd/%d", fd);
    real_return = realpath(fdpath, real_path);
    status = fclose_fn_ptr(f);

    if (!real_return) return(status);

    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG fclose continue %p %s\n", f, real_path );

    return shimpost(real_path, status) ;
}

/*


FIXME:
  
  Dunno if I want to go down this rabbit hole.  If someone opens a file and doesn't close it...
  it only matters for readonly files (SR_POST_READS)
  to deal with read on open would need:

  fopen
  fdopen
  fdreopen(
  open( 2args)
  open( 3 args )
  creat(
  openat( 3args )
  openat( 4args )
 
  dlopen(   
  dlmopen(


static int fopen_init_done = 0;
typedef FILE* (*fopen_fn) (const char *, const char *);
static fopen_fn fopen_fn_ptr = fopen;

FILE *fopen(const char *pathname, const char *mode)
{

    FILE *f = NULL;

    if (!fopen_init_done) {
        fopen_fn_ptr = (fopen_fn) dlsym(RTLD_NEXT, "fopen");
        fopen_init_done = 1;
        if (getenv("SR_POST_READS"))
           srshim_initialize( "post" );
    }

    if ( (!strcmp(mode,"r")) && ( !sr_c || !( SR_READ & sr_c->cfg->events ) ) )
        return fopen_fn_ptr( pathname, mode );

    f = fopen_fn_ptr( pathname, mode);
    
    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG fopen continue %s %s\n", pathname, mode );

    shimpost( pathname, (f==NULL) );
 
    return(f);
    
}

// MG modified open for 2 or 3 args

static int open_init_done = 0;
typedef int (*open_fn) (const char *, int, ...  );
static open_fn open_fn_ptr = open;

int open(const char *pathname, int flags, ... )
{
    int status = 0;
    int fd;

    // to support 2 or 3 args
    va_list args;
    va_start(args,flags);

    if (!open_init_done) {
        open_fn_ptr = (open_fn) dlsym(RTLD_NEXT, "open");
        open_init_done = 1;
        if (getenv("SR_POST_READS"))
           srshim_initialize( "post" );
    }

    if ( (flags & O_RDONLY) && ( !sr_c || !( SR_READ & sr_c->cfg->events ) ) )
        return open_fn_ptr( pathname, flags, args );

    fd = open_fn_ptr( pathname, flags, args );
    if ( fd == -1 ) status = -1;
    
    if ( getenv("SR_SHIMDEBUG")) fprintf( stderr, "SR_SHIMDEBUG open continue %s %04x\n", pathname, flags );

    status = shimpost( pathname, status );
    return fd;
 
}

 */
