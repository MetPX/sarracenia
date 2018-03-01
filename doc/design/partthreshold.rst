=======================
 Paritioning Threshold
=======================

Deciding when to split a file into multiple chunks.

compare fsize
  < 50 mb -> 1
  > 50 mb -> divide by 3.
  > 500   -> divide by 10
  > 5g    -> 500mb.

rephrased... 

Say threshold setting is t.

  if sz > 100*t : 
    bs=10*t
  elif sz > 10*t : 
    bs=fs/10
  elif sz > t : 
    bs=fs/3
  else:
    bs=fs
  fi
 
and we just have a t setting, = 50 by default but people can change it.

t=0 disables partitioning.

This will produce files of varying sizes.  I think that for anti-virus and such,
less predictable partitioning makes it harder to craft malware.


------------

We might make it harder for malware people by having t be in a range, rather than
a fixed value, selected at random... t= something between 35 and 80 mb ...

but the client picks the partition... malicious client could pick it just so.. but
they would have to know quite a bit. hmm...

