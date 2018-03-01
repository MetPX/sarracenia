
=============================
Re-thinking of Report Routing
=============================

A central concept of sarracenia is to provide reports on deliveries to data sources.
in releases prior to Prior to 2016/08, this was called sr_log.  To eliminate that confusion,
this was renamed to sr_report in 2016/08.  As part of initial deployment with a reasonable
volume of messages, a number of scaling issues were encountered:

Routing all messages through a single winnow component made it a bottleneck.  Scaling
of winnowing was achieved by adding the post_exchange_split, to allow multiple winnow
processes to share a given flow.   There are similar bottlenecks present in the report
management flow, which was not expected.  In practical situations, one needs to be able 
to have a tunable number of instances for the various report routing components.

Currently (2016/08) there are three report routing components:

sr_2xreport
 
  Reads reports from xs_subscriber exchanges and posts them to xreport exchange.
  in the event of a really popular user, such as xs_anonymous, it may be
  necessary to have multiple instances to support the report flow.
  There is no way to express that need in the current configuration.


sr_report2clusters.py

  subscribe to reports posted in xreport exchange and send them to other pumps
  as defined by report2clusters.conf, which defines a single instance per cluster.
  There is no way to express the need for > 1 instance between two clusters.


sr_report2source.py
  
  subscribe to reports posted in xreport exchange that are for sources which are local (xr_<user>)
  Have an instance per source that sends each one the reports destined for them.
  Again, the number of instances is fixed, and busy sources cannot be served by multiple instances.

All of the components have "oddball" configurations which are different from the other ones,
sr_sarra, sr_sender, sr_subscribe, and sr_shovel, which all have a consistent configuration grammr.

Options to get the configurability needed:

Add to each component grammars

  For each component, for each tunable parameter, add new configuration logic, instance, pre-fetch, 
  rate limiting, etc... if there are many setings, they all have to be duplicated.

Rethink the grammars for the oddball configurations.

  Perhaps start the grammars for configuration for the oddballs is just poorly thought out, 
  and we should start over.


Drop the components, use sr_shovel.

  When these components were conceived, sr_shovel did not exist.  sr_shovel can be configured
  to do what all the oddballs do.   Replacing the oddball components with configurations of 
  sr_shovel will increase the amount  configuration needed, but with less configuration formats to
  understand, it might be easier to understand and use.

  sr_audit is a component that reads the main configuration and is used to set up exchanges,
  but that functionality could easily be extended to create initial configurations to replace
  all the components above.



-------------
Use sr_shovel
-------------


Replacing 2xreport, for each 'subscriber', say 'Bob', create 'Bob2xreport' configuation.

sr_shovel::

  subtopic: v02.report.#
  exchange: xs_Bob.
  post_exchange: xreport.

This would be part of the user creation logic, when the user is a subscriber or source.


Replacing report2source...  for each 'source',  say 'Alice', create 'xreport2Alice'

sr_shovel::

  subtopic: v02.report.#
  check source == Alice
  exchange: xreport
  post_exchange:  xr_Alice

This would be part of the user creation logic, only when the user is a source.

Replacing report2cluster... for each cluster, say 'C', create xreport2C

In both the above cases, create shovel configuration files when they don't exist in ~/.config/sarra/shovel

For cluster routing, do we just do it manually?


sr_shovel::
  subtopic: v02.report.#
  check from_cluster == C
  exchange: xreport@local_cluster
  post_exchange:  xreport@destination_cluster














  

  
