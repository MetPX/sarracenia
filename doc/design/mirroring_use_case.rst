

This is a first post on this topic giving background about the mirroring issue to explain the current status. In November 2016, ECCC asked for very large directory trees to be mirrored.  It was already known from the outset that these trees would be too large to deal with using ordinary tools. It has indeed been a nearly a year since we started on this effort. There are essentially three parts of the problem:
 
   -- obtain the list of files which are modified.
   -- copy them to the other cluster.
   -- aspirational deadline to deliver a mirrored file: five minutes.
 
The actual trees to mirror are the following:
 
as037@eccc1-ppp1:/home/sarr111/.config/sarra/poll$ grep directory *hall1*.conf
policy_hall1_admin.conf:directory /fs/site1/ops/eccc/cmod/prod/admin
policy_hall1_archive_dbase.conf:directory /fs/site1/ops/eccc/cmod/prod/archive.dbase
policy_hall1_cmop.conf:directory /fs/site1/ops/eccc/cmod/cmop/data/maestro/smco500
policy_hall1_daily_scores.conf:directory /fs/site1/ops/eccc/cmod/prod/daily_scores
policy_hall1_hubs.conf:directory /fs/site1/ops/eccc/cmod/prod/hubs
policy_hall1_products.conf:directory /fs/site1/ops/eccc/cmod/prod/products
policy_hall1_stats.conf:directory /fs/site1/ops/eccc/cmod/prod/stats
policy_hall1_version_control.conf:directory /fs/site1/ops/eccc/cmod/prod/version_control
policy_hall1_work_ops.conf:directory /fs/site1/ops/eccc/cmod/prod/work_ops
policy_hall1_work_par.conf:directory /fs/site1/ops/eccc/cmod/prod/work_par
pas037@eccc1-ppp1:/home/sarr111/.config/sarra/poll$ 
 
The most efficient way to copy these trees, as was stated at the outset, would be for all of the jobs writing files in the trees to explicitly announce the files to be copied.  This would involve users modifying their jobs to include invocation of sr_post (a command which queues up file transfers for third parties to perform.)  ECCC set the additional constraint that modification of user jobs was not feasible, so the method used to obtain the list of files to copy had to be implicit (done by the system without active user involvement.)
 
One could just scan at a higher level in order to scan a single parent directory, but the half-dozen sub-trees trees were picked in order to have smaller ones which worked more quickly, regardless of the method being used to obtain lists of new files.  What do we mean when we say these trees are too large? The largest of these trees is *hubs* ( /fs/site1/ops/eccc/cmod/prod/hubs. )  I ran rsync on the *hubs* directory, as just walking the tree once, without any file copying going on.  The walk of the tree, using rsync with checksumming disabled as an optimization, resulted in the log below:
 
pas037@eccc1-ppp1:~/test$ more tt_walk_hubs.log
nohup: ignoring input
rsync starting @ Sat Oct  7 14:56:52 GMT 2017
number of files examined is on the order of: rsync --dry-run --links -avi --size-only /fs/site1/ops/eccc/cmod/prod/hubs /fs/site2/ops/eccc
/cmod/prod/hubs |& wc -l
27182247
rsync end @ Sat Oct  7 20:06:31 GMT 2017
pas037@eccc1-ppp1:~/test$
 
A single pass took over five hours, to examine 27 million files. The maximum rate of running rsyncs, is thus on the order of once every six hours (to allow some time for copying) for this tree.   Note that any standard method of copying a directory tree requires traversing it, and that there is no reason to believe that any other tool such as find, dump, tar, tree, etc... would be significantly quicker than rsync. We need a faster method of knowing which files have been modified so that they can be copied.  
 
There is a standard Linux feature known as INOTIFY, which can trigger an event when a file is modified.  By setting an INOTIFY trigger on every directory in the tree, we can be notified of when any file is modified in the tree.  This was the initial approach taken.  It turns out (last January), that INOTIFY is indeed a Linux feature, in that the INOTIFY events only propagate across a single erver.   With a cluster file system like GPFS, one needs to run an INOTIFY monitor on every kernel where files are written.   So rather than running a single daemon, we were faced with running around several hundred daemons (one per physical node), each monitoring the same set of 10's of millions of files.  
 
An alternate approach is, instead of running the modification detection at the Linux level, use the file system itself, which is database driven, to indicate which files had been modified. This is the GPFS-policy, where a query is run against the file system database at as high a rhythm as can be sustained (around five to ten minutes per query.) combined with sr_poll.  
 
Over the winter, both of these methods were implemented. The Inotify based sr_watch was the fastest method (instantaneous), but the daemons were having stability and memory consumption problems, and they also took too long to startup ( requires an initial tree traversal.). While slower (taking longer to notice a file was modified), the GPFS policy had acceptable performance and was far more reliable than the parallel sr_watch method,and by the spring, with deployment expected for early July, needed to choose one to focus on. We chose the GPFS policy approach.
 
As the migration progressed, the file systems got more filled, and the GPFS-policy method got progressively slower.  Already in July, this was not an acceptable solution. At this point, the idea of intercepting jobs' file i/o calls with a shim library was introduced.  ECCC told SSC at the time, that having correct feeds, and having everything ready for transition was the priority, so the focus of efforts was in that direction until the migration was achieved in September.  In spite of being a lower priority over the summer, a C implementation of the sending portion of the sarra library was implemented along with a prototype shim library to call it.
 
It needs to be noted that while all of this work was progressing on the 'obtain the list of files to be copied' part of the problem, we were also working on the 'copy the files to the other side' part of the problem. Over the summer, results of performance tests and other considerations militated frequent changes in tactics.
 
Many different sources and destinations (ppp, nfs, and protocol nodes), as well many different methods ( rcp, scp, bbcp, sscp, cp, dd ) and were all trialled to different degrees at different times, and many different criteria were considered (such as: impact on nfs nodes, protocol nodes, other nodes,  speed, system load,)  The final configuration selected of using cp  is not the fastest transfer method available (bbcp was) but it was chosen because it spread the load out better and resulted in more stable NFS and protocol nodes.  It looks like the 'copy the files to the other side' part of the problem is stable, and the impact on system stability has been minimized.
 
SSC fully appreciates that the mirroring between sites is not currently working, and that unless it works extremely well, it simply isn't usable by the ECCC.  While the transition occurred at the beginning of September, there were several weeks of intense effort to ensure that feeds were functional.  This work continues today as new issues are uncovered on a declining frequency. Work on libcshim started up again in mid-September, and with excellent technical co-operation from ECCC, we have been learning details of dynamic linking and kernel calls on linux, which has made the implementation much more elaborate than initially expected.  However, we now believe we are close to a point where we should make more rapid progress.   
 
While we hope to get to the libcshim approach in the next few weeks or at most a few months, in the mean-time, there are problems with the GPFS-policy approach that are being worked on as well:
 

    lack of transmission of symbolic links.  The GPFS policy currently does not identify symbolic links which appear, only regular files.  Naturally, they are not copied.
    missing files:  Users have complained about missing files.

 
So there we have the status as of 2017/10/12.
 
