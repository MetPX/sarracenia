Glossaire
=========

La documentation de Sarracenia utilise un certain nombre de mots d’une manière particulière.
Ce glossaire devrait faciliter la compréhension du reste de la documentation.

AMQP
----

AMQP est le Advanced Message Queuing Protocol, qui a émergé dans l’industrie du trading financier et a progressivement
mûri. Les implémentations sont apparues pour la première fois en 2007, et il existe maintenant plusieurs implémentations open source. L'implémentation AMQP
n'est pas la plomberie JMS. JMS standardise l’API utilisée par les programmeurs, mais pas le protocole on-the-wire. Ainsi
en règle générale, on ne peut pas échanger de messages entre des personnes utilisant différents fournisseurs JMS. L’AMQP normalise
l’interopérabilité, et fonctionne efficacement comme une cale d’interopérabilité pour JMS, sans être
limité à Java. AMQP est neutre sur le plan linguistique et neutre sur le plan du message. Il existe de nombreux déploiements utilisant
Python, C++ et Ruby. On pourrait adapter très facilement les protocoles WMO-GTS pour fonctionner sur AMQP.
Les fournisseurs JMS sont très orientés Java.


* `www.amqp.org <http://www.amqp.org>`_ - Définir AMQP
* `www.openamq.org <http://www.openamq.org>`_ - Implémentation originale GPL implementation de JPMorganChase
* `www.rabbitmq.com <http://www.rabbitmq.com>`_ - Une autre implementation gratuite. Celle qu'on utilise et qui nous convient
* `Apache Qpid <http://cwiki.apache.org/qpid>`_ - Une autre implémentation gratuite
* `Apache ActiveMQ <http://activemq.apache.org/>`_ - C'est un fournisseur JMS avec un pont AMQP. Ils préfèrent leur propre protocole openwire.

Sarracenia s’appuie fortement sur l’utilisation de courtiers et d’échanges thématiques, qui occupaient une place importante
dans les efforts de normalisation de l’AMQP avant la version 1.0, ou ils ont été supprimés. On espère que ces concepts seront réintroduits à un moment donné. Jusqu’à
cette fois-là, l’application s’appuiera sur des agents de messages standard antérieurs à la version 1.0, tels que rabbitmq.

Contre-Pression (anglais: Back Pressure)
----------------------------------------
Lorsqu’un nœud de pompage de données connaît une latence élevée, il est préférable de ne pas importer plus de données
à un rythme élevé et aggraver la surcharge. Au lieu de cela, il faut s’abstenir d’accepter des messages
à partir du nœud afin que ceux en amont maintiennent des files d’attente, et d’autres nœuds moins occupés peuvent prendre
plus de la charge. La lenteur du traitement affecte l’ingestion de nouveaux messages en est un exemple
d’appliquer une contre-pression à un flux de transfert.

Exemple d’absence de contre-pression : la bibliothèque paho-python-mqtt v3 a actuellement des accusés de réception
intégré à la bibliothèque, de sorte que l’accusé de réception se produit sans le contrôle de l’utilisateur, et il y a
aucun nombre maximal de messages pouvant se trouver dans la bibliothèque, avant que l’application ne les
voie. Si l’application s’arrête, tous ces messages, encore invisibles par l’application,
sont perdus. Dans MQTT v5, il existe un paramètre receiveMaximum qui limite au moins le nombre
des messages que la bibliothèque mettra en fil d’attente pour l’application, mais idéalement,
la bibliothèque python obtiendrait des accusés de réception contrôlés par l’application, comme la bibliothèque Java l’a déjà fait.

Pompes sans Données (anglais: Dataless Pumps)
---------------------------------------------
Il y a des pompes qui n’ont pas de moteur de transport, elles ne font que servir de médiateur
entre transferts pour d’autres serveurs, en mettant les messages à la disposition des clients et
de serveurs dans leur zone de réseau.

Transferts sans Données (Dataless Transfers)
--------------------------------------------
Parfois, les transferts à travers les pompes se font sans utiliser d’espace local sur la pompe.

Latence (anglais: Latency)
-------------------------
Temps écoulé entre l’insertion des données dans un réseau (l’heure à laquelle le message relatif à un fichier est publié pour la première fois)
au moment où il est mis à disposition sur un point final.  Nous voulons minimiser la latence dans les transferts,
et une latence élevée peut indiquer des problèmes de configuration ou de capacité.

MQTT
----
Le Message Queue Telemetry Transport (MQTT) version 5 est un deuxième protocole de fil d’attente de messages avec toutes les fonctionnalités
nécessaire pour soutenir les modèles d’échange de données de sarracenia.

* `mqtt.org <https://mqtt.org>`_
* `mosquitto.org <https://mosquitto.org>`_
* `EMQX.io <emqx.io>`_

Cartes Réseau (anglais: Network Maps)
-------------------------------------
Chaque pompe doit fournir une carte du réseau pour informer les utilisateurs de la destination connue
qu’ils devraient faire de la publicité pour envoyer à. *FIXME* non défini jusqu’à présent.

Poste, Notice, Notification, Avis, Annonce
------------------------------------------
Il s’agit de messages AMQP créés par post, poll ou watch pour permettre aux utilisateurs
de savoir qu’un fichier particulier est prêt. Le format de ces messages AMQP est
décrit par la page de manuel `sr_post(7) <../Reference/sr_post.7.html>`_. Tous ces
mots sont utilisés de manière interchangeable. Les annonces à chaque étape préservent la
source d’origine de la publication, afin que les messages de rapport puissent être réacheminés
à la source.

Pompe
-----
Une pompe est un hôte exécutant Sarracenia, soit un serveur AMQP rabbitmq, soit un MQTT
comme mosquitto. Le middleware de mise en fil d’attente des messages s’appelle un *broker*.
La pompe a des utilisateurs administratifs et gère le courtier MQP
en tant que ressource dédiée. Une sorte de moteur de transport, comme un serveur apache,
ou un serveur openssh est utilisé pour prendre en charge les transferts de fichiers. SFTP, et
HTTP / HTTPS sont les protocoles qui sont entièrement pris en charge par sarracenia. Les pompes
copient des fichiers de quelque part et les écrit localement. Ils font ensuite de la publicité à nouveau pour la
copie locale à ses pompes voisines, et les utilisateurs qui sont abonnés peuvent
obtenir les données de cette pompe.

.. Remaqrque::
  Pour les utilisateurs finaux, une pompe et un courtier sont la même chose pour toutes les buts pratiques.
  Toutefois, lorsque les administrateurs de pompe configurent des clusters multi-hôtes, un
  Broker peut s’exécuter sur deux hôtes, et le même broker peut être utilisé par
  de nombreux moteurs de transport. L’ensemble du cluster serait considéré comme une pompe. Ainsi,
  deux mots ne sont pas toujours les mêmes.

Réseau de Pompage (anglais: Pumping Network)
--------------------------------------------
Un certain nombre de serveurs d’interconnexion exécutant la stack sarracenia. Chaque stack
détermine la façon dont il achemine les éléments vers le suivant, de sorte que la taille ou l’étendue entière
du réseau peut ne pas être connu à ceux qui y mettent des données.

Messages de Rapport (anglais: Report messages)
----------------------------------------------

Il s’agit de messages AMQP (dans le format `sr_post(7) <../Reference/sr_post.7.html>`_), avec le champ _report_
inclus) construit par les consommateurs de messages, pour indiquer ce qu’une pompe de données
ou l’abonné a décidé de faire avec un message. Ils s’écoulent conceptuellement dans le
direction opposée des notifications dans un réseau, pour revenir à la source.
Dans les documents de la phase de conception originale de 2015, les rapports étaient appelés *log messages*.
Cela a été modifié pour réduire la confusion avec les données dans les fichiers journaux de l’application.

Source
------

Quelqu’un qui veut envoyer des données à quelqu’un d’autre. Ils le font en annonçant un
arborescences de fichiers copiés du point de départ vers une ou plusieurs pompes
dans le réseau. Les sources publicitaires produites indiquent aux autres exactement où
et comment télécharger les fichiers, et les sources doivent dire où elles veulent les
données auxquelles accéder.

Les sources utilisent le `post <../Reference/sr3.1.html#post>`_,
`sr_watch.1 <../Reference/sr3.1.html#watch>`_, et
`sr_poll(1) <../Reference/sr3.1.html#poll>`_ les composants à créer
leurs publicités.


Abonnés (anglais: Subscribers)
------------------------------
sont ceux qui examinent les publicités sur les fichiers disponibles, et
téléchargent les fichiers qui les intéressent.

Les abonnés utilisent `subscribe(1) <../Reference/sr3.1.html#subscribe>`_


Sundew
------
`MetPX Sundew <https://github.com/MetPX/Sundew>`_ est l’ancêtre de Sarracenia.
Il s’agit d’une pompe de données orientée TCP/IP WMO 386 pure. Les fichiers de configuration se ressemblent,
mais les algorithmes et les concepts de routage sont très différents. MetPX est une push-only
méthode de distribution de fichiers, qui a implémenté des sockets WMO 386, des sockets AM et
d’autres technologies obsolètes. Il ne fait pas pub / sub.
Plus d’histoire `here <History/Evolution.html>`_


WMO
---
L’Organisation météorologique mondiale, est une partie des Nations Unies qui fait de la surveillance, prévision et alerte
environnementale et de temps de chaque pays en tant que membres. Depuis de nombreuses décennies, il y a
un échange en temps réel de données météorologiques entre les pays, souvent même en temps de guerre.  Les normes
qui couvrent ces échanges sont :

- Manuel sur le système mondial des télécommunications: Manuel 386 de WMO. La référence standard pour ce
  domaine. (une copie probablement périmée est `ici <WMO-386.pdf>`_.) Essayez https://www.wmo.int pour la dernière version.

Habituellement, ces liens sont appelés collectivement *les CGV*.  Les normes sont très anciennes, et une modernisation
de processus est en cours depuis une dizaine d’années ou deux. Certains travaux en cours sur le remplacement de GTS sont ici:

- `WMO Task Team on message queueing protocols <https://github.com/wmo-im/GTStoWIS2>`_

Les discussions autour de ce sujet sont des moteurs importants pour Sarracenia.
