
================
 Release process
================

------------------------------------
Developping and releasing sarracenia
------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

When developping sarracenia, here is what I do to evolve to another release

Develop, code, test the new functionnalities.
When confident :

NOTE :  ONE would need to verify all the credentials requiered and server
        accessibility that the tests requiere ...

1- rerun basic self test

   some_self_test.sh

2- rerun and check results for

   test_sr_post.sh
   test_sr_watch.sh
   test_sr_subscribe.sh
   test_sr_sarra.sh

   Note :  some tests error ...
           in test_sr_sarra.sh ... there are lots of ftp/sftp connections
           so some config settings like sshd_config (MaxStartups 500) might
           might be requiered to have successfull tests.


3- making a local wheel and installing on your workstation

   in the git clone tree ...    metpx-git/sarracenia
   create a wheel by running

   python3 setup.py bdist_wheel

   it creates a wheel package under  dist/metpx*.whl
   than as root  install that new package

   pip3 install --upgrade ...<path>/dist/metpx*.whl




4- Have a sarracenia environment in your home...
   with copies of some of our operational settings ...
   correctly modified not to impact the operations.
   (like no "delete True"  etc...)
   And other sarra configurations ... try running sarra.

   sr start

   Watch for errors... check in logs... etc.

   Should you see things that are suspicious 
   
       a) stop the process
       b) run the process in debug and foreground
          <sr_program> --debug <configname> foreground
       c) check interactive output for any hint


5- if confident, make a release <Dev.rst>


6- Start deploying the release when the least
   impact :

   dev servers...  : make sure everything is ok
   stage servers...: make sure everything is ok
   and finally ... one by one the operational 
   servers...


 current list of servers implementing sarracenia :

dev :   bunny[1,2]-dev.cmc
        urpd[1,2].cmc

Kind of stage for now:
        dms-ops-host[1,2,3,4].edm
        ddi[1,2].edm
        ddi[1,2].cmc

Operational :
        pxatx[1,2]-ops
        px[1,2,3,4,5,6,7,8]-ops


7- How to  :

   a) minor releases (update/bug fix)  99% of the time.

    (as sarra ?) sr stop
    (as root   ) pip3 install --upgrage metpx_sarracania
    (as sarra ?) sr start


   b) you should be really carefull if you change default settings
      for exchanges / queues ... 

      when a program declares an exchange or a queue for its own use
      it needs to declare the resource with the same settings as it
      resides on the rabbitmq-server... if it declares it with a different
      setting, the access to the resource will not be granted by the server.
      (??? perhaps there is a way to get access to a resource as is... no declare)
      (??? should be investigated)

      Changing the default require the removal and recreation of the resource.
      This has a major impact on processes...


      I had to do this once a specially on the operational ddsr... 
      queue's default was changing from no expire to expire after a week...
      For this event:


      update sarracenia half of ddsr
           px[5,6,7,8]-ops

           On the rabbitmq web application of ddsr.cmc
           deleted queues related to local sarracenia processes

           Installed the new sarracenia on these nodes



      Keep passive pxatx-ops as backup (old sarracenia) but stop it
           sr stop

      *** now critical time

      stop remaining of the sarracenia on ddsr
           sr stop on px[1,2,3,4]-ops

      On the active pxatx-ops... 
           sr stop
           update sarracenia package

      On the rabbitm web application
         delete queues related to ddsr's local processes
         leave queue from other servers (ddi.cmc... etc)

      On updated px[5678]-op
         sr start  (new queues with proper settings are created)

      On active pxatx-ops  
         sr start

      If everything ok: update left half kept as failover...

      Proceed with the upgrade of the stopped  px[1,2,3,4]-ops
      and passive pxatx-ops
      restart sarracenia with new version there too.
      

      NOTE:  
             I have intentiallaly left half of the server on the old
             sarracenia version to be able to restart quickly with that
             should there be a problem... (would have to switch pxatx... 
             but it is ok)

