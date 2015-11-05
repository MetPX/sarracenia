
=========================
 Sarracenia in 5 Minutes
=========================


.. Note::
   This text accompanies the A2B.dia diagram, one opens the diagram, 
   Selects view/layers, and at each cue, change the visible layers to provide
   animation.

This is a quick explanation of how Sarracenia helps transferring files 
through complicated networks.  

cue: +People

Alice and Bob are colleagues that work in different companies, and are far 
away from each other.  Alice wants to send her Frog DNA file to Bob.

There are networks between them.

cue: +network,+Datastr

Alice could try to send it directly to Bob, but it turns out 

cue: +Firewalls

 - there are many firewalls in the way, stopping direct transfers,
 - Even if direct transfers work, it might not take the fastest path,
 - Even if it takes the right path, the transfer tool could be slow.

What Alice needs is for someone to figure out the best path to get her file
from A to B, taking into account network layout and firewalls, placing 
data pumps wherever they are needed to forward the data where it needs to go.

cue: +pumps,-firewalls,

So Alice only needs to talk to the data pump nearest her, that would be 
Sarracenia pump A.  Alice says: I want my frog DNA to go to B and F!  
(she does that with an sr_post command.)

cue: +tAl2A..,+Alice2A

Switch A, runs an sr_sara service, that picks up Alice's frog DNA file, 
copying the data onto A, and then "Announces" to anyone listening, 
(using an AMQP message) that Alice's file is on A, and looking for a way 
to get to B and F.

cue: -tal2Aa...,+tal2ax,+al2atr..

The Green messages are the AMQP messages.
There is one from Alice to A advertising the file.
the black line, is the actual data being transferred using sftp from 
Alice's server to the pump. Once that has completed, A Tells
Alice with a (green) AMQP log message. 

Pump C is listening (or subscribed) to Pump A, and since it knows 
the way to B and F, it acquires the file from A, and then announces to 
anyone listening that Alice's file is on C, and trying to get to B and F.  
This process repeats.

cue: -tal2ax,+tAC,+A2Dvector

Blue represents using HTTP instead of SFTP to transfer the data. Pumps 
may use different tools, but Alice does not worry about it. The forwarding
is set up once by administrators, and works for anyone's future data going 
through.

There is no need for a central authority.  The Sarracenia pumps operate 
as peers, with no trust relationships between them, and Bob does not have
to trust Alice either. they just agree to pump data on each others' behalf.

cue: +D2Bvector,+D2E,+BobgetsfromB,-tAC

But what if Pump E has a problem?

cue: +Eboom,-BobgetfromB,-E2B

Alice really wanted to make sure Bob could get her file, so she sent it to
B AND F. 

cue: +D2F,BobfromF

Bob does not have to decide which pump is the primary, and which is the backup.
Look, B is not even in trouble here, it just is not getting any data from
E.  With Sarracenia, Bob can listen to both B and F all the time, and get 
Alice's file from the pump that announces it first.

Sarracenia has complete logging, so Alice will know that pump D got the file,
and will see that Bob got the file through Pump F.  

------- <under 3 minutes...


-- timeliness. history dd_subscribe.

-- multiple streams for large files.

-- cover local file notifications?

-- how it is really meant for dissemination (feeding web accessible folders?)

-- walk through dd?
