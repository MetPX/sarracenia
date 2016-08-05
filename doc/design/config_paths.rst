
--------------------
Config File Location
--------------------

Place to note down rationale behind the preferences storage.  Some feedback received has been that such files should be stored
in /etc, as per system applications and the File Hierarchy Standard, particularly based on previous practice.  This is not
what we decided to do, for the following reasons:

  - It is best practice for applications (such as daemons) to have users created corresponding to the application, and daemons are usually expected to run under those users.
  - Sarracenia can be used in many ways.  It can be used on a dedicated data pump as the "main application" or it can be used on a shared server by a hundred different users for a hundred different purposes, much like users would use the rsync, or ssh commands.  It is not exclusively a system level tool.
  - The standard for storing user preferences, as adopted by both KDE and gnome, involves use of the .config hierarchy as described in:

    https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

    Sarracenia conforms to that standard.    In that standard, A given user's configuration files are stored under ~/.config/<app>/

One of the improvements of the new configuration scheme is to discourage/avoid putting passwords directly in configuration files.
We have many long experiences where passwords are unintentionally divulged to various audiences as a result of just sharing configuration files.  
The storage of passwords in sarracenia is explicitly placed in a separate file ~/.config/sarra/credentials.conf, and if the permissions on that
file are checked regularly to ensure they are not public readable.

While sarracenia can be used as a traditional daemon-style app, that is just a matter of creating a user dedicated to that usage, and configuring the init script to use that user when invoking it.   On the same machine,  ten users can all invoke "sr start" and ten different sets of processes will be started up as a result, and the result of sr status will also be different between all of them.  

The use of files in the user's home directory is long standing practice, and the current active standard is the one listed above.
There are older packages that 
SSH also has configuration files, that it stores in ~/.ssh, 


-- 
