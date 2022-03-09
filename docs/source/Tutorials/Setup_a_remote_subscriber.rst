================================
How to setup a Remote Subscriber
================================
This example goes over how to subscribe to the swob files from the Environment Canada Weather office.

.. contents:: Table of Contents:

FIXME: v03 edit is broken.

Setup
~~~~~

Initialize the credentials storage in the `~/.config/sr3/credentials.conf` file::

  $ sr3 edit credentials.conf
    amqps://anonymous:anonymous@dd.weather.gc.ca

The format is a complete url on each line (`amqps://<user>:<password>@<target.url>`).
This credentials.conf file should be private (linux octal permissions: 0600).  
.conf files placed in the ``~/.config/sr3/subscribe_directory`` will be automatically found by ``sr_subscribe``, rather than giving the full path.

The *edit* command starts the user's configured editor on the file to be created, in the correct directory::

  $ sr3 edit subscribe/swob.conf
    broker amqps://anonymous@dd.weather.gc.ca
    subtopic observations.swob-ml.#
    directory /tmp/swob_downloads
    accept .*
  $ mkdir /tmp/swob_downloads
  $ sr3 status subscribe/swob
    2017-12-14 06:54:54,010 [INFO] sr_subscribe swob 01 is stopped

.. ERROR::
  
  Currrently edit is failing if there isn't a file in the expected location
  (it does in fact, not create a file)
  See issue `#251 <https://github.com/MetPX/sarracenia/issues/251>`_ for more info or to complain.
  In the interim instead use::

    $ mkdir -p .config/sarra/subscribe
    $ touch $_/swob.conf
    $ sr3 edit swob.conf


*broker* indicates where to connect to get the stream of notifications.
The term *broker* is taken from AMQP (http://www.amqp.org), the protocol used to transfer the notifications.
The notifications that will be received all have *topics* that correspond to their URL.

.. NOTE::

  Omitting ``directory`` from the config file will write the files in the present working directory.
  Given how quickly they arrive, be prepared to clean up.

Startup
~~~~~~~

Now start up the newly created subscriber::

  $ sr3 start swob
    2015-12-03 06:53:35,268 [INFO] user_config = 0 ../swob.conf
    2015-12-03 06:53:35,269 [INFO] instances 1 
    2015-12-03 06:53:35,270 [INFO] sr subscribe swob 0001 started

Activity can be monitored via log files in ``~/.cache/sarra/log/`` or with the *log* command::

  $ sr3 log swob
    
    2015-12-03 06:53:35,635 [INFO] Binding queue q_anonymous.sr_subscribe.swob.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
    2015-12-03 17:32:01,834 [INFO] user_config = 1 ../swob.conf
    2015-12-03 17:32:01,835 [INFO] sr_subscribe start
    2015-12-03 17:32:01,835 [INFO] sr_subscribe run
    2015-12-03 17:32:01,835 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
    2015-12-03 17:32:01,835 [INFO] AMQP  input :    exchange(xpublic) topic(v02.post.observations.swob-ml.#)
    2015-12-03 17:32:01,835 [INFO] AMQP  output:    exchange(xs_anonymous) topic(v02.report.#)
    
    2015-12-03 17:32:08,191 [INFO] Binding queue q_anonymous.sr_subscribe.swob.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/


``[Ctrl] + [C]`` to exit watching the logs.
The startup log appears normal, indicating the authentication information was accepted.
``sr_subscribe`` will get the notification and download the file into the present working directory
(unless otherwise specified in the configuration file).

----

A normal download looks like this::

  2015-12-03 17:32:15,031 [INFO] Received topic   v02.post.observations.swob-ml.20151203.CMED
  2015-12-03 17:32:15,031 [INFO] Received notice  20151203223214.699 http://dd2.weather.gc.ca/observations/swob-ml/20151203/CMED/2015-12-03-2200-CMED-AUTO-swob.xml
  2015-12-03 17:32:15,031 [INFO] Received headers {'filename': '2015-12-03-2200-CMED-AUTO-swob.xml', 'parts': '1,3738,1,0,0', 'sum': 'd,157a9e98406e38a8252eaadf68c0ed60', 'source': 'metpx', 'to_clusters': 'DD,DDI.CMC,DDI.ED M', 'from_cluster': 'DD'}
  2015-12-03 17:32:15,031 [INFO] downloading/copying into ./2015-12-03-2200-CMED-AUTO-swob.xml 

Giving all the information contained in the notification.
Here is a failure::

  2015-12-03 17:32:30,715 [INFO] Downloads: http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml  into ./2015-12-03-2200-CXFB-AUTO-swob.xml 0-6791
  2015-12-03 17:32:30,786 [ERROR] Download failed http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml
  2015-12-03 17:32:30,787 [ERROR] Server couldn't fulfill the request. Error code: 404, Not Found

This message is not always a failure as ``sr_subscribe`` retries a few times before giving up.
After a few minutes, here is what the download directory looks like::

  $ ls -al | tail
    -rw-rw-rw-  1 peter peter   7875 Dec  3 17:36 2015-12-03-2236-CL3D-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7868 Dec  3 17:37 2015-12-03-2236-CL3G-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7022 Dec  3 17:37 2015-12-03-2236-CTRY-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   6876 Dec  3 17:37 2015-12-03-2236-CYPY-AUTO-swob.xml
    -rw-rw-rw-  1 peter peter   6574 Dec  3 17:36 2015-12-03-2236-CYZP-AUTO-swob.xml
    -rw-rw-rw-  1 peter peter   7871 Dec  3 17:37 2015-12-03-2237-CL3D-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7873 Dec  3 17:37 2015-12-03-2237-CL3G-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7037 Dec  3 17:37 2015-12-03-2237-CTBF-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7022 Dec  3 17:37 2015-12-03-2237-CTRY-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter 122140 Dec  3 17:38 sr_subscribe_dd_swob_0001.log

Cleanup
~~~~~~~

To not download more files, stop the subscriber::
  
  $ sr_subscribe stop swob
    2015-12-03 17:32:22,219 [INFO] sr_subscribe swob 01 stopped

This however leaves the queue that ``sr_subscribe start`` setup on the broker active,
as to allow a failed subscriber to attempt reconnecting without loosing progress.
That is until the broker times out the queue and removes it.
To tell the broker that we are finished with the queue, tell the subscriber to cleanup::

  $ sr_subscribe cleanup swob
  2015-12-03 17:32:22,008 [INFO] sr_subscribe swob cleanup
  2015-12-03 17:32:22,008 [INFO] AMQP broker(dd.weatheer.gc.ca) user(anonymous) vhost()
  2015-12-03 17:32:22,008 [INFO] Using amqp module (AMQP 0-9-1)
  2015-12-03 17:32:22,008 [INFO] deleting queue q_anonymous.sr_subscribe.swob.21096474.62787751 (anonymous@dd.weather.gc.ca)

Best practice is to clear the queue when done as to lessen the load on the broker.