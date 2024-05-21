==================
Message v01 Format
==================

Status: Approved-Draft1-20150805

Description of the message protocol / format.

This file documents final conclusions/proposals, reasoning/debates goes elsewhere.

Messages posted include a ´topic´ and a ´body.´

The message topic breaks down as follows::

	<version>.<type>.[varies by version].<dir>.<dir>.<dir>...

	<version>:
		exp -- initial version, deprecated (not covered in this document)
		v00 -- used for NURP & PAN-AM in 2013-2014. (not covered in this document)
		v01 -- 2015 version.

	<type>:
		adm  - change settings 
			´admin´, ´config´, etc...

		log  - report status of operations.

		notify - ´post´ but in exp and v00 versions. (not covered here.)

		post - announce or notify that a new product block is available.
	       		possible strings: post,ann(ounce), not(ify)
		
	<source>:

Rest of this document assumes version 1 (v01 topic):

topic: <version>.<type>.<src>(.<dir>.)*.<filename>
content: 1st line:
<date stamp> <blocksize in bytes> <filesize in blocks> <block#> <remainder> <flags> <md5sum> <flowid> <srcpath> <relpath>

breaks down to::

  <date stamp>: date
	YYYYMMDDHHMMSS.<decimal> 

  <blocksize in bytes>: bsz
        the number of bytes in a block.
	checksums are calculated per block, so one post 

  <filesize in blocks>: fzb
	the integer total number of blocks in the file
	FIXME: (including the last block or not?)
	if set to 1.
	
  <block#>: bno
  	0 origin, the block number covered by this posting.

  <remainder>: brem
	normally 0, on the last block, it remaining blocks in the file 
        to transfer.

	-- if (fzb=1 and brem=0) 
	       then bsz=fsz in bytes in bytes. 
	       -- entire files replaced.
	       -- this is the same as rsync's --whole-file mode.

  <flags>:a comma-separated list of option letters, some with arguments after ´=´.

	checksum setting contained in ´flags´ field, but is not the whole 
	thing.  Other letters/digits could be there to designate other things.
	´=´ acts as a separator of flags from arguments.  

        results in ´flags´ entry:

        0 - no checksums (unconditional copy.)
        d - checksum the entire data
        n - checksum the file name
        c=<script> - checksum with a script, named <script>

		<script> should be ´registered´ in the switch network.
       			registered means that all downstream subscribers 
			can obtain the script to validate the checksum. 
			there needs to be a retrieval mechanism.

	other possible flag values:

		u - unlinked... for files that have been removed? 'r'?

        File Segment strategy:        
		i - inplace (do not create temporary files, just lseek
			within file.)
		    may result in .ddsig file being created?
		p - part files.  use .part files,  suffix fixed.
		    do not know which will be default.
	   - file segment strategy can be overridden by client. just a suggestion.
	   - analogous to rsync options: --inplace, --partial, 

  <flowid>
	an arbitrary tag used for tracking of data through the network.

  The two paths are subtly inter-related.  Neither can be interpreted on their own.  
  One must consider both path components.
  ------

	what if there are spaces in the file name?
	it is url-encoded, so a space should turn into: %20

  ------


  <srcpath> -- the base URL used to retrieve the data.

	options: Complete URL:

	sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_000.gif

	in the case where the URL does not end with a path separator ('/'), 
        the src path is taken to be the complete source of the file to retrieve.


	Static URL:

	sftp://afsiext@cmcdataserver/  

	If the URL ends with a path separator ('/'), then the src URL is 
        considered a prefix for the variable part of the retrieval URL.


  <relpath> -- The relative path from the current directory in which to 
  	place the file.
	
	Two cases based on the end being a path separator or not.

	case 1: NURP/GIF/	

	based on the current working directory of the downloading client, 
	create a subdirectory called URP, and within that, a subdirectory 
	called GIF will be created.  The file name will be taken from the 
	srcpath.

	if the srcpath ends in pathsep, then the relpath here will be 
	concatenated to the srcpath, forming the complete retrieval URL.

	case 2: NRP/GIF/mine.gif

	if the  srcpath ends in pathsep, then the relpath will be concatenated 
	to srcpath for form the complete retrieval URL.

	if the src path does not end in pathsep, then the src URL is taken 
	as complete, and the file is renamed on download according to the 
	specification (in this case, mine.gif)

	


FIXME: verify the following:
	fsz = Size of a file in bytes = ( bsz * (fsb-1) ) + brem ?


example 1::

  v01.post.ec_cmc.NRDPS.GIF.NRDPS_HiRes_000.gif
  201506011357.345 457 1 0 0 d <md5sum> exp13 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif NRDPS/GIF/ 

	v01 - version of protocol
	post - indicates the type of message 

	version and type together determine format of following topics and the message body.

	ec_cmc - the account used to issue the post (unique in a network).
  
	  -- blocksize is 457  (== file size)
	  -- block count is 1
	  -- remainder is 0.
	  -- block number is 0.
	  -- d - checksum was calculated on the body.
	  -- flow is an argument after the relative path.
	  -- complete source URL specified (does not end in '/')
	  -- relative path specified for 

	pull from: 
		sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif

	complete relative download path:
		NRDPS/GIF/NRDPS_HiRes_000.gif

		-- takes file name from srcpath.
		-- may be modified by validation process.


example 2::

  v01.post.ec_cmc.NRDPS.GIF.NRDPS_HiRes_000.gif
  201506011357.345 457 1 0 0 d <md5sum> exp13 http://afsiext@cmcdataserver/data/  NRDPS/GIF/NRDPS_HiRes_000.gif

  in this case, the
	pull from: 
		http://afsiext@cmcdataserver/data/NRPDS/GIF/NRDPS_HiRes_000.gif

		-- srcpath ends in '/', so concatenated, takes file from relative URL.
		-- true 'mirror'


	complete relative download path:
		NRDPS/GIF/NRDPS_HiRes_000.gif

		-- may be modified by validation process.


Log messages
------------


Log message contains:

is only emitted after processing is completed, to indicate a final status.

topic matches notification message message except...

v01.log.<source>.<consumer>...... 

version is protocol version, should increment in sync with notify.

start is as per post... just add fields after:

	<date> blksz blckcnt remainder blocknum flags <flow> baseurl relativeurl <status> <host> <client> <duration> 


CFG messages
------------

just a place holder.

really not baked yet. thinking is in configuration.txt

v01.cfg  
