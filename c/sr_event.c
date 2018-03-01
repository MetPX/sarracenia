
#include <string.h>

#include "sr_event.h"



void str2event( char *evstr, sr_event_t *evbm )
{
  if (!strcmp(evstr,"modify")) (*evbm) |= SR_MODIFY;
  if (!strcmp(evstr,"link"))   (*evbm) |= SR_LINK;
  if (!strcmp(evstr,"delete")) (*evbm) |= SR_DELETE;
  if (!strcmp(evstr,"create")) (*evbm) |= SR_CREATE;
  if (!strcmp(evstr,"read")) (*evbm) |= SR_READ;
}

sr_event_t parse_events( char *el )
{
  char *es;
  sr_event_t e;
  
  e=0;
  es = strtok( el, "," );
  while ( es ) 
  {
     str2event( es, &e );
     es = strtok( NULL, "," );
  }
  return(e);
}


