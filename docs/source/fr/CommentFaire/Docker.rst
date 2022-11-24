
-----------------------------
Exécution de MetPX via Docker
-----------------------------


Introduction
------------

Alors que Sarracenia peut être installé via pip, debian / Ubuntu, une capacité `Docker`_
est également fourni à l’appui de la conteneurisation et du cloud « run anywhere »
d'environnements natifs.

Pour offrir une flexibilité maximale, l’image par défaut de Sarracenia n’inclut pas
un courtier ou un point d’entrée.  C’est à l’utilisateur d’orchestrer davantage son
déploiement en conséquence.  `Docker Compose`_ est l’une de ces capacités d’orchestration.

Vous trouverez ci-dessous différents flux de travail pour créer, orchestrer et exécuter sarracenia via Docker::

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

Journalisation
--------------

Les normes dans le monde docker sont d’envoyer des messages à la sortie standard, donc
l’option *logStdout* doit être utilisée dans toutes les configurations d’un conteneur docker.
Cela permettra aux *journaux docker* de fonctionner comme prévu dans un environnement docker, en imprimant
à la sortie standard.

.. _`Docker`: https://docker.com
.. _`Docker Compose`: https://docs.docker.com/compose/
