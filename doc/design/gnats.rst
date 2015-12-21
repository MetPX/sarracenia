
Gnats - Issues noticed but not raising until a good time.
  Sort of deferred bug reports.

Last Review: 2015-12-20

unlessed prefixed as minor... the issue is considered a release blocker.
a release blocker is something that prevents a version from proceeding
to ´beta´ status.

minor: self-test:
  really cool that there are now TEST options for some of the modules.
  But the test modules hard code the broker and other settings, so
  cannot be used elsewhere.
  TEST modules should use a configuration module:
  ~/.config/sarra/<component>/test.conf

  so that self-test can work anywhere.

sr_subscribe:
  Looks like mirror True makes the directory tree, but does not place files in it. 


~/.conf/sarra/credentials.conf -- permissions.
  should force credentials to 600.


sr_sender1 does not exist.

sr_sender2 does not exist.

sr_winnow does not exist.

Cannot run as a pump (currently only start individual components.)

User guides do not exist.

minor: Windows doesn´t work (ie. fully.) perhaps not an issue for initial release.




Windows Worries:

  - hard links ?   
    createhardlink call exists on windows now.

  - cron ?   	   
    modern windows has schtasks and can be done from Scheduled Tasks control panel.
    Just need setup for the windows tool.

  - file permissions  
    how to make sure credentials.conf is private on multi-user systems.
  
