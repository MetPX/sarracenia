
sr_watch
   need to watch for writes without file close

  sample usage:
      -- logs (always appending)
      -- sequencer output (appending to a large file.)

  so need to treat IN_MODIFY event.  how?

  want to group writes, 
   - keep track of previous write
   - if contiguous, then group together as one bigger write.
   	- if reached part boundary, then 
              emit part update post
              note end of last part as beginning of last write.
 
        - 
     else (not contiguous)
        - i dunno ?! wrong use case.
        - trigger send part containing contiguous write, if pending?
        - mark part dirty?
        - complain? 
	- skip until file close?
        - very poorly suited for this mechanism.
	- ie. db record updates...

  on_close
    - trigger send part containing contiguous write, if pending?

    - write dirty parts. ... ugh... lot to track..
       - does it need to do this anyways?
    or:
       - just re-post everything on close? no tracking.
       - if sums the same, first stop will filter.


 when sr_watch starts, does it post everything in the initial tree?


