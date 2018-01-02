===========================
 Case Study: HPC Mirroring 
===========================

--------------------------------------------------------------------------------------------
 Transparent User Controlled Real-Time Mirroring of 27 Million File Tree in a Supercomputer
--------------------------------------------------------------------------------------------

.. warning::
   This is a bit speculative at the time of this writing (2017/12) We expect to deploy over the winter
   and be completed in 2018/03. Given the volumes being copied the exact performance isn't easily measured.
   hope to improve this article to reflect the advancing solution.

.. contents::


Summary
=======

This project was over a year long as the entire problem space was explored with the help of a very patient
client, and the tools developed to implement the efficient solution eventually settled on. The client
as actually more of a partner, as the client had the large test cases available and ended up shouldering
the responsibility for all of us to understand whether the solution was working or not.  While there 
are many specificities of this implementation, the resulting tool relies on no specific features beyond a 
normal Linux file system to achieve a 60:1 speedup relative compared to rsync on real-time continuous 
mirroring a tree of over 20 million files. With the lessons learned and the tools now available, 
it should be straight-forward to apply this solution to other cases.


Case-Study:  HPC Mirroring Millions of Files in Real-Time 
=========================================================

In November 2016, Environment and Climate Change Canada's (ECCC) Meteorological Service of Canada (MSC), 
as part of a the High Performance Computing Replacement (HPCR) project asked for very large directory 
trees to be mirrored in real-time. It was known from the outset that these trees would be too large to 
deal with using ordinary tools. It is expected to take about 15 months to explore the issue and 
arrive at an effective operational deployment.

It should be noted that SSC worked throughout this period in close partnership with ECCC, and that this
deployment required the very active participation of very sophisticated users, to follow along with
the twists and turns and different avenues explored and implemented.

The Computing environment is Canada's national weather centre, whose primary applicaiton a "production" numerical 
weather prediction suite, where models run 7/24 hours/day running different simulations (models of the atmosphere, 
and sometimes waterways and ocean, and the land under the atmosphere) either ingesting current observations 
aka *assimilation*, mapping them to a grid *analysis*, and then walking the grid forward in 
time *prediction/prognostic*. The forecasts follow a precise schedule throughout the 24hour cycle, and 
delays have ripples, so considerable effort is expended to avoid interruptions and maintain that schedule.

 * *FIXME: insert system diagram here... show SC1,PPP1,SS1 <-> SC2,PPP2,SS2* 

There is a pair of clusters running these simulations, one normally mostly working on operations,
with the other as a *spare* (running research and development loads.)  When the primary fails,
the intent is to run operations on the other supercomputer, using a *spare* disk to which all the
live data has been mirrored. As there are (nearly) always runs in progress, the directories never 
stop being modified, and there is no maintenance period when one can catch up if one falls behind.
The site stores are clusters in their own right:

 * FIXME: someone else should have a diagram of this.
 * data movers connect via Infiniband to the disk units themselves.
 * meta data managers?
 * protocol and NFS nodes GPFS nodes that serve those outside the cluster, via NFS.

There are essentially three parts of the problem:
 
 * obtain the list of files which have been modified (recently.)
 * copy them to the other cluster.
 * aspirational deadline to deliver a mirrored file: five minutes.
 
The actual trees to mirror are the following::
 
 pas999@eccc1-ppp1:/home/sarr111/.config/sarra/poll$ grep directory *hall1*.conf
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
 pas999@eccc1-ppp1:/home/sarr111/.config/sarra/poll$ 
 
Initially, we knew the number of files was large, but we had no knowledge of the actual amounts involved.
Nor was that data even available until much later.

The most efficient way to copy these trees, as was stated at the outset, would be for all of the jobs 
writing files in the trees to explicitly announce the files to be copied. This would involve users 
modifying their jobs to include invocation of sr_post (a command which queues up file transfers for 
third parties to perform.) ECCC set the additional constraint that modification of user jobs was 
not feasible, so the method used to obtain the list of files to copy had to be implicit (done by the 
system without active user involvement.)
 
One could just scan at a higher level in order to scan a single parent directory, but the half-dozen 
sub-trees trees were picked in order to have smaller ones which worked more quickly, regardless of the 
method being used to obtain lists of new files. What do we mean when we say these trees are too large? 
The largest of these trees is *hubs* ( /fs/site1/ops/eccc/cmod/prod/hubs. ) rsync was run on the *hubs* 
directory, as just walking the tree once, without any file copying going on. The walk of the tree, using 
rsync with checksumming disabled as an optimization, resulted in the log below::
 
 pas999@eccc1-ppp1:~/test$ more tt_walk_hubs.log
 nohup: ignoring input
 rsync starting @ Sat Oct  7 14:56:52 GMT 2017
 number of files examined is on the order of: rsync --dry-run --links -avi --size-only /fs/site1/ops/eccc/cmod/prod/hubs /fs/site2/ops/eccc/cmod/prod/hubs |& wc -l
 27182247
 rsync end @ Sat Oct  7 20:06:31 GMT 2017
 pas999@eccc1-ppp1:~/test$
 
A single pass took over five hours, to examine 27 million files, or examining about 1500 files per second. 
The maximum rate of running rsyncs on this tree is thus on the order of once every six hours (to allow some 
time for copying) for this tree. Note that any usual method of copying a directory tree requires traversing 
it, and that there is no reason to believe that any other tool such as find, dump, tar, tree, etc... would 
be significantly quicker than rsync. We need a faster method of knowing which files have been modified 
so that they can be copied.  

There is a standard Linux feature known as INOTIFY, which can trigger an event when a file is modified. By setting an INOTIFY trigger on every directory in the tree, we can be notified of when any file is modified in the tree. This was the initial approach taken. It turns out (last January), that INOTIFY is indeed a Linux feature, in that the INOTIFY events only propagate across a single erver. With a cluster file system like GPFS, one needs to run an INOTIFY monitor on every kernel where files are written. So rather than running a single daemon, we were faced with running around several hundred daemons (one per physical node), each monitoring the same set of 10's of millions of files. Since the deamons were running on many nodes, the memory use rose into the terabyte range. 
 
An alternate approach is, instead of running the modification detection at the Linux level, use the file system itself, which is database driven, to indicate which files had been modified. The HPC solution's main storage system uses IBM's General Parallel File System, or GPFS.  Using the *GPFS-policy* method, a query is run against the file system database at as high a rhythm as can be sustained (around five to ten minutes per query.) combined with sr_poll to announce of files modified (and thus eligible for copying.)
 
Over the winter 2016/2017, both of these methods were implemented. The Inotify based sr_watch was the fastest method (instantaneous), but the daemons were having stability and memory consumption problems, and they also took too long to startup ( requires an initial tree traversal, which takes the same time as the rsync). While slower (taking longer to notice a file was modified), the GPFS policy had *acceptable* performance and was far more reliable than the parallel sr_watch method,and by the spring, with deployment expected for early July 2017, the GPFS policy approach was selected.
 
As the migration progressed, the file systems got more filled, and the GPFS-policy method got progressively slower. Already in July, this was not an acceptable solution. At this point, the idea of intercepting jobs' file i/o calls with a shim library was introduced. ECCC told SSC at the time, that having correct feeds, and having everything ready for transition was the priority, so the focus of efforts was in that direction until the migration was achieved in September. In spite of being a lower priority over the summer, a C implementation of the sending portion of the sarra library was implemented along with a prototype shim library to call it.
 
It needs to be noted that while all of this work was progressing on the 'obtain the list of files to be copied' part of the problem, we were 
also working on the 'copy the files to the other side' part of the problem. Over the summer, results of performance tests and other 
considerations militated frequent changes in tactics. Many different sources and destinations (ppp, nfs, and protocol nodes), as well many 
different methods ( rcp, scp, bbcp, sscp, cp, dd ) and were all trialled to different degrees at different times. At this point several 
strengths of sarracenia were evident:

* The separation of publishing from subscribing means that one can subscribe on the source node and push to the destination, or on the
  destination and pull from the source. It is easy to adapt for either approach. (ended up on destination protocol nodes, pulling from the source 
* The separation of copying from the computational jobs means that the models run times are unaffected, as the i/o jobs are completely separate.
* The ability to scale the number of workers to the performance needed.  (Eventually settled on 40 workers performing copies in parallel.)
* The availability of plugins *download_cp*, *download_rcp*, *download_dd*, allow many different copy programs (and hence protocols) to be easily
  applied to the transfer problem.

Many different criteria were considered (such as: load on nfs/protocol nodes, other nodes, transfer speed, load on PPP nodes,) The final configuration 
selected of using *cp* (via the *download_cp* plugin) is not the fastest transfer method tested (*bbcp* was faster) but it was chosen because it 
spread the load out better and resulted in more stable NFS and protocol nodes. The 'copy the files to the other side' part of the problem was 
stable by the end of the summer of 2017, and the impact on system stability has been minimized.
 
Unfortunately, the mirroring between sites was not working. It was, in principle working with about a 10 minutes lag on the source files 
system ( or about 30 times faster than an a naive rsync approach. ), but because the file selection part was only working in principle, with 
many files missing in practice, it wasn't usable for it's intended purpose. The operational commissioning of the new solution (with mirroring 
deferred.) occurred in September of 2017, and work on mirroring essentially stopped until October (because of activities related to 
the commissioning work.)

We continued work on two approaches, the libcshim, and the GPFS-policy. The queries run by the GPFS-policy had to to be tuned, eventually an overlap
of 75 seconds (where a succeeding query would ask for file modifications up to a point 75 seconds before the last one ended.) because there were 
issues with files being missing in the copies. Even with this level of overlap, there were still missing files. At this point, in late
November, early December, the libcshim was working well enough to be so encouraging that folks lost interest in the GPFS policy.  In contrast
to an average of about 10 minutes delay starting a file copy with GPFS-policy queries, the libcshim approach has the copy initiated as soon
as the file is closed on the source file system.

It should be noted that when the work began, the python implementation of Sarracenia was a data distribution tool, with no support for mirroring.
as the year progressed features:  symbolic link support, file attribute transportation, file removal support were added to the initial package.
The idea of periodic processing (called heartbeats) was added, first to detect failures of clients (by seeing idle logs) but later to initiate
garbage collection for the duplicates cache, memory use policing, and complex error recovery. The use case precipitated many improvements in
the application, including a second implementation in C for environments where the requisit python3 environment was difficult to establish, or
where efficiency was paramount (the libc-shim case.)

The question naturally arose, if the directory tree cannot be traversed, how do we know that the source and destination trees are the same?
A program to pick random files on the source tree is used to feed an sr_poll, which then adjusts the path to compare it to the same file
on the destination.  Over a large number of samples, we get a quantification of how accurate the copy is.  The plugin for this comparison
is still in development.

* FIXME: include links to plugins

In December 2017, the software for the libcshim approach looks ready, it is deployed in some small parallel (non-operational runs.) It is
expected that in January 2018, more parallel runs will be tried, and it should proceed to operations this winter. It is expected that the
delay in files appearing on the second file system will be on the order of five minutes after they are written on the source tree, 
or 60 times faster than rsync.

