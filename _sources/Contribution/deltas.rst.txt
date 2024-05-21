
Status: Pre-Draft


==============================================
 Discussion of File Modification Propagation
==============================================

This was early thinking about how to deal with file updates.
The early versions of the protocol only concerned itself with entire files.
when the file sets are large enough, partial updates become very desirable.
Also, when the size of individual files is large enough, and when traversing
WAN links, one can obtain substantial practical advantage by sending sending
data using multiple streams, rather than just one.

So in v02 there is a header 'parts' which indicates the partitioning method
used for a given transfer, and the conclusion about the format/protocol
is now documented in the sr_post(7) man page.  This file contains early
discussions & notes.

Algorithm used (regardless of tool):
	- for each ´block´ (blocksize interesting) generate a signature.
	- when a subscriber reads an notification message, it includes the signature.
	- he compares the signatures on the file he already has, and updates it to match.

the zsync algorithm is the right idea, can perhaps use it directly.


What If Each Notification is for a Block, not a File ?
------------------------------------------------------

gedanken experiment... per block messages, rather than entire files ?
what if the messages we send are all per block?

Why is this really cool?  

 - It does the gridftp thing, splitting out single file transfers 
   into parallel streams.

 - For large files, the ddsr's might have a whole bunch of part files, 
   instead of the complete ones, because the transfer is split over
   multiple nodes, no problem, as long as later stages are subscribed 
   to all ddsr's.

 - intervening switches do not need to store the largest file
   that can be transferred, only some number of the largest chunks.
   eliminates the maximum file size problem. 

 - This also deals with files that are written over time, without waiting
   until they are complete before hitting send.

 - for the client to do multi-threaded send, they just start up
   any number of sr_senders listening to their own input exchange.
   sharing the subscription, just like sr_subscribe (dd_subscribe) does.

 - for large files, you can see progress reports sources receive
   confirmation of each switching layer receiving each chunk.

say we set a blocksize of 10MB, and we checksum that block, noting the offset, then
continue?

so v01.post:
blocksz sz-inblocks remainder blocknum flags chksum base-url relative-path flow ....

see logging.txt for a description of 'flow', user settable, with a default.

flags says whether the chksum is for the name or the body. (if checksum is for name,
then cannot use blocking chksums.) ... says name checksums should only be used for smallish files.

The blocksz establishes the multiplier for the sz and the blocknum.  the remainder
is the last bit of the file after the last block boundary.

So you calculating the checksum for each block you send off a message with the block, 

this way, for large files, the transfer can be split over a large number of nodes.
but then re-assembly is a bit of a puzzle.  will each node of ddsr have only
fractional (aka sparse) large files?   as long as the sr_sub is to both ddsr's, it should
get everything.   what happens with sparse  files?

https://administratosphere.wordpress.com/2008/05/23/sparse-files-what-why-and-how/

that´s it's OK...
it would work, on linux, but it's a bit strange, and would like cause confusion in
practice.  Besides, how do we know when we are done?

--- Re-assembly ---
How about the following.  when sr_subscribe(dd_subscribe) writes files, it writes to a file
suffixed .sr§1 when it receives a file, and there is a .sr§ it checks the size
of the file, if the current part is contiguous, it just appends (via lseek & write) 
the data to the .sr§ file.  If not, it creates a separate .sr§<blocknum>

.sr§ suffix 
-----------

but that means they advertise the parts... hmm... the names now mean something, 
We use the Section Character instead of part.  to avoid that, pick a name that 
is more unusual that .part something like .sr§partnum (using utf-8 interesting 
to see what url-encoding will do to that.)  It is good to use UTF special 
characters, because no-one else uses them, so unlikely to clash.

what is someone advertises a .sr§ file? what does it mean? do we need to
detect it?
 
Then it looks in the directory to see if a .sr§<blocknum +1> exists, and appends
it if it does, and loops until all contiguous parts are appended (the corresponding
files deleted.)  

NOTE: Do not use append writing .sr§, but always lseek and write.  This prevents 
race conditions from causing havoc.  If there are multiple sr_subscribe (dd_subscribes) writing 
the file they will just both write the same data multiple times (worst case.)

anyways when you run out of contiguous parts, you stop.

if the last contiguous block received includes the end of the file, then
do the file completion logic.

How to Select Chunksize
-----------------------

	- source choice?
	- we impose our own on ddsr?
	
a default to 10*1024*1024=10485760 bytes, with override possible.

might want the validation part to impose a minimum chunksize
on posted files, in addition to the file path.

we set a minimum, say 10MB, then if that is less than 5% of the file,
then use 5%, until we get to a maximum chunksize... say 500MB.
override with size 0 (no chunking one long send.)

what is the overhead to send a block?
  - there are no fixed width fields in the messages, are all variable length ASCII.
  - estimate that an avereage notification is 100 bytes,
  - log message is perhaps 120 bytes.

for each block transferred.
	notification goes in one direction, 
	at least one log message per scope hope goes through in the other direction.

	if we say two hops + client delivery (a third hop)	

	so a block will have on the order of 100+4*120 = 580 bytes.

It accepted that there is substantial protocol overhead on small files.

However, one would hope the overhead would get more reasonable for bigger files,
but that is limited by the blocksize.  
Aesthetically, need to choose a size that dwarfs the overhead.



if we do blockwise cksums, path from v00 
----------------------------------------

compatibility... upgrading...
v00.notify alerts boil down to:

v01.post could be:

   filesz 1 0 0  ...
	- the blocksize is the length of the entire file, 1 block ithe sz
	- no remainder.
	- 0th block (the first one, zero origin counting)

or we take the convention that a blocksize of zero means no blocking...
in which chase it would be:

   0 1 filesz 0 ... 
	- store the sz as the remainder.
	- disable blocking for that file.

if there is validation on the blocking size, needs to be a way to deal with it.


Digression about ZSync 
----------------------

zsync is available in repositories  and zsync(1) is the existing download client.  
zsyncmake(1) builds the signatures, with a programmable block size. 

It looks ike zsync is usable as is?

downside:  portability.
    need zsync on Windows and mac for downloads, dependency a pain.
	there is a Windows binary, made once in 2011... hmm...
	have not seein it on Mac OS either... sigh...

we send the signatures in the notification messages, rather than posting on the site.
If we set the blocksize high, then for files < 1 block, there is no signature.

should sr_sarra post the signature to the site, for zsync compatibility? 

Do not want to be forking zsyncmake for every product...
even if we do not use zsync itself, might want to be compatible... so use
a third party format and have a comparable.  1st implementation would do
forking, 2nd version might replicate the algorithm internally.

perhaps we have a threshold, if the file is less than a megabyte, we just send
the new one.  The intent is not to replicate source trees, but large data sets.  

	- for most cases (when writing a new file) we do not want extra overhead.
	- target is large files that change, for small ones, transfer again, is not a big deal.
	- want to minimize signature size (as will travel with notifications.)
	- so set a block size to really large.

Perhaps build the zsync client into sr_subscribe (dd_subscribe), but use zsync make on the server side ?
or when the file is big enough, forking a zsync is no big deal? but mac & win...


Server/Protocol Considerations
------------------------------

HTTP:
	-- uses byte range feature of HTTP.
	-- FIXME: find samples from other email.


in SFTP/python/paramiko...
	-- there is readv( ... ) which allows to read subsets of a file.
	-- the read command in SFTP PROTOCOL spec has offset as a standard argument of read
	
