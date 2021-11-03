
==================
 Docker Guide
==================

------------------------------------------------
Running MetPX via Docker
------------------------------------------------

[ `version française <fr/docker.rst>`_ ]


.. contents::

Revision Record
---------------

:version: @Version@
:date: @Date@


Introduction
------------

While sarracenia can be installed via pip, debian/Ubuntu, a `Docker`_ capability
is also provided in support of "run anywhere" containerization and cloud
native environments.

To provide maximum flexibility, sarracenia's default image does not include
a broker or an entrypoint.  It is up to the user to further orchestrate their
deployment accordingly.  `Docker Compose`_ is one such orchestration capability.

Below are various workflows to build, orchestrate and run sarracenia via Docker::

  # clone repo
  git clone https://github.com/MetPX/sarracenia.git
  cd sarracenia

  # build image
  docker build -t metpx-sr3:latest .

  # sarracenia connected to a rabbitmq setup
  # start
  docker-compose -f docker/compose/pump/docker-compose.yml up
  # stop
  docker-compose -f docker/compose/pump/docker-compose.yml down


.. _`Docker`: https://docker.com
.. _`Docker Compose`: https://docs.docker.com/compose/
