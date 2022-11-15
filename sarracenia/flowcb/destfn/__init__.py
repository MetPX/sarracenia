"""
   Task: look at the fields in the message, and perhaps settings and
         return a new file name for the target of the send or download.

kind of a last resort function, exists mostly for sundew compatibility.
can be used for selective renaming using accept clauses.

The flowcb modules here are for compatiblity with sundew "filename" options.
a module that is focused on changing the names of files being sent or downloaded
is called a Destination File Name script ... or DESTFNSCRIPT 

These are floscb modules that are focused on the destfn entry point.

def destfn( self, msg ):

It's only argument is msg, the message containing the fields to modify.


destfn plugin script is used by senders or subscribers to do complex file naming.
one can invoke a destfn using the *filename* option in a configuration::

     filename DESTFNSCRIPT=sarracenia.flowcb.destfn.sample.Sample

An alternative method of invocation is to apply it selectively in an *accept* line::

     accept k* DESTFNSCRIPT=destfn.sample

As with other flowcb plugins, the import will be done using normal
python import mechanism equivalent to:

     import sarracenia.flowcb.destfn.sample

The destfn routine consults the fields in the given message, and based on them,
return a new file name for the file to have after transfer (download or send.)

the routines have access to the settings via options provided to init,
accessed, by convention, as self.o.

The routine can also modify fields create new ones in the message.

the destfn routine returns the new name of the file.

"""

pass
