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
#include <time.h>
#include <fcntl.h>
#include <linux/limits.h>

#include <openssl/md5.h>
#include <openssl/sha.h>

#include <stdint.h>
#include <amqp_tcp_socket.h>
#include <amqp_ssl_socket.h>
#include <amqp.h>
#include <amqp_framing.h>

#include "sr_consume.h"


static struct sr_message_t msg;

int sr_consume_cleanup(struct sr_context *sr_c)
{
  amqp_rpc_reply_t reply;
  char p[PATH_MAX];

  amqp_queue_delete( sr_c->cfg->broker->conn, 1, amqp_cstring_bytes(sr_c->cfg->queuename), 0, 0 );

  reply = amqp_get_rpc_reply(sr_c->cfg->broker->conn);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
      sr_amqp_reply_print(reply, "queue delete failed");
      return(0);
  }
  /* PS - should this be in sr_config? see sr_config_finalize for the other end of this
   */

  sprintf( p, "%s/.cache/sarra/%s/%s/sr_%s.%s.%s", getenv("HOME"),
            sr_c->cfg->progname, sr_c->cfg->configname, sr_c->cfg->progname, 
            sr_c->cfg->configname, sr_c->cfg->broker->user );
  unlink(p);
  return(1);
}

int sr_consume_setup(struct sr_context *sr_c) 
 /*
    declare a queue and bind it to the configured exchange.

  */
{
  amqp_rpc_reply_t reply;
  amqp_boolean_t  passive = 0;
  amqp_boolean_t  exclusive = 0;
  amqp_boolean_t  auto_delete = 0;
  struct sr_topic_t *t;
  amqp_basic_properties_t props;
  amqp_table_t table;
  amqp_table_entry_t table_entries[2];


  int tecnt = 0;

  props._flags = AMQP_BASIC_CONTENT_TYPE_FLAG ;
  props.content_type = amqp_cstring_bytes("text/plain");
  if ( sr_c->cfg->expire > 0 ) 
  {
      table_entries[tecnt].key = amqp_cstring_bytes("x-expiry");
      table_entries[tecnt].value.kind = AMQP_FIELD_KIND_I64;
      table_entries[tecnt].value.value.i64 = sr_c->cfg->expire ;
      tecnt++;
      props._flags |= AMQP_BASIC_EXPIRATION_FLAG ;
  } 
  
  if ( sr_c->cfg->message_ttl > 0 ) 
  {
      table_entries[tecnt].key = amqp_cstring_bytes("x-message-ttl");
      table_entries[tecnt].value.kind = AMQP_FIELD_KIND_I64;
      table_entries[tecnt].value.value.i64 = sr_c->cfg->message_ttl ;
      tecnt++;
      props._flags |= AMQP_BASIC_TIMESTAMP_FLAG ;
  } 
  table.num_entries = tecnt;
  table.entries = table_entries;
  
  props.delivery_mode = 2; /* persistent delivery mode */
  props.headers = table;



  msg.user_headers=NULL;

  //amqp_queue_declare_ok_t *r = 
  amqp_queue_declare( 
             sr_c->cfg->broker->conn, 
             1, 
             amqp_cstring_bytes(sr_c->cfg->queuename), 
             passive,
             sr_c->cfg->durable, 
             exclusive, 
             auto_delete, 
             table 
  );
  /* FIXME how to parse r for error? */

  reply = amqp_get_rpc_reply(sr_c->cfg->broker->conn);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
      sr_amqp_reply_print(reply, "queue declare failed");
      return(0);
  }

  /*
    FIXME: topic bindings are not working properly...
   */
  if ( ! sr_c->cfg->topics ) 
  {
      sr_add_topic(sr_c->cfg, "#" );
  }
  log_msg( LOG_DEBUG, "topics: %p, string=+%s+\n", sr_c->cfg->topics,  sr_c->cfg->topics  );

  for( t = sr_c->cfg->topics; t ; t=t->next )
  {
      log_msg( LOG_INFO, "queue %s bound with topic %s to %s\n",
              sr_c->cfg->queuename, t->topic, sr_broker_uri( sr_c->cfg->broker ) );
      amqp_queue_bind(sr_c->cfg->broker->conn, 1, 
            amqp_cstring_bytes(sr_c->cfg->queuename), 
            amqp_cstring_bytes(sr_c->cfg->broker->exchange), 
            amqp_cstring_bytes(t->topic),
            amqp_empty_table);

      reply = amqp_get_rpc_reply(sr_c->cfg->broker->conn);
      if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
          sr_amqp_reply_print(reply, "binding failed");
          return(0);
      }
  }
  return(1);
}

char *sr_message_partstr(struct sr_message_t *m)
{
   static char smallbuf[255];

   if (( m->sum[0] != 'R' ) && ( m->sum[0] != 'L' ))
       sprintf( smallbuf, "%c,%ld,%ld,%ld,%ld", m->parts_s, m->parts_blksz, m->parts_blkcount, m->parts_rem, m->parts_num );
    else
       memset( smallbuf, '\0', 255);

    return(smallbuf);
}

void assign_field( const char* key, char *value )
 /* Assign the value of the field given by key to the corresponding member
    of the static msg struct.
  */
{
     char *s;
     struct sr_header_t *h;

     //log_msg( LOG_DEBUG, "parsing: \"%s\" : \"%s\"\n", key, value );
     if ( !strcmp(key,"atime") ) {
         strcpy(msg.atime,value); 
     } else if ( !strcmp(key,"from_cluster") ) {
         strcpy(msg.from_cluster,value); 
     } else if ( !strcmp(key,"mode") ) {
         msg.mode=strtoul( value, NULL, 8);
     } else if ( !strcmp(key,"mtime") ) {
         strcpy(msg.mtime,value); 
     } else if ( !strcmp(key,"parts") ) {
         //FIXME: no error checking, invalid parts header will cause a bobo.
         msg.parts_s=value[0];
         s=strtok(&(value[2]),",");
         msg.parts_blksz = atol(s);
         s=strtok(NULL,",");
         msg.parts_blkcount = atol(s);
         s=strtok(NULL,",");
         msg.parts_rem = atol(s);
         s=strtok(NULL,",");
         msg.parts_num = atol(s);
     } else if ( !strcmp(key,"path") ) {
         strcpy(msg.path,value); 
     } else if ( !strcmp(key,"source") ) {
         strcpy(msg.source,value); 
     } else if ( !strcmp(key,"sum") ) {
         strcpy(msg.sum,value); 
     } else if ( !strcmp(key,"to_clusters") ) {
         strcpy(msg.to_clusters,value); 
     } else if ( !strcmp(key,"url") ) {
         strcpy(msg.url,value); 
     } else {
         h = (struct sr_header_t *)malloc( sizeof(struct sr_header_t) );
         h->key=strdup(key);
         h->value=strdup(value);
         h->next=msg.user_headers;
         msg.user_headers = h;
     }
}

void json_dump_strheader(char *tag, char*value)
{
    printf( "\"%s\": \"%s\"", tag, value );
}

char *sr_message_2log(struct sr_message_t *m)
{
     static char b[10240]; // FIXME!  need more than 10K for a log message? check?
     
     sprintf( b, "%s %s %s topic=%s", m->datestamp, m->url, m->path, m->routing_key );
     sprintf( strchr( b, '\0' ), " sum=%s source=%s", m->sum, m->source  );
     sprintf( strchr( b, '\0' ), " to_clusters=%s from_cluster=%s", m->to_clusters, m->from_cluster );


     if (( m->sum[0] != 'R' ) && ( m->sum[0] != 'L' ))
     {
        sprintf( strchr( b, '\0' ), " mtime=%s atime=%s", m->mtime, m->atime  );

        if (m->mode)
           sprintf( strchr( b, '\0' ), " mode=%04o", m->mode );

        sprintf(  strchr( b, '\0' ), " parts=%c,%ld,%ld,%ld,%ld", m->parts_s, m->parts_blksz, m->parts_blkcount, m->parts_rem, m->parts_num );
     }
     for( struct sr_header_t *h = msg.user_headers ; h ; h=h->next ) 
          sprintf( strchr( b, '\0' ), " %s=%s", h->key, h->value );
     return(b);
}


void sr_message_2json(struct sr_message_t *m)
{
     struct sr_header_t *h;

     printf( "[" );
     printf( " \"%s\", { ", m->routing_key );
     json_dump_strheader( "atime", m->atime );
     printf( ", " );
     printf( "\"mode\": \"%04o\"", m->mode );
     printf( ", " );
     json_dump_strheader( "mtime", m->mtime );
     printf( ", " );
     printf( "\"parts\": \"%c,%ld,%ld,%ld,%ld\"", 
           m->parts_s, m->parts_blksz, m->parts_blkcount, m->parts_rem, m->parts_num );
     printf( ", " );
     json_dump_strheader( "from_cluster", m->from_cluster );
     json_dump_strheader( "source", m->source );
     json_dump_strheader( "sum", m->sum );
     printf( ", " );
     json_dump_strheader( "to_clusters", m->to_clusters );

     for(  h=msg.user_headers; h ; h=h->next ) 
     {
          printf( ", " );
          json_dump_strheader( h->key, h->value );
     } 
     printf( " } \"%s %s  %s\"", m->datestamp, m->url, m->path );
     printf( "]\n" );
}

void sr_message_2url(struct sr_message_t *m)
{
     printf( "%s/%s\n", m->url, m->path );
}


struct sr_message_t *sr_consume(struct sr_context *sr_c) 
 /*
    read messages from the queue. dump to stdout in json format.

  */
{
    amqp_rpc_reply_t reply;
    amqp_frame_t frame;
    int result;
    char buf[2*PATH_MAXNUL];

    amqp_basic_deliver_t *d;
    amqp_basic_properties_t *p;
    int is_report;
    char *tok;
    size_t body_target;
    size_t body_received;
    char tag[AMQP_MAX_SS];
    char value[AMQP_MAX_SS];
    struct sr_header_t *tmph;

    while (msg.user_headers)
    {
        tmph=msg.user_headers;
        free(tmph->key);        
        free(tmph->value);        
        msg.user_headers=tmph->next;
        free(tmph);
    }

    amqp_basic_consume(sr_c->cfg->broker->conn, 1, 
          amqp_cstring_bytes(sr_c->cfg->queuename), 
          amqp_empty_bytes, // consumer_tag
          0,  // no_local
          1,  // ack
          0,  // not_exclusive
          amqp_empty_table);

    reply = amqp_get_rpc_reply(sr_c->cfg->broker->conn);
    if (reply.reply_type != AMQP_RESPONSE_NORMAL ) 
    {
        sr_amqp_reply_print(reply, "consume failed");
        return(NULL);
    }

    amqp_maybe_release_buffers(sr_c->cfg->broker->conn);
    result = amqp_simple_wait_frame(sr_c->cfg->broker->conn, &frame);

    //log_msg( LOG_DEBUG, "Result %d\n", result);
    if (result < 0) return(NULL);
  
    //log_msg( LOG_DEBUG, "Frame type %d, channel %d\n", frame.frame_type, frame.channel);

    if (frame.frame_type != AMQP_FRAME_METHOD) return(NULL);
  
    //log_msg( LOG_DEBUG, "Method %s\n", amqp_method_name(frame.payload.method.id));

    if (frame.payload.method.id != AMQP_BASIC_DELIVER_METHOD) return(NULL);
  
    d = (amqp_basic_deliver_t *) frame.payload.method.decoded;

    /*
    log_msg( stdout, " {\n\t\"exchange\": \"%.*s\",\n\t\"routingkey\": \"%.*s\",\n",
               (int) d->exchange.len, (char *) d->exchange.bytes,
               (int) d->routing_key.len, (char *) d->routing_key.bytes);
     */
  
    sprintf( msg.exchange, "%.*s",  (int) d->exchange.len, (char *) d->exchange.bytes );
    sprintf( msg.routing_key, "%.*s",  (int) d->routing_key.len, (char *) d->routing_key.bytes );

    is_report = ( ! strncmp( d->routing_key.bytes, "v02.report", 10 )  );
   
    result = amqp_simple_wait_frame(sr_c->cfg->broker->conn, &frame);

    if (result < 0) return(NULL);
  
    if (frame.frame_type != AMQP_FRAME_HEADER) 
    {
            log_msg( LOG_ERROR, "Expected header!");
            abort();
    }

    p = (amqp_basic_properties_t *) frame.payload.properties.decoded;

    for ( int i=0; i < p->headers.num_entries; i++ ) 
    {
            if ( p->headers.entries[i].value.kind == AMQP_FIELD_KIND_UTF8 )
            {
                sprintf( tag, "%.*s",  
                           (int) p->headers.entries[i].key.len, 
                        (char *) p->headers.entries[i].key.bytes );

                sprintf( value, "%.*s",  
                           (int) p->headers.entries[i].value.value.bytes.len, 
                        (char *) p->headers.entries[i].value.value.bytes.bytes );

                assign_field( tag, value );

              /*
                log_msg( stdout, "\t\"%.*s\": \"%.*s\",\n",
                     (int) p->headers.entries[i].key.len, 
                     (char *) p->headers.entries[i].key.bytes,
                     (int) p->headers.entries[i].value.value.bytes.len,
                     (char *) p->headers.entries[i].value.value.bytes.bytes
                 );
               */
            } else
                log_msg( LOG_ERROR, "header not UTF8\n");
    }

    body_target = frame.payload.properties.body_size;
    body_received = 0;
  
    while (body_received < body_target) 
    {
            result = amqp_simple_wait_frame(sr_c->cfg->broker->conn, &frame);

            if (result < 0) return(NULL);
    
            if (frame.frame_type != AMQP_FRAME_BODY) 
            {
                log_msg( LOG_ERROR, "Expected body!");
                abort();
            }
    
        body_received += frame.payload.body_fragment.len;
        //assert(body_received <= body_target);
    
        strncpy( buf, (char*) frame.payload.body_fragment.bytes, (int)frame.payload.body_fragment.len );
        buf[frame.payload.body_fragment.len]='\0';
        tok = strtok(buf," ");
        //fprintf( stdout, "\t\"datestamp\" : \"%s\",\n", tok);
        strcpy( msg.datestamp, tok );
        tok = strtok(NULL," ");
        //fprintf( stdout, "\t\"url\" : \"%s\", \n", tok);
        strcpy( msg.url, tok );
        tok = strtok(NULL," ");
        //fprintf( stdout, "\t\"path\" : \"%s\", \n", tok);
        strcpy( msg.path, tok );
        if (is_report) 
        {
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"statuscode\" : \"%s\", \n", tok);
                msg.statuscode = atoi( tok );
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"consumingurl\" : \"%s\", \n", tok);
                strcpy( msg.consumingurl, tok );
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"consuminguser\" : \"%s\", \n", tok);
                strcpy( msg.consuminguser, tok );
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"duration\" : \"%s\", \n", tok);
                msg.duration = atof( tok );
        } else {
            msg.statuscode=0;
            msg.consumingurl[0]='\0';
            msg.consuminguser[0]='\0';
            msg.duration=0.0;
       
        }
        //fprintf( stdout, " }\n");
    /*
    fprintf( stdout, "\t\"body\" : \"%.*s\"\n }\n",
                 (int) frame.payload.body_fragment.len, 
                 (char *)frame.payload.body_fragment.bytes 
            );
     */
    }
  
    if (body_received != body_target) return(NULL);
          /* Can only happen when amqp_simple_wait_frame returns <= 0 */
          /* We break here to close the connection */
    return(&msg);
}

