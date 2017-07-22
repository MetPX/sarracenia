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


#define HDRMAX (20)
amqp_table_entry_t headers[HDRMAX];

int hdrcnt = 0 ;

void header_reset() {
    hdrcnt = 0 ;
}

void header_add( char *tag, const char * value ) {

  if ( hdrcnt >= HDRMAX ) 
  {
     fprintf( stderr, "ERROR too many headers! ignoring %s=%s\n", tag, value );
     return;
  }
  headers[hdrcnt].key = amqp_cstring_bytes(tag);
  headers[hdrcnt].value.kind = AMQP_FIELD_KIND_UTF8;
  headers[hdrcnt].value.value.bytes = amqp_cstring_bytes(value);
  hdrcnt++;
  //fprintf( stderr, "Adding header: %s=%s hdrcnt=%d\n", tag, value, hdrcnt );
}

// SHA512 being the longest digest...
char sumstr[ SR_SUMSTRLEN ];

void hash2sumstr( unsigned char *h, int l )
{
  int i;
  for(i=1; i < l+1; i++ )
     //printf( "h[%d] = %u\n", i, (unsigned char)h[i] );
     sprintf( &(sumstr[i*2]), "%02x", (unsigned char)h[i-1]);
  sumstr[2*i]='\0';
}

#define SUMBUFSIZE (4096*1024)

char *set_sumstr( char algo, const char* fn, unsigned long block_size, unsigned long block_count, 
       unsigned long block_rem, unsigned long block_num )
 /* 
   return a correct sumstring (assume it is big enough)  as per sr_post(7)
   algo = 
     '0' - no checksum, value is random.
     'd' - md5sum of block.
     'n' - md5sum of filename (fn).
     's' - sha512 sum of block.

   block starts at block_size * block_num, and ends 
  */
{
   MD5_CTX md5ctx;
   SHA512_CTX shactx;
   unsigned char hash[SHA512_DIGEST_LENGTH]; // Assumed longest possible hash.

   static int fd;
   static char buf[SUMBUFSIZE];
   long bytes_read ; 
   long how_many_to_read;
   char *just_the_name;

   unsigned long start = block_size * block_num ;
   unsigned long end;

   end =  (block_num == (block_count-1)) ? (start + block_rem) : (start +block_size );

   sumstr[0]=algo;
   sumstr[1]=',';
   sumstr[2]='\0'; 
   switch (algo) {

   case '0' : case 'R' : case 'L' :  // null checksum, removal, or symlinks.
       sprintf( sumstr+2, "%ld", random()%1000 );
       break;

   case 'd' :
       MD5_Init(&md5ctx);

       // keep file open through repeated calls.
       if ( ! (fd > 0) ) fd = open( fn, O_RDONLY );
       if ( fd < 0 ) 
       { 
           fprintf( stderr, "unable to read file for checksumming\n" );
           return(NULL);
       } 
       lseek( fd, start, SEEK_SET );
       //fprintf( stderr, "checksumming start: %lu to %lu\n", start, end );
       while ( start < end ) 
       {
           how_many_to_read= ( SUMBUFSIZE < (end-start) ) ? SUMBUFSIZE : (end-start) ;

           bytes_read=read(fd,buf, how_many_to_read );           
           if ( bytes_read >= 0 ) 
           {
              MD5_Update(&md5ctx, buf, bytes_read );
              start += bytes_read;
           } else {
              fprintf( stderr, "error reading %s\n", fn );
              break;
           } 
       }

       // close fd, when end of file reached.
       if ( end >= ((block_count-1)*block_size+block_rem)) close(fd);

       MD5_Final(hash, &md5ctx);
       hash2sumstr(hash,MD5_DIGEST_LENGTH); 
       break;

   case 'n' :
       MD5_Init(&md5ctx);
       just_the_name = rindex(fn,'/')+1;
       MD5_Update(&md5ctx, just_the_name, strlen(just_the_name) );
       MD5_Final(hash, &md5ctx);
       hash2sumstr(hash,MD5_DIGEST_LENGTH); 
       break;
       
   case 's' :
       SHA512_Init(&shactx);

       // keep file open through repeated calls.
       if ( ! (fd > 0) ) fd = open( fn, O_RDONLY );
       if ( fd < 0 ) 
       { 
           fprintf( stderr, "unable to read file for checksumming\n" );
           return(NULL);
       } 
       lseek( fd, start, SEEK_SET );
       //fprintf( stderr, "checksumming start: %lu to %lu\n", start, end );
       while ( start < end ) 
       {
           how_many_to_read= ( SUMBUFSIZE < (end-start) ) ? SUMBUFSIZE : (end-start) ;

           bytes_read=read(fd,buf, how_many_to_read );           

           //fprintf( stderr, "checksumming how_many_to_read: %lu bytes_read: %lu\n", 
           //    how_many_to_read, bytes_read );

           if ( bytes_read >= 0 ) 
           {
              SHA512_Update(&shactx, buf, bytes_read );
              start += bytes_read;
           } else {
              fprintf( stderr, "error reading %s\n", fn );
              break;
           } 
       }

       // close fd, when end of file reached.
       if ( end >= ((block_count-1)*block_size+block_rem)) close(fd);

       SHA512_Final(hash, &shactx);
       hash2sumstr(hash,SHA512_DIGEST_LENGTH); 
       break;

   default:
       fprintf( stderr, "sum algorithm %c unimplemented\n", algo );
       return(NULL);
   }
   return(sumstr);

}

void set_url( char* m, char* spec ) 
  /* append a url spec to the given message buffer
   */
{
  static const char* cu_url = NULL;
  char *sp;

  if ( strchr(spec,',') ) {
     //fprintf( stderr, "1 picking url, set=%s, cu=%s\n", spec, cu_url );
     if (cu_url) {
         cu_url = strchr(cu_url,','); // if there is a previous one, pick the next one.
         //fprintf( stderr, "2 picking url, set=%s, cu=%s\n", spec, cu_url );
     }
     if (cu_url) {
         cu_url++;                    // skip to after the comma.
         //fprintf( stderr, "3 picking url, set=%s, cu=%s\n", spec, cu_url );
     } else {
         cu_url = spec ;                // start from the beginning.
         //fprintf( stderr, "4 picking url, set=%s, cu=%s\n", spec, cu_url );
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


void sr_post(struct sr_context *sr_c, const char *pathspec, struct stat *sb ) 
{

  char routingkey[255];
  char message_body[1024];
  char partstr[255];
  char modebuf[6];
  char linkstr[PATH_MAXNUL];
  char fn[PATH_MAXNUL];
  int  linklen;
  char atimestr[18];
  char mtimestr[18];
  char sumalgo;
  signed int status;
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
      strcpy( fn, pathspec );
  }

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "sr_cpost called with: %s sb=%p\n", fn, sb );

  /* apply the accept/reject clauses */
  mask = isMatchingPattern(sr_c->cfg, fn);

  if ( (mask && !(mask->accepting)) || (!mask && !(sr_c->cfg->accept_unmatched)) )
  {
      if ( (sr_c->cfg) && sr_c->cfg->debug ) 
          fprintf( stderr, "rejecting: %s\n", fn );
      return;
  }
  if ( sb && S_ISDIR(sb->st_mode) ) {
      if ( (sr_c->cfg) && sr_c->cfg->debug )
          fprintf( stderr, "sr_cpost cannot post directories: %s\n", fn );
      return;
  }
  if ( (sr_c->cfg) && sr_c->cfg->debug )
     fprintf( stderr, "sr_cpost accepted posting to exchange:  %s\n", sr_c->exchange );

  strcpy( routingkey, sr_c->cfg->topic_prefix );

  strcat( routingkey, fn );
  for( int i=strlen(sr_c->cfg->topic_prefix) ; i< strlen(routingkey) ; i++ )
      if ( routingkey[i] == '/' ) routingkey[i]='.';

  if ( (sr_c->cfg) && sr_c->cfg->debug )
     fprintf( stderr, "posting, routingkey: %s\n", routingkey );

  strcpy( message_body, sr_time2str(NULL));
  strcat( message_body, " " );
  set_url( message_body, sr_c->cfg->url );
  strcat( message_body, " " );
  strcat( message_body, fn);

  if ( (sr_c->cfg) && sr_c->cfg->debug )
     fprintf( stderr, "sr_cpost message_body: %s sumalgo:%c sb:%p event:%x\n", 
          message_body, sr_c->cfg->sumalgo, sb, sr_c->cfg->events );

  header_reset();

  header_add( "to_clusters", sr_c->to );

  for(  uh=sr_c->cfg->user_headers; uh ; uh=uh->next )
     header_add(uh->key, uh->value);

  sumalgo = sr_c->cfg->sumalgo;
  block_count = 1;

  if ( !sb ) {
      if ( ! ((sr_c->cfg->events)&SR_DELETE) ) return;
      sumalgo='R';
  } else if ( S_ISLNK(sb->st_mode) ) {
      if ( ! ((sr_c->cfg->events)&SR_LINK) ) return;
      sumalgo='L';
      linklen = readlink( fn, linkstr, PATH_MAX );
      linkstr[linklen]='\0';
      header_add( "link", linkstr );

  } else if (S_ISREG(sb->st_mode)) {  /* regular files, add mode and determine block parameters */
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
      }

      if (! set_sumstr( sumalgo, fn, block_size, block_count, block_rem, block_num ) ) 
      {
         fprintf( stderr, "sr_cpost unable to generate %c checksum for: %s\n", sumalgo, fn );
         return;
      }
      header_add( "sum", sumstr );

      table.num_entries = hdrcnt;
      table.entries=headers;

      props._flags = AMQP_BASIC_HEADERS_FLAG | AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_DELIVERY_MODE_FLAG;
      props.content_type = amqp_cstring_bytes("text/plain");
      props.delivery_mode = 2; /* persistent delivery mode */
      props.headers = table;

      status = amqp_basic_publish(sr_c->conn, 1, amqp_cstring_bytes(sr_c->exchange), 
          amqp_cstring_bytes(routingkey), 0, 0, &props, amqp_cstring_bytes(message_body));

      block_num++;

      if ( status < 0 ) 
          fprintf( stderr, "ERROR: sr_cpost: publish of block %lu of %lu failed.\n", block_num, block_count );
      else if ( (sr_c->cfg) && sr_c->cfg->debug )
          fprintf( stderr, "posting, publish block %lu of %lu.\n", block_num, block_count );

  }
}

int sr_post_cleanup( struct sr_context *sr_c )
{
    amqp_rpc_reply_t reply;

    amqp_exchange_delete( sr_c->conn, 1, amqp_cstring_bytes(sr_c->cfg->exchange), 0 );

    reply = amqp_get_rpc_reply(sr_c->conn);
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

    amqp_exchange_declare( sr_c->conn, 1, amqp_cstring_bytes(sr_c->cfg->exchange),
          amqp_cstring_bytes("topic"), 0, 1, 0, 0, amqp_empty_table );

    reply = amqp_get_rpc_reply(sr_c->conn);
    if (reply.reply_type != AMQP_RESPONSE_NORMAL ) 
    {
        sr_amqp_reply_print(reply, "failed AMQP get_rpc_reply exchange declare");
        return(0);
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
     fprintf( stderr, "post null\n" );
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
     sr_c = sr_context_init_config(&sr_cfg);
  } 
  if (!sr_c) return;
 
  mask = isMatchingPattern(&sr_cfg, fn);
  if ( (mask && !(mask->accepting)) || (!mask && !(sr_cfg.accept_unmatched)) )
  { //reject.
      fprintf( stderr, "mask: %p, mask->accepting=%d accept_unmatched=%d\n", 
            mask, mask->accepting, sr_cfg.accept_unmatched );
      if (sr_cfg.debug) fprintf( stderr, "sr_cpost rejected 2: %s\n", fn );
      return;
  }

  sr_c = sr_context_connect(sr_c);
  if (sr_c == NULL ) 
  {
    fprintf( stderr, "failed to parse AMQP broker settings\n");
    return;
  }
  if ( lstat( fn, &sb ) ) sr_post( sr_c, fn, NULL );
  else sr_post( sr_c, fn, &sb );

  sr_context_close(sr_c);
}



