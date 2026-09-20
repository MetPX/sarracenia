
===============
SR3 CREDENTIALS
===============

--------------------------
SR3 Credential File Format
--------------------------

:manual section: 7
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia

CONFIGURATION
=============

One normally does not specify passwords in configuration files.  Rather they are placed
in the credentials file::

   edit ~/.config/sr3/credentials.conf

For every url specified that requires a password, one places
a matching entry in credentials.conf.
The broker option sets all the credential information to connect to the  **RabbitMQ** server

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqps://anonymous:anonymous@dd.weather.gc.ca/ )

For all **sarracenia** programs, the confidential parts of credentials are stored
only in ~/.config/sarra/credentials.conf.  This includes the destination and the broker
passwords and settings needed by components.  The format is one entry per line.  Examples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **amqps://usern:passwd@host/ login_method=PLAIN**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**
- **sftp://user5:password5@host  sftp_compat_mode**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:De%3Aize@host  passive,binary,tls**
- **ftps://user8:%2fdot8@host:2121  active,ascii,tls,prot_p**
- **ftp://user8:%2fdot8@host:990  implicit_ftps**
- **https://ladsweb.modaps.eosdis.nasa.gov/ bearer_token=89APCBF0-FEBE-11EA-A705-B0QR41911BF4**

- **s3://bucket-name s3_anonymous**
- **s3://access_key_id:secret_access_key@bucket-name**
- **s3://access_key_id:secret_access_key@bucket-name s3_session_token=a_big_string**
- **s3://access_key_id:secret_access_key@bucket-name s3_endpoint=https://my-endpoint.com/**

- **azure://account_name:account_key@your_storage_account.blob.core.windows.net/**
    - Any special characters in the account_key should be URL (%) encoded when using this format. 
- **azure://your_storage_account.blob.core.windows.net/ azure_storage_credentials=account_key**


In other configuration files or on the command line, the url simply lacks the
password or key specification.  The url given in the other files is looked
up in credentials.conf.

Credential Details
------------------

You may need to specify additional options for specific credential entries. These details can be added after the end of the URL, with multiple details separated by commas (see examples above).

Supported details:

- ``ssh_keyfile=<path>`` - (SFTP) Path to SSH keyfile. For SFTP, prefer an entry in
  ``~/.ssh/config`` instead, see `SFTP and ~/.ssh/config`_ below. ``ssh_keyfile`` is not
  seen by the ``scp`` command used for accelerated transfers.
- ``passive`` - (FTP) Use passive mode
- ``active`` - (FTP) Use active mode
- ``binary`` - (FTP) Use binary mode
- ``ascii`` - (FTP) Use ASCII mode
- ``ssl`` - (FTP) Use SSL/standard FTP
- ``tls`` - (FTP) Use FTPS with TLS
- ``prot_p`` - (FTPS) Use a secure data connection for TLS connections (otherwise, clear text is used)
- ``bearer_token=<token>`` (or ``bt=<token>``) - (HTTP) Bearer token for authentication
- ``login_method=<PLAIN|AMQPLAIN|EXTERNAL|GSSAPI>`` - (AMQP) By default, the login method will be automatically determined. This can be overriden by explicity specifying a login method, which may be required if a broker supports multiple methods and an incorrect one is automatically selected.
- ``implicit_ftps`` - (FTPS) Use implicit FTPS (otherwise, explicit FTPS is used). Setting this will also set ``tls`` to True.
- ``sftp_compat_mode`` - (SFTP) Disable some performance enhancements (prefetch reads, pipelined writes) that could potentially cause compatibility issues with certain SFTP servers.
- Details for the S3 protocol:
    - ``s3_endpoint=<url>`` - use a specific endpoint, such as a non-Amazon S3 service.
    - ``s3_session_token=<string>`` - when specifying credentials for S3, the username field is used as the "Access Key ID", the password as the "Secret Access Key". Sometimes a Session Token is also required, and can be provided with this option.
    - ``s3_anonymous`` - do not sign requests (anonymous access). Equivalent to ``--no-sign-request`` when using the S3 CLI.
- Details for Azure blob storage:
    - ``azure_storage_credentials=<string>`` - your account key. This is an alternative to using ``azure://account_name:account_key@your_storage_account.blob.core.windows.net/``. 

Note::
 SFTP credentials are optional, in that sarracenia will look in the .ssh directory
 and use the normal SSH credentials found there.

 These strings are URL encoded, so if an account has a password with a special 
 character, its URL encoded equivalent can be supplied.  In the last example above, 
 **%2f** means that the actual password is: **/dot8**
 The next to last password is:  **De:olonize**. ( %3a being the url encoded value for a colon character. )


SFTP and ~/.ssh/config
----------------------

For SFTP, put the connection settings in ``~/.ssh/config`` rather than in
``credentials.conf``, and leave out the ``credentials.conf`` entry entirely.

Sarracenia has two ways of moving a file over SFTP. Ordinary transfers use the paramiko
library, which Sarracenia configures from ``credentials.conf``. Transfers larger than
``accelThreshold`` are handed to the ``scp`` command instead (see ``accelScpCommand``).
``scp`` reads ``~/.ssh/config`` and knows nothing about ``credentials.conf``, so anything
recorded only there is invisible to it. A key named by ``ssh_keyfile`` works for ordinary
transfers and is silently missing from accelerated ones, which shows up as a configuration
that works until a file crosses ``accelThreshold``.

Settings in ``~/.ssh/config`` avoid that, because both paths read them: ``scp`` natively,
and paramiko because Sarracenia looks the host up in ``~/.ssh/config`` itself and picks up
``HostName``, ``User``, ``Port`` and ``IdentityFile``.

Define a stanza naming the host, the account and the key::

    Host weather-pump
        HostName sftp.example.com
        User sarra
        IdentityFile ~/.ssh/id_ecdsa_weather_pump
        IdentitiesOnly yes

Then use the alias as the host name wherever the server appears::

    sendTo sftp://weather-pump/

and add nothing to ``credentials.conf`` for it.

The alias is a label, not a host name, so a server reachable several ways can have one
stanza per way, each with its own alias, and a server that moves only needs its stanza
edited.

Do not put a port number in the URL. Give the port in the stanza instead::

    Host weather-pump-alt
        HostName sftp.example.com
        Port 2222
        User sarra
        IdentityFile ~/.ssh/id_ecdsa_weather_pump

A port in the URL is not passed on to ``scp`` correctly, so an accelerated transfer to
``sftp://sarra@host:2222/`` fails while an ordinary transfer to the same URL succeeds.

Note::
 Sarracenia only consults ``~/.ssh/config`` when the credential does not already answer
 the question: when no user is known, or when neither a key nor a password was supplied.
 A ``credentials.conf`` entry carrying a user and a password takes precedence and the
 stanza is not read. Omitting the entry is the reliable way to have ``~/.ssh/config``
 apply.


SEE ALSO
========



`sr3(1) <sr3.1.html>`_ - Sarracenia main command line interface.

`sr3_post(1) <sr3_post.1.html>`_ - post file notification messages (python implementation.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - post file announcemensts (C implementation.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - C implementation of the shovel component. (copy messages)

**Formats:**

`sr3_options(7) <sr_options.7.html>`_ - the configuration options

`sr3_post(7) <sr_post.7.html>`_ - the format of notification messages.

**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: a real-time pub/sub data sharing management toolkit 


