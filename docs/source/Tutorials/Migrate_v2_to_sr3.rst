Migrating from Sarracenia v2 to sr3
===================================

This document is intended to be a short tutorial to help a Sarracenia v2
user convert their configurations to sr3. It assumes the user is already
familiar with basic v2 usage, and does not cover more detailed topics,
such as plugins.

.. IMPORTANT::

   This tutorial assumes that you have already installed
   sr3. If not, use `these
   instructions <../Tutorials/Install.html>`_
   to install sr3 first.

.. NOTE::

   Both Sarracenia v2 and sr3 can run alongside each other on the same computer.

For further reading, see:

- `How2Guides/UPGRADING <../How2Guides/UPGRADING.html#v2-to-sr3>`_ - notes
  about major changes between v2 and sr3
- `Contribution/v03 <../Contribution/v03.html>`_ - in-depth documentation
  about sr3’s design and changes from v2
- `How2Guides/Plugins_v2ToSr3 <../How2Guides/Plugins_v2ToSr3.html>`_ - detailed instructions
  for developers who want to port their v2 plugins to sr3

Background Information
----------------------

New Command-Line Interface (CLI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sr3 has a new command-line interface that is documented in detail
`here <../Explanation/CommandLineGuide.html>`_.
The ``sr3`` command syntax is ``sr3 action component/config ...``, which
replaces the *component-specific* commands of v2 (e.g. ``sr_subscribe``
for the subscribe component).

.. HINT::

   A *component* is the general name for a *subscribe*, *sarra*,
   *watch*, *shovel*, etc.

For example:

+--------------------------------------------+----------------------------------------+
| v2 Command                                 | sr3 Equivalent Command                 |
+============================================+========================================+
| ``sr_subscribe start my_subscriber``       | ``sr3 start subscribe/my_subscriber``  |
+--------------------------------------------+----------------------------------------+
| ``sr_subscribe status my_subscriber``      | ``sr3 status subscribe/my_subscriber`` |
+--------------------------------------------+----------------------------------------+
| ``sr_watch restart my_files``              | ``sr3 restart watch/my_files``         |
+--------------------------------------------+----------------------------------------+
| ``sr status``                              | ``sr3 status``                         |
+--------------------------------------------+----------------------------------------+
| ``sr_subscribe start``                     | ``sr3 start subscribe/*``              |
+--------------------------------------------+----------------------------------------+

New Config and Cache Locations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sr3 also changes the location of logs and configurations:

======= =================== =================
Item    v2 Location         sr3 Location
======= =================== =================
Configs ``~/.config/sarra`` ``~/.config/sr3``
Cache   ``~/.cache/sarra``  ``~/.cache/sr3``
Logs    ``~/.cache/sarra``  ``~/.cache/sr3``
======= =================== =================

Migrating a v2 Configuration to sr3
-----------------------------------

sr3 slightly changes some of the keywords used in config files. Full
documentation for all the options that can be used in an sr3 config file
can be found
`here <../Reference/sr3_options.7.html>`_.

sr3 recognizes the v2 keywords, so a v2 config file should be usable in
sr3 without modification, but we recommend using the built-in converter
to “upgrade” your configs to sr3 syntax.

Pre-conversion Preparation
~~~~~~~~~~~~~~~~~~~~~~~~~~

credentials.conf and default.conf
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have modified v2’s credentials.conf
(``~/.config/sarra/credentials.conf``) or default.conf
(``~/.config/sarra/default.conf``), you should copy those files over to
sr3’s config directory:

.. code:: bash

   cp ~/.config/sarra/credentials.conf ~/.config/sr3/credentials.conf
   cp ~/.config/sarra/default.conf ~/.config/sarra/default.conf

.. IMPORTANT::

   If you are converting from v2 to sr3, it is very likely
   that the source you are subscribing to (e.g. the MSC Datamart) is
   still publishing messages in the v2 format. Prior to converting your
   configs, you should add ``topicPrefix v02.post`` to your sr3
   ``default.conf`` file.

   To do this, run:

   .. code:: bash

      echo 'topicPrefix v02.post' >> ~/.config/sr3/default.conf

Step-by-step Conversion
~~~~~~~~~~~~~~~~~~~~~~~

Here is a step by step example demonstrating how to convert a v2
subscriber to sr3 using the converter, and how to disable the v2 config
once it’s complete.

.. code:: bash

   # the comments in this section, denoted by # provide explanation

   # commands are shown in the lines with a prompt that ends with $, for example:
   #                prompt command
   #                     ↓ ↓
   #    sarra@my-server:~$ my_command

   # the output from commands is shown after the line with the prompt and command

.. code:: bash

   # sr status --> show the status of your v2 configs
   #   In the example below, it shows that we have
   #   one *subscribe* config running named "dd_amis"
   sarra@my-server:~$ sr status
   status:
   Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
   ---------  -----      -----  --- ------------------------------
   audit      running    OK       1
   cpost      stopped    OK       0
   cpump      stopped    OK       0
   poll       stopped    OK       0
   post       stopped    OK       0
   report     stopped    OK       0
   sarra      stopped    OK       0
   sender     stopped    OK       0
   shovel     stopped    OK       0
   subscribe  running    OK       1 dd_amis-i5/0
   watch      stopped    OK       0
   winnow     stopped    OK       0
         total running configs:   1 ( processes: 6 missing: 0 stray: 0 )


   # sr3 status --> show the status of your sr3 configs
   #   In the example below, we do not have any sr3 configs
   sarra@my-server:~$ sr3 status
   status:
   Component/Config     Processes                                         Rates
                        State   Run Retry  Que     Lag  Last    %rej  messages      Data
                        -----   --- -----  ---     ---  ----    ----  --------      ----
         Total Running Configs:   0/0 ( Processes: 0 missing: 0 stray: 0 )
                        Memory: uss:0Bytes rss:0Bytes vms:0Bytes
                      CPU Time: User:0.00s System:0.00s
              Pub/Sub Received: 0m/s (0B/s), Sent:  0m/s (0B/s) Queued: 0 Retry: 0, Mean lag: 0.00s
                 Data Received: 0f/s (0B/s), Sent: 0f/s (0B/s)


   #####################
   # Convert v2 to sr3 #
   #####################

   # sr3 convert component/config --> convert a v2 config to sr3
   #   We will convert our v2 subscriber named "dd_amis" to an sr3 subscriber, also named "dd_amis".
   #   This will convert any v2 syntax to sr3 and place the resulting config file in
   #   ~/.config/sr3/subscribe/dd_amis.conf.
   sarra@my-server:~$ sr3 convert subscribe/dd_amis
   v2_config: ['subscribe/dd_amis']
   2025-08-25 17:21:20,858 2241245 [INFO] sarracenia.sr convert1 wrote conversion from v2 subscribe/dd_amis to sr3


   # Now sr3 status shows that we have one sr3 config.
   # the state "new" indicates that the config has never been started before.
   sarra@my-server:~$ sr3 status
   status:
   Component/Config     Processes                                         Rates
                        State   Run Retry  Que     Lag  Last    %rej  messages      Data
                        -----   --- -----  ---     ---  ----    ----  --------      ----
   subscribe/dd_amis    new     0/0    -    -       -      -       -       -           -
         Total Running Configs:   0/1 ( Processes: 0 missing: 0 stray: 0 )
                        Memory: uss:0Bytes rss:0Bytes vms:0Bytes
                      CPU Time: User:0.00s System:0.00s
              Pub/Sub Received: 0m/s (0B/s), Sent:  0m/s (0B/s) Queued: 0 Retry: 0, Mean lag: 0.00s
                 Data Received: 0f/s (0B/s), Sent: 0f/s (0B/s)


   # sr3 start component/config --> start a config
   #   We will start our new subscriber. That the v2 subscriber will also continue
   #   running, so duplicate data may be received while both subscribers are active.
   #
   #   NOTE: The ERROR message stating that the subscription write failed can be ignored.
   #         It will be removed in a future version.
   sarra@my-server:~$ sr3 start subscribe/dd_amis
   2025-08-25 17:28:08,410 2242079 [ERROR] sarracenia.config.subscription write failed: /home/sarra/.cache/sr3/subscribe/dd_amis/subscriptions.json: [Errno 2] No such file or directory: '/home/sarra/.cache/sr3/subscribe/dd_amis/subscriptions.json'
   starting:.( 5 ) Done


   # Now sr3 status shows that the config is running, in idle state:
   # (see Note below/Command Line Guide document for information about sr3's states)
   sarra@my-server:~$ sr3 status
   status:
   Component/Config     Processes                                         Rates
                        State   Run Retry  Que     Lag  Last    %rej  messages      Data
                        -----   --- -----  ---     ---  ----    ----  --------      ----
   subscribe/dd_amis    idle    5/5    0    0    0.00s   n/a    0.0%     0m/s       0B/s
         Total Running Configs:   1/1 ( Processes: 5 missing: 0 stray: 0 )
                        Memory: uss:210.9MiB rss:288.9MiB vms:428.1MiB
                      CPU Time: User:2.34s System:0.18s
              Pub/Sub Received: 0m/s (0B/s), Sent:  0m/s (0B/s) Queued: 0 Retry: 0, Mean lag: 0.00s
                 Data Received: 0f/s (0B/s), Sent: 0f/s (0B/s)


   ################################
   # Stop & Disable v2 Subscriber #
   ################################

   # Now that sr3 has been started, you can stop, cleanup and disable your v2 subscriber:

   # sr_subscribe stop --> stop the v2 subscriber
   sarra@my-server:~$ sr_subscribe stop dd_amis
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 01 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 02 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 03 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 04 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 05 stopped


   # sr_subscribe cleanup --> cleanup files in ~/.cache/sarra and delete queue on the broker
   sarra@my-server:~$ sr_subscribe cleanup dd_amis
   2025-08-25 17:32:49,264 [INFO] sr_subscribe dd_amis cleanup
   2025-08-25 17:32:49,264 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
   2025-08-25 17:32:49,264 [INFO] Using amqp module (AMQP 0-9-1)
   2025-08-25 17:32:49,282 [INFO] deleting queue q_anonymous.sr_subscribe.dd_amis.00483673.20371363 (anonymous@dd.weather.gc.ca)


   # sr status now shows that the v2 subscriber is stopped
   sarra@my-server:~$ sr status
   status:
   Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
   ---------  -----      -----  --- ------------------------------
   audit      running    OK       1
   cpost      stopped    OK       0
   cpump      stopped    OK       0
   poll       stopped    OK       0
   post       stopped    OK       0
   report     stopped    OK       0
   sarra      stopped    OK       0
   sender     stopped    OK       0
   shovel     stopped    OK       0
   subscribe  stopped    OK       1 dd_amis
   watch      stopped    OK       0
   winnow     stopped    OK       0
         total running configs:   0 ( processes: 1 missing: 0 stray: 0 )


   # sr_subscribe disable --> prevent the v2 config from being started in the future
   #   disable renames the config file from ...conf to ...conf.off
   #   e.g. ~/.config/sarra/subscribe/dd_amis.conf becomes ~/.config/sarra/subscribe/dd_amis.conf.off
   sarra@my-server:~$ sr_subscribe disable dd_amis


   # sr status now shows that the v2 subscriber is removed/disabled
   sarra@my-server:~$ sr status
   status:
   Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
   ---------  -----      -----  --- ------------------------------
   audit      running    OK       1
   cpost      stopped    OK       0
   cpump      stopped    OK       0
   poll       stopped    OK       0
   post       stopped    OK       0
   report     stopped    OK       0
   sarra      stopped    OK       0
   sender     stopped    OK       0
   shovel     stopped    OK       0
   subscribe  stopped    OK       0
   watch      stopped    OK       0
   winnow     stopped    OK       0
         total running configs:   0 ( processes: 1 missing: 0 stray: 0 )

You should now have a working sr3 subscriber! You can repeat the process
above as many times as necessary to convert all your v2 configurations
to sr3.

The sr3 CLI also accepts *multiple component/config combinations at the
same time* and *wildcards*, so you can convert all your configs in one
command. For example:

- ``sr3 convert subscribe/my_config1 poll/test_poll``
- ``sr3 convert 'subscribe/*'``
- ``sr3 convert '*/*'``

.. NOTE::

   sr3's status command provides more detailed ``states`` than v2. For an explanation
   of each possible state, read the `Command Line Guide document <../Explanation/CommandLineGuide.html#status>`_.
