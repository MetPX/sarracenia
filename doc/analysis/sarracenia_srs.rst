=====================================================
Sarracenia Software Requirement Specifications (SSRS)
=====================================================


Introduction
------------

Overall Description
-------------------

System Features
---------------

F.i0 Basic requirements
~~~~~~~~~~~~~~~~~~~~~~~

F.i0.1 Configuration interface::

    F.i0.1.1 Sarracenia should read the configuration option for a source ( '' ) broker, if any
    F.i0.1.2 Sarracenia should read the configuration option for a destination ( 'post' ) broker, if any
    F.i0.1.3 Sarracenia should read the configuration option for a source ( '' ) exchange, if any
    F.i0.1.4 Sarracenia should read the configuration option for a destination ( 'post' ) exchange, if any
    F.i0.1.3 Sarracenia should read the configuration option for a source ( '' ) topic prefix, if any
    F.i0.1.4 Sarracenia should read the configuration option for a destination ( 'post' ) exchange, if any

F.i0.2 Self Auditing::

    F.i0.1.1 Sarracenia should add the source ( '' ) exchange, if any to the RabbitMQ broker
    F.i0.1.1 Sarracenia should add the destination ( 'post' ) exchange, if any, to the RabbitMQ broker
    F.i0.1.1 Sarracenia should add user name
    F.i0.1.1 Sarracenia should configure user permission

F.i227 RabbitMQ´s MQTT plugin (aka RabbitMQTT) support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

F.i227.1 MQTT configuration interface::

    F.i227.1.1 Sarracenia must detect the availability status of RabbitMQTT
    F.i227.1.2 Sarracenia must resolve RabbitMQTT exchange
    F.i227.1.3 Sarracenia must resolve RabbitMQTT user
    F.i227.1.4 Sarracenia must provide a configuration interface that enables the consumption from RabbitMQTT
    F.i227.1.5 Sarracenia must provide a configuration interface that enables the publication to RabbitMQTT

F.i227.2 RabbitMQTT connection interface::

    F.i227.2.1 Sarracenia should subscribe to RabbitMQTT with a MQTT topic
    F.i227.2.2 Sarracenia must consumes messages received from a RabbitMQTT exchange
    F.i227.2.3 Sarracenia should publish a message to a RabbitMQTT exchange
    F.i227.2.4 Sarracenia should transform an AMQP message to a MQTT message
    F.i227.2.5 Sarracenia should transform a MQTT message to an AMQP message

F.i227.3 Map RabbitMQTT to normal Sarracenia usage::

    F.i227.3.1 Sarracenia must encode the RabbitMQTT topic as a concatenation of the origin AMQP exchange name (the prefix) and the accept  (the suffix)
    F.i227.3.2 Sarracenia must decode the RabbitMQTT message to V02 messages (verify if it needs more features than the V03toV02 decoding)
    F.i227.3.3 Sarracenia must encode its V02 message to RabbitMQTT message. (verify if it needs more features than the V02toV03 encoding)

NF.i227 Others non-functionnal requirements (NR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NF.i227.1 Interoperability::

    NF.i227.1.1 Sarracenia must be compliant with V03 message definition
    NF.i227.1.2 Sarracenia must support MQTT permission model

NF.i227.2 Security::

    NF.i227.2.1 Sarracenia must rely on AMQP permission model
    NF.i227.2.2 Sarracenia must allow anonymous users in read-only mode
