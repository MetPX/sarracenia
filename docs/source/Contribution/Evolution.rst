
Design Changes since Original (2015)
====================================

as of 2022/03, the design has not changed much, but sr3's implementation
is totally different from v2. Design changes:

* explicit core application support for reports were ripped out 
  as they were never used, can easily be re-inserted as callbacks
  and conventions.
* nobody used segmented files, and they were very complicated,
  but everyone finds them fantastic in theory. Need to re-implement
  post sr3 re-factor.  
* mirroring was a use case we had to address, changing some
  so added more metadata.
* the cluster routing concepts have been removed (cluster_from, cluster_to, etc...)
  it got in the analysts' way more than it helped. Dead easy to 
  implement using flow callbacks, if we ever want them back.
* the `Flow algorithm <../Explanation/Concepts.html#the-flow-algorithm>`_
  emerged as a unifying concept for all the different components
  originally envisaged. In early work on v2, we didn't know if
  all the components would work the same, so they were written
  separately from scratch. A lot of copy/paste code among
  entry points.
