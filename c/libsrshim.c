
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
 preload proof of concept from Alain St-Denis...
 with mods to work with sr_context

 */

/*
  to avoid recursive calls.
 */

static int in_librshim_already_dammit = 0;

int shimpost( const char *path, int status )
{
    if (in_librshim_already_dammit) return(status);

    in_librshim_already_dammit=1;

    if (!status) connect_and_post(path,"post");

    in_librshim_already_dammit=0;

    return(status);
}

static int symlink_init_done = 0;
typedef int  (*symlink_fn) (const char*,const char*);
static symlink_fn symlink_fn_ptr = symlink;


int symlink(const char *target, const char* linkpath) 
{
    int status;

fprintf( stderr, "symlink %s %s\n", target, linkpath );
    if (!symlink_init_done) {
        symlink_fn_ptr = (symlink_fn) dlsym(RTLD_NEXT, "symlink");
        symlink_init_done = 1;
    }
    status = symlink_fn_ptr(target,linkpath);
    if ( !strncmp(linkpath,"/dev/", 5) ) return(status);

    return(shimpost(linkpath, status));
}


static int link_init_done = 0;
typedef int  (*link_fn) (const char*,const char*);
static link_fn link_fn_ptr = link;

int link(const char *target, const char* linkpath) 
{
    int status;

fprintf( stderr, "link %s %s\n", target, linkpath );
    if (!link_init_done) {
        link_fn_ptr = (link_fn) dlsym(RTLD_NEXT, "link");
        link_init_done = 1;
    }
    status = link_fn_ptr(target,linkpath);
    if ( !strncmp(target,"/dev/", 5) ) return(status);

    return(shimpost(linkpath, status));
}

static int unlinkat_init_done = 0;
typedef int  (*unlinkat_fn) (int dirfd, const char*, int flags);
static unlinkat_fn unlinkat_fn_ptr = unlinkat;

int unlinkat(int dirfd, const char *path, int flags) 
{
    int status;
    char fdpath[32];
    char real_path[PATH_MAX];
    char *real_return;

fprintf( stderr, "unlinkat %s\n", path );
    if (!unlinkat_init_done) {
        unlinkat_fn_ptr = (unlinkat_fn) dlsym(RTLD_NEXT, "unlinkat");
        unlinkat_init_done = 1;
    }
    status = unlinkat_fn_ptr(dirfd, path, flags);

    snprintf( fdpath, 32, "/proc/self/fd/%d", dirfd );
    real_return = realpath(fdpath, real_path);
 
    if (!real_return) return(status);
    if ( !strncmp(path,"/dev/", 5) ) return(status);

    strcat(real_path,"/");
    strcat(real_path,path);

    return(shimpost(real_path,status));
}

static int unlink_init_done = 0;
typedef int  (*unlink_fn) (const char*);
static unlink_fn unlink_fn_ptr = unlink;

int unlink(const char *path) 
{
    int status;

fprintf( stderr, "unlink %s\n", path );
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

fprintf( stderr, "renameat %s %s\n", oldpath, newpath );
    if (!rename_init_done) 
    {
        rename_fn_ptr = (rename_fn) dlsym(RTLD_NEXT, "rename");
        rename_init_done = 1;
    }
    status = rename_fn_ptr(oldpath,newpath);
    if ( !strncmp(newpath,"/dev/", 5) ) return(status);

    // delete old if necessary...
    if (!status) shimpost(oldpath,0);

    return(shimpost(newpath,status));
}

static int renameat_init_done = 0;
typedef int  (*renameat_fn) (int, const char*, int, const char*);
static renameat_fn renameat_fn_ptr = renameat;

int renameat(int olddirfd, const char *oldpath, int newdirfd, const char *newpath)
{
    int status;
    char fdpath[32];
    char real_path[PATH_MAX];
    char *real_return;
    char oreal_path[PATH_MAX];
    char *oreal_return;
    

fprintf( stderr, "renameat %s %s\n", oldpath, newpath );
    if (!renameat_init_done) 
    {
        renameat_fn_ptr = (renameat_fn) dlsym(RTLD_NEXT, "renameat");
        renameat_init_done = 1;
    }
    status = renameat_fn_ptr(olddirfd, oldpath, newdirfd, newpath);

    snprintf( fdpath, 32, "/proc/self/fd/%d", newdirfd );
    real_return = realpath(fdpath, real_path);

    if (!real_return) return(status);
    if ( !strncmp(real_path,"/dev/", 5) ) return(status);

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
    char real_path[PATH_MAX];
    char *real_return;
    char oreal_path[PATH_MAX];
    char *oreal_return;

fprintf( stderr, "renameat2 %s %s\n", oldpath, newpath );
    if (!renameat2_init_done) 
    {
        renameat2_fn_ptr = (renameat2_fn) dlsym(RTLD_NEXT, "renameat2");
        renameat2_init_done = 1;
    }
    status = renameat2_fn_ptr(olddirfd, oldpath, newdirfd, newpath, flags);

    snprintf( fdpath, 32, "/proc/self/fd/%d", newdirfd );
    real_return = realpath(fdpath, real_path);

    if (!real_return) return(status);
    if ( !strncmp(real_path,"/dev/", 5) ) return(status);

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


static int copy_file_range_init_done = 0;
typedef int  (*copy_file_range_fn) (int, loff_t *, int, loff_t *, size_t, unsigned int);
static copy_file_range_fn copy_file_range_fn_ptr = NULL;

int copy_file_range(int fd_in, loff_t *off_in, int fd_out, loff_t *off_out, size_t len, unsigned int flags)
{
    int status;
    char fdpath[32];
    char real_path[PATH_MAX];
    char *real_return;

fprintf( stderr, "copy_file_range\n" );
    if (!copy_file_range_init_done) 
    {
        copy_file_range_fn_ptr = (copy_file_range_fn) dlsym(RTLD_NEXT, "copy_file_range");
        copy_file_range_init_done = 1;
    }
    status = copy_file_range_fn_ptr( fd_in, off_in, fd_out, off_out, len, flags );

    snprintf( fdpath, 32, "/proc/self/fd/%d", fd_out );
    real_return = realpath(fdpath, real_path);

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
    char real_path[PATH_MAX];
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

    return shimpost(real_path, status) ;
}

