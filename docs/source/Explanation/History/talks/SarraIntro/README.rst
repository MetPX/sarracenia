
HUGE CAVEAT... BEFORE YOU TRY EDITING THE IMAGE IN DIA...

dia stores absolute paths for images that are included in the file,
so if someone git clones your repo, the .dia file won't work for them.

As soon as you make any save of the file in dia, before you commit the work
for others to use, you need to do something like::

     cp A2B.dia A2B.gz
     gunzip A2B.gz

The file A2B is now XML, which can be (painfully) edited.
In the editor, you need to remove all the references to the directory
leaving only reltive paths for include::

    vi A2B
    # :%s+`cwd`++
    # :wq
    gzip A2B
    mv A2B.gz A2B.dia

This replaces the old .dia file, might be upsetting...

Then we run awk in the Makefile to produce a .rst file for sphinx.

then when sphinx runs, it puts the paths back in
