
=====================================
 MetPX-Sarracenia for Administrators
=====================================

.. Contents::


LDAP integration requires RABBITMQ > 3.3.x ...
----------------------------------------------

Was searching on how to use LDAP strictly for password authentication
The answer I got from the Rabbitmq gurus ::
  
  On 07/08/14 20:51, michel.grenier@ec.gc.ca wrote:
  > I am trying to find a way to use our ldap server  only for 
  > authentification...
  > The user's  permissions, vhost ... etc  would already be set directly 
  > on the server
  > with rabbitmqctl...   The only thing ldap would be used for would be
  > logging.
  > Is that possible... ?   I am asking because our ldap schema is quite
  > different from
  > what rabbitmq-server requieres.
  
  Yes (as long as you're using at least 3.3.x).
  
  You need something like:
  
  {rabbit,[{auth_backends,
             [{rabbit_auth_backend_ldap, rabbit_auth_backend_internal}]}]}
  
  See http://www.rabbitmq.com/ldap.html and in particular:
  
  "The list can contain names of modules (in which case the same module is used for both authentication and authorisation), *or 2-tuples like {ModN, ModZ} in which case ModN is used for authentication and ModZ is used for authorisation*."
  
  Here ModN is rabbit_auth_backend_ldap and ModZ is rabbit_auth_backend_internal.
  
  Cheers, Simon
  
  
