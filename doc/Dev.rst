
====================================
 MetPX-Sarracenia Developer's Guide
====================================

.. contents::

------------------
Building a Release
------------------

PyPi
----

What commands are needed to perform a release:

- git branch
- make ?
- python3 setup.py upload?

Debian/Ubuntu
-------------

- check the **build-depends** line in *debian/control* for requirements to build from source.
- The following steps will build sarracenia but not sign the changes or the source package::

    cd metpx/sarracenia
    dpkg-buildpackage -uc -us


RPM
---


Windows
-------

Just do the whole python install thing with all steps for now.
