
Status: Pre-Draft

=========
Use Cases
=========

.. section-numbering::


Use Cases / Deployment Scenarios 
--------------------------------

propose some strawman problems with a variety of cluster configurations to address them.
explore strengths and weaknesses.

Questions to examine for each:

   Three layers of diagram for each case:   
		post/subscribe, transport (sftp/http), log

   1. Storage Distribution
       how is storage provisioned (1 per server, common, grouped?)
       where do the files (or blocks) reside?

   2. Server Software Distribution 
       where are brokers and http/sftp servers? (together? separate scopes? )

   3. Authentication Distribution
       does it make sense to share auth between amqp and sftp? (plan to do that for http.)
       note which credentials are used where.

   4. Naming/scopes?
       what is a good name for this use case/scope?

   5. Retention quota strategy?
       how long does one keep each file/block?  
       delete immediately after passing on?  for big stuff, this makes sense.
       if in user space, upto the user.

       where do quotas apply?
  
   6. bandwidth/scaling.
       what are the limits to bandwidth for this configuration?
       where will the choke points be.
       where is a reasonable place to insert bandwidth controls?

	



.. include:: uc001_3TiBTransfer.rst
.. include:: uc002_RockSolidop0hr.rst
.. include:: uc003_srStyle.rst
.. include:: uc004_pxpaz.rst
.. include:: uc005_Acqui1TiBfromInternet.rst
.. include:: uc006_LocalFileNotification.rst

========
Diagrams
========

The diagrams are meant to represent the network environment in which data transfers need to occur.
In General, there are many networks with firewalls that prevent direct connection from one end point
to another.  The organizations exchanging data have no trust relationship between one another, and
little technological co-operation.

This results in a a table with nine sections, reminiscent of a tic-tac-toe game, with three columns,
the side columns representing partner department networks, and the centre one representing science.gc.ca 
networks.  the three rows correspond to the the level of external access.  The top row is government
only, the middle row is extranet, where government and external collaborators work together, and the
final row is the home networks of those collaborators to which government has little or no access or
control.

The ->| sign shows traffic going from the left to the right, but not the other direction.
unidirectional flows which are staples for network zoning.



.. include:: uc010_EC2Science.rst
.. include:: uc011_Corp2NRCviaHPC.rst
.. include:: uc012_HPC2Internet+GOC+24x7.rst


