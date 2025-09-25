Migrer de Sarracenia v2 à sr3
=============================

Ce document est destiné à être un court tutoriel pour aider un utilisateur
de Sarracenia v2 à convertir sa configuration à sr3. Cela suppose que 
l'utilisateur est déjà familier avec l'usage de base de v2, et ne couvre
pas des sujets plus detaillés, tels que les plugins. 

.. IMPORTANT::

   Ce tutoriel suppose que vous avez déjà installé sr3. 
   Si ce n'est pas le cas, utilisez `ces
   instructions <../Tutoriel/Installer.html>`_
   pour installer sr3 en premier.

.. NOTE::

   Sarracenia v2 et sr3 peuvent tous les deux être exécutés en même temps sur le même ordinateur. 

Pour en savoir plus, voir:

- `CommentFaire/MiseANiveau <../CommentFaire/MiseANiveau.html#v2-to-sr3>`_ - notes 
  concernant les changements majeurs entre v2 et sr3
- `Contribution/v03 <../Contribution/v03.html>`_ - documentation détaillée
  à propos de la conception et les changements par rapport à v2
- `CommentFaire/v2ASr3 <../CommentFaire/v2ASr3.html>`_ - instructions détaillées 
  pour des développeurs qui veulent envoyer leur plugins v2 à sr3

Informations générales
----------------------

Nouvelle Interface en ligne de commande (ILC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sr3 a une nouvelle interface en ligne de commande qui est documentée 
en détails `ici <../Explication/GuideLigneDeCommande.html>`_.

La syntaxe de la commande ``sr3`` est ``sr3 action composant/config ...``,
qui remplace les commandes *specifique-au-composant* de v2 
(par exemple ``sr_subscribe`` pour le composant d'abonnement).

.. HINT::
   un *composant* est le nom général pour les mots clé *subscribe*,
   *sarra*, *watch*, *shovel*, etc.

Par exemple:

+--------------------------------------------+----------------------------------------+
| Commande v2                                | Commande équivalente sr3               |
+============================================+========================================+
| ``sr_subscribe start my_subscriber``       | ``sr3 start subscribe/my_subscriber``  |
+--------------------------------------------+----------------------------------------+
| ``sr_subscribe status my_subscriber``      | ``sr3 status subscribe/my_subscriber`` |
+--------------------------------------------+----------------------------------------+
| ``sr_watch restart my_files``              | ``sr3 restart watch/my_files``         |
+--------------------------------------------+----------------------------------------+
| ``sr status``                              | ``sr3 status``                         |
+--------------------------------------------+----------------------------------------+
| ``sr_subscribe start``                     | ``sr3 start subscribe/*``              |
+--------------------------------------------+----------------------------------------+

Nouvelle configuration et emplacement du cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

sr3 change l'emplacement des logs et configurations aussi:

======= =================== =================
Item    emplacement v2      emplacement sr3
======= =================== =================
Configs ``~/.config/sarra`` ``~/.config/sr3``
Cache   ``~/.cache/sarra``  ``~/.cache/sr3``
Logs    ``~/.cache/sarra``  ``~/.cache/sr3``
======= =================== =================

Migrer une configuration v2 vers sr3
------------------------------------

sr3 modifie légèrement certains des mots-clés utilisés dans les fichiers de configuration. 
La documentation complète de toutes les options utilisables dans un fichier de 
configuration sr3 est disponible 
`ici <../Reference/sr3_options.7.html>`_.


sr3 reconnaît les mots-clés v2, alors un fichier de configuration v2 
devrait donc être utilisable dans sr3 sans modification. 
Par contre, nous recommandons d'utiliser le convertisseur 
intégré pour <<mettre à niveau>> vos configurations en syntaxe sr3.

Préparation avant la conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

credentials.conf et default.conf
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Si vous avez modifié le fichier credentials.conf de v2
(``~/.config/sarra/credentials.conf``) ou default.conf
(``~/.config/sarra/default.conf``), vous devez copier ces fichers 
dans le répertoire de configuration de sr3.

.. code:: bash

   cp ~/.config/sarra/credentials.conf ~/.config/sr3/credentials.conf
   cp ~/.config/sarra/default.conf ~/.config/sarra/default.conf

.. IMPORTANT::

   Si vous convertissez de v2 à sr3, 
   il est fort probable que la source à laquelle vous êtes abonné 
   (par exemple, le Datamart du SMC) publie toujours des messages au format v2. 
   Avant de convertir vos configurations, vous devez ajouter 
   `topicPrefix v02.post`` à votre fichier ``default.conf`` de sr3.

   Pour ce faire, exécutez :

   .. code:: bash

      echo 'topicPrefix v02.post' >> ~/.config/sr3/default.conf

Conversion étape par étape
~~~~~~~~~~~~~~~~~~~~~~~~~~

Voici un exemple étape par étape montrant comment convertir un abonné v2 
en sr3 à l'aide du convertisseur, et comment désactiver 
la configuration v2 une fois l'opération terminée.

.. code:: bash
   
   # les commentaires dans cette section, indiqués par #, fournissent des explications

   # les commandes sont affichées dans les lignes qui avec une invite de commande qui se termine par $, 
   # par exemple : 
   
   #       invite de commande commande
   #                       ↓ ↓
   #    sarra@mon-serveur:~$ ma_commande

   # la sortie des commandes est affichée après la ligne avec l'invite de commande et la commande 

.. code:: bash

   # sr status --> afficher l'état de vos configurations v2
   #   Dans l'exemple ci-dessous, cela montre que nous avons
   #   une configuration *subscribe* en cours d'exécution nommée "dd_amis"
   sarra@mon-serveur:~$ sr status
   status:
   Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
   ---------  -----      -----  --- ------------------------------
   audit      running    OK       1
   cpost      stopped    OK       0
   cpump      stopped    OK       0
   poll       stopped    OK       0
   post       stopped    OK       0
   report     stopped    OK       0
   sarra      stopped    OK       0
   sender     stopped    OK       0
   shovel     stopped    OK       0
   subscribe  running    OK       1 dd_amis-i5/0
   watch      stopped    OK       0
   winnow     stopped    OK       0
         total running configs:   1 ( processes: 6 missing: 0 stray: 0 )


   # sr3 status --> afficher l'état de vos configurations sr3
   #   Dans l'exemple ci-dessous, nous n'avons aucune configuration sr3
   sarra@mon-serveur:~$ sr3 status
   status:
   Component/Config     Processes                                         Rates
                        State   Run Retry  Que     Lag  Last    %rej  messages      Data
                        -----   --- -----  ---     ---  ----    ----  --------      ----
         Total Running Configs:   0/0 ( Processes: 0 missing: 0 stray: 0 )
                        Memory: uss:0Bytes rss:0Bytes vms:0Bytes
                      CPU Time: User:0.00s System:0.00s
              Pub/Sub Received: 0m/s (0B/s), Sent:  0m/s (0B/s) Queued: 0 Retry: 0, Mean lag: 0.00s
                 Data Received: 0f/s (0B/s), Sent: 0f/s (0B/s)


   ######################
   # Convertir v2 à sr3 #
   ######################

   # sr3 convert composant/configuration --> Convertir une configuration v2 en sr3
   #   Nous allons convertir notre abonné v2 nommé « dd_amis » en abonné sr3, également nommé « dd_amis ».
   #   Ceci convertira toute syntaxe v2 en sr3 et placera le fichier de configuration résultant dans
   #   ~/.config/sr3/subscribe/dd_amis.conf.
   sarra@mon-serveur:~$ sr3 convert subscribe/dd_amis
   v2_config: ['subscribe/dd_amis']
   2025-08-25 17:21:20,858 2241245 [INFO] sarracenia.sr convert1 wrote conversion from v2 subscribe/dd_amis to sr3


   # Maintenant, L'état sr3 indique que nous avons une configuration sr3.
   # L'état « new » indique que la configuration n'a jamais été démarrée auparavant.
   sarra@mon-serveur:~$ sr3 status
   status:
   Component/Config     Processes                                         Rates
                        State   Run Retry  Que     Lag  Last    %rej  messages      Data
                        -----   --- -----  ---     ---  ----    ----  --------      ----
   subscribe/dd_amis    new     0/0    -    -       -      -       -       -           -
         Total Running Configs:   0/1 ( Processes: 0 missing: 0 stray: 0 )
                        Memory: uss:0Bytes rss:0Bytes vms:0Bytes
                      CPU Time: User:0.00s System:0.00s
              Pub/Sub Received: 0m/s (0B/s), Sent:  0m/s (0B/s) Queued: 0 Retry: 0, Mean lag: 0.00s
                 Data Received: 0f/s (0B/s), Sent: 0f/s (0B/s)


   # sr3 start component/config --> démarrer une configuration
   #   Nous allons démarrer notre nouvel abonné. L'abonné v2 continuera également à fonctionner, 
   #   ce qui peut entraîner la réception de données en double pendant que les deux abonnés sont actifs.
   #
   #   REMARQUE : Le message d'erreur «ERROR» indiquant l'échec de l'écriture de l'abonnement peut être ignoré.
   #              Ce sera supprimé dans une prochaine version.
   
   sarra@my-server:~$ sr3 start subscribe/dd_amis
   2025-08-25 17:28:08,410 2242079 [ERROR] sarracenia.config.subscription write failed: /home/sarra/.cache/sr3/subscribe/dd_amis/subscriptions.json: [Errno 2] No such file or directory: '/home/sarra/.cache/sr3/subscribe/dd_amis/subscriptions.json'
   starting:.( 5 ) Done


   # Maintenant, l'état sr3 indique que la configuration est en cours d'exécution, mais n'a pas
   # transféré de données depuis longtemps (état «idle») :
   # (voir la note ci-dessous/le document Guide de ligne de commande pour 
   #  plus d'informations sur les états de sr3)
   sarra@mon-serveur:~$ sr3 status
   status:
   Component/Config     Processes                                         Rates
                        State   Run Retry  Que     Lag  Last    %rej  messages      Data
                        -----   --- -----  ---     ---  ----    ----  --------      ----
   subscribe/dd_amis    idle    5/5    0    0    0.00s   n/a    0.0%     0m/s       0B/s
         Total Running Configs:   1/1 ( Processes: 5 missing: 0 stray: 0 )
                        Memory: uss:210.9MiB rss:288.9MiB vms:428.1MiB
                      CPU Time: User:2.34s System:0.18s
              Pub/Sub Received: 0m/s (0B/s), Sent:  0m/s (0B/s) Queued: 0 Retry: 0, Mean lag: 0.00s
                 Data Received: 0f/s (0B/s), Sent: 0f/s (0B/s)


   #####################################
   # Arrêter et désactiver l'abonné v2 #
   #####################################

   # Maintenant que sr3 a démarré, vous pouvez arrêter, nettoyer et désactiver votre abonné v2 :
   
   # sr_subscribe stop --> arrêter l'abonné v2
   sarra@mon-serveur:~$ sr_subscribe stop dd_amis
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 01 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 02 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 03 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 04 stopped
   2025-08-25 17:31:54,247 [INFO] sr_subscribe dd_amis 05 stopped


   # sr_subscribe cleanup --> nettoyer les fichiers dans ~/.cache/sarra et supprimer la file d'attente sur le courtier
   sarra@mon-serveur:~$ sr_subscribe cleanup dd_amis
   2025-08-25 17:32:49,264 [INFO] sr_subscribe dd_amis cleanup
   2025-08-25 17:32:49,264 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
   2025-08-25 17:32:49,264 [INFO] Using amqp module (AMQP 0-9-1)
   2025-08-25 17:32:49,282 [INFO] deleting queue q_anonymous.sr_subscribe.dd_amis.00483673.20371363 (anonymous@dd.weather.gc.ca)


   # sr status indique maintenant que l'abonné v2 est arrêté
   sarra@mon-serveur:~$ sr status
   status:
   Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
   ---------  -----      -----  --- ------------------------------
   audit      running    OK       1
   cpost      stopped    OK       0
   cpump      stopped    OK       0
   poll       stopped    OK       0
   post       stopped    OK       0
   report     stopped    OK       0
   sarra      stopped    OK       0
   sender     stopped    OK       0
   shovel     stopped    OK       0
   subscribe  stopped    OK       1 dd_amis
   watch      stopped    OK       0
   winnow     stopped    OK       0
         total running configs:   0 ( processes: 1 missing: 0 stray: 0 )


   # sr_subscribe disable --> Empêcher le lancement futur de la configuration v2
   # disable renomme le fichier de configuration de ...conf à ...conf.off
   #   Par exemple, ~/.config/sarra/subscribe/dd_amis.conf devient ~/.config/sarra/subscribe/dd_amis.conf.off
   sarra@mon-serveur:~$ sr_subscribe disable dd_amis


   # sr status indique maintenant que l'abonné v2 est supprimé/désactivé
   sarra@mon-serveur:~$ sr status
   status:
   Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
   ---------  -----      -----  --- ------------------------------
   audit      running    OK       1
   cpost      stopped    OK       0
   cpump      stopped    OK       0
   poll       stopped    OK       0
   post       stopped    OK       0
   report     stopped    OK       0
   sarra      stopped    OK       0
   sender     stopped    OK       0
   shovel     stopped    OK       0
   subscribe  stopped    OK       0
   watch      stopped    OK       0
   winnow     stopped    OK       0
         total running configs:   0 ( processes: 1 missing: 0 stray: 0 )

Vous devriez maintenant avoir un abonné sr3 fonctionnel ! Vous pouvez répéter la procédure 
ci-dessus autant de fois que nécessaire pour convertir toutes vos configurations v2
en sr3.

L'interface de ligne de commande sr3 accepte également *plusieurs combinaisons composant/configuration
simultanément* et les *caractères génériques* (wildcards), 
vous permettant ainsi de convertir toutes vos configurations en une seule
commande. Par exemple :

- ``sr3 convert subscribe/my_config1 poll/test_poll``
- ``sr3 convert 'subscribe/*'`` 
- ``sr3 convert '*/*'``

.. NOTE::

   La commande status de sr3 fournit des informations plus détaillées que la version 2.
   Pour une explication de chaque état possible, consultez le document
   `Command Line Guide <../Explication/GuideLigneDeCommande.html#status>`_.
