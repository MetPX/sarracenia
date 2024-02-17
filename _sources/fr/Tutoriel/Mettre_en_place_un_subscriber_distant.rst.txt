
====================================
Comment configurer un abonné distant
====================================

Cet exemple explique comment s’abonner aux fichiers swob du bureau météo d’Environnement Canada.


Mise en Place
~~~~~~~~~~~~~

Initialiser le stockage des informations d’identification dans le fichier `~/.config/sr3/credentials.conf` ::

  $ sr3 edit credentials.conf
    amqps://anonymous:anonymous@dd.weather.gc.ca

Le format est un URL complet sur chaque ligne (`amqps://<user>:<password>@<target.url>`).
Le fichier credentials.conf devrait être privé (permissions octale linux: 0600).  
Les fichiers .conf placés dans ``~/.config/sr3/subscribe_directory``seront automatiquement trouvé par ``sr_subscribe``, plutôt que de donner le chemin complet.

La commande *edit* démarre l’éditeur configuré par l’utilisateur sur le fichier à créer, dans le répertoire approprié::

  $ sr3 edit subscribe/swob.conf
    broker amqps://anonymous@dd.weather.gc.ca
    subtopic observations.swob-ml.#
    directory /tmp/swob_downloads
    accept .*
  $ mkdir /tmp/swob_downloads
  $ sr3 status subscribe/swob
    2017-12-14 06:54:54,010 [INFO] sr_subscribe swob 01 is stopped

.. ERROR::
  
  La modification actuelle échoue s’il n’y a pas de fichier à l’emplacement prévu
  (en fait, il ne crée pas de fichier)act, not create a file)
  Voir l'issue `#251 <https://github.com/MetPX/sarracenia/issues/251>`_ pour plus d’informations ou pour se plaindre.
  En attendant, utilisez plutôt::
  
    $ mkdir -p .config/sarra/subscribe
    $ touch $_/swob.conf
    $ sr3 edit swob.conf


*broker* indique où se connecter pour recevoir le flux de notifications.
Le terme *broker* est tiré de AMQP (http://www.amqp.org), le protocole utilisé pour transférer les notifications. 
Les notifications qui seront reçues ont toutes des *topics* qui correspondent à leur URL.

.. NOTE::

  Omettre ``directory`` du fichier de configuration écrira les fichiers dans le répertoire actuel.
  Compte tenu de la rapidité avec laquelle ils arrivent, soyez prêt à nettoyer.
 

Démarrage
~~~~~~~~~

Maintenant, démarrez l’abonné nouvellement créé::

  $ sr3 start swob
    2015-12-03 06:53:35,268 [INFO] user_config = 0 ../swob.conf
    2015-12-03 06:53:35,269 [INFO] instances 1 
    2015-12-03 06:53:35,270 [INFO] sr3 subscribe swob 0001 started


L’activité peut être surveillée via des fichiers journaux dans  ``~/.cache/sarra/log/`` ou avec la commande *log* ::

  $ sr3 log swob
    
    2015-12-03 06:53:35,635 [INFO] Binding queue q_anonymous.sr_subscribe.swob.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
    2015-12-03 17:32:01,834 [INFO] user_config = 1 ../swob.conf
    2015-12-03 17:32:01,835 [INFO] sr_subscribe start
    2015-12-03 17:32:01,835 [INFO] sr_subscribe run
    2015-12-03 17:32:01,835 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
    2015-12-03 17:32:01,835 [INFO] AMQP  input :    exchange(xpublic) topic(v02.post.observations.swob-ml.#)
    2015-12-03 17:32:01,835 [INFO] AMQP  output:    exchange(xs_anonymous) topic(v02.report.#)
    
    2015-12-03 17:32:08,191 [INFO] Binding queue q_anonymous.sr_subscribe.swob.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/


``[Ctrl] + [C]`` pour quitter la surveillance des journaux.
Le journal de démarrage semble normal, indiquant que les informations d’authentification ont été acceptées.
``sr_subscribe`` recevra la notification et téléchargera le fichier dans le répertoire actuel
(sauf indication contraire dans le fichier de configuration).


Un téléchargement normal ressemble à ceci ::

  2015-12-03 17:32:15,031 [INFO] Received topic   v02.post.observations.swob-ml.20151203.CMED
  2015-12-03 17:32:15,031 [INFO] Received notice  20151203223214.699 http://dd2.weather.gc.ca/observations/swob-ml/20151203/CMED/2015-12-03-2200-CMED-AUTO-swob.xml
  2015-12-03 17:32:15,031 [INFO] Received headers {'filename': '2015-12-03-2200-CMED-AUTO-swob.xml', 'parts': '1,3738,1,0,0', 'sum': 'd,157a9e98406e38a8252eaadf68c0ed60', 'source': 'metpx', 'to_clusters': 'DD,DDI.CMC,DDI.ED M', 'from_cluster': 'DD'}
  2015-12-03 17:32:15,031 [INFO] downloading/copying into ./2015-12-03-2200-CMED-AUTO-swob.xml 

Donner toutes les informations contenues dans la notification.
Voici un échec ::

  2015-12-03 17:32:30,715 [INFO] Downloads: http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml  into ./2015-12-03-2200-CXFB-AUTO-swob.xml 0-6791
  2015-12-03 17:32:30,786 [ERROR] Download failed http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml
  2015-12-03 17:32:30,787 [ERROR] Server couldn't fulfill the request. Error code: 404, Not Found

Ce message n’est pas toujours un échec car ``sr_subscribe`` tente à plusieurs reprises avant d’abandonner.
Après quelques minutes, voici à quoi ressemble le répertoire de téléchargement ::

  $ ls -al | tail
    -rw-rw-rw-  1 peter peter   7875 Dec  3 17:36 2015-12-03-2236-CL3D-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7868 Dec  3 17:37 2015-12-03-2236-CL3G-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7022 Dec  3 17:37 2015-12-03-2236-CTRY-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   6876 Dec  3 17:37 2015-12-03-2236-CYPY-AUTO-swob.xml
    -rw-rw-rw-  1 peter peter   6574 Dec  3 17:36 2015-12-03-2236-CYZP-AUTO-swob.xml
    -rw-rw-rw-  1 peter peter   7871 Dec  3 17:37 2015-12-03-2237-CL3D-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7873 Dec  3 17:37 2015-12-03-2237-CL3G-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7037 Dec  3 17:37 2015-12-03-2237-CTBF-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter   7022 Dec  3 17:37 2015-12-03-2237-CTRY-AUTO-minute-swob.xml
    -rw-rw-rw-  1 peter peter 122140 Dec  3 17:38 sr_subscribe_dd_swob_0001.log


Nettoyage
~~~~~~~~~

Pour ne pas télécharger plus de fichiers, arrêtez l’abonné ::
  
  $ sr_subscribe stop swob
    2015-12-03 17:32:22,219 [INFO] sr_subscribe swob 01 stopped

Cela laisse cependant la fil d’attente que ``sr_subscribe start`` a configuré sur le courtier active,
pour permettre à un abonné défaillant de tenter de se reconnecter sans perdre de progression.
C’est jusqu’à ce que le courtier expire la fil d’attente et la supprime.
Pour indiquer au courtier que nous avons terminé la fil d’attente, demandez à l’abonné de nettoyer ::

  $ sr_subscribe cleanup swob
  2015-12-03 17:32:22,008 [INFO] sr_subscribe swob cleanup
  2015-12-03 17:32:22,008 [INFO] AMQP broker(dd.weatheer.gc.ca) user(anonymous) vhost()
  2015-12-03 17:32:22,008 [INFO] Using amqp module (AMQP 0-9-1)
  2015-12-03 17:32:22,008 [INFO] deleting queue q_anonymous.sr_subscribe.swob.21096474.62787751 (anonymous@dd.weather.gc.ca)

La meilleure pratique consiste à effacer la fil d’attente lorsque terminé afin de réduire la charge sur le courtier.
