=====
About
=====

Mailing Lists
=============

* `metpx-devel <http://lists.sourceforge.net/lists/listinfo/metpx-devel>`_  : Discussions about development. 
* `metpx-commit <http://lists.sourceforge.net/lists/listinfo/metpx-commit>`_ : Shows logs of commits to the repository

References & Links
==================

Other, somewhat similar software, no endorsements or judgements should be taken from these links:

- Manual on the Global Telecommunications´ System: WMO Manual 386. The standard reference for this domain. (a likely stale copy is  `here <WMO-386.pdf>`_.) Try http://www.wmo.int for the latest version.
- `Local Data Manager <http://www.unidata.ucar.edu/software/ldm>`_ LDM includes a network protocol, and it fundamentally wishes to exchange with other LDM systems.  This package was instructive in interesting ways, in the early 2000's there was an effort called NLDM which layered meteorological messaging over a standard TCP/IP protocol.  That effort died, however, but the inspiration of keeping the domain (weather) separate from the transport layer (TCP/IP) was an important motivation for MetPX.
- `Automatic File Distributor  <http://www.dwd.de/AFD>`_ - from the German Weather Service.  Routes files using the transport protocol of the user's choice.  Philosophically close to MetPX.
- `Corobor <http://www.corobor.com>`_ - commercial WMO switch supplier. 
- `Netsys  <http://www.netsys.co.za>`_ - commercial WMO switch supplier.
- `IBLSoft <http://www.iblsoft.com>`_ - commercial WMO switch supplier.
- variety of file transfer engines: Standard Networks Move IT DMZ, Softlink B-HUB & FEST, Globalscape EFT Server, Axway XFB, Primeur Spazio, Tumbleweed Secure File Transfer, Messageway.
- `Quantum <https://www.websocket.org/quantum.html>`_ about HTML5 web sockets. A good discussion of why traditional web push is awful, showing how web sockets can help.  AMQP is a pure socket solution that has the same advantages websockets for efficiency. Note: KAAZING wrote the piece, not disinterested.
- `Rsync  <https://rsync.samba.org/>`_ provides fast incremental file transfer.
- `Lsyncd <https://github.com/axkibe/lsyncd>`_ Live syncing (Mirror) Daemon.
- `Zsync <http://zsync.moria.org.uk>`_ optimised rsync over HTTP.
