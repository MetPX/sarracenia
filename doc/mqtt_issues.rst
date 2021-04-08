

=========================
MQTT Implementation Notes
=========================



v3 vs. v5
---------

* version 3 has resends sent on a timed basis, every few seconds (perhaps as much as 20 seconds.)
  If you ever have a backlog, these retransmits will be a storm of ever increasing traffic.

* version 3 does not have shared subscriptions, can only use one process per subscription.
  load balancing more difficult.


Shared Subscriptions
--------------------

* once you join a group, you are there until the session is dead, even if you disconnect,
  it will pile 1/n messages in your queue.


Back Pressure
-------------

1. paho client is async, 
2. best practice is to have very light-weight on_message handlers.
3. paho client acknowledges in the library around the time on_message is called.

If you have an application that is falling behind... say it is slow at processing
but since the reception is async, all this means is you will get an ever bigger
queue of messages on the local host. Ideally, it would let the broker know that
things are going poorly and the broker would send less data there.

Methods:

1. v5: Receive Maximum ... limit the number of messages in flight between broker and client.
   with mosquitto, reaching this value means drop messages for that client... 
   that's ok when there are multiple client sharing a subscription, and those messages go to
   other clients (to be verified.)
   not good when the share has only one client in it (or all the clients are backed up.)

2. disconnect.  just disconnect, and it should queue while you are gone... seems sad
   to have to do that.

Ideas?


If you don't provide backpressure, then:

1) you need to persist messages on receipt, and a node that is stuck will build
   and acknowledge receipt of an every increasing number of messages, and will fall further
   and further behind, providing no feedback for the broker doling out messages in a shared subscription.


