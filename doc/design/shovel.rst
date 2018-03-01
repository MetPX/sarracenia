
=========
 Shovels
=========

Design of the "shovel" implementation.
There really isn't much, it is easy to implement given all the existing components.
It was written up in a day or so.  The question is, why?

We need shovels for several use cases:
 - routing of logs  (with log messages)
 - multi-source reliable schemes (with post messages)

multi-source involves configuring two or more shovels to deliver into a single exchange.
The exchange is read by sr_winnow, which winnows the stream, and reposts for consumers.

We initially examined rabbitmq static shovels.  In order for an end user to make use of shovels:

 - they have to cope with erlang syntax, which the user doesn't need for the rest of the app.
 - adding/removing shovels requires admin access.
 - the error debugging all requires admin level access to the broker, which adds a constraint
   on shovel configuration.
 - even with admin access, the messaging provided is minimal and inscrutable.
 - part of syntax is that certain typos are silently ignored (you just created an atom it does not use.)
 - keywords placed in the wrong place have the same effect.
 - It took many hours to understand how to configure, two people working together.  
   Yes, once understood, it it simple and elegant, but the barrier to understanding is too high.
 - Configurers have to understand the parameters provided to shovel command.
 - any trivial errors they make result in a completely broken broker (punishment for errors 
   is out of proportion to the sin.)
 - They have to understand conventions of sr_*'s naming and permission conventions (the use of q_* and 
   x* for queues and exchanges) and implement them manually, rather than having it done for them by a 
   script.  And any error will be reported by the inscrutable error reporting.
 - they have to place the passwords in the configuration files for rabbitmq.config.
 - the documentation states that a shovel is implemented by just invoking an erlang client,
   so it isn't clear that there is an important advantage to it's use.
 - this method is completely broker specific.  If we ever want to support additional brokers,
   whatever is done for rabbitmq shovels, will need to be completely re-implemented.

If we use sr_shovel:

 - configuration of the component is consistent with the others, as is monitoring and logging.
 - if the component fails or the configuration is wrong, it does not affect the broker as a whole.
 - passwords are stored in the central location, like the other components.
 - can be debugged without admin or management access to broker.
 - can be deployed without special broker permissions.
 - queue and exchange names will conform to permission conventions without user labour.
 - should work unchanged on brokers other than rabbitmq.



So those advantages were considered important enough to create our own shovel implementation.

