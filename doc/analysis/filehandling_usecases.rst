============================
Post File handling Scenarios
============================

.. section-numbering::

This document formalize the behavior expected for Sarracenia file handling from/with posts

**WARNING This document is not formal, it is a work in progress only in an effort to better analyse Sarracenia requirements**

Name after posts scenarios
--------------------------

#. Old exists, but file path changed -> old file will be move
#. Old exists, but mismatch -> download new file, unlink old file
#. Old doesn't exists -> download new file
#. New file path is rejected -> Unlink old file (if it exists)

Name before posts scenarios
---------------------------

#. New accepted, content OK -> defer to #1.
#. Old exists, but mismatch -> defer to #2.
#. Old doesn't exists -> download name before file (or defer to #3. ??)
#. New file path is rejected -> Unlink name before file (if it exists)

