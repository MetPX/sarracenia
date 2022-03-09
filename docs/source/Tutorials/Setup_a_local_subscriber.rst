===============================
How to setup a Local Subscriber
===============================
This example goes over how to subscribe to the swob files from the Environment Canada Weather office.

.. contents:: Table of Contents:

::

  $ sudo apt install rabbitmq-server
  $ sudo rabbitmqctl list_users
    Listing users ...
    user    tags
    guest   [administrator]

  $ sudo rabbitmqctl add_user 'bob'
    Adding user "bob" ...
    Password: robert

  $ sudo rabbitmqctl list_vhosts
    Listing vhosts ...
    name
    /

Set user permissions for vhost for bob's configure:read:write::

  $ sudo rabbitmqctl set_permissions -p "/" "bob" ".*" ".*" ".*"
    Settting permissions for user "bob" in vhost "/" ...

  $ sudo rabbitmqctl set_user_tags bob management
    Setting tags for user "bob" to [management] ...

  $ sudo rabbitmq-plugins enable rabbitmq_management
  $ /etc/init.d/rabbitmq-server restart

For more on the different kinds of user tags, see `rabbitmq access and permissions. <https://www.rabbitmq.com/management.html#permissions>`_
Open http://localhost:15672/ in a web browser.
Log in with the username/password created above.
Click the ``Queues`` tab to monitor the progress from the broker's perspective.
Back in terminal::

  $ mkdir .config/sarra/subscribe
  $ vi .config/sarra/subscribe/test-subscribe.conf
    broker amqp://bob:robert@localhost/
    exchange xs_bob
    directory /tmp/sarra/output
    accept .*

Setup the bits that post changes to the exchange::

  $ mkdir .config/sarra/watch
  $ vi $_/test-watch.conf
    post_broker amqp://bob:robert@localhost/
    post_exchange xs_bob
    path /tmp/sarra/input/
    events modify,create
  
  $ mkdir -p /tmp/sarra/{in,out}put
  $ sr start
  $ sr_watch log test-watch

--> All reporting normal.::

  $ sr_subscribe log test-subscribe
    .
    .
    2020-08-20 16:29:26,111 [ERROR] standard queue name based on: 
      prefix=q_bob
      program_name=sr_subscribe
      exchange_split=False
      no=1

--> Note the line with **[ERROR]**, it was unable to find the queue.
this is because the queue needs to first be created by sr_watch and since we started the
subscriber and watch at the same time with '``sr start``' we ran into a small race condition.
This was soon after resolved as the sr_subscribe has a 1 second retry time.
This can be confirmed with the 'RabbitMQ Queues' page showing a ``q_bob.sr_subscribe.test_subscribe. ...`` queue in the list.::

  $ touch /tmp/sarra/input/testfile1.txt
  $ ls /tmp/sarra/input/
    testfile1.txt
  $ ls /tmp/sarra/output/
      testfile1.txt
  $ sr_subscribe log test-subscribe
    .
    .
    2020-08-20 16:29:26,078 [INFO] file_log downloaded to: /tmp/sarra/output/testfile1.txt

  $ sr_watch log test-watch
    2020-08-20 16:29:20,612 [INFO] post_log notice=20200820212920.611807823 file:/ /tmp/sarra/input/testfile1.txt headers={'to_clusters':'localhost', 'mtime':'20200820212920.0259232521', 'atime': '20200820212920.0259232521', 'mode': '644', 'parts': '1,0,1,0,0', 'sum':'d,d41d8cd98f00b204e9800998ecf8427e'}
    
  $ touch /tmp/sarra/input/testfile{2..9}.txt
  $ for i in {001..015}; do echo "file #$i" > file$i.txt; done
  $ watch -n 1 ls /tmp/sarra/output/

Now you can watch the files trickle into the output folder,
also watch the 'RabbitMQ Queues' page receive and process AMQP messages.
When all is completed you can shut down both the subscriber and watcher with::

  $ sr stop
    ...
  $ sr_subscribe cleanup test-subscribe
    ...

Now the queue has been deleted from RabbitMQ and all services have been stopped.