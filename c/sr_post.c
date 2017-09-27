/* vim:set ft=c ts=2 sw=2 sts=2 et cindent: */

/*
 * Usage info after license block.
 *
 * This code is by Peter Silva copyright (c) 2017 part of MetPX.
 * copyright is to the Government of Canada. code is GPL.
 *
 * based on a amqp_sendstring from rabbitmq-c package
 * the original license is below:
 */

/* 
  Minimal c implementation to allow posting of sr_post(7) messages.
  It has a lot of limitations, and no error checking for now.

  how to use:

  In a shell, to use an sr_config(7) style configuration file:
  set the SR_POST_CONFIG environment variable to the name of the
  file to use.

 
 limitations:
    - Doesn't support document_root, absolute paths posted.
    - Doesn't support cache.
    - does support csv for url, to allow load spreading.
    - seems to be about 30x faster than python version.

 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/limits.h>

#include <openssl/md5.h>
#include <openssl/sha.h>

#include <stdint.h>
#include <amqp_tcp_socket.h>
#include <amqp_ssl_socket.h>
#include <amqp.h>
#include <amqp_framing.h>

#include "sr_context.h"

// needed for sr_post_message.
#include "sr_consume.h"

/*
 Statically assign the maximum number of headers that can be included in a message.
 just picked a number.  I remember picking a larger one before, and it bombed, don't know why.

 */
#define HDRMAX (255)


amqp_table_entry_t headers[HDRMAX];

int hdrcnt = 0 ;

void header_reset() {
    hdrcnt--;
    for(; (hdrcnt>=0) ; hdrcnt--)
    {
        headers[hdrcnt].key = amqp_cstring_bytes("");
        headers[hdrcnt].value.kind = AMQP_FIELD_KIND_VOID;
        headers[hdrcnt].value.value.bytes = amqp_cstring_bytes("");
    }
    hdrcnt=0;
}

void header_add( char *tag, const char * value ) {

  if ( hdrcnt >= HDRMAX ) 
  {
     log_msg( LOG_ERROR, "ERROR too many headers! ignoring %s=%s\n", tag, value );
     return;
  }
  headers[hdrcnt].key = amqp_cstring_bytes(tag);
  headers[hdrcnt].value.kind = AMQP_FIELD_KIND_UTF8;
  headers[hdrcnt].value.value.bytes = amqp_cstring_bytes(value);
  hdrcnt++;
  //log_msg( LOG_DEBUG, "Adding header: %s=%s hdrcnt=%d\n", tag, value, hdrcnt );
}

void set_url( char* m, char* spec ) 
  /* append a url spec to the given message buffer
   */
{
  static const char* cu_url = NULL;
  char *sp;

  if ( strchr(spec,',') ) {
     //log_msg( LOG_DEBUG, "1 picking url, set=%s, cu=%s\n", spec, cu_url );
     if (cu_url) {
         cu_url = strchr(cu_url,','); // if there is a previous one, pick the next one.
         //log_msg( LOG_DEBUG, "2 picking url, set=%s, cu=%s\n", spec, cu_url );
     }
     if (cu_url) {
         cu_url++;                    // skip to after the comma.
         //log_msg( LOG_DEBUG, "3 picking url, set=%s, cu=%s\n", spec, cu_url );
     } else {
         cu_url = spec ;                // start from the beginning.
         //log_msg( LOG_DEBUG, "4 picking url, set=%s, cu=%s\n", spec, cu_url );
     }
     sp=strchr(cu_url,',');
     if (sp) strncat( m, cu_url, sp-cu_url );
     else strcat( m, cu_url );
  } else  {
     strcat( m, spec );
  }
}

unsigned long int set_blocksize( long int bssetting, size_t fsz )
{
      unsigned long int tfactor =  (50*1024*1024) ;

      switch( bssetting )
      {
        case 0: // autocompute 
             if ( fsz > 100*tfactor ) return( 10*tfactor );
             else if ( fsz > 10*tfactor ) return( (unsigned long int)( (fsz+9)/10) );
             else if ( fsz > tfactor ) return( (unsigned long int)( (fsz+2)/3) ) ;
             else return(fsz);
             break;

        case 1: // send file as one piece.
             return(fsz);
             break;

       default: // partstr=i
             return(bssetting);
             break;
      }

}


void sr_post_message( struct sr_context *sr_c, struct sr_message_t *m )
{
    char message_body[1024];
    char smallbuf[256];
    amqp_table_t table;
    amqp_basic_properties_t props;
    signed int status;
    struct sr_header_t *uh;

    if (( m->sum[0] != 'R' ) && ( m->sum[0] != 'L' ))
       sprintf( smallbuf, "%c,%ld,%ld,%ld,%ld", m->parts_s, m->parts_blksz, m->parts_blkcount, m->parts_rem, m->parts_num );
    else 
       sprintf( smallbuf, "" );

    fprintf( stderr, "parts=%s\n", smallbuf);

    if ( sr_c->cfg->cache > 0 ) 
    { 
           status = sr_cache_check( sr_c->cfg->cachep, m->sum[0], m->sum, m->path, smallbuf ) ; 
           log_msg( LOG_DEBUG, "post_message cache_check result=%d\n", status );
           if (!status) return; // cache hit.
    }
    strcpy( message_body, m->datestamp);
    strcat( message_body, " " );
    strcat( message_body, m->url );
    strcat( message_body, " " );
    strcat( message_body, m->path );
    strcat( message_body, " \n" );
 
    header_reset();

    header_add( "atime", m->atime );
    header_add( "from_cluster", m->from_cluster );

    sprintf( smallbuf, "%04o", m->mode );
    header_add( "mode", smallbuf );
    header_add( "mtime", m->mtime );

    if (( m->sum[0] != 'R' ) && ( m->sum[0] != 'L' ))
    {
       sprintf( smallbuf, "%c,%ld,%ld,%ld,%ld", m->parts_s, m->parts_blksz, m->parts_blkcount, m->parts_rem, m->parts_num );
       header_add( "parts", smallbuf );
    }

    header_add( "sum", sr_hash2sumstr(m->sum));
    header_add( "to_clusters", m->to_clusters );

    for(  uh=m->user_headers; uh ; uh=uh->next )
        header_add(uh->key, uh->value);

    table.num_entries = hdrcnt;
    table.entries=headers;

    props._flags = AMQP_BASIC_HEADERS_FLAG | AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_DELIVERY_MODE_FLAG;
    props.content_type = amqp_cstring_bytes("text/plain");
    props.delivery_mode = 2; /* persistent delivery mode */
    props.headers = table;

    status = amqp_basic_publish(sr_c->cfg->post_broker->conn, 1, amqp_cstring_bytes(sr_c->cfg->post_broker->exchange), 
              amqp_cstring_bytes(m->routing_key), 0, 0, &props, amqp_cstring_bytes(message_body));

    if ( status < 0 ) 
        log_msg( LOG_ERROR, "sr_%s: publish of message for  %s%s failed.\n", sr_c->cfg->progname, m->url, m->path );
    else 
        log_msg( LOG_INFO, "published: %s\n", sr_message_2log(m) );

}
int sr_file2message_start(struct sr_context *sr_c, const char *pathspec, struct stat *sb, struct sr_message_t *m ) 
/*
  reading a file, initialize the message that corresponds to it. Return the number of parts that will be needed.
 */
{
   return(0);
}

struct sr_message_t *sr_file2message_seq(const char *pathspec, int seq, struct sr_message_t *m ) 
/*
  Given a message from a "started" file, the prototype message, and a sequence number ( sequence is number of blocks of partsze )
  return the adjusted prototype message.  (requires reading part of the file to checksum it.)
 */
{
  return(NULL);
}


void sr_post(struct sr_context *sr_c, const char *pathspec, struct stat *sb ) 
{

  char  routingkey[255];
  char  message_body[1024];
  char  partstr[255];
  char  modebuf[6];
  char  fn[PATH_MAXNUL];
  char  postfn[PATH_MAXNUL];
  char  *drfound;
  char  linkstr[PATH_MAXNUL];
  char *linkp;
  int   linklen;
  char  atimestr[18];
  char  mtimestr[18];
  char  sumalgo;
  char *sumstr;
  signed int status;
  int lasti;
  int commonhdridx;
  unsigned long block_size;
  unsigned long block_count;
  unsigned long block_num;
  unsigned long block_rem;
  amqp_table_t table;
  struct sr_header_t *uh;
  amqp_basic_properties_t props;
  struct sr_mask_t *mask;
  char psc;                     // part strategy character.

  if (*pathspec != '/' ) // need absolute path.
  { 
      getcwd( fn, PATH_MAX);
      strcat( fn, "/" );
      strcat( fn, pathspec);
  } else {
      if ( sr_c->cfg->realpath ) 
          realpath( pathspec, fn );
      else
          strcpy( fn, pathspec );
  }


  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     log_msg( LOG_DEBUG, "sr_%s called with: %s sb=%p\n", sr_c->cfg->progname, fn, sb );

  /* apply the accept/reject clauses */
  mask = isMatchingPattern(sr_c->cfg, fn);

  if ( (mask && !(mask->accepting)) || (!mask && !(sr_c->cfg->accept_unmatched)) )
  {
      if ( (sr_c->cfg) && sr_c->cfg->debug ) 
          log_msg( LOG_DEBUG, "rejecting: %s\n", fn );
      return;
  }
  if ( sb && S_ISDIR(sb->st_mode) ) 
  {
      if ( (sr_c->cfg) && sr_c->cfg->debug )
          log_msg( LOG_DEBUG, "sr_cpost cannot post directories: %s\n", fn );
      return;
  }
  
  //if ( (sr_c->cfg) && sr_c->cfg->debug )
  //   log_msg( LOG_DEBUG, "sr_cpost accepted posting to exchange:  %s\n", sr_c->cfg->post_broker->exchange );


  strcpy( postfn, fn );
  if (sr_c->cfg->documentroot) 
  {
      drfound = strstr(fn, sr_c->cfg->documentroot ); 
   
      if (drfound) 
      {
          drfound += strlen(sr_c->cfg->documentroot) ; 
          strcpy( postfn, drfound );
      } 
  } 
  strcpy( routingkey, sr_c->cfg->topic_prefix );

  strcat( routingkey, postfn );
  lasti=0;
  for( int i=strlen(sr_c->cfg->topic_prefix) ; i< strlen(routingkey) ; i++ )
  {
      if ( routingkey[i] == '/' ) 
      {
           if ( lasti > 0 ) 
           {
              routingkey[lasti]='.';
           }
           lasti=i;
      }
  }
  routingkey[lasti]='\0';

  strcpy( message_body, sr_time2str(NULL));
  strcat( message_body, " " );
  set_url( message_body, sr_c->cfg->url );
  strcat( message_body, " " );
  strcat( message_body, postfn );

/*
  if ( sr_c->cfg->documentroot ) 
  {
      if ( !strncmp( sr_c->cfg->documentroot, fn, strlen(sr_c->cfg->documentroot) ) ) 
          strcat( message_body, fn+strlen(sr_c->cfg->documentroot) );
  } else 
     strcat( message_body, fn);
 */

  if ( (sr_c->cfg) && sr_c->cfg->debug )
     log_msg( LOG_DEBUG, "sr_%s routingkey: %s message_body: %s sumalgo:%c sb:%p event: 0x%x\n",  sr_c->cfg->progname,
          routingkey, message_body, sr_c->cfg->sumalgo, sb, sr_c->cfg->events );

  header_reset();

  header_add( "to_clusters", sr_c->cfg->to );

  for(  uh=sr_c->cfg->user_headers; uh ; uh=uh->next )
     header_add(uh->key, uh->value);

  sumalgo = sr_c->cfg->sumalgo;
  block_count = 1;

  if ( !sb ) 
  {
      if ( ! ((sr_c->cfg->events)&SR_DELETE) ) return;
      sumalgo='R';
  } else if ( S_ISLNK(sb->st_mode) ) 
  {
      if ( ! ((sr_c->cfg->events)&SR_LINK) ) return;

      sumalgo='L';
      linklen = readlink( fn, linkstr, PATH_MAX );
      linkstr[linklen]='\0';
      if ( sr_c->cfg->realpath ) 
      {
          linkp = realpath( linkstr, NULL );
          if (linkp) 
          {
               strcpy( linkstr, linkp );
               free(linkp);
          }
      }
      header_add( "link", linkstr );

  } else if (S_ISREG(sb->st_mode)) 
  {   /* regular files, add mode and determine block parameters */

      if ( ! ((sr_c->cfg->events)&(SR_CREATE|SR_MODIFY)) ) return;

      if ( access( fn, R_OK ) ) return; // will not be able to checksum if we cannot read.

      strcpy( atimestr, sr_time2str(&(sb->st_atim)));
      header_add( "atime", atimestr);

      strcpy( mtimestr, sr_time2str(&(sb->st_mtim)));
      header_add( "mtime", mtimestr );
      sprintf( modebuf, "%04o", (sb->st_mode & 07777) );
      header_add( "mode", modebuf);
      block_size = set_blocksize( sr_c->cfg->blocksize, sb->st_size );
      psc = (block_size < sb->st_size )? 'i':'1' ;

      if ( block_size == 0 ) {
          block_rem = 0;
      } else {
          block_rem = sb->st_size%block_size ;
          block_count = ( sb->st_size / block_size ) + ( block_rem?1:0 );
      }

  } 
  /* FIXME:  should we do these as well?
   else 
      S_ISIFO(sb->st_mode)  -> sumstr P,random
      S_ISCHR(sb->st_mode)  -> sumstr C,maj,min
      S_ISBLK(sb->st_mode)  -> sumstr B,maj,min
      could be done, does it make any sense?

   */
 
  commonhdridx = hdrcnt; // save location of headers common to all messages.
  block_num = 0;

  while ( block_num < block_count ) 
  { /* Footnote 1: FIXME: posting partitioned parts not implemented, see end notes */
      hdrcnt = commonhdridx;

      if ( ( sumalgo != 'L' ) && ( sumalgo != 'R' ) )  {

          sprintf( partstr, "%c,%lu,%lu,%lu,%lu", psc, block_size, 
              block_count, block_rem, block_num );
          header_add( "parts", partstr );
      } else
          strcpy(partstr,"");

      /* log_msg( LOG_DEBUG, "sumaglo: %c, fn=+%s+, partstr=+%s+, linkstr=+%s+\n", sumalgo, fn, partstr, linkstr );
      log_msg( LOG_DEBUG, " bsz=%ld, bc=%ld, brem=%ld, bnum=%ld\n", block_size, block_count, block_rem, block_num ) ;
       */
      sumstr = set_sumstr( sumalgo, fn, partstr, linkstr, block_size, block_count, block_rem, block_num ); 

      if ( !sumstr ) 
      {
         log_msg( LOG_ERROR, "sr_post unable to generate %c checksum for: %s\n", sumalgo, fn );
         return;
      }
      header_add( "sum", sumstr );
      
      table.num_entries = hdrcnt;
      table.entries=headers;

      props._flags = AMQP_BASIC_HEADERS_FLAG | AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_DELIVERY_MODE_FLAG;
      props.content_type = amqp_cstring_bytes("text/plain");
      props.delivery_mode = 2; /* persistent delivery mode */
      props.headers = table;

      if ( sr_c->cfg->cache > 0 ) 
      { 
           status = sr_cache_check( sr_c->cfg->cachep, sumalgo, sr_sumstr2hash(sumstr), fn, partstr ) ; 
           log_msg( LOG_DEBUG, "cache_check result=%d\n", status );
           //sr_cache_save( sr_c->cfg->cachep, 1 );
      } else {
           status = 1;
      }

      if ( status != 0 )
      {
          status = amqp_basic_publish(sr_c->cfg->post_broker->conn, 1, amqp_cstring_bytes(sr_c->cfg->post_broker->exchange), 
              amqp_cstring_bytes(routingkey), 0, 0, &props, amqp_cstring_bytes(message_body));
      }
      block_num++;
 
      if ( status < 0 ) 
      {
          log_msg( LOG_ERROR, "sr_%s: publish of block %lu of %lu failed.\n", sr_c->cfg->progname, block_num, block_count );
      } else {
          log_msg( LOG_INFO, "published: %s topic=%s sum=%s \n" , message_body, 
              routingkey, sumstr );
              // parts, modebuf, atimestr, mtimestr );
      }
  }
}

int sr_post_cleanup( struct sr_context *sr_c )
{
    amqp_rpc_reply_t reply;

    amqp_exchange_delete( sr_c->cfg->post_broker->conn, 1, amqp_cstring_bytes(sr_c->cfg->exchange), 0 );

    reply = amqp_get_rpc_reply(sr_c->cfg->post_broker->conn);
    if (reply.reply_type != AMQP_RESPONSE_NORMAL ) 
    {
        sr_amqp_reply_print(reply, "failed AMQP get_rpc_reply exchange delete");
        return(0);
    }
    return(1);
}

int sr_post_init( struct sr_context *sr_c )
{
    amqp_rpc_reply_t reply;

    amqp_exchange_declare( sr_c->cfg->post_broker->conn, 1, amqp_cstring_bytes(sr_c->cfg->exchange),
          amqp_cstring_bytes("topic"), 0, sr_c->cfg->durable, 0, 0, amqp_empty_table );

 
    reply = amqp_get_rpc_reply(sr_c->cfg->post_broker->conn);
    if (reply.reply_type != AMQP_RESPONSE_NORMAL ) 
    {
        sr_amqp_reply_print(reply, "failed AMQP get_rpc_reply exchange declare");
        //return(0);
    }

    return(1);
}

void connect_and_post(const char *fn,const char* progname) 
{

  static struct sr_config_t sr_cfg; 
  static int config_read = 0;
  struct sr_mask_t *mask; 
  struct sr_context *sr_c = NULL;
  char *setstr;
  struct stat sb;

  if ( !fn ) 
  {
     log_msg( LOG_ERROR, "post null\n" );
     return;
  }

  setstr = getenv( "SR_POST_CONFIG" ) ;
  if ( setstr != NULL )
  { 
     if ( config_read == 0 ) 
     {
       sr_config_init(&sr_cfg,progname);
       config_read = sr_config_read(&sr_cfg,setstr);
       if (!config_read) return;
     }
     if ( !sr_config_finalize( &sr_cfg, 0 )) return;

     sr_c = sr_context_init_config(&sr_cfg);
  } 
  if (!sr_c) return;
 
  mask = isMatchingPattern(&sr_cfg, fn);
  if ( (mask && !(mask->accepting)) || (!mask && !(sr_cfg.accept_unmatched)) )
  { //reject.
      log_msg( LOG_INFO, "mask: %p, mask->accepting=%d accept_unmatched=%d\n", 
            mask, mask->accepting, sr_cfg.accept_unmatched );
      if (sr_cfg.debug) log_msg( LOG_DEBUG, "sr_cpost rejected 2: %s\n", fn );
      return;
  }

  sr_c = sr_context_connect(sr_c);
  if (sr_c == NULL ) 
  {
    log_msg( LOG_ERROR, "failed to parse AMQP post_broker settings\n");
    return;
  }
  if ( lstat( fn, &sb ) ) sr_post( sr_c, fn, NULL );
  else sr_post( sr_c, fn, &sb );

  sr_context_close(sr_c);
}



