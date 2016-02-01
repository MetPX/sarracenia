MetPX Website
=============

The MetPX website is built from the documentation in the various modules in the project. It builds using all **.rst** files found in **sarracenia/doc** as well as *some* of the **.rst** files found in **sundew/doc**.

Building Locally
----------------

In order to build the HTML pages, the following software must be available on your workstation:

* `dia <http://dia-installer.de/>`_
* `docutils <http://docutils.sourceforge.net/>`_
* `groff <http://www.gnu.org/software/groff/>`_

From a command shell::

  cd site
  make


Updating The Website
--------------------  

To publish the site to sourceforge (updating metpx.sourceforge.net), you must have a sourceforge.net account
and have the required permissions to modify the site.

From a shell, run::

  make SFUSER=myuser deploy
  
   
