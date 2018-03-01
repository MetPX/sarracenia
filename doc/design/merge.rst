
================
 Source Merging
================

A Merged source is a source produced from other sources.

A feature to collapse multiple sources into a single source for downstream purposes.
Is this of any use? Examples:

AirNow
   airnow-qc,sk,bc,on....

on the acquisition switch, you want individual circuits so that you know when a given source is down, and it doesn't affect others.

but on the disseamination-side, you probably just want one 'source' for all the data.    

propose an option in sarra:

merge airnow airnow-bc airnow-sk airnow-on airnow-qc

the first argument to merge is the 'destination'... the others are the 'sources' to be merged.

when sarra sees data from the 'airnow-sk' source, it get gets re-mapped:

20160202/airnow-sk --> 20160202/airnow/airnow-sk

for re-publish:
  from_cluster=the cluster doing the merge.
  source=airnow



Question 1: what happens to log messages?

option 1a:  we don't care.
  it's an artificial source, we just provide authentication to someone who cares.
  so log flows break at this point (or you need to track the two sources separately.)


option 1b:  we split the log messages

so when the log message gets routed to the from_cluster with a merged source as the source,
we look at the second directory, and re-write the source as that...
but no way to guess the original from_cluster... 
  

So far, I'm voting for 1b.





