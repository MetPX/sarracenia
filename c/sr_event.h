
typedef unsigned char sr_event_t;

#define SR_CREATE ((sr_event_t)(0x01))
#define SR_MODIFY ((sr_event_t)(0x02))
#define SR_LINK   ((sr_event_t)(0x04))
#define SR_DELETE ((sr_event_t)(0x08))


sr_event_t parse_events( char * );
