
==============
 SR_Log2Save 
==============

-----------------------------------------------
Convert _log Entries to .save Format for Reload
-----------------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_log2save**


DESCRIPTION
===========

In order to resend items to a given destination, one can recover the advertisement
for a given file given a standard log file entry for it.  *sr_log2save* reads log
files from standard input, and write them to standard output converted into the
save format usable by *sr_shovel* with *-restore_to_queue*.


EXAMPLE
-------

Example usage::
   cat ~/test/save.conf <<EOT
       
   broker amqp://tfeed@localhost/
   topic_prefix v02.post
   exchange xpublic
    
   post_rate_limit 5
   on_post post_rate_limit 
    
   post_broker amqp://tfeed@localhost/
    
   EOT
    
   sr_log2save <log/sr_sarra_download_0003.log >shovel/save/sr_shovel_save_0000.save
   sr_shovel -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 save.conf foreground


SEE ALSO
--------

`sr_shovel(8) <sr_shovel.8.html>`_ - copies messages between pumps.


