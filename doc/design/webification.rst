
Status: Pre-Draft.  Deferred. 


Problem: Every adopter is going to have to approach their firewall people
	and get them to approve use of AMQP protocol.  
        Having Security approve use of raw AMQP is probably the best
        technical approach, but as this is unusual it typically is
        an impediment to deployment.
      

proposal:  Nowadays HTML5 has web sockets.  These are connections that start
	out as HTTP.  Once the connection is established, it hands off to any
        binary protocol.  In other words it becomes a socket.
        Sockets are what AMQP uses for communications anyways, so this
	would likely work.

        Doing this would also have the side-benefit of making web-based 
        clients possible, ad web-based monitoring much easier.


Note that "Everyone" has this "problem".   There are many different approaches people
have taken to solving it.  Some approaches are general, others highly specific.
It also breaks down into client, and server problems.  Both need to be solved,
and in order to have some flexibility, there would be some standards around that.
It hasn't gelled in a significant way yet.


	- KAAZING - is commercial, and huge.
	  here's a demo:

http://blog.kaazing.com/2013/04/01/remote-controlling-a-car-over-the-web-ingredients-smartphone-websocket-and-raspberry-pi/
	  the demo uses kaazing, and an additional level of indirection.. it writes 
          through a JMS, which is unnecessary.

	  at any rate, there is a direct AMQP gateway option.  
	  The project involves setting it up.

          This is the method likely to work most easily, but it is completely custom.
          no standards compliance (ie. you need to use kaazing libraries on client and server.)

	  rather complicated.


	- jwebsocket.org. is opeen source.

neither one seems to have python bindings, so the unpleasant problem is
either figuring that out... 

	- pubnub ( https://github.com/pubnub/python )

This one has python bindings, working standalone,
or with tornado or twisted.  hmm... would probably try using tornado first?
clients are all open soure.  slight problem: requires use of cloud 
servers (no self-hosting) -- eliminated on that basis alone.

fabric8 on openshift?

there is also another approach hinted at in the 'Scaling rabbitmq to 11' deck
http://www.slideshare.net/gavinmroy/scaling-rabbitmq-to-11

::

	vorpal bunny
		https://github.com/MeetMe/VorpalBunny
	which introduces a php layer...fab...


some approaches:
	1. try to hook up ws4py and amqplib somehow.
	2. write new javascript versions of sr_post, sr_send, and sr_subscribe clients.
	3. try to write a new ws2amqp gateway in python.
		to work with something created in 1.
	4. try out the vorpal bunny on the server, write a python client for it, or
           implement new clients in php.
	5. Other?

There is also a new AMQP standards proposed web socket binding for AMQP... (in 2014)
	http://docs.oasis-open.org/amqp-bindmap/amqp-wsb/v1.0/csprd01/amqp-wsb-v1.0-csprd01.html

        That would be great, but haven't found any server implementations or 
        client-side bindings for that yet.

None of these are straightforward and guaranteed to actually work in practice.
All of them require a lot of work to validate.
Choosing among the options is not obvious either.
So this is deferred for now.

