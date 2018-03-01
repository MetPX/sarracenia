
Status: Pre-Draft

==================================
 Alternatives for Private Routing
==================================

Looking at different alternatives for shipping data
which is not meant for general dissemination.  
´Public´ routing, as initially implemented, makes
data available to all while it is in transit.  Consider
methods of securing data in transit.

.. contents::

Considerations
--------------

Goldi-locks Data Sharing
~~~~~~~~~~~~~~~~~~~~~~~~

Systems with no encryption and logs available to all are the easiest to
troubleshoot.  On the other end of the spectrum, one can have a system 
that forwards data with perfect secrecy, but no-one can figure out what 
it is doing, so when there is a problem, it is hard to troubleshoot.  

The main way the Goldilocks problem arises is that when transferring through
multiple switches, each intervening switch needs to have enough information
to obtain the data so that it can be made available to the next hop.
So each switch needs all the metadata required to do it´s job.
Ideally each intervening switch would hide that data from users.

ddsr Private?
~~~~~~~~~~~~~

If one assumes that ddsr will only allow other switches and ´special´ users
(not anonymous) to go over those switches, so that xpublic acts like xprivate
(one can assume co-operative clients), then many security concerns are
easier.  All transfers are ´virtually private´, only becoming public
on ddi clusters.

until now, ddsr, had been considered as public as ddi configs.  Maybe that´s
the problem?  This is perhaps key to making the problem tractable.


Security Scanning
~~~~~~~~~~~~~~~~~

If security staff want to have content scanning in place, then the network
needs to be able to decrypt the data to feed it to the malware scanning
software. (Not sure if this is a requirement or not... further questions
required.)


Separation
----------

In this approach, the network is aware of two transfer modes:
public, and private.  when a source injects a tree into the network
it is labelled ´private´ and so the announcements are put
in a separate exchange xprivate used only for inter-switch transfer accounts.

.. NOTE::
  Difficulty: The data has to follow the messages.  How to make the data 
  available for private transfers and not public ones.  
  Seems to need multiple copies...

Thought a bit about this, was the initial approach.  It is not clear 
that there is any elegant solution so far, but it is not clear that 
there is not either.  Waiting for public routing to be delivered,
then revisit.



Payload PK Encryption
---------------------

The network routes the data itself as public data, but the data is encrypted
for recipients, making use of public-private key pairs. likely leverage existing
solutions such as gpg.  Could take the form of integrating support for gpg into
sarracenia.

Alice wants to send to Bob.

Bob sends his public key to Alice.  Alice encrypts her data with a symmetric
key. She puts that key in a message, encrypted with Bob´s private key.
Alice can then send the data over the public transfer method, and only bob
will have the symmettric key to decrypt it.

If Alice wants to send the data to Bob and Carlos, she posts once with the
symmetric key encrypted for Bob, and a second time for Carlos.  Each one will
ignore the posting not meant for them.

Data is encrypted once, and sent once (assuming Bob and Carlos are on the same
destination switch.)


Just Encrypt the Key 
~~~~~~~~~~~~~~~~~~~~

First idea: just encrypt the key as payload in the post.  Could use a 
different generated key for every block.

Information exposed: 
  - That there are private messages. If ddsr´s are public, then this is significant
    If ddsr exchanges are considered sensitive (no public access), then
    the messages are only exposed on the recipients´ end-point switches,
    because the routing network will not post to irrelevant ones.
 
  - the topic is visible to all, which gives the directory and file name.
    all the switches along the way need that information to be able
    to forward the data from switch to switch.

routing is completely standard, uses the normal public routing.
So ability to transfer arbitrary sized files, and use meshes for redundancy and
distribution all remain in effect.  All the encryption does is obscure the 
data itself.

This is very straight-forward.  The only thing it requires is a mechanism
for exchanging keys. oh... Bob posts his public Key to Alice, which tells
Alice where he is, so she can ´Reply´ to him encrypted.

Bob needs to know a to_cluster to get to Alice.

sr-post   
to_cluster=Alice@ddsrcmc
<Bob´s public key is the payload of his message>

Alice receives the key, and then stores the key in her credential store.
When she wants to send to Bob and Carlos, she prepares a post, and chooses
a symmetric encryption key for the block.  She builds a post for Bob, encrypting
the symmetric key for Bob using Bob´s public key, and a second post for Carlos encrypting
the same key using Carlos´s public key.

All the data transfers normally, it is just that the checksums are for the encrypted
forms of the data.  Data stored on ddi servers is encrypted using the symmetric key.

 - This is easiest to support, as client and admins see the same file names.
 - I´m having trouble with fileA is file A everywhere.
 - log messages flow normally, and are easily intelligible to all.

Exposes a lot of information, as a tradeoff for simplicity and quality of support which can be provided.


Encrypt Most of the Post
~~~~~~~~~~~~~~~~~~~~~~~~

Second idea: encrypt the entire message... how does this work?

I don´t yet see how this can work because all the intervening switches 
need enough information to forward blocks of data. They need paths, 
checksums etc... 

Dunno...
each switch has a public/private key pair.
encrypt the message for the switch.  
to_cluster= 
is set. to forward route the destination cluster.
on receipt, destination cluster decrypts the post.
This gives full topic hierarchy.
The post is for Bob, so post it on a Bob specific reception
exchange xr_Bob ?

Bob can then receive

Inside the message, encrypt the 
data encryption key using Bob´s public key.


Use Directory Encryption
------------------------

Well heck, there are tools to encrypt file trees.  Just use EncFS on both ends.
Alice and Bob both know the symmetric key.  They share the key through other
means, or perhaps exchange it using posts, encrypted as above.

Here is an example of it´s use with Dropbox, which is the identical problem:

http://www.howtogeek.com/121737/how-to-encrypt-cloud-storage-on-linux-and-windows-with-encfs/

In this method, all directory file names are obscured, which is a step up.
I´m not sure that sarracenia needs any features at all (any more than Dropbox does)  
It´s just a bit complicated for end users.

Leverages well-known, mature encryption implementation.  May have weaknesses, but
they are also well understood. Works on Windows and Linux with No code (just a matter 
of procedures for end users.)

Other options?  there is ecryptfs, which is mature, but looks like it is Linux-only.
Will work, just share the encrypted backing store, and you are done. 

Disadvantage: the filtering really doesn´t work well, because you
are filtering encrypted file names... so you end up sharing entire directory
trees, rather than subsets.  Granularity suffers.

Do we need a way for people to safely post each other keys?  would be nice,
but not necessary.

Email...  they send the letter with the key in entrust, or some other existing means.
perhaps integration with gpg to do send people fs encryption keys using public-private keys.
Not clear on the value of this addition might be simpler to leave it to end users?

In this method, we are logging back encrypted file names, so intevening admin´s see
the encrypted blocks transferring, but have no idea what file corresponds to what 
end user file.  

Disadvantage:  Encryption makes stuff hard to understand (Duh!)

example:

User complaint: my_experiment/try2/result.tgz is corrupt?

Admin sees: sgdsad/1242135/asgargqe.thgd  uh... which file is that?
    uh... just repost it OK?

Disadvantage:  Every time a user accesses the file on either end, they incur 
encryption penalty.  mitigation: they may choose to use it as a transfer directory
and move stuff elsewhere before and after transfer.


