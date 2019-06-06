
=====================================
 Administration de MetPX-Sarracenia 
=====================================

.. Contents::


Revision Record
---------------

:version: @Version@
:date: @Date@


Conditions préalables
---------------------

Idéalement, il faut être familier avec l'accès des utilisateurs aux pompes 
existantes comme `subscriber <subscriber.rst>`_ ou `source <source.rst>`_ 
avant de procéder à l'administration.  Ce manuel se veut prescriptif plutôt 
qu'explicatif.  Pour les raisons pour lesquelles les choses sont
construit comme ils sont, veuillez consulter `Concepts.rst <Concepts.rst>`_`_.


Exigences minimales
~~~~~~~~~~~~~~~~~~~

Le courtier AMQP est extrêmement léger sur les serveurs d'aujourd'hui. Les 
exemples dans ce manuel a été implémenté sur un serveur privé virtuel 
commercial (VPS) avec 256 Mo de RAM, et 700 Mo de swap à partir d'un disque
de 20 Go. Un tel une configuration minuscule est capable de suivre une
alimentation presque complète à partir de dd.weather.gc.ca (qui comprend 
tous les services météorologiques et les services à l'intention du public).
données environnementales d'Environnement et changements climatiques Canada. 
gros fichiers de prédiction numérique (GRIB et plusieurs GRIB dans les 
fichiers tar) ont été exclus pour réduire l'utilisation de la bande 
passante, mais en termes de performance dans la transmission des messages, 
il a assez bien supporter un client.

Chaque processus Sarra représente environ 80 Mo de mémoire virtuelle, mais 
seulement 3 Mo environ est résident, et vous avez besoin d'en exécuter 
suffisamment pour suivre (sur le petit VPS,) donc environ 30 mégaoctets 
de RAM réellement utilisés. Le RAM du courtier est ce qui détermine le 
nombre de clients qui peuvent être servis. Plus lent les clients ont 
besoin de plus de RAM pour leurs files d'attente. Donc, s'occuper des tâches
de courtage et un nettoyage agressif peut réduire l'empreinte mémoire globale.
Le courtier était configuré pour utiliser 128 Mo de RAM dans les exemples de
ce manuel. Le reste de la RAM a été utilisé par les processus apache pour le
moteur de transport web.

Bien que ce qui précède soit adéquat pour la preuve de concept, le nombre 
de clients qui peuvent être soutenu est assez limitée. 1 Go de RAM pour 
tous les sarra relatifs à la sarra les activités devraient être suffisantes 
pour de nombreux cas utiles.


Opérations
----------

Pour faire fonctionner une pompe, un utilisateur doit être désigné comme 
administrateur. L'administrateur est différent des autres usagers, surtout en
ce qui concerne l'autorisation accordée de créer des échanges arbitraires, et
la capacité d'exécuter des processus qui envoient des avis à des échanges
communs (xpublic, xreport, etc....) Tous les autres utilisateurs sont limités
à la possibilité de n'accéder qu'à leurs propres ressources (échange et 
files d'attente).

Le nom d'utilisateur administratif est un choix d'installation, et exactement 
comme pour n'importe quel autre utilisateur. Les fichiers de configuration sont
placés sous ~/.config/sarra/, les fichiers de configuration sont placés 
sous ~/.config/sarra/, avec l'option par défaut sous admin.conf, et les 
configurations pour les composants sous les répertoires nommés d'après chaque
composant. Dans les répertoires des composants, Les fichiers de configuration
ont le suffixe.conf.

Les processus administratifs effectuent la validation des écritures à partir
des sources. Une fois ils sont validés, transmettent les messages aux bourses
publiques pour que les abonnés y aient accès.  Les processus qui sont 
généralement exécutés sur un courtier :

- sr_audit - purger les files d'attente inutiles, créer des échanges et des utilisateurs, définir les permissions des utilisateurs en fonction de leurs rôles.
- sr_poll - pour les sources qui ne produisent pas d´avis , retour au sondage
  explicite pour l'injection initiale de donneées.
- sr_sarra - diverses configurations pour extraire les données d'autres pompes 
  afin de les rendre disponibles à partir de la pompe locale.
- sr_sender - envoyer des données aux clients ou à d'autres pompes qui ne peuvent 
  pas s´abonner à la pompe locale (généralement à cause des pare-feu).
- sr_winnow - lorsqu'il y a plusieurs sources de données redondantes, sélectionner la première à arriver et alimenter sr_sarra.
- sr_shovel - copie des avis d'une pompe à une autre, généralement pour alimenter sr_winnow.

Comme pour tout autre utilisateur, il peut y avoir un nombre illimité de configurations.
à mettre en place, et il se peut qu'ils aient tous besoin de courir en même temps. Pour le faire facilement, on peut invoquer: :

  sr start

pour démarrer tous les fichiers avec les configurations nommées de chaque 
composant (sarra, subscribe, winnow, log, log, etc....) Il y a deux 
utilisateurs/rôles qui doivent être réglés pour utiliser une pompe. Ce sont
les options admin et feeder. Ils sont définis dans ~/.config/sarra/admin.conf 
comme suit::

  feeder amqp://pumpUser@localhost/
  admin  amqps://adminUser@boule.example.com/


Ensuite, les composants du rapport et de l'audit sont également lancés. Il est
la convention d'utiliser une utilisateur *feeder* (différente utilisateur 
administrateur AMQP) pour les movement d´avis et données à l´intérieur 
d´une pompe: des tâches de flux de données, telles que l'extraction et la 
comptabilisation des données, effectuées par l'utilisateur du serveur.
Normalement, on place les informations d'identification dans 
~/.config/sarra/credentials.conf et les tâches ponctuels tel la 
création d´un l'échange ou un utilisateurs, sont effectuées par l'administrateur.  


Entretien ménager - sr_audit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsqu'un client se connecte à un courtier, il crée une file d'attente qui est
ensuite liée à une bourse. L'utilisateur peut choisir d'avoir 
l'autodestruction du client lorsqu'il est déconnecté (*auto-delete*), ou il 
peut spécifier *durable* ce qui signifie qu'il doit rester, en attendant que 
le client se connecte à nouveau, même si le courtier ou serveur est reparti.
Les clients veulent souvent reprendre là où ils se sont arrêtés, de sorte que
les files d'attente doivent rester.

Le courtier rabbitmq ne détruira jamais une file d'attente qui n'est pas en
auto-delete (ou durable).  Ils s'accumuleront au fil du temps, alors sr_audit
périodiquement rechercher les files d'attente inutilisées et les nettoyer.
Actuellement, la valeur par défaut est que toute file d'attente inutilisée
ayant plus de 25000 messages sera supprimée.  On peut changer cette limite 
en ayant l'option *max_queue_size 50000* dans default.conf.


Excès de file d'attente/performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque rabbitmq a des centaines de milliers de messages en file d'attente, la
performance du courtier peut en souffrir. Un tel accumulation peuvent se 
produire lorsque la destination d'un expéditeur est en panne pour une période
prolongée, ou n'est pas disponible pour une raison quelconque. Dans de nombreux
cas, on peut simplement fermer l'expéditeur et supprimer la file d'attente du
courtier. Bien que cela résout le problème de la performance des courtiers, 
l'utilisateur ne recevra pas les avis. 

Pour éviter la perte de données, veuillez consulter la page de manuel 
`sr_sender(1) *DESTINATION INDISPONIBLE* <sr_sender.1.rst#destination-indisponible>`_
pour plus de détails sur les options de sauvegarde et de restauration. En bref, 
quand un expéditeur est placé en mode *Enregistrer*, plutôt que de tenter 
d'envoyer chaque fichier, les messages écrits sur un fichier disque. Lorsque 
l'utilisateur distant est de retour, on invoque le mode *restore*, et le 
fichier disque est relu, et les fichiers sont envoyés.  Dans les versions 
>= 2.18, il est logique d'enregistrer automatiquement les transferts échoués 
pour les réessayer plus tard, le rechargement de la file d'attente du courtier 
se fait automatiquement, de sorte qu'aucune intervention n'est nécessaire.

Dans le cas de composants autres qu'un expéditeur, veuillez consulter la 
section Sauvegarde/Restauration de QUEUE de la page de manuel sr_shovel(8). 
Il existe un mécanisme similaire utilisé pour écrire des messages en file 
d'attente sur le disque, pour éviter qu'ils surchargent le courtier. Lorsque 
le consommateur est de nouveau en service, L'option *restore_to_queue* peut 
être utilisée pour récupérer les messages manquants.

Si l'on arrive au point où le trafic à travers une file d'attente est excessif
(plusieurs centaines de messages par seconde à une seule file d'attente), 
surtout s'il y a plusieurs instances partageant la même file d'attente.
(si plus de 40 instances pour desservir une seule file d'attente) alors on
peut se heurter à un point où l'ajout d'instances n'améliore pas le débit
global. Par exemple, rabbitmq utilise un seul processeur pour servir une file
d'attente. Dans de tels cas, la création de configurations multiples,
(chacun avec sa propre file d'attente) diviser le trafic entre eux permettra
d'autres améliorations de débit.

sr_winnow est utilisé pour supprimer les doublons.  **Notez que le cache de
 suppression des doublons est local pour chaque instance**. Lorsque N instances
partagent une file d'attente, la première fois qu'un message est reçu, il 
pourrait être choisi par une instance, et si un duplicata est reçu  il 
serait probablement pris en charge par une autre instance. **Pour une suppression
efficace des doublons avec les instances**, il faut **déployer deux couches 
d'abonnés**. Utiliser une **première couche d'abonnés (sr_shovels)** 
avec la suppression de doublons désactivée et avec *post_exchange_split*, qui 
route les messages par checksum jusqu'à une **seconde couche de 
d'abonnées (sr_winnow) dont les caches de suppression de doublons sont actives.**



Routage
-------

L'interconnexion de plusieurs pompes se fait, côté données, par chaînage en guirlande.
sr_sarra et/ou sr_sender d'une pompe à l'autre.

les en-têtes *to_clusters* et *source* sont utilisés pour les décisions de routage.
implémenté dans les plugins *msg_to_clusters*, et *msg_by_source* respectivement.
d'être utilisateur par émetteur ou par composants sarra pour limiter les 
transferts de données entre pompes.

Pour la gamme d'états, l'en-tête *from_cluster* est interprété par l'attribut
*msg_from_cluster* plugin. Les messages de rapport sont définis dans la page
de manuel `sr_report(7) <sr_report.1.rst>`_ Ils sont émis par les 
*consommateurs* à la fin, ainsi que par les *feeders* comme les les messages
traversent les pompes. Les messages de rapport sont envoyés à l'échange 
xs\_<user> exchange, et après validation envoyée à l'échange xreport par 
des configurations shovel créées par sr_audit.



Que se passe-t-il ?
-------------------

La commande sr_report peut être invoquée pour lier à 'xreport' au lieu de 
l'échange d'utilisateurs par défaut pour obtenir des informations de 
rapport pour l'ensemble d'un courtier.

La configuration sr_report avec une action *on_message* peut être configurée pour
recueillir de l'information statistique. 

.. NOTE: :
   FIXME:**FIXME:** la première configuration sr_report en conserve serait speedo.....
   speedo : taux total de poteaux/seconde, taux total de logs/seconde.
   question : les messages doivent-ils aussi aller dans le journal ?
   avant les opérations, nous devons trouver comment Nagios va le surveiller.

   Est-ce que tout cela est nécessaire, ou est-ce que l'interface utilisateur 
   graphique du lapin est suffisante ?



Intégration Init
~~~~~~~~~~~~~~~~

Par défaut, lorsque sarracenia est installé, il s'agit d'un outil utilisateur 
et non d'une ressource à l'échelle du système. Le répertoire 
tools/sous-répertoire permet l'intégration avec des outils pour différents
scénarios d'utilisation.


.. NOTE::
   tools/sr.init -- script pour sysv-init où upstart 
   tools/sarra_system.service -- pour systemd et déploiment système
   tools/sarra_user.service -- pour systemd par usage.


Processus d'installation du système, par l'administrateur::


   groupadd sarra
   useradd sarra
   cp tools/sarra_system.service /etc/systemd/system/sarra.service  (if a package installs it, it should go in /usr/lib/systemd/system )
   cp tools/sarra_user.service /etc/systemd/user/sarra.service (or /usr/lib/systemd/user, if installed by a package )
   systemctl daemon-reload
  
Il est alors supposé que l'on utilise le compte 'sarra' pour 
stocker la configuration sarra orientée démon (ou à l'échelle du système).
Les utilisateurs peuvent également exécuter leur configuration personnelle 
dans les sessions via::

  systemctl --user enable sarra
  systemctl --user start sarra

Sur un système basé sur upstart ou sysv-init::

  cp tools/sr.init /etc/init.d/sr
  <insérer la magic pour le faire activer.>


Installation Rabbitmq Rabbitmq
------------------------------

Exemple d'information sur l´implantation d'un courtier rabbitmq pour Sarracenia. Le 
courtier n'est pas tenu de être sur le même hôte que n'importe quoi d'autre, 
mais il doit y être accessible à partir d'au moins l'un de ces hôtes
moteurs de transport.

Installation
~~~~~~~~~~~~

D'une manière générale, nous voulons rester au-dessus de la version 3.x.

https://www.rabbitmq.com/install-debian.html

Brièvement::


 apt-get update
 apt-get install erlang-nox
 apt-get install rabbitmq-server

Ou bien prendre la version d´un ubuntu actuel.


WebUI
~~~~~

Sr_audit utilise une variété d'appels à l'interface de gestion web.
sr_audit est le composant qui, comme son nom l'indique, audite les 
configurations pour les files d'attente restantes ou les tentatives
d'utilisation malveillante. Sans ce genre de l'audit, le passage est
susceptible d'accumuler rapidement des messages, qui le ralentit 
davantage au fur et à mesure que le nombre de messages en attente
augmente potentiellement débordant sur le disque.

Fondamentalement, à partir d'un shell administrative, il faut::

 rabbitmq-plugins enable rabbitmq_management rabbitmq_management

qui activera l'interface web pour le courtier. Pour empêcher l'accès 
à la gestion interface pour les indésirables, l'utilisation de 
pare-feu, ou l'écoute uniquement de localhost interface pour 
la gestion ui est suggérée.


TLS
~~~

Il faut crypter le trafic des courtiers. L'obtention de certificats
n'entre pas dans le champ d'application de ces instructions, de 
sorte qu'il n'est pas discuté en détail. Aux fins de l'exemple, 
une méthode consiste à obtenir des certificats à partir 
de `letsencrypt <http://www.letsencrypt.org>`http://www.letsencrypt.org>`_ ::


    root@boule:~# git clone https://github.com/letsencrypt/letsencrypt
    Cloning into 'letsencrypt'...
    remote: Counting objects: 33423, done.
    remote: Total 33423 (delta 0), reused 0 (delta 0), pack-reused 33423
    Receiving objects: 100% (33423/33423), 8.80 MiB | 5.74 MiB/s, done.
    Resolving deltas: 100% (23745/23745), done.
    Checking connectivity... done.
    root@boule:~# cd letsencrypt
    root@boule:~/letsencrypt#
    root@boule:~/letsencrypt# ./letsencrypt-auto certonly --standalone -d boule.example.com
    Checking for new version...
    Requesting root privileges to run letsencrypt...
       /root/.local/share/letsencrypt/bin/letsencrypt certonly --standalone -d boule.example.com
    IMPORTANT NOTES:
     - Congratulations! Your certificate and chain have been saved at
       /etc/letsencrypt/live/boule.example.com/fullchain.pem. Your
       cert will expire on 2016-06-26. To obtain a new version of the
       certificate in the future, simply run Let's Encrypt again.
     - If you like Let's Encrypt, please consider supporting our work by:

       Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
       Donating to EFF:                    https://eff.org/donate-le

    root@boule:~# ls /etc/letsencrypt/live/boule.example.com/
    cert.pem  chain.pem  fullchain.pem  privkey.pem
    root@boule:~#


Ce processus produit des fichiers clés lisibles uniquement par root. Pour faire les fichiers
lisible par le courtier (qui fonctionne sous le nom d'utilisateur rabbitmq) on aura
pour ajuster les permissions afin de permettre au courtier de lire les fichiers.
probablement que la façon la plus simple de le faire est de les copier ailleurs::


    root@boule:~# cd /etc/letsencrypt/live/boule*
    root@boule:/etc/letsencrypt/archive# mkdir /etc/rabbitmq/boule.example.com
    root@boule:/etc/letsencrypt/archive# cp -r * /etc/rabbitmq/boule.example.com
    root@boule:~# cd /etc/rabbitmq
    root@boule:~# chown -R rabbitmq.rabbitmq boule*

Maintenant que nous avons la bonne chaîne de certificats, configurez 
rabbitmq pour utilisez que le `RabbitMQ TLS Support <https://www.rabbitmq.com/ssl.rst>`https://www.rabbitmq.com/ssl.rst>`_ (voir
également `RabbitMQ Management <https://www.rabbitmq.com/management.rst>`_)::


    root@boule:~#  cat >/etc/rabbitmq/rabbitmq.config <<EOT

    [
      {rabbit, [
         {tcp_listeners, [{"127.0.0.1", 5672}]},
         {ssl_listeners, [5671]},
         {ssl_options, [{cacertfile,"/etc/rabbitmq/boule.example.com/fullchain.pem"},
                        {certfile,"/etc/rabbitmq/boule.example.com/cert.pem"},
                        {keyfile,"/etc/rabbitmq/boule.example.com/privkey.pem"},
                        {verify,verify_peer},
                        {fail_if_no_peer_cert,false}]}
       ]}
      {rabbitmq_management, [{listener,
         [{port,     15671},
               {ssl,      true},
               {ssl_opts, [{cacertfile,"/etc/rabbitmq/boule.example.com/fullchain.pem"},
                              {certfile,"/etc/rabbitmq/boule.example.com/cert.pem"},
                              {keyfile,"/etc/rabbitmq/boule.example.com/privkey.pem"} ]}
         ]}
      ]}
    ].

    EOT


Maintenant, le courtier et l'interface de gestion sont configurés pour 
crypter tout le trafic entre le client et le courtier. Un écouteur non crypté
a été configuré pour localhost, où le cryptage sur la machine locale est
inutile, et ajoute la charge du processeur. Mais la direction seulement
a un seul écouteur crypté configuré.

.. NOTE::

  Actuellement, sr_audit sr_audit s'attend à ce que l'interface de gestion 
  soit sur le port 15671 si elle est cryptée, 15672 sinon. Sarra n'a pas de
  réglage de configuration pour lui dire le contraire. Choisir un autre
  port brisera sr_audit. **FIXME**.


Modifier les valeurs par défaut
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Afin d'effectuer des changements de configuration, le courtier doit être en 
cours d'exécution. Il faut démarrer le courtier rabbitmq. Sur les systèmes 
ubuntu plus anciens, cela serait fait par::

  service rabbitmq-server start

Sur les nouveaux systèmes avec systemd, la meilleure méthode est::

  systemctl start rabbitmq-server

Par défaut, l'installation d'un serveur rabbitmq fait de l'utilisateur guest l'administrateur.... avec mot de passe guest.
Avec un serveur rabbitmq en cours d'exécution, on peut maintenant changer cela pour une implémentation opérationnelle.....
Pour annuler l'utilisateur invité, nous suggérons::

  rabbitmqctl delete_user guest

Un autre administrateur doit être défini.... appelons-le *bunnymaster*, en fixant le mot de passe à *MaestroDelConejito*... ::


  root@boule:~# rabbitmqctl add_user bunnymaster MaestroDelConejito
  Creating user "bunnymaster" ...
  ...done.
  root@boule:~#

  root@boule:~# rabbitmqctl set_user_tags bunnymaster administrator
  Setting tags for user "bunnymaster" to [administrator] ...
  ...done.
  root@boule:~# rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
  Setting permissions for user "bunnymaster" in vhost "/" ...
  ...done.
  root@boule:~#


Créez un compte linux local sous lequel les tâches administratives de sarra s'exécuteront (disons Sarra).
C'est là que les informations d'identification et la configuration pour les activités au niveau de la pompe seront stockées.
Comme la configuration est maintenue avec cet utilisateur, on s'attend à ce qu'il soit utilisé activement.
par les humains, et devrait donc avoir un environnement de coquille interactif approprié. Un peu d'administration
l'accès est nécessaire, donc l'utilisateur est ajouté au groupe sudo::

  root@boule:~# useradd -m sarra
  root@boule:~# usermod -a -G sudo sarra
  root@boule:~# mkdir ~sarra/.config
  root@boule:~# mkdir ~sarra/.config/sarra

d'abord besoin d'entrées dans les fichiers credentials.conf et admin.conf::


  root@boule:~# echo "amqps://bunnymaster:MaestroDelConejito@boule.example.com/" >~sarra/.config/sarra/credentials.conf
  root@boule:~# echo "admin amqps://bunnymaster@boule.example.com/" >~sarra/.config/sarra/admin.conf
  root@boule:~# chown -R sarra.sarra ~sarra/.config
  root@boule:~# passwd sarra
  Enter new UNIX password:
  Retype new UNIX password:
  passwd: password updated successfully
  root@boule:~#
  root@boule:~# chsh -s /bin/bash sarra  # for comfort

l'aide de TLS (aka amqps), la vérification empêche l'utilisation 
de *localhost*  même pour l'accès sur la machine locale, le nom d'hôte 
pleinement qualifié doit être utilisé.  Suivant::


  root@boule:~#  cd /usr/local/bin
  root@boule:/usr/local/bin# wget https://boule.example.com:15671/cli/rabbitmqadmin
  --2016-03-27 23:13:07--  https://boule.example.com:15671/cli/rabbitmqadmin
  Resolving boule.example.com (boule.example.com)... 192.184.92.216
  Connecting to boule.example.com (boule.example.com)|192.184.92.216|:15671... connected.
  HTTP request sent, awaiting response... 200 OK
  Length: 32406 (32K) [text/plain]
  Saving to: ‘rabbitmqadmin’

  rabbitmqadmin              100%[=======================================>]  31.65K  --.-KB/s   in 0.04s

  2016-03-27 23:13:07 (863 KB/s) - ‘rabbitmqadmin’ saved [32406/32406]

  root@boule:/usr/local/bin#
  root@boule:/usr/local/bin# chmod 755 rabbitmqadmin


Il est nécessaire de télécharger *rabbitmqadmin*, une commande 
d'aide qui est incluse dans RabbitMQ, mais qui n'est pas installée 
automatiquement.  Il faut le télécharger à partir de l'interface de 
gestion, et le placer dans un emplacement raisonnable dans le chemin 
d'accès, donc qu'il sera trouvé lorsqu'il est appelé par sr_admin::

  root@boule:/usr/local/bin# su - sarra

A partir de ce point, la racine n'est généralement pas nécessaire, car toute
la configuration peut être effectuée à partir du compte *sarra* non privilégié.

.. NOTE: :
   Hors de la portée de cette discussion, mais à part les permissions du système de fichiers,
   il est pratique de permettre à l'utilisateur de sarra sudo d'accéder à rabbitmqctl.
   Grâce à cela, l'ensemble du système peut être administré sans accès administratif au système.

Gestion des utilisateurs d'une pompe à l'aide de Sr_audit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour configurer une pompe, on a besoin d'un utilisateur administratif courtier
(dans les exemples : sarra.). et un utilisateur de feeder (dans les exemples: 
feeder.) La gestion des autres utilisateurs se fait à l'aide de le programme
sr_audit.

Tout d'abord, écrivez les informations d'identification correctes pour les 
utilisateurs admin et feeder dans le fichier le fichier 
credentials.config/sarra/credentials.conf ::

 amqps://bunnymaster:MaestroDelConejito@boule.example.com/
 amqp:///feeder:NoHayPanDuro@localhost/localhost
 amqps://feeder:NoHayPanDuro@boule.example.com/
 amqps://anonymous:anonyomous@boule.example.com/
 amqps://peter:piper@boule.example.com/

Notez que les informations d'identification du serveur sont présentées deux
fois, une fois pour permettre un accès non crypté par l'intermédiaire de
localhost, et une deuxième fois pour permettre l'accès par TLS, potentiellement
à partir d'autres hôtes (nécessaire) lorsqu'un courtier opère dans un cluster,
avec des processus d'alimentation fonctionnant sur plusieurs transports nœuds
du moteur.) L'étape suivante est de mettre les rôles 
dans .config/sarra/admin.conf ::


 admin  amqps://root@boule.example.com/
 feeder amqp://feeder@localhost/


Spécifiez tous les utilisateurs connus que vous voulez implémenter avec leurs rôles.
dans le fichier .config/sarra/admin.conf ::


 declare subscriber anonymous
 declare source peter



Maintenant, pour configurer la pompe, exécutez ce qui suit: :


 *sr_audit --users foreground*

resultat::

  sarra@boule:~/.config/sarra$ sr_audit foreground --debug --users 
  2016-03-28 00:41:25,380 [INFO] sr_audit start
  2016-03-28 00:41:25,380 [INFO] sr_audit run
  2016-03-28 00:41:25,380 [INFO] sr_audit waking up
  2016-03-28 00:41:25,673 [INFO] adding user feeder
  2016-03-28 00:41:25,787 [INFO] permission user 'feeder' role feeder  configure='.*' write='.*' read='.*'
  2016-03-28 00:41:25,897 [INFO] adding user peter
  2016-03-28 00:41:26,018 [INFO] permission user 'peter' role source  configure='^q_peter.*' write='^q_peter.*|^xs_peter_.*|^xs_peter_.*' read='^q_peter_.*|^xl_peter$|^.*xpublic$'
  2016-03-28 00:41:26,136 [INFO] adding user anonymous
  2016-03-28 00:41:26,247 [INFO] permission user 'anonymous' role source  configure='^q_anonymous.*' write='^q_anonymous.*|^xs_anonymous$' read='^q_anonymous.*|^xpublic$'
  2016-03-28 00:41:26,497 [INFO] adding exchange 'xreport'
  2016-03-28 00:41:26,610 [INFO] adding exchange 'xpublic'
  2016-03-28 00:41:26,730 [INFO] adding exchange 'xs_peter'
  2016-03-28 00:41:26,854 [INFO] adding exchange 'xl_peter'
  2016-03-28 00:41:26,963 [INFO] adding exchange 'xs_anonymous'
  sarra@boule:~/.config/sarra$

Le programme *sr_audit* :

- utilise le compte *admin* de .config/sarra/admin.conf pour s'authentifier auprès du courtier.
- crée des échanges *xpublic* et *xreport* s'ils n'existent pas.
- lit les rôles dans .config/sarra/admin.conf.
- obtient une liste d'utilisateurs et d'échanges sur la pompe.
- pour chaque utilisateur dans une option *déclarer*::

      déclarer l'utilisateur sur le courtier s'il manque.
      définir les permissions utilisateur correspondant à son rôle (lors de la création)
      créer des échanges d'utilisateurs correspondant à son rôle

- les utilisateurs qui n'ont pas de rôle déclaré sont supprimés.
- les échanges d'utilisateurs qui ne correspondent pas aux rôles des utilisateurs sont supprimés ('xl\_*,xs\_*,xs\_*')
- les échanges qui ne commencent pas par "x" (à l'exception de ceux qui sont intégrés) sont supprimés.

On peut inspecter si la commande sr_audit a fait tout ce qu'elle devait faire en utilisant l'interface graphique de gestion.
ou l'outil en ligne de commande::

  sarra@boule:~$ sudo rabbitmqctl  list_exchanges
  Listing exchanges ...
    direct
  amq.direct    direct
  amq.fanout    fanout
  amq.headers   headers
  amq.match headers
  amq.rabbitmq.log  topic
  amq.rabbitmq.trace    topic
  amq.topic topic
  xl_peter  topic
  xreport   topic
  xpublic   topic
  xs_anonymous  topic
  xs_peter  topic
  ...done.
  sarra@boule:~$
  sarra@boule:~$ sudo rabbitmqctl  list_users
  Listing users ...
  anonymous []
  bunnymaster   [administrator]
  feeder    []
  peter []
  ...done.
  sarra@boule:~$ sudo rabbitmqctl  list_permissions
  Listing permissions in vhost "/" ...
  anonymous ^q_anonymous.*  ^q_anonymous.*|^xs_anonymous$   ^q_anonymous.*|^xpublic$
  bunnymaster   .*  .*  .*
  feeder    .*  .*  .*
  peter ^q_peter.*  ^q_peter.*|^xs_peter$   ^q_peter.*|^xl_peter$|^xpublic$
  ...done.
  sarra@boule:~$

De ce qui précède, il semble que *sr_audit* a fait son travail.
En bref, voici les permissions et les échanges *sr_audit* gère::


  admin user : le seul à créer des utilisateurs......
  utilisateurs admin/feeder : ont tous les droits sur les files d'attente et les échanges.

  subscribe user : permet d'écrire des messages de rapport à échanger en commençant par xs_<brokerUser>>. 
                      peut lire les messages de l'échange xpublic xpublic
                      ont toutes les permissions sur la file d'attente nommé q_<brokerUser>*.

  utilisateur source : peut écrire des messages aux échanges commençant par xs_<brokerUser>>. 
                      peut lire les messages de l'échange xpublic xpublic
                      peut lire les messages de rapport de l'échange xl_<brokerUser> créé pour lui
                      ont toutes les permissions sur la file d'attente nommé q_<brokerUser>*.


Pour ajouter Alice en utilisant sr_audit, on ajouterait ce qui suit à ~/.config/sarra/admin.conf ::

  declare source Alice

puis ajoutez une entrée amqp appropriée dans ~/.config/sarra/credentials.conf pour définir le mot de passe,
puis lancez::

  sr_audit --users foreground 

Pour supprimer des utilisateurs, il suffit de supprimer *declare source Alice* du fichier admin.conf, et d'exécuter::

  sr_audit --users foreground 


Premier abonnement
~~~~~~~~~~~~~~~

Lors de la configuration d'une pompe, le but est normalement de la connecter à une autre pompe. Pour régler
le paramétrage d'un abonnement nous aide à paramétrer les paramètres pour sarra plus tard. Donc d'abord
essayer un abonnement à une pompe amont::


  sarra@boule:~$ ls
  sarra@boule:~$ cd ~/.config/sarra/
  sarra@boule:~/.config/sarra$ mkdir subscribe
  sarra@boule:~/.config/sarra$ cd subscribe
  sarra@boule:~/.config/sarra/subscribe$ sr_subscribe edit dd.conf 
  broker amqps://anonymous@dd.weather.gc.ca/

  mirror True
  directory /var/www/html

  # numerical weather model files will overwhelm a small server.
  reject .*/\.tar
  reject .*/model_giops/.*
  reject .*/grib2/.*

  accept .*

ajouter le mot de passe de la pompe amont dans credentials.conf ::


  sarra@boule:~/.config/sarra$ echo "amqps://anonymous:anonymous@dd.weather.gc.ca/" >>../credentials.conf

puis faites un court passage au premier plan, pour voir si ça marche. Appuyez sur Ctrl-C pour l'arrêter après quelques messages::


  sarra@boule:~/.config/sarra$ sr_subscribe foreground dd
  2016-03-28 09:21:27,708 [INFO] sr_subscribe start
  2016-03-28 09:21:27,708 [INFO] sr_subscribe run
  2016-03-28 09:21:27,708 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-03-28 09:21:28,375 [INFO] Binding queue q_anonymous.sr_subscribe.dd.78321126.82151209 with key v02.post.# from exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  2016-03-28 09:21:28,933 [INFO] Received notice  20160328130240.645 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml
  2016-03-28 09:21:29,297 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CWRM 20160328130240.645 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml 201 boule.example.com anonymous 1128.560235 parts=1,6451,1,0,0 sum=d,f17299b2afd78ae8d894fe85d3236488 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:29,389 [INFO] Received notice  20160328130240.646 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml
  2016-03-28 09:21:29,662 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CWSK 20160328130240.646 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml 201 boule.example.com anonymous 1128.924688 parts=1,7041,1,0,0 sum=d,8cdc3420109c25910577af888ae6b617 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:29,765 [INFO] Received notice  20160328130240.647 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml
  2016-03-28 09:21:30,045 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CWWA 20160328130240.647 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml 201 boule.example.com anonymous 1129.306662 parts=1,7027,1,0,0 sum=d,aabb00e0403ebc9caa57022285ff0e18 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:30,138 [INFO] Received notice  20160328130240.649 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml
  2016-03-28 09:21:30,431 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CXVG 20160328130240.649 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml 201 boule.example.com anonymous 1129.690082 parts=1,7046,1,0,0 sum=d,186fa9627e844a089c79764feda781a7 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:30,524 [INFO] Received notice  20160328130240.964 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/CA/CWAO/13/CACN00_CWAO_281300__TBO_05037
  ^C2016-03-28 09:21:30,692 [INFO] signal stop
  2016-03-28 09:21:30,693 [INFO] sr_subscribe stop


La connexion à l'amont est donc fonctionnelle. La connexion au serveur signifie
qu'une file d'attente est allouée sur le serveur, et il continuera à accumuler 
des messages, en attendant que le client se connecte à nouveau. Ce n'était qu'un test
alors on veut que le serveur supprime la file d'attente::


  sarra@boule:~/.config/sarra/subscribe$ sr_subscribe cleanup dd

permet maintenant de s'assurer que l'abonnement ne démarre pas automatiquement::

  sarra@boule:~/.config/sarra/subscribe$ mv dd.conf dd.off

et se tourner vers une application de sarra. 

Sarra d'une autre pompe
~~~~~~~~~~~~~~~~~~~~~~~

Sarra est utilisé pour permettre à une pompe en aval de ré-annoncer des 
produits à partir d'une pompe en amont. Sarra a besoin de toute la
configuration d'un abonnement, mais a aussi besoin de la configuration pour
poster vers le courtier en aval. Le compte d'alimentation du courtier est
utilisé pour ce travail, et est un utilisateur semi-administratif, capable 
de publier des avis à n'importe quel échange. Supposons qu'Apache est 
configuré (non couvert ici) avec un racine du document /var/www/html. Le 
compte linux que nous avons créé pour exécuter tous les processus sr est'*sarra*'.
la racine du document est inscriptible dans ces processus::

  sarra@boule:~$ cd ~/.config/sarra/sarra
  sarra@boule:~/.config/sarra/sarra$ sudo chown sarra.sarra /var/www/html

Ensuite, nous créons une configuration: :


  sarra@boule:~$ cat >>dd.off <<EOT

  broker amqps://anonymous@dd.weather.gc.ca/
  exchange xpublic

  gateway_for DD

  mirror False  # usually True, except for this server!

  # Numerical Weather Model files will overwhelm a small server.
  reject .*/\.tar
  reject .*/model_giops/.*
  reject .*/grib2/.*

  directory /var/www/html
  accept .*

  url http://boule.example.com/
  document_root /var/www/html
  post_broker amqps://feeder@boule.example.com/

  EOT

Par rapport à l'exemple précédent, Nous avons ajouté :

exchange xpublic
  sarra est souvent utilisé pour les transferts spécialisés, de sorte que l'échangexpublic n'est pas supposé, comme c'est le cas pour les abonnements.

msg_to_clusters DD

on_message msg_to_clusters

   sarra implémente le routage par cluster, donc si les données ne sont pas destinées à ce cluster, il sautera (et non pas téléchargera) un produit.
   L'inspection de la sortie sr_subscribe ci-dessus révèle que les produits sont destinés à la grappe DD.
   pour cela, afin que le téléchargement se fasse.

url et document_root
   ces derniers sont nécessaires pour construire les postes locaux qui seront affichés sur le ....

post_broker
   où nous annoncerons à nouveau les fichiers que nous avons téléchargés.

miroir Faux
  Ceci n'est généralement pas nécessaire, quand on copie entre pompes, il est normal de faire des copies directes.
  Cependant, la pompe dd.weather.gc.ca est antérieure à la norme du préfixe jour/source.
  facilité de nettoyage.


alors essayez-le::

  sarra@boule:~/.config/sarra/sarra$ sr_sarra foreground dd.off 
  2016-03-28 10:38:16,999 [INFO] sr_sarra start
  2016-03-28 10:38:16,999 [INFO] sr_sarra run
  2016-03-28 10:38:17,000 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-03-28 10:38:17,604 [INFO] Binding queue q_anonymous.sr_sarra.dd.off with key v02.post.# from exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  2016-03-28 10:38:19,172 [INFO] Received v02.post.bulletins.alphanumeric.20160328.UA.CWAO.14 '20160328143820.166 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422' parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM
  2016-03-28 10:38:19,172 [INFO] downloading/copying into /var/www/html/bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422
  2016-03-28 10:38:19,515 [INFO] 201 Downloaded : v02.report.bulletins.alphanumeric.20160328.UA.CWAO.14 20160328143820.166 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422 201 boule.bsqt.example.com anonymous -0.736602 parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM message=Downloaded
  2016-03-28 10:38:19,517 [INFO] Published: '20160328143820.166 http://boule.bsqt.example.com/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422' parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM
  2016-03-28 10:38:19,602 [INFO] 201 Published : v02.report.bulletins.alphanumeric.20160328.UA.CWAO.14.UANT01_CWAO_281438___22422 20160328143820.166 http://boule.bsqt.example.com/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422 201 boule.bsqt.example.com anonymous -0.648599 parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM message=Published
  ^C2016-03-28 10:38:20,328 [INFO] signal stop
  2016-03-28 10:38:20,328 [INFO] sr_sarra stop
  sarra@boule:~/.config/sarra/sarra$


Le fichier a le suffixe 'off' de sorte qu'il ne sera pas invoqué par défaut lorsque 
toute la configuration de sarra est démarrée. On peut toujours démarrer le fichier 
quand il est dans le réglage off, en spécifiant le chemin (dans ce cas, il est dans
le répertoire courant) donc initialement avoir des fichiers 'off' pendant le 
débogage des paramètres. Comme la configuration fonctionne correctement, 
renommez-la pour qu'elle soit utilisée au démarrage::

  sarra@boule:~/.config/sarra/sarra$ mv dd.off dd.conf
  sarra@boule:~/.config/sarra/sarra$



Rapports
~~~~~~~~

Maintenant que les données circulent, nous devons jeter un coup d'oeil au 
flux des messages de rapport, qui sont essentiellement utilisés par chaque
pompe pour indiquer en amont que les données ont été téléchargées. Sr_audit
aide au routage en créant les configurations suivantes:

- Pour chaque abonné, une configuration de pelle nommée rr_<user>2xreport.conf est créée.
- Pour chaque source, une configuration de pelle nommée rr_xreport2<user>user>user.conf est créée.

Les pelles *2xreport* s'abonne aux messages postés dans l'échange xs_ de 
chaque utilisateur et les poste à l'échange xreport commun. Exemple de fichier 
de configuration::

  # Configuration du routage du rapport initial créé par sr_audit, ajuster au goût.
  #  Pour récupérer l'original, supprimez simplement ce fichier, et lancez sr_audit (ou attendez quelques minutes)
  # Pour supprimer le routage des rapports, renommez ce fichier en rr_anonymous2xreport.conf.conf.off.  

  broker amqp://tfeed@localhost/
  exchange xs_anonymous
  topic_prefix v02.report
  subtopic #
  accept_unmatch True
  on_message None
  on_post None
  report_back False
  post_broker amqp://tfeed@localhost/
  post_exchange xreport

Explications :
  - Les pelles de routage de rapports sont des fonctions administratives, et c'est donc l'utilisateur de l'alimentateur qui est utilisé.
  - Cette configuration permet d'acheminer les rapports soumis par l'utilisateur " anonyme ".
  - on_message None, on_post None, réduire la journalisation non désirée sur le système local.
  - report_back Faux réduire les rapports non désirés (les sources veulent-elles comprendre la circulation des pelleteuses ?
  - poster sur l'échange xreport.

Les pelles *2<user>* regardent tous les messages dans l'échange xreport, et les copient aux utilisateurs xr\_ exchange.
Échantillon: :

  # Routage du rapport initial vers la configuration des sources, par sr_audit, réglage au goût. 
  # Pour récupérer l'original, supprimez simplement ce fichier, et lancez sr_audit (ou attendez quelques minutes)
  # Pour supprimer le routage des rapports, renommez ce fichier en rr_xreport2tsource2tsource2.conf.off.  

  
  broker amqp://tfeed@localhost/
  exchange xreport
  topic_prefix v02.report
  subtopic #
  accept_unmatch True
  msg_by_source tsource2
  on_message msg_by_source
  on_post None
  report_back False
  post_broker amqp://tfeed@localhost/
  post_exchange xr_tsource2


Explications :
  msg_by_source tsource2 sélectionne que seuls les rapports pour les données 
  injectées par l'utilisateur tsource2 doivent être sélectionnés.
  les rapports sélectionnés doivent être copiés dans l'échange xr\_ de 
  l'utilisateur, où l'utilisateur qui invoque sr_report les trouvera.

Lorsqu'une source invoque le composant sr_report, l'échange par défaut sera 
xr\_ (eXchange for Reporting). Tous les rapports reçus des abonnés aux données
de cette source seront acheminées vers cet échange.

Si un administrateur invoque sr_report, il sera par défaut sur l'échange 
xreport, et affichera les rapports de tous les abonnés sur le cluster.

Exemple::

  blacklab% more boulelog.conf

  broker amqps://feeder@boule.example.com/
  exchange xreport
  accept .*

  blacklab%

  blacklab% sr_report foreground boulelog.conf 
  2016-03-28 16:29:53,721 [INFO] sr_report start
  2016-03-28 16:29:53,721 [INFO] sr_report run
  2016-03-28 16:29:53,722 [INFO] AMQP  broker(boule.example.com) user(feeder) vhost(/)
  2016-03-28 16:29:54,484 [INFO] Binding queue q_feeder.sr_report.boulelog.06413933.71328785 with key v02.report.# from exchange xreport on broker amqps://feeder@boule.example.com/
  2016-03-28 16:29:55,732 [INFO] Received notice  20160328202955.139 http://boule.example.com/ radar/CAPPI/GIF/XLA/201603282030_XLA_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.040751
  2016-03-28 16:29:56,393 [INFO] Received notice  20160328202956.212 http://boule.example.com/ radar/CAPPI/GIF/XMB/201603282030_XMB_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.159043
  2016-03-28 16:29:56,479 [INFO] Received notice  20160328202956.179 http://boule.example.com/ radar/CAPPI/GIF/XLA/201603282030_XLA_CAPPI_1.0_SNOW.gif 201 blacklab anonymous 0.143819
  2016-03-28 16:29:56,561 [INFO] Received notice  20160328202956.528 http://boule.example.com/ radar/CAPPI/GIF/XMB/201603282030_XMB_CAPPI_1.0_SNOW.gif 201 blacklab anonymous -0.119164
  2016-03-28 16:29:57,557 [INFO] Received notice  20160328202957.405 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01910 201 blacklab anonymous -0.161522
  2016-03-28 16:29:57,642 [INFO] Received notice  20160328202957.406 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01911 201 blacklab anonymous -0.089808
  2016-03-28 16:29:57,729 [INFO] Received notice  20160328202957.408 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01912 201 blacklab anonymous -0.043441
  2016-03-28 16:29:58,723 [INFO] Received notice  20160328202958.471 http://boule.example.com/ radar/CAPPI/GIF/WKR/201603282030_WKR_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.131236
  2016-03-28 16:29:59,400 [INFO] signal stop
  2016-03-28 16:29:59,400 [INFO] sr_report stop
  blacklab%

on peut voir qu'un abonné sur blacklab télécharge activement depuis la 
nouvelle pompe sur boule.  Fondamentalement, les deux sortes de pelles 
construites automatiquement par sr_audit feront tout le routage nécessaire 
au sein d'un cluster. Lorsqu'il y a des problèmes de volume, ces configurations
peuvent être modifiées pour augmenter le nombre d'instances ou l'utilisation.
post_exchange_split le cas échéant.

La configuration manuelle de la pelle est également nécessaire pour acheminer 
les messages entre les groupes. C'est juste une variation de routage des 
rapports intra-cluster.


Sarra D'une source
~~~~~~~~~~~~~~~~~~~

Lorsque l'on lit les messages directement depuis une source, il faut activer
la validation. FIXME : exemple de la façon dont les messages des utilisateurs
sont traités.

  - set source_from_exchange - set source_from_exchange
  - set mirror False to get date/source tree prepended
  - valider que la somme de contrôle fonctionne......

autre chose ?


Nettoyage
~~~~~~~~~

Ce sont des exemples, la mise en œuvre du nettoyage n'est pas couverte par 
Sarracenia. Étant donné qu'un arbre raisonnablement petit comme donné
ci-dessus, il peut être pratique de scanner l'arbre et d'élaguer les anciens
fichiers à partir de celui-ci. Un travail de cron comme ça::

  root@boule:/etc/cron.d# more sarra_clean
  # supprimer les fichiers une heure après leur apparition.
  Pour la production météo, 37 minutes ont passé l'heure est un bon moment.
  enlever les annuaires le lendemain de la dernière fois qu'ils ont été touchés.
  37 4 * * * * root find /var/www/html -mindepth 1 -maxdepth 1 -type d -mtime +0 | xargs rm -rf

Cela peut sembler un peu agressif, mais ce fichier se trouvait sur un 
très petit serveur virtuel qui n'était qu'un petit serveur virtuel.
pour le transfert de données en temps réel afin de conserver les données 
pendant des périodes prolongées a rempli le disque et arrêté tous les 
transferts. Dans les transferts à grande échelle, il y a toujours un échange
entre l'aspect pratique de conserver les données pour toujours et le besoin
de performance ce qui nous oblige à tailler régulièrement les arborescences 
de répertoires. Les performances du système de fichiers sont optimales avec
les arbres de taille raisonnable, et quand les arbres deviennent trop grands,
le processus de "find" pour les traverser peut deviennent trop onéreux.

On peut plus facilement maintenir de plus petits arbres de répertoires en 
les faisant rouler régulièrement. Si vous avoir assez d'espace disque pour 
durer un ou plusieurs jours, puis une seule tâche cron logique qui 
fonctionnerait sur les arbres quotidiens sans encourir la pénalité d'une 
découverte, est une bonne approche.

Remplacer le contenu ci-dessus par::

  34 4 * * * root find /var/www/html -mindepth 1 -maxdepth 1  -type d -regex '/var/www/html/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]' -mtime +1 | xargs rm -rf


où le +1 peut être remplacé par le nombre de jours à conserver. (...) (....) 
aurait préféré [0-9]{8}, mais il semblerait que la syntaxe de find 
regex n'inclut pas les répétitions. )

Il est à noter que les logs se nettoieront par eux-mêmes, par défaut, après 5 rotations le log
le plus ancien sera enlevé à minuit, seulement si la configuration par défaut a été utilisée
depuis la première rotation. Il est possible de racourcir ce nombre en ajoutant *logrotate 1d*
à default.conf.

Démarrage
~~~~~~~

FIXME : /etc/init.d/ intégration manquante.


Sr_Poll
~~~~~~~

CORRIGE : alimenter la sarra à partir de la source configurée avec un sr_poll. configuré.


Sr_winnow
~~~~~~~~~

CORRIGE : exemple de configuration sr_winnow expliqué, avec quelques pelles aussi.

Sr_sender
~~~~~~~~~

Lorsque les pare-feu empêchent l'utilisation de sarra pour tirer d'une pompe comme le ferait un abonné, on peut inverser l'alimentation en ayant la commande
la pompe amont alimente explicitement la pompe aval.

FIXME : configuration élaborée de l'échantillon sr_sender.


Ajout manuel d'utilisateurs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour éviter l'utilisation de sr_admin, ou pour contourner les problèmes, on peut ajuster les paramètres utilisateur manuellement::


        /var/lib/rabbitmq/.erlang.cookie  same on all nodes

        on each node restart  /etc/init.d/rabbitmq-server stop/start

        on one of the node

        rabbitmqctl stop_app
        rabbitmqctl join_cluster rabbit@"other node"
        rabbitmqctl start_app
        rabbitmqctl cluster_status


        # having high availability queue...
        # here all queues that starts with "cmc." will be highly available on all the cluster nodes

        rabbitmqctl set_policy ha-all "^(cmc|q_)\.*" '{"ha-mode":"all"}'



Configuration de la conservation des courtiers en grappe
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dans cet exemple, bunny-op est un vip qui migre entre bunny1-op et bunny2-op.
Keepalived déplace le vip entre les deux::


  #=============================================
  # vip bunny-op 192.101.12.59 port 5672
  #=============================================

  vrrp_script chk_rabbitmq {
          script "killall -0 rabbitmq-server"
          interval 2
  }

  vrrp_instance bunny-op {
          state BACKUP
          interface eth0
          virtual_router_id 247
          priority 150
          track_interface {
                  eth0
          }
          advert_int 1
          preempt_delay 5
          authentication {
                  auth_type PASS
                  auth_pass bunop
          }
          virtual_ipaddress {
  # bunny-op
                  192.101.12.59 dev eth0
          }
          track_script {
                  chk_rabbitmq
          }
  }




Intégration LDAP
~~~~~~~~~~~~~~~~

Pour activer l'authentification LDAP pour rabbitmq::


         rabbitmq-plugins enable rabbitmq_auth_backend_ldap

         # replace username by ldap username
         # clear password (will be verified through the ldap one)
         rabbitmqctl add_user username aaa
         rabbitmqctl clear_password username
         rabbitmqctl set_permissions -p / username "^xpublic|^amq.gen.*$|^cmc.*$" "^amq.gen.*$|^cmc.*$" "^xpublic|^amq.gen.*$|^cmc.*$"



Et vous devez configurer les paramètres LDAP dans le fichier de configuration du courtier :
(cet exemple de configuration ldap-dev test config a fonctionné lorsque nous l'avons testé....)::


  cat /etc/rabbitmq/rabbitmq.config
  [ {rabbit, [{auth_backends, [ {rabbit_auth_backend_ldap,rabbit_auth_backend_internal}, rabbit_auth_backend_internal]}]},
    {rabbitmq_auth_backend_ldap,
     [ {servers,               ["ldap-dev.cmc.ec.gc.ca"]},
       {user_dn_pattern,       "uid=${username},ou=People,ou=depot,dc=ec,dc=gc,dc=ca"},
       {use_ssl,               false},
       {port,                  389},
       {log,                   true},
       {network,               true},
      {vhost_access_query,    {in_group,
                               "ou=${vhost}-users,ou=vhosts,dc=ec,dc=gc,dc=ca"}},
      {resource_access_query,
       {for, [{permission, configure, {in_group, "cn=admin,dc=ec,dc=gc,dc=ca"}},
              {permission, write,
               {for, [{resource, queue,    {in_group, "cn=admin,dc=ec,dc=gc,dc=ca"}},
                      {resource, exchange, {constant, true}}]}},
              {permission, read,
               {for, [{resource, exchange, {in_group, "cn=admin,dc=ec,dc=gc,dc=ca"}},
                      {resource, queue,    {constant, true}}]}}
             ]
       }},
    {tag_queries,           [{administrator, {constant, false}},
                             {management,    {constant, true}}]}
   ]
  }
  ].

Nécessite RABBITMQ > 3.3.3.x
~~~~~~~~~~~~~~~~~~~~~~~~~

Cherchait à savoir comment utiliser LDAP strictement pour l'authentification par mot de passe.
La réponse que j'ai eue des gourous de Rabbitmq::


  On 07/08/14 20:51, michel.grenier@ec.gc.ca wrote:
  > I am trying to find a way to use our ldap server  only for
  > authentification...
  > The user's  permissions, vhost ... etc  would already be set directly
  > on the server
  > with rabbitmqctl...  The only thing ldap would be used for would be
  > logging.
  > Is that possible... ?   I am asking because our ldap schema is quite
  > different from
  > what rabbitmq-server requieres.

  Yes (as long as you're using at least 3.3.x).

  You need something like:

  {rabbit,[{auth_backends,
             [{rabbit_auth_backend_ldap, rabbit_auth_backend_internal}]}]}

  See http://www.rabbitmq.com/ldap.html and in particular:

  "The list can contain names of modules (in which case the same module is used for both authentication and authorisation), *or 2-tuples like {ModN, ModZ} in which case ModN is used for authentication and ModZ is used for authorisation*."

  Here ModN is rabbit_auth_backend_ldap and ModZ is rabbit_auth_backend_internal.

  Cheers, Simon



Crochets de Sundew
-------------------

Cette information n'est très probablement pas pertinente pour presque tous les utilisateurs. Sundew est un autre module de MetPX qui est essentiellement en cours de développement.
remplacé par Sarracénie. Cette information n'est utile qu'à ceux qui ont une base installée de Sundew souhaitant faire le pont
à la sarracénie. Les premiers travaux sur la sarracénie n'ont utilisé que le client d'abonnement comme téléchargeur, et le module de commutation de l'OMM existant.
de MetPX comme source de données. Il n'y avait pas de concept d'utilisateurs multiples, car le commutateur fonctionne comme une diffusion unique.
et outil de routage. Cette section décrit les types de *colle* utilisés pour nourrir les abonnés à la sarracénie à partir d'une source Sundew.
Il suppose une compréhension profonde de MetPX-Sundew. Actuellement, le script dd_notify.py crée des messages pour le fichier
protocole exp., v00. et v02 (dernière version du protocole de sarracénie)



Notifications sur DD
~~~~~~~~~~~~~~~~~~~~

En remplacement des flux Atom/RSS qui indiquent aux abonnés quand de nouvelles données sont disponibles, nous mettons un courtier en ligne
sur notre serveur de diffusion de données (dd.weather.gc.ca.) Les clients peuvent s'y abonner. Pour créer les notifications, nous avons
un Sundew Sender (nommé wxo-b1-oper-dd.conf) avec un script d'envoi::


  type script
  send_script sftp_amqp.py

  # connection info
  protocol    ftp
  host        wxo-b1.cmc.ec.gc.ca
  user        wxofeed
  password    **********
  ftp_mode    active

  noduplicates false

  # no filename validation (pds format)
  validation  False

  # delivery method
  lock  umask
  chmod 775
  batch 100

Nous voyons toutes les informations de configuration pour un expéditeur à fichier unique, mais le script send_script remplace le paramètre
expéditeur normal avec quelque chose qui construit aussi des messages AMQP. Cette configuration de l'expéditeur Sundew
invoque *sftp_amqp.py* comme un script pour faire l'envoi proprement dit, mais aussi pour placer la charge utile d'un fichier
Message AMQP dans le fichier /apps/px/txq/dd-notify-wxo-b1/, le mettant en file d'attente pour un expéditeur AMQP Sundew.
Cette configuration sender´s c'est::


   type amqp

   validation False
   noduplicates False

   protocol amqp
   host wxo-b1.cmc.ec.gc.ca
   user feeder
   password ********

   exchange_name cmc
   exchange_key  v02.post.${0}
   exchange_type topic

   reject ^ensemble.naefs.grib2.raw.*

   accept ^(.*)\+\+.*

La clé du sujet comprend une substitution. L'arborescence *${0}* contient l'arborescence des répertoires dans laquelle la balise
a été placé sur dd (avec le / remplacé par .) Par exemple, voici une entrée de fichier journal::

  2013-06-06 14:47:11,368 [INFO] (86 Bytes) Message radar.24_HR_ACCUM.GIF.XSS++201306061440_XSS_24_HR_ACCUM_MM.gif:URP:XSS:RADAR:GIF::20130606144709  delivered (lat=1.368449,speed=168950.887119)

- alors la clé (thème) est: v02.post.radar.24_HR_ACCUM.GIF.XSS
- le fichier est placé sous:  http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS
- et l´url complète sera: http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS/201306061440_XSS_24_HR_ACCUM_MM.gif






