
====================================
Administration de Rabbitmq Adddendum
====================================

Les anciennes modifications que les gens voulaient garder?

Introduction
~~~~~~~~~~~~

AMQP signifie Advanced Message Queuing Protocol.
C’est la définition d’un protocole qui vient de la nécessité de standardiser un système de changement de message asynchrone.
Dans le jargon de l’AMQP, nous parlerons des producteurs de messages, des consommateurs de messages et des courtiers.

installation RABBITMQ-SERVER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sur nos machines qui doivent traiter les messages AMQP,
nous installons le broker, en installant le paquet rabbitmq-server_3.3.5-1_all.deb.
L’installation de base se fait comme suit sur toutes nos machines ::

    # installing package taken on the rabbitmq homepage
    # rabbitmq-server version > 3.3.x  required to use ldap for passwords verification only
    
    apt-get install erlang-nox
    dpkg -i /tmp/rabbitmq-server_3.3.5-1_all.deb
    
    # create anonymous user
    # password ********* provided in potato
    #                                          conf write read
    rabbitmqctl add_user anonymous *********
    rabbitmqctl set_permissions -p / anonymous   "^xpublic|^amq.gen.*$|^cmc.*$"     "^amq.gen.*$|^cmc.*$"    "^xpublic|^amq.gen.*$|^cmc.*$"
    rabbitmqctl list_user_permissions anonymous
    
    # create feeder user
    # password ********* provided in potato
    #                                       conf write read
    rabbitmqctl add_user feeder ********
    rabbitmqctl set_permissions -p / feeder  ".*"  ".*"  ".*"
    rabbitmqctl list_user_permissions feeder
    
    # create administrator user 
    # password ********* provided in potato
    
    rabbitmqctl add_user root   *********
    rabbitmqctl set_user_tags root administrator
    
    # takeaway administrator privileges from guest
    rabbitmqctl set_user_tags guest
    rabbitmqctl list_user_permissions guest
    rabbitmqctl change_password guest *************
    
    # list users 
    rabbitmqctl list_users
     
    
    # enabling management web application 
    # this is important since sr_rabbit uses this management facility/port access
    # to retrieve some important info
    
    rabbitmq-plugins enable rabbitmq_management
    /etc/init.d/rabbitmq-server restart



Installation d'un RABBITMQ-SERVER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sur le bunny, nous avons opté pour une installation en cluster.
Pour ce faire, nous suivons les instructions suivantes::

    Stop rabbitmq-server on all nodes....
    
    /var/lib/rabbitmq/.erlang.cookie  same on all nodes
    
    on each node restart  /etc/init.d/rabbitmq-server stop/start
    
    on one of the node
    
    rabbitmqctl stop_app
    rabbitmqctl join_cluster rabbit@"other node"
    rabbitmqctl start_app
    rabbitmqctl cluster_status
    
    
    # having high availability queue...
    # here all queues that starts with "cmc." will be highly available on all the cluster nodes
    
    rabbitmqctl set_policy ha-all "^cmc\." '{"ha-mode":"all"}'



installation ldap RABBITMQ-SERVER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sur les serveurs où nous voulons avoir une authentification en utilisant les instructions suivantes::

         rabbitmq-plugins enable rabbitmq_auth_backend_ldap

         # replace username by ldap username
         # clear password (will be verified through the ldap one)
         rabbitmqctl add_user username aaa
         rabbitmqctl clear_password username
         rabbitmqctl set_permissions -p / username "^xpublic|^amq.gen.*$|^cmc.*$" "^amq.gen.*$|^cmc.*$" "^xpublic|^amq.gen.*$|^cmc.*$"


Et nous configurons les services LDAP dans le fichier de configuration rabbitmq-server
(ancienne configuration de test de ldap-dev qui ne fonctionnait que...)::

    cat /etc/rabbitmq/rabbitmq.config
    [
    {rabbit, [{auth_backends, [ {rabbit_auth_backend_ldap,rabbit_auth_backend_internal}, rabbit_auth_backend_internal]}]},
    {rabbitmq_auth_backend_ldap,
        [ 
        {servers,               ["ldap-dev.cmc.ec.gc.ca"]},
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



Utilisation de l’AMQP sur DD (DDI, DD.BETA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Nous (Peter) voulions faire une implémentation d’AMQP dans METPX.
Pour ce faire, nous utilisons la bibliothèque python-amqplib qui implémente les fonctionnalités
nécessaires d’AMQP en python.
Nous avons ainsi développé un pxSender de type amqp qui est le producteur de messages de notification
ainsi qu’un pxReceiver de type amqp qui sert de consommateur de messages de notification.
En tant que courtier, nous utilisons rabbitmq-server qui est un paquet Debian standard d’un courtier AMQP.

Un pxSender de type amqp, lit le contenu d’un fichier dans sa fil d’attente,
crée un message auquel il joint un "topic" et l’envoie au broker.
Un pxReceiver de type amqp annoncera au broker le "topic" pour lequel il est
intéressé à recevoir des messages de notification, et le broker lui enverra
chaque message correspondant à son choix.

Comme un message peut être n’importe quoi, au niveau du pxSender,
nous avons également joint le nom du fichier d’où provient le message.
Ainsi, dans notre pxReceiver, nous pouvons assurer le contenu du message dans le nom de fichier correspondant.
Cette astuce n’est inutile que pour les changements amqp entre un expéditeur et un récepteur amqp...

Notifications pour DD
---------------------

Nous avons trouvé dans AMQP une opportunité d’annoncer des produits lorsqu’ils arrivent sur DD.
Donc un utilisateur, au lieu de vérifier constamment si un produit est présent sur DD.
Pour le modifier, il pouvait s’abonner (topic AMQP) pour recevoir un message (l’url du produit)
qui ne serait omis qu’à la livraison du produit sur DD.
Nous ne ferions pas cet exercice pour les newsletters... mais pour d’autres produits (grib, images... etc.)

Pour mettre cela en œuvre, nous avons utilisé une possibilité de pxSender, le sender_script.
Nous avons écrit un script sftp_amqp.py qui effectue les livraisons à DD et pour chaque produit, il crée un fichier
contenant l’URL sous laquelle le produit sera présent. Voici le début de la configuration de wxo-b1-oper-dd.conf ::

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

Nous voyons dans cette configuration que toutes les informations pour un expéditeur à fichier unique sont là.
Mais parce que le type est script... et la send_script sftp_amqp.py est fournie, nous sommes en mesure de
demander à notre expéditeur d’en faire plus...

Le fichier contenant l’URL est placé sous le txq d’un expéditeur AMQP
/apps/px/txq/dd-notify-wxo-b1 pour que la notification AMQP soit effectuée.
Pour envoyer les fichiers dans cette fil d’attente, un expéditeur doit avoir
écrit dd-notify-wxo-b1.conf qui est configuré comme suit ::

    type amqp
    
    validation False
    noduplicates False
    
    protocol amqp
    host wxo-b1.cmc.ec.gc.ca
    user feeder
    password ********
    
    exchange_name cmc  
    exchange_key  exp.dd.notify.${0}
    exchange_type topic
    
    reject ^ensemble.naefs.grib2.raw.*
    
    accept ^(.*)\+\+.*


Encore une fois, le cl du topic contient une partie programmée.
La partie ${0} contient l’arborescence où le produit est placé sur dd...
Par exemple, voici une ligne de journal de dd-notify-wxo-b1.log::

    2013-06-06 14:47:11,368 [INFO] (86 Bytes) Message radar.24_HR_ACCUM.GIF.XSS++201306061440_XSS_24_HR_ACCUM_MM.gif:URP:XSS:RADAR:GIF::20130606144709  delivered (lat=1.368449,speed=168950.887119)

===================================  ========================================================================================
Et ainsi serait le cl.               ``exp.dd.notify.radar.24_HR_ACCUM.GIF.XSS``
Et l’emplacement du fichier          ``http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS``
Et l’URL complète dans le message    ``http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS/201306061440_XSS_24_HR_ACCUM_MM.gif``
===================================  ========================================================================================


Utilitaires installés sur les serveurs DD
-----------------------------------------

Lorsqu’un client se connecte au broker (rabbitmq-server), il doit créer une file
d’attente et l’attacher à un échange. Nous pouvons donner à cette fil d’attente
l’option qu’elle s’autodétruit lorsqu’elle n’est plus utilisée ou qu’elle est
conservée et continue d’empiler les produits si le client est hors ligne.
En général, nous aimerions que la fil d’attente soit préservée et donc que la
reprise de la connexion redémarre la collection de produits sans perte.


queue_manager.py
    Le rabbitmq-server ne détruira jamais une fil d’attente créée par un client
    si elle n’est pas en mode de suppression automatique (et encore moins si elle est créée avec durabilité).
    Cela peut causer un problème. Par exemple, un client qui développe un processus, peut changer d’IDE plusieurs
    fois et entasser sur le serveur une multitude de files d’attente qui ne seront jamais utilisées.
    Nous avons donc créé un script queue_manager.py qui vérifie si les files d’attente inutilisées ont
    plus de X produits en attente ou prennent plus de Y Mo...
    Si c’est le cas, ils sont détruits par le script.

    Au moment de la rédaction du présent document, les limites sont les suivantes  : ``25000 messages and 50Mb.``


dd-xml-inotify.py
    Sur notre datamart public, il y a des produits qui ne proviennent pas directement de pds/px/pxatx.
    Comme nos notifications sont effectuées à partir de la livraison du produit, nous n’avons pas de
    messages de notification pour eux. C’est le cas pour les produits XML sous les répertoires :
    ``citypage_weather`` and ``marine_weather``. Pour surmonter cette situation, le démon dd-xml-inotify.py
    a été créé et installé. Ce script python utilise inotify pour surveiller la modification des produits
    sous leurs répertoires.
    Si un produit est modifié ou ajouté, une notification amqp est envoyée au serveur.
    Ainsi, tous les produits du datamart sont couverts par l’envoi de message.


Utilisation d’AMQP avec URP, BUNNY, PDS-OP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. note:: s’applique également au développement...


De URP-1/2 annoncer à BUNNY-OP qu’un produit est prêt
-----------------------------------------------------

Sur urp-1/2 un metpx roule l’expéditeur amqp_expose_db.conf qui annonce qu’un produit
vient d’arriver dans la db de metpx avec un message de la forme ::

    Md5sum of product name           file-size  url                        dbname
    a985c32cbdee8af2ab5d7b8f6022e781 498081     http://urp-1.cmc.ec.gc.ca/ db/20150120/RADAR/URP/IWA/201501201810~~PA,60,10,PA_PRECIPET,MM_HR,MM:URP:IWA:RADAR:META::20150120180902

Ces messages AMQP sont envoyés au serveur rabbitmq sur bunny-op avec une clé d’échange qui commence par
``v00.urp.input``suivie par convention par le chemin de db avec le '/' remplacé par '.'.

.. note:: que urp-1/2 exécute apache et que l’annonce du produit se trouve dans la base de données de
          metpx et est visible à partir de l’URL du message.

BUNNY-OP et dd_dispatcher.py
----------------------------

bunny-op est un vip qui vit sur bunny1-op ou bunny2-op.
C’est avec keepalived que nous nous assurons que ce vip réside sur l’un des bunny-op.
Nous testons également que rabbitmq-server fonctionne sur le même serveur.
La partie configuration de keepalived qui traite de le vip est::

    vip bunny-op 142.135.12.59 port 5672

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
                    142.135.12.59 dev eth0
            }
            track_script {
                    chk_rabbitmq
            }
    }

Les serveurs rabbitmq sur ces machines sont installés dans un cluster.
Nous mettons la haute disponibilité sur les files d’attente en commençant par ``cmc.*``.
Sur chacune des machines, exécutez l’utilitaire ``dd_dispatcher.py``.
Ce programme vérifie si le vip bunny-op et proc dera a son travail uniquement sur le serveur où vit le vip.
(S’il y a un commutateur, détection automatique en 5 secondes et les files d’attente restent inchangées)

L’utilitaire dd_dispatcher.py s’abonne aux messages de notification ``v00.urp.input.#`` et redirige
ainsi les messages de notification des 2 serveurs opérationnels URP.
À la réception d’un premier produit, le md5dum du produit est placé dans une cache et le message est re-expédié
mais cette fois avec ``v00.urp.notify`` comme clé d’échange.
Si un autre message arrive de ``v00.urp.input`` avec le même md5sum que le premier, il est ignoré,
de sorte que les produits annoncés à partir de la clé d’échange ``v00.urp.notify``
sont uniques et représentent la première arrivée des 2 URP opérationnels.

Réceptions PDS-OP de messages de notification de répartition, wget de produits radar
------------------------------------------------------------------------------------

Sur pds-op, un récepteur pull_urp, exécutez le fx_script pull_amqp_wget.py.
Dans ce script, la commande suivante ::

    # shared queue : each pull receive 1 message (prefetch_count=1)
    self.channel.basic_qos(prefetch_size=0,prefetch_count=1,a_global=False)

fait que la distribution des messages de notification ``v00.urp.notify`` sera répartie
également sur les 5 serveurs sous pds-op. Nous garantissons donc une traction distribuée.
Pour chaque message du formulaire ::

    a985c32cbdee8af2ab5d7b8f6022e781 498081 http://urp-1.cmc.ec.gc.ca/ db/20150120/RADAR/URP/IWA/201501201810~~PA,60,10,PA_PRECIPET,MM_HR,MM:URP:IWA:RADAR:META::20150120180902

l’url est rebuted à partir des 2 derniers champs du message et un wget du produit est fait
et placé dans la fil d’attente du récepteur qui est ensuite ignoré / acheminé de manière ordinaire.

Vérification / Dépannage
------------------------

Dans l’ordre de production

1. Sur ``urp-1/2``:
    - Vérifiez que les produits radar sont générés sur urp-1/2.
    - Vérifiez que les notifications sont générées sur urp-1/2 /apps/px/log/tx_amqp_expose_db.log
2. Sur ``bunny1/2-op``
    - Vérifiez où réside bunny-op
    - Vérifiez les journaux de dd_dispatcher.py ``/var/log/dd_dispatcher_xxxx.log`` où xxxx est le processus pid
3. Sur ``pds-op``
    - Vérifiez le pull_urp

La réparation des processus qui ne fonctionnent pas correctement devrait résoudre les problèmes en général.
Plus de détails seront ajoutés ici au fur et à mesure que les problèmes sont rencontrés et corrigés.

