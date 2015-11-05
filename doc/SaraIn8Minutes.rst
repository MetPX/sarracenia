
=========================
 Sarracenia in 8 Minutes
=========================


.. Note::
   This text accompanies the A2B.dia diagram, one opens the diagram, 
   Selects view/layers, and at each cue, change the visible layers to provide
   animation.

This is a quick explanation of how Sarracenia helps transferring files 
through complicated networks.  

cue: +People

Alice and Bob are colleagues that work in different companies, and are far 
away from each other.  Alice wants to send her folder with Frog DNA to Bob.

There are networks between them.

cue: +network,+Datastr

Alice could try to send it directly to Bob, but it turns out:

cue: +Firewalls

 - there are firewalls in the way, stopping direct transfers,
 - Even if direct transfers work, it might not take the fastest path,
 - Even if it takes the right path, the transfer tools available to Alice and Bob
   might be slow

What Alice needs is for someone to figure out the best path to get her folder
from A to B, taking into account network layout and firewalls, and placing 
data pumps wherever they are needed to forward the data where it needs to go.

cue: +pumps,-firewalls,

Each pump posts messages to for the next one using the Advanced Message 
Queueing Protocol, a very mature internet standard for messaging middleware. 
Once a pump knows it wants some data, it copies it from it's neighbour
using normal transfer methods like HTTP or SFTP.  This is set up
in advance by administrators so that optimal paths and methods are used.

So Alice only needs to talk to the data pump nearest her, that would be 
Sarracenia pump A.  Alice says: I want my frog DNA to go to B and F!  
(she does that with an sr_post command.)

cue: +tAl2A..,+Alice2A

Switch A, runs an sr_sara service, that acquires Alice's frog DNA folder, 
copying the data onto A, and then "Announces" to anyone listening, that 
Alice's folder is on A, and looking for a way to get to B and F.

cue: -tal2Aa...,+tal2ax,+al2atr..

The Green arrows are the AMQP messages.
There is one from Alice to A advertising the folder.
the black line, is the actual data transferred using sftp from 
Alice's server to the pump. Once that has completed, A Tells
Alice it has finished with a (green) AMQP log message. 

Pump C is listening (or subscribed) to Pump A, and since it knows 
the way to B and F, it acquires the folder from A, and then announces to 
anyone listening that Alice's folder is on C, and trying to get to B and F.  
This process repeats.

cue: -tal2ax,+tAC,+A2Dvector

Blue represents using HTTP instead of SFTP to transfer the data. Pumps 
may use different tools, but Alice does not worry about it. The forwarding
is set up once by administrators, and works for anyone's future data going 
through.

There is no need for a central authority.  The Sarracenia pumps operate 
as peers, with no trust relationships between them, they just agree to 
pump data on each others' behalf.  and of course, Bob does not have to 
trust Alice either. 

So the pumps forward the data to B, and Bob picks it up from there.

cue: +D2Bvector,+D2E,+BobgetsfromB,-tAC

But what if Pump E has a problem?

cue: +Eboom,-BobgetfromB,-E2B,-D2Evector

Alice really wanted to make sure Bob got her folder, so she sent it to
B AND F. 

cue: +D2F,BobfromF

Bob does not have to decide which pump is the primary, and which is the backup.
Look, B is not even in trouble here, it just is not getting any data from
E.  With Sarracenia, Bob can listen to both B and F all the time, and get 
Alice's folder from the pump that announces it first.

cue: +BobGet

Because of Sarracenia's logging, Alice will know each pump that got the folder,
and will see that Bob got the folder through Pump F.  

cue: +OtherPeople

If others are interested in the folder, they subscribe to it at their nearest pump
as well.  As the folder passes through the network, they will be notified and 
they can get it too, and Alice will know they got it.  The data only has to pass 
through the long-haul, expensive networks once to get to everyone. 

Of course, if Alice only wants to share with Bob, the folder can be encrypted 
with a key she only shares with Bob.

Sarracenia Speed
----------------

Sarracenia should be fast:

  - performance in today's networks is hard to understand. Admins optimize
    the topology to reflect our experiments so Alice doesn't have to.
  - AMQP messaging is very efficient and effective to provide a control path.
  - Like a Star Trek Transporter, Large files in Alice's folders are divided into 
    parts and sent separately.  The parts traverse the network in parallel, 
    providing multi-streaming, important for latency hiding over long-haul links. 
  - When a file in the folder is changed, only that block will propagate through
    the network.  Each block is checksummed, to allow people to know what they have already 
    received.
  - Sarracenia uses standard data transfer protocols today: http, sftp.  if something better 
    shows up, sarracenia will adopt it, without Alice needing to worry about it.
  - because the transfers go through data pumps. the traffic is much more visible
    to administrators, giving them a chance to understand problems better when they arise.

Is Sarracenia fast?
  We have not measured it yet.  We are getting the way it works right first.


Other uses for Sarracenia?
--------------------------

  - Sometimes networks are simpler.  One can use Sarracenia protocol without sending any data 
    through a pump.  sftp.science.gc.ca is a pump that just manages 
    the control flow, where data is transferred directly from Alice's server to Bob's in 
    the science.gc.ca HPC domain. This is useful, for example, if Alice is just Bob in drag.

  - Sarracenia notifications are very efficient, much more efficient than polling a directory 
    with 'ls'.  So even if all you want to do is know that a file that you already have access 
    to is changed, where there is a lot of people interested in the same files, it can be more
    efficient than local file i/o.

