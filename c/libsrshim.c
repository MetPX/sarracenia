
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

fprintf( stderr, "symlink\n");

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

fprintf( stderr, "link\n");
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

fprintf( stderr, "unlinkat\n");
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

fprintf( stderr, "unlink\n");
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

fprintf( stderr, "rename\n");
    if (!rename_init_done) 
    {
        rename_fn_ptr = (rename_fn) dlsym(RTLD_NEXT, "rename");
        rename_init_done = 1;
    }
    status = rename_fn_ptr(oldpath,newpath);
    if ( !strncmp(newpath,"/dev/", 5) ) return(status);
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

fprintf( stderr, "renameat\n");
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

fprintf( stderr, "renameat2\n");
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

