
=================
Télécharger MetPX
=================

... contents::

Obtenir le code source
----------------------

Le développement se fait sur la branche *master*, et les versions se font sur une branche fréquente.
base. Le code source contient à la fois des composants *Sundew* et *Sarracenia*,
bien qu'actuellement, seule la *Sarracenia* est en cours de développement.

Avec ces explications, n'hésitez pas à saisir une version instantanée à l'aide de
git via: :

    git clone https://github.com/MetPX/sarracenia sarracenia


Disponible pour un accès anonyme en lecture seule. On peut aussi obtenir une version stable.
en vérifiant une etiquette ( *tag* ) de publication::

  blacklab% git tag
    
  .
  .
  .
  v2.18.04b2
  v2.18.04b3
  v2.18.04b4
  v2.18.04b5
  v2.18.05b1
  v2.18.05b2
  v2.18.05b3
  v2.18.05b4

  blacklab% git checkout v2.18.05b4
  

Bâtiment à partir de la source
------------------------------

Sundew
~~~~~~

Veuillez vous référer au guide du développeur `Sundew developer guide <http://github.com/MetPX/Sundew/blob/master/doc/dev/DevGuide.rst>`_ pour les instructions concernant
comment construire *Metpx-Sundew*. Actuellement, les installations internes sont effectuées, l'une d'entre elles à
un temps, de la source. Le développement se fait sur la version du tronc. Quand nous installons
sur le plan opérationnel, le processus consiste à créer une branche et à l'exécuter.
sur un système d'échelonnement, puis mise en œuvre sur des systèmes opérationnels. Il y a
des fichiers README et INSTALL qui peuvent être utilisés pour l'installation de sundew. On peut
suivre ces instructions pour obtenir un système initial installé.

Pour exécuter sundew, il est essentiel d'installer les tâches de nettoyage cron (mr-clean) puisque
sinon le serveur ralentira continuellement au fil du temps jusqu'à ce qu'il ralentisse pour devenir un serveur
ramper. Il est recommandé de s'inscrire à la liste de diffusion et de nous faire savoir ce qui suit
c'est de vous empêcher de l'essayer, ça pourrait nous inspirer à travailler sur cette partie.
plus rapide pour mettre en place une collaboration.

Sarracénie
~~~~~~~~~~

Veuillez vous référer au `Guide du développeur Sarracenia <Dev.rst>`_ pour les instructions sur la construction *Metpx-Sarracenia* à partir des sources.

Binaires Sundew
---------------

MetPx-Sundew n'est disponible en téléchargement qu'à partir de la section `Sundew <https://github.com/MetPX/Sundew/>`_ du stockage de fichiers sourceforge du projet, .

binaires Sarracenia
-------------------

Veuillez vous référer au `Guide d'installation de Sarracenia <Install.rst>`_ pour savoir comment télécharger et installer les binaires *Metpx-Sarracenia*.


