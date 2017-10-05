
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

#include "sr_post.h"

/*
 libsrshim.


 FIXME:  1024, and PATH_MAX, should likely be replaced by code that mallocs properly.

 */


static int in_librshim_already_dammit = 0;

int shimpost( const char *path, int status )
{
    char *cwd=NULL;
    char *real_path=NULL;

    if (in_librshim_already_dammit) return(status);

    in_librshim_already_dammit=1;
    if (!status) 
    {
       if (path[0] == '/' )
       {
          if (getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG absolute shimpost %s\n", path );
          connect_and_post(path,"post");
       } else {
          cwd = get_current_dir_name();
          real_path = (char*)malloc( strlen(cwd) + strlen(path) + 2048 );
          //getwd(real_path);
          strcpy(real_path,cwd);
          strcat(real_path,"/");
          strcat(real_path,path);
          if (getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG relative shimpost %s\n", real_path );
          connect_and_post( real_path ,"post");
          free(real_path);
          free(cwd);
       }
    }
    in_librshim_already_dammit=0;

    return(status);
}


static int symlink_init_done = 0;
typedef int  (*symlink_fn) (const char*,const char*);
static symlink_fn symlink_fn_ptr = symlink;


int symlink(const char *target, const char* linkpath) 
{
    int status;

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG symlink %s %s\n", target, linkpath );
    if (!symlink_init_done) {
        symlink_fn_ptr = (symlink_fn) dlsym(RTLD_NEXT, "symlink");
        symlink_init_done = 1;
    }
    status = symlink_fn_ptr(target,linkpath);
    if ( !strncmp(linkpath,"/dev/", 5) ) return(status);
    if ( !strncmp(linkpath,"/proc/", 6) ) return(status);

    return(shimpost(linkpath, status));
}


static int link_init_done = 0;
typedef int  (*link_fn) (const char*,const char*);
static link_fn link_fn_ptr = link;

int link(const char *target, const char* linkpath) 
{
    int status;

    if (getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG link %s %s\n", target, linkpath );
    if (!link_init_done) {
        link_fn_ptr = (link_fn) dlsym(RTLD_NEXT, "link");
        link_init_done = 1;
    }
    status = link_fn_ptr(target,linkpath);
    if ( !strncmp(target,"/dev/", 5) ) return(status);
    if ( !strncmp(target,"/proc/", 6) ) return(status);

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

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG unlinkat %s dirfd=%d\n", path, dirfd );
    if (!unlinkat_init_done) {
        unlinkat_fn_ptr = (unlinkat_fn) dlsym(RTLD_NEXT, "unlinkat");
        unlinkat_init_done = 1;
    }
    status = unlinkat_fn_ptr(dirfd, path, flags);

    if ( dirfd == AT_FDCWD ) 
       return(shimpost(path,status));
    
    snprintf( fdpath, 32, "/proc/self/fd/%d", dirfd );
    real_return = realpath(fdpath, real_path);
    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG unlinkat relative directory %s real_return=%p\n", fdpath, real_return );
    strcat(real_path,"/");
    strcat(real_path,path);
    if (!real_return) return(status);

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG unlinkat realpath %s\n", real_path );

    return(shimpost(real_path,status));
}

static int unlink_init_done = 0;
typedef int  (*unlink_fn) (const char*);
static unlink_fn unlink_fn_ptr = unlink;

int unlink(const char *path) 
{
    int status;

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG unlink %s\n", path );
    if (!unlink_init_done) 
    {
        unlink_fn_ptr = (unlink_fn) dlsym(RTLD_NEXT, "unlink");
        unlink_init_done = 1;
    }
    status = unlink_fn_ptr(path);
    if ( !strncmp(path,"/dev/", 5) ) return(status);

    return(shimpost(path,status));
}

static int rename_init_done = 0;
typedef int  (*rename_fn) (const char*,const char*);
static rename_fn rename_fn_ptr = rename;

int rename(const char *oldpath, const char *newpath)
{
    int status;

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG rename %s %s\n", oldpath, newpath );
    if (!rename_init_done) 
    {
        rename_fn_ptr = (rename_fn) dlsym(RTLD_NEXT, "rename");
        rename_init_done = 1;
    }
    status = rename_fn_ptr(oldpath,newpath);
    if ( !strncmp(newpath,"/dev/", 5) ) return(status);
    if ( !strncmp(newpath,"/proc/", 6) ) return(status);

    // delete old if necessary...
    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG rm %s \n", oldpath );
    if (!status) shimpost(oldpath,0);

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG announce %s \n", newpath );
    return(shimpost(newpath,status));
}

static int renameat_init_done = 0;
typedef int  (*renameat_fn) (int, const char*, int, const char*);
static renameat_fn renameat_fn_ptr = renameat;

int renameat(int olddirfd, const char *oldpath, int newdirfd, const char *newpath)
{
    int status;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;
    char oreal_path[PATH_MAX+1];
    char *oreal_return;
    

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG renameat %s %s\n", oldpath, newpath );
    if (!renameat_init_done) 
    {
        renameat_fn_ptr = (renameat_fn) dlsym(RTLD_NEXT, "renameat");
        renameat_init_done = 1;
    }
    status = renameat_fn_ptr(olddirfd, oldpath, newdirfd, newpath);

    if ( newdirfd == AT_FDCWD ) 
       return(shimpost(newpath,status));

    snprintf( fdpath, 32, "/proc/self/fd/%d", newdirfd );
    real_return = realpath(fdpath, real_path);

    if (!real_return) return(status);

    strcat(real_path,"/");
    strcat(real_path,newpath);

    if (!status) 
    {
        snprintf( fdpath, 32, "/proc/self/fd/%d", olddirfd );
        oreal_return = realpath(fdpath, oreal_path);
        if (oreal_return) 
        {
            strcat(oreal_path,"/");
            strcat(oreal_path,oldpath);
            shimpost( oreal_path, 0 );
        }
        
    }
    return(shimpost(real_path,status));
}

static int renameat2_init_done = 0;
typedef int  (*renameat2_fn) (int, const char*, int, const char*, unsigned int);
static renameat2_fn renameat2_fn_ptr = NULL;

int renameat2(int olddirfd, const char *oldpath, int newdirfd, const char *newpath, unsigned int flags)
{
    int status;
    char fdpath[32];
    char real_path[PATH_MAX+1];
    char *real_return;
    char oreal_path[PATH_MAX+1];
    char *oreal_return;

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG renameat2 %s %s\n", oldpath, newpath );
    if (!renameat2_init_done) 
    {
        renameat2_fn_ptr = (renameat2_fn) dlsym(RTLD_NEXT, "renameat2");
        renameat2_init_done = 1;
    }
    status = renameat2_fn_ptr(olddirfd, oldpath, newdirfd, newpath, flags);

    if ( newdirfd == AT_FDCWD ) 
       return(shimpost(newpath,status));

    snprintf( fdpath, 32, "/proc/self/fd/%d", newdirfd );
    real_return = realpath(fdpath, real_path);

    if (!real_return) return(status);

    strcat(real_path,"/");
    strcat(real_path,newpath);

    if (!status) 
    {
        snprintf( fdpath, 32, "/proc/self/fd/%d", olddirfd );
        oreal_return = realpath(fdpath, oreal_path);
        if (oreal_return) 
        {
            strcat(oreal_path,"/");
            strcat(oreal_path,oldpath);
            shimpost( oreal_path, 0 );
        }
    }
    return(shimpost(real_path,status));
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

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG sendfile to %s\n", real_path );

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

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG copy_file_range to %s\n", real_path );

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
    }
    
    fdstat = fcntl(fd, F_GETFL);

    if ( (fdstat & O_ACCMODE) == O_RDONLY ) return close_fn_ptr(fd);
  
    snprintf(fdpath, 32, "/proc/self/fd/%d", fd);
    real_return = realpath(fdpath, real_path);
    status = close_fn_ptr(fd);

    if (!real_return) return(status);

    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG close %s\n", real_path );

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
    }
    fd = fileno(f);
 
    fdstat = fcntl(fd, F_GETFL);

    if ( (fdstat & O_ACCMODE) == O_RDONLY ) return fclose_fn_ptr(f);
  
    snprintf(fdpath, 32, "/proc/self/fd/%d", fd);
    real_return = realpath(fdpath, real_path);
    status = fclose_fn_ptr(f);

    if (!real_return) return(status);

    if ( !strncmp(real_path,"/dev/", 5) ) return(status);
    if ( !strncmp(real_path,"/proc/", 6) ) return(status);

    if ( getenv("SRSHIMDEBUG")) fprintf( stderr, "SRSHIMDEBUG fclose continue %p %s\n", f, real_path );

    return shimpost(real_path, status) ;
}

