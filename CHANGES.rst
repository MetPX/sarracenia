===============
 Release Notes 
===============

lists all changes between versions.

**git repo**

**3.00.17**

 * #539 French documentation for sr3 now exists.
 * #547, #504 v03 post format revised to separate checksums from non-data file operations.
 * above is a breaking change... old versions will not be able to understand v03 encoding of certain files.
 * #466 retry queue for failed send, also post retry queue.
 * improved documentation #552 
 * #522 honor permLog 
 * #465 simulation mode for sender (not yet complete.)
 * #438 v2 to sr3 config converter added (still has some problems, but mostly working.)
 * #513 improved shutdown on signal receipt.
 * 

**3.00.16**
 * wrapped all calls to callbacks with try/except and error messaging.
 * more obvious errors when extra dependencies are missing.
 * more documentation improvements.
 * change appauthor from 'science.gc.ca' to 'MetPX'

**3.00.15b2**

  * #490 implemented CI/CD matrix doing flow tests with multiple python versions.
  * #489 sourceFromExchange was missing implementation.
  * #488 there was a problem with recovering from connection failures.
  * #487 fixed to ignore unjustified flow test failures.
  * #486 problem with inflight.
  * #483, #455, #479 debian packaging working again, based on use of extras (optional components.)
  * improved messaging of mdelaylatest flow callback.
  * large, numerous improvements in the documentation (approaching release quality.) 
  * tls_rigour becomes tlsRigour (in implementation, was only documented that way before.)
  * #480 sr3 status display problem not ignoring files that are not .conf ones.
  * #477 sr3 edit of default.conf, credentials.conf, admin.conf work again.

**3.00.14.b1**

  * forked off from v2.
  * has MQTT support.
  * just incrementing minor release as dev. 
  * non-stable releases for now.
  * now in beta: no more breaking changes expected.
  * 3.x is a deep re-factor vs. 2.x 
  * for more information, see new web-site: https://metpx.github.io/sarracenia
