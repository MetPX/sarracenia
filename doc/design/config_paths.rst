
--------------------
Config File Location
--------------------

for what it's worth.  I took some time to go over why the preferences are stored where they are:

   -- it is best practice for applications (such as daemons) to have users created corresponding to the application, and daemons are usually expected to run under those users.

sample reference:

( https://www.debian.org/doc/manuals/securing-debian-howto/ch9.en.html 
 

   9.2  "If your software runs a daemon that does not need root privileges, you need to create a user for it."

  -- Sarracenia can be used in many ways.  It can be used on a dedicated data pump as the "main application" or it can be used on a shared server by a hundred different users for a hundred different purposes, much like users would use the rsync, or ssh commands.  It is not exclusively a system level tool.

 -- The standard for storing user preferences, as adopted by both KDE and gnome, involves use of the .config hierarchy as described in:

https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

Sarracenia conforms to that standard.    In that standard, A given user's configuration files are stored under ~/.config/<app>/

We just combined the standard for storage of user specific preferences, with the best practice that application daemons should have a user associated with them to give us a standard location to store preferences with zero code associated with it, since it works exactly the same 
way for admins as it will for all the users, the only difference being the name of the user running the tool.   To do otherwise would mean creating code to differentiate between the case where a "normal" user invoked it, versus a "special" one,  knowing which user is "special".  It would be added code and additional complexity in the application.

A separate point is that one of the improvements of the new configuration scheme is to discourage/avoid putting passwords directly in configuration files.  We have innumerable experiences where passwords have been unintentionally divulged to various audiences as a result of just sharing configuration files.   The storage of passwords in sarracenia is explicitly placed in a separate file ~/.config/sarra/credentials.conf, and the permissions on that file are checked regularly to ensure they are not public readable.

While sarracenia can be used as a traditional daemon-style app, that is just a matter of creating a user dedicated to that usage, and configuring the init script to use that user when invoking it.   On the same machine,  ten users can all invoke "sr start" and ten different sets of processes will be started up as a result, and the result of sr status will also be different between all of them, because the configuration is not system-wide, but per user.  So it makes no sense to put the configuration files in /etc, as those files will not be referenced by or relevant to the individual user configurations, including the "systemish" one that could run under the "sarra" user.

This isn't a mistake or oversight.  It is a considered, conscious change from previous practice.


