==============================
SR3 Guide De Ligne De Commande
==============================


SR3 - Tout
==========

**sr3* est un outil de ligne de commande pour gérer les configurations
`Sarracenia <https://github.com/MetPX/sarracenia>`_ individuellement ou en groupe. Pour l’utilisateur actuel,
il lit sur tous les fichiers de configuration, des fichiers d’état et consulte la table de processus pour déterminer
l’état de tous les composants. Il effectue ensuite la modification demandée.

  **sr3** *options* *action* [ *composant/configuration* ... ]

Les composants sr3 sont utilisés pour publier et télécharger des fichiers à partir de sites Web ou de serveurs de fichiers
qui fournissent des `sr3_post(7) <.. Notifications du protocole /Reference/sr3_post.7.rst>`_. Ces sites
publient des messages pour chaque fichier dès qu’il est disponible. Les clients se connectent à un
*broker* (souvent le même que le serveur) et s'abonnent aux notifications.
Les notifications *sr3_post* fournissent de véritables notifications push pour les dossiers accessibles sur le Web (WAF),
et sont beaucoup plus efficaces que l’interrogation périodique des répertoires ou le style ATOM/RSS
de notifications. Sr_subscribe peut être configuré pour publier des messages après leur téléchargement,
les mettre à la disposition des consommateurs pour un traitement ultérieur ou des transferts.

**sr3** peut également être utilisé à des fins autres que le téléchargement (par exemple, pour
fourniture à un programme externe) en spécifiant le -n (égal à : *download off*)
supprimer le comportement de téléchargement et publier uniquement l’URL sur la sortie standard. La
sortie standard peut être redirigée vers d’autres processus dans le style de filtre de texte UNIX classique.

Les composants de sarracenia sont des groupes de valeurs choisi par défaut sur l’algorithme principal,
pour réduire la taille des composants individuels.  Les composants sont les suivants :

 - cpump - copier des messages d'une pompe a une autre (une implémentation C d'un shovel.)
 - poll  - interroger un serveur Web ou de fichiers non sarracenia pour créer des messages à traiter.
 - post & watch - créer des messages pour les fichiers à traiter.
 - sarra  - télécharger le fichier d’un serveur distant vers le serveur local et les republier pour d’autres.
 - sender - envoyer des fichiers d’un serveur local à un serveur distant.
 - shovel - copier des messages, uniquement, pas des fichiers.
 - watch - créer des messages pour chaque nouveau fichier qui arrive dans un répertoire ou à un chemin défini.
 - winnow - copier des messages, en supprimant les doublons.

Tous ces composants acceptent les mêmes options, avec les mêmes effets.
Il existe également des `sr3_cpump(1). <../Reference/sr3_cpump.1.rst>`_ qui est une version C qui implémente un
sous-ensemble des options ici, mais là où elles sont implémentées, elles ont le même effet.

La commande **sr3** prend généralement deux arguments : une action suivie d’une liste
de fichiers de configuration. Lorsqu’un composant est appelé, une opération et un
fichier de configuration sont spécifiés. Si la configuration est omise, cela signifie que
l’action s'applique à toutes les configurations. L’action est l’une des suivantes :

 - foreground: exécuter une seule instance au premier plan, écrivant le journal à l´erreur standard.
 - restart: arrêter puis démarrer la configuration.
 - sanity: recherche les instances qui se sont plantées ou ont bloqué et les redémarre.
 - start:  démarrer la configuration
 - status: vérifier si la configuration est en cours d'exécution.
 - stop: arrêter la configuration.

Les actions restantes gèrent les ressources (échanges, files d’attente) utilisées par le composant sur
le courtier ou pour gérer les configurations.

 - cleanup:       supprime les ressources du composant sur le serveur
 - declare:       crée les ressources du composant sur le serveur.
 - setup:         comme declare, fait en plus des liaisons de file d'attente.
 - add:           copie une configuration à la liste des configurations disponibles.
 - list:          Énumérer toutes les configurations disponibles.
 - list plugins:  Énumérer toutes les *plugins* disponibles.
 - list examples: Énumérer toutes les exemples disponibles.
 - show           voir une version interpreté d'un fichier de configuration.
 - edit:          modifier une configuration existante.
 - remove:        Supprimer une configuration
 - disable:       marquer une configuration comme non éligible à l'exécution.
 - enable:        marquer une configuration comme éligible à l'exécution.
 - convert:       convertir une configuration de la version2 à la version3

Par exemple: *sr_subscribe foreground dd* exécute une instance du composant sr_subscribe en avant plan
en se servant de la configuration dd.

L'action **foreground** est utilisée lors de la construction d'une
configuration ou pour le débogage. L'instance **foreground** sera exécutée
indépendamment des autres instances qui sont en cours d'exécution.
Si des instances sont en cours d'exécution, il partage la même file d'attente
d'avis avec eux. Un utilisateur arrête l'instance **foreground** en
utilisant simplement <ctrl-c> sur linux. ou utilise d'autres moyens pour tuer le processus.

Une fois qu’une configuration a été affinée, *start* lance le composant en tant que service d'arrière-plan
(démon ou flotte de démons dont le numéro est contrôlé par l’option *instances*).
Si plusieurs configurations et composants doivent être exécutés ensemble, l’ensemble de la flotte
peut être contrôlé de la même manière à l’aide de la commande `sr3(1). <../Reference/sr3.1.html>'`_.

Pour que les composants roulent tous en meme temps,sur Linux on peut utiliser l'intégration
`systemd <https://www.freedesktop.org/wiki/Software/systemd/>`_ , comme décrit dans
`Admin Guide <../How2Guides/Admin.rst>`_ . Sur Windows, il est possible de configurer un service,
comme décrit dans `Windows user manual <../Tutorials/Windows.html>`_

Les actions **cleanup**, **declare**, **setup** peuvent être utilisées pour gérer les
ressources sur le courtier rabbitmq. Les ressources sont soit des files d'attente,
soit des échanges. **declare** crée les ressources. **setup** crée les files
d'attente et les liaisons.

Les actions **add, remove, list, edit, enable & disable** sont utilisées pour gérer la liste
de configurations et *plugins*. On peut voir toutes les configurations disponibles en utilisant l´action **list**.
et les *plugins* disponibles avec **list plugins**.
En utilisant l'option **edit**, on peut travailler sur une configuration particulière.
Une configuration **disabled** ne sera pas démarrée ou redémarrée par les actions **start**
ou **restart**. Cela peut être utilisé pour mettre une configuration temporairement de côté.

L'option **convert** est utilisé pour traduire une configuration écrite avec des options de la version2
de Sarracenia, avec des options de la version3. Le fichier de configuration de la version2 doit etre
placé dans le réportoire *~/.config/sarra/composant/v2_config.conf* et la version traduite sera placé
dans le répertoire *~/.config/sr3/composant/v3_config.conf*. Pas exemple, cette action serais invoqué avec
*sr3 convert composant/config*.


ACTIONS
-------

declare|setup
~~~~~~~~~~~~~

Appeler la fonction correspondante pour chacune des configurations::

  $ sr3 declare
    declare: 2020-09-06 23:22:18,043 [INFO] root declare looking at cpost/pelle_dd1_f04 
    2020-09-06 23:22:18,048 [INFO] sarra.moth.amqp __putSetup exchange declared: xcvan00 (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,049 [INFO] sarra.moth.amqp __putSetup exchange declared: xcvan01 (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,049 [INFO] root declare looking at cpost/veille_f34 
    2020-09-06 23:22:18,053 [INFO] sarra.moth.amqp __putSetup exchange declared: xcpublic (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,053 [INFO] root declare looking at cpost/pelle_dd2_f05 
    ...
    2020-09-06 23:22:18,106 [INFO] root declare looking at cpost/pelle_dd2_f05 
    2020-09-06 23:22:18,106 [INFO] root declare looking at cpump/xvan_f14 
    2020-09-06 23:22:18,110 [INFO] sarra.moth.amqp __getSetup queue declared q_tfeed.sr_cpump.xvan_f14.23011811.49631644 (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,110 [INFO] sarra.moth.amqp __getSetup um..: pfx: v03, exchange: xcvan00, values: #
    2020-09-06 23:22:18,110 [INFO] sarra.moth.amqp __getSetup binding q_tfeed.sr_cpump.xvan_f14.23011811.49631644 with v03.# to xcvan00 (as: amqp://tfeed@localhost/)
    2020-09-06 23:22:18,111 [INFO] root declare looking at cpump/xvan_f15 
    2020-09-06 23:22:18,115 [INFO] sarra.moth.amqp __getSetup queue declared q_tfeed.sr_cpump.xvan_f15.50074940.98161482 (as: amqp://tfeed@localhost/) 


Déclare les files d’attente et les échanges liés à chaque configuration.
On peut également l’appeler avec --users, afin qu’il déclare les utilisateurs ainsi que les échanges et les files d’attente::

  $ sr3 --users declare
    2020-09-06 23:28:56,211 [INFO] sarra.rabbitmq_admin add_user permission user 'ender' role source  configure='^q_ender.*|^xs_ender.*' write='^q_ender.*|^xs_ender.*' read='^q_ender.*|^x[lrs]_ender.*|^x.*public$' 
    ...


dump
~~~~

imprimer les trois structures de données utilisées par sr.  Il existe trois listes :

* processus considérés comme liés à sr.

* configurations présentes

* contenu des fichiers d’état.

**dump** est utilisé pour le débogage ou pour obtenir plus de détails que ce qui est fourni par status::

    Running Processes
         4238: name:sr_poll.py cmdline:['/usr/bin/python3', '/home/peter/src/sarracenia/sarra/sr_poll.py', '--no', '1', 'start', 'pulse']
         .
         . 
         .
    Configs
       cpost 
           veille_f34 : {'status': 'running', 'instances': 1}

    States
       cpost
           veille_f34 : {'instance_pids': {1: 4251}, 'queue_name': None, 'instances_expected': 0, 'has_state': False, 'missing_instances': []}

    Missing
       

C’est assez long, et donc un peu trop d’informations à regarder à l’état brut.
Généralement utilisé en conjonction avec des filtres Linux, tels que grep.
par exemple::

  $ sr3 dump  | grep stopped
    WMO_mesh_post : {'status': 'stopped', 'instances': 0}
    shim_f63 : {'status': 'stopped', 'instances': 0}
    test2_f61 : {'status': 'stopped', 'instances': 0}

  $ sr3 dump  | grep disabled
    amqp_f30.conf : {'status': 'disabled', 'instances': 5}


fournit une méthode simple pour déterminer quelles configurations sont dans un état particulier.
Autre exemple, si *sr status* signale que l’expéditeur/tsource2send_f50 est partiel, alors
on peut utiliser dump pour obtenir plus de détails::

  $ sr3 dump | grep sender/tsource2send_f50
    49308: name:sr3_sender.py cmdline:['/usr/bin/python3', '/usr/lib/python3/dist-packages/sarracenia/instance.py', '--no', '1', 'start', 'sender/tsource2send_f50']
    q_tsource.sr_sender.tsource2send_f50.58710892.12372870: ['sender/tsource2send_f50']


foreground
~~~~~~~~~~

exécuter une seule instance d’une configuration unique en tant que processus interactif de journalisation à la sortie stderr/terminal actuelle.
pour le débogage.

**list**

montre à l’utilisateur les fichiers de configuration présents ::

  $ sr3 list
    User Configurations: (from: /home/peter/.config/sarra )
    cpost/pelle_dd1_f04.conf         cpost/pelle_dd2_f05.conf         cpost/veille_f34.conf            
    cpump/xvan_f14.conf              cpump/xvan_f15.conf              poll/f62.conf                    
    post/shim_f63.conf               post/t_dd1_f00.conf              post/t_dd2_f00.conf              
    post/test2_f61.conf              sarra/download_f20.conf          sender/tsource2send_f50.conf     
    shovel/rabbitmqtt_f22.conf       subscribe/amqp_f30.conf          subscribe/cclean_f91.conf        
    subscribe/cdnld_f21.conf         subscribe/cfile_f44.conf         subscribe/cp_f61.conf            
    subscribe/ftp_f70.conf           subscribe/q_f71.conf             subscribe/rabbitmqtt_f31.conf    
    subscribe/u_sftp_f60.conf        watch/f40.conf                   admin.conf                       
    credentials.conf                 default.conf                     
    logs are in: /home/peter/.cache/sarra/log
    
La dernière ligne indique dans quel répertoire se trouvent les fichiers journaux.

*list examples* montre également les modèles de configuration inclus disponibles comme points de départ avec l’action *add* ::

  $ sr3 list examples
    Sample Configurations: (from: /home/peter/Sarracenia/v03_wip/sarra/examples )
    cpump/cno_trouble_f00.inc        poll/aws-nexrad.conf             poll/pollingest.conf             
    poll/pollnoaa.conf               poll/pollsoapshc.conf            poll/pollusgs.conf               
    poll/pulse.conf                  post/WMO_mesh_post.conf          sarra/wmo_mesh.conf              
    sender/ec2collab.conf            sender/pitcher_push.conf         shovel/no_trouble_f00.inc        
    subscribe/WMO_Sketch_2mqtt.conf  subscribe/WMO_Sketch_2v3.conf    subscribe/WMO_mesh_CMC.conf      
    subscribe/WMO_mesh_Peer.conf     subscribe/aws-nexrad.conf        subscribe/dd_2mqtt.conf          
    subscribe/dd_all.conf            subscribe/dd_amis.conf           subscribe/dd_aqhi.conf           
    subscribe/dd_cacn_bulletins.conf subscribe/dd_citypage.conf       subscribe/dd_cmml.conf           
    subscribe/dd_gdps.conf           subscribe/dd_ping.conf           subscribe/dd_radar.conf          
    subscribe/dd_rdps.conf           subscribe/dd_swob.conf           subscribe/ddc_cap-xml.conf       
    subscribe/ddc_normal.conf        subscribe/downloademail.conf     subscribe/ec_ninjo-a.conf        
    subscribe/hpfx_amis.conf         subscribe/local_sub.conf         subscribe/pitcher_pull.conf      
    subscribe/sci2ec.conf            subscribe/subnoaa.conf           subscribe/subsoapshc.conf        
    subscribe/subusgs.conf           watch/master.conf                watch/pitcher_client.conf        
    watch/pitcher_server.conf        watch/sci2ec.conf                


  $ sr3 add dd_all.conf
    add: 2021-01-24 18:04:57,018 [INFO] sarracenia.sr add copying: /usr/lib/python3/dist-packages/sarracenia/examples/subscribe/dd_all.conf to /home/peter/.config/sr3/subscribe/dd_all.conf 
  $ sr3 edit dd_all.conf

Les actions **add, remove, list, edit, enable & disable** sont utilisées pour gérer la liste
des configurations.  On peut voir toutes les configurations disponibles en utilisant l'action **list**.
Pour afficher les plugins disponibles, utilisez **list plugins**. À l’aide de l’option **edit**,
on peut travailler sur une configuration particulière.  Un *disabled* met une configuration de côté
(en ajoutant *.off* au nom) afin qu’elle ne soit pas démarrée ou redémarrée par
les actions **start**, **foreground** ou **restart**.

show
~~~~

Afficher tous les paramètres de configuration (le résultat de toutes les analyses... ce que les composants du flux voient réellement) ::

    
    % sr3 show subscribe/q_f71
    2022-03-20 15:30:32,507 1084652 [INFO] sarracenia.config parse_file download_f20.conf:35 obsolete v2:"on_message msg_log" converted to sr3:"logEvents after_accept"
    2022-03-20 15:30:32,508 1084652 [INFO] sarracenia.config parse_file tsource2send_f50.conf:26 obsolete v2:"on_message msg_rawlog" converted to sr3:"logEvents after_accept"
    2022-03-20 15:30:32,508 1084652 [INFO] sarracenia.config parse_file rabbitmqtt_f22.conf:6 obsolete v2:"on_message msg_log" converted to sr3:"logEvents after_accept"
    
    Config of subscribe/q_f71: 
    {'_Config__admin': 'amqp://bunnymaster@localhost/ None True True False False None None',
     '_Config__broker': 'amqp://tsource@localhost/ None True True False False None None',
     '_Config__post_broker': None,
     'accelThreshold': 0,
     'acceptSizeWrong': False,
     'acceptUnmatched': False,
     'admin': 'amqp://bunnymaster@localhost/ None True True False False None None',
     'attempts': 3,
     'auto_delete': False,
     'baseDir': None,
     'baseUrl_relPath': False,
     'batch': 1,
     'bindings': [('xs_tsource_poll', ['v03', 'post'], ['#'])],
     'broker': 'amqp://tsource@localhost/ None True True False False None None',
     'bufsize': 1048576,
     'byteRateMax': None,
     'cfg_run_dir': '/home/peter/.cache/sr3/subscribe/q_f71',
     'component': 'subscribe',
     'config': 'q_f71',
     'currentDir': None,
     'debug': False,
     'declared_exchanges': [],
     'declared_users': {'anonymous': 'subscriber', 'eggmeister': 'subscriber', 'ender': 'source', 'tfeed': 'feeder', 'tsource': 'source', 'tsub': 'subscriber'},
     'delete': False,
     'destfn_script': None,
     'directory': '//home/peter/sarra_devdocroot/recd_by_srpoll_test1',
     'discard': False,
     'documentRoot': None,
     'download': True,
     'durable': True,
     'env_declared': ['FLOWBROKER', 'MQP', 'SFTPUSER', 'TESTDOCROOT'],
     'exchange': 'xs_tsource_poll',
     'exchangeDeclare': True,
     'exchangeSuffix': 'poll',
     'expire': 1800.0,
     'feeder': ParseResult(scheme='amqp', netloc='tfeed@localhost', path='/', params='', query='', fragment=''),
     'fileEvents': {'create', 'link', 'modify', 'delete'},
     'file_total_interval': '0',
     'filename': 'WHATFN',
     'fixed_headers': {},
     'flatten': '/',
     'hostdir': 'fractal',
     'hostname': 'fractal',
     'housekeeping': 300,
     'imports': [],
     'inflight': None,
     'inline': False,
     'inlineByteMax': 4096,
     'inlineEncoding': 'guess',
     'inlineOnly': False,
     'instances': 1,
     'integrity_arbitrary_value': None,
     'integrity_method': 'sha512',
     'logEvents': {'after_work', 'after_accept', 'on_housekeeping'},
     'logFormat': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
     'logLevel': 'info',
     'logReject': False,
     'logRotateCount': 5,
     'logRotateInterval': 1,
     'logStdout': True,
     'log_flowcb_needed': False,
     'masks': ['accept .* into //home/peter/sarra_devdocroot/recd_by_srpoll_test1 with mirror:True strip:.*sent_by_tsource2send/'],
     'messageAgeMax': 0,
     'messageCountMax': 0,
     'messageDebugDump': False,
     'messageRateMax': 0,
     'messageRateMin': 0,
     'message_strategy': {'failure_duration': '5m', 'reset': True, 'stubborn': True},
     'message_ttl': 0,
     'mirror': True,
     'msg_total_interval': '0',
     'nodupe_fileAgeMax': 0,
     'nodupe_ttl': 0,
     'overwrite': True,
     'permCopy': True,
     'permDefault': 0,
     'permDirDefault': 509,
     'permLog': 384,
     'plugins_early': [],
     'plugins_late': ['sarracenia.flowcb.log.Log'],
     'post_baseDir': None,
     'post_baseUrl': None,
     'post_broker': None,
     'post_documentRoot': None,
     'post_exchanges': [],
     'post_topicPrefix': ['v03', 'post'],
     'prefetch': 25,
     'pstrip': '.*sent_by_tsource2send/',
     'queueBind': True,
     'queueDeclare': True,
     'queueName': 'q_tsource_subscribe.q_f71.76359618.62916076',
     'queue_filename': '/home/peter/.cache/sr3/subscribe/q_f71/subscribe.q_f71.tsource.qname',
     'randid': 'cedf',
     'randomize': False,
     'realpath_post': False,
     'rename': None,
     'report': False,
     'reset': False,
     'resolved_qname': 'q_tsource_subscribe.q_f71.76359618.62916076',
     'retry_ttl': 1800.0,
     'settings': {},
     'sleep': 0.1,
     'statehost': False,
     'strip': 0,
     'subtopic': [],
     'timeCopy': True,
     'timeout': 300,
     'timezone': 'UTC',
     'tls_rigour': 'normal',
     'topicPrefix': ['v03', 'post'],
     'undeclared': ['msg_total_interval', 'file_total_interval'],
     'users': False,
     'v2plugin_options': [],
     'v2plugins': {'plugin': ['msg_total_save', 'file_total_save']},
     'vhost': '/',
     'vip': None}
    
    % 


convert
~~~~~~~

Conversion d’une configuration : les deux formats sont acceptés, ainsi que les fichiers d’inclusion (.inc) ::

  $ sr3 convert poll/sftp_f62
    2022-06-14 15:00:00,762 1093345 [INFO] root convert converting poll/sftp_f62 from v2 to v3

  $ sr3 convert poll/sftp_f62.conf
    2022-06-14 15:01:11,766 1093467 [INFO] root convert converting poll/sftp_f62.conf from v2 to v3

  $ sr3 convert shovel/no_trouble_f00.inc
    2022-06-14 15:03:29,918 1093655 [INFO] root convert converting shovel/no_trouble_f00.inc from v2 to v3

start
~~~~~

lancer tous les composants configurés::

  $ sr3 start
    gathering global state: procs, configs, state files, logs, analysis - Done. 
    starting...Done


stop
~~~~

arrêter tous les processus::

  $ sr3 stop
    gathering global state: procs, configs, state files, logs, analysis - Done. 
    stopping........Done
    Waiting 1 sec. to check if 93 processes stopped (try: 0)
    All stopped after try 0
 


status
~~~~~~

Exemple d’état OK (sr3 est en cours d’exécution) ::

  $ sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
    cpost/pelle_dd1_f04                      stopped        0     0     0     0
    cpost/pelle_dd2_f05                      stopped        0     0     0     0
    cpost/veille_f34                         partial        0     1     1     0
    cpump/xvan_f14                           partial        0     1     1     0
    cpump/xvan_f15                           partial        0     1     1     0
    poll/f62                                 running        1     0     1     0
    post/shim_f63                            stopped        0     0     0     0
    post/t_dd1_f00                           stopped        0     0     0     0
    post/t_dd2_f00                           stopped        0     0     0     0
    post/test2_f61                           stopped        0     0     0     0
    report/tsarra_f20                        running        1     0     1     0
    sarra/download_f20                       running        1     0     1     0
    sender/tsource2send_f50                  running        1     0     1     0
    shovel/rabbitmqtt_f22                    running        1     0     1     0
    subscribe/amqp_f30                       running        1     0     1     0
    subscribe/cclean_f91                     running        1     0     1     0
    subscribe/cdnld_f21                      running        1     0     1     0
    subscribe/cfile_f44                      running        1     0     1     0
    subscribe/cp_f61                         running        1     0     1     0
    subscribe/dd_all                         stopped        0     0     0     0
    subscribe/ftp_f70                        running        1     0     1     0
    subscribe/q_f71                          running        1     0     1     0
    subscribe/rabbitmqtt_f31                 running        1     0     1     0
    subscribe/u_sftp_f60                     running        1     0     1     0
    watch/f40                                running        1     0     1     0
          total running configs:  15 ( processes: 15 missing: 3 stray: 0 )


Les configurations sont répertoriées sur la gauche. Pour chaque configuration, l’état
sera :

* stopped:  aucun processus n’est en cours d’exécution.
* running:  tout les processus sont en cours d’exécution.
* partial:  certains processus sont en cours d’exécution.
* disabled: configuré pour ne pas s’exécuter.

Les colonnes à droite donnent plus d’informations, détaillant le nombre de processus en cours d’exécution et les processus manquants.
L’entrée attendu indique le nombre de processus à exécuter en fonction de la configuration et indique si elle est arrêtée
ou pas.  Le contenu des colonnes Run et Miss doit toujours correspondre à ce qui se trouve dans la colonne Exp.

La dernière colonne est le nombre de messages stockés dans la file d’attente de nouvelles tentatives locale, indiquant quels
channels ont des difficultés de traitement. Voici un exemple d’une seule configuration qui est en cours d’exécution, en l’arrêtant, et
en la nettoyant::

  $ sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
    subscribe/dd_all                         running        5     0     1     0
          total running configs:   1 ( processes: 5 missing: 0 stray: 0 )

  $ sr3 stop subscribe/dd_all
    Stopping: sending SIGTERM ..... ( 5 ) Done
    Waiting 1 sec. to check if 5 processes stopped (try: 0)
    Waiting 2 sec. to check if 3 processes stopped (try: 1)
    pid: 818881-['/usr/bin/python3', '/usr/lib/python3/dist-packages/sarracenia/instance.py', '--no', '3', 'start'] does not match any configured instance, sending it TERM
    Waiting 4 sec. to check if 3 processes stopped (try: 2)
    All stopped after try 2
    
  $ sr3 cleanup subscribe/dd_all
    cleanup: queues to delete: [(ParseResult(scheme='amqps', netloc='anonymous:anonymous@dd.weather.gc.ca', path='/', params='', query='', fragment=''), 'q_anonymous.sr_subscribe.dd_all.47257736.46056854')]
    removing state file: /home/peter/.cache/sr3/subscribe/dd_all/sr_subscribe.dd_all.anonymous.qname
    
  $ sr3 remove subscribe/dd_all
    2021-01-24 23:57:59,800 [INFO] root remove FIXME remove! ['subscribe/dd_all']
    2021-01-24 23:57:59,800 [INFO] root remove removing /home/peter/.config/sr3/subscribe/dd_all.conf 
    
  $ sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
          total running configs:   0 ( processes: 0 missing: 0 stray: 0 )


CONSUMER
========

La plupart des composants Metpx Sarracenia boucle sur la réception et la
consommation de messages AMQP. Habituellement, les messages d'intérêt sont
dans le format d´une *avis* `sr_post(7) <sr_post.7.rst>`_, annonçant la disponibilité
d'un fichier en publiant l'URL pour l´accéder (ou une partie de celle-ci).
Il y a également le format *rappor* `sr_report(7) <sr_report.7.rst>`_ qui peuvent
être traités avec les mêmes outils. Les messages AMQP sont publiés avec
un *exchange* comme destinataire.  Sur un courtier (serveur AMQP.) L'exchange
délivre des messages aux files d'attente. Pour recevoir de messages,
on doit fournir les informations d'identification pour se connecter au
courtier (message AMQP).  Une fois connecté, un consommateur doit créer
une file d'attente pour retenir les messages en attente. Le consommateur
doit ensuite lier la file d'attente à une ou plusieurs échanges de manière
à ce qu'il mette dans sa file d'attente.

Une fois les liaisons (anglais: *bindings*) établies, le programme peut
recevoir des messages. Lorsqu'un message est reçu, un filtrage
supplémentaire est possible en utilisant des expressions régulières sur
les messages AMQP. Après qu'un message a passé avec succès ce processus
de sélection et d'autres validations internes, le processus peut exécuter
un script de plugin **on_message** pour traiter le message davantage
de façon spécialisé. Si ce plugin retourne False comme résultat, le
message est rejeté. Si c'est vrai, le traitement du message se poursuit.

Les sections suivantes expliquent toutes les options pour régler cette
partie "consommateur" de les programmes de Sarracenia.



Setting the Broker 
------------------

**broker [amqp|mqtt]{s}://<user>:<password>@<brokerhost>[:port]/<vhost>**

Un URI AMQP est utilisé pour configurer une connexion à une pompe à messages
(AMQP broker). Certains composants de Sarracenia définissent une valeur par
défaut raisonnable pour cette option. Vous fournissez l'utilisateur normal,
l'hôte, le port des connexions. Dans la plupart des fichiers de configuration,
le mot de passe est manquant. Le mot de passe n'est normalement inclus que dans
le fichier credentials.conf.

L´application Sarracenia n'a pas utilisé vhosts, donc **vhost** devrait toujours être **/**.

pour plus d'informations sur le format URI de l'AMQP : ( https://www.rabbitmq.com/uri-spec.html))


soit dans le fichier default.conf, soit dans chaque fichier de configuration spécifique.
L'option courtier indique à chaque composante quel courtier contacter.

**broker [amqp|mqtt]{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (par défaut : Aucun et il est obligatoire de le définir)

Une fois connecté à un courtier AMQP, l'utilisateur doit lier une file d'attente.
à l´*exchange* et aux thèmes (*topics*) pour déterminer les messages intérêsseants.

Creating the Queue
------------------

Une fois connecté à un courtier AMQP, l'utilisateur doit créer une file d'attente.

Mise en file d'attente sur broker :

- **queue <nom> (par défaut : q_<brokerUser>.<programName>.<configName>.<configName>)**
- **expire <durée> (par défaut : 5m == cinq minutes. À OUTREPASSER)**
- **message_ttl <durée> (par défaut : Aucun)**
- **prefetch <N> (par défaut : 1)**


Habituellement, les composants devinent des valeurs par défaut raisonnables pour
toutes ces valeurs et les utilisateurs n'ont pas besoin de les définir.  Pour
les cas moins habituels, l'utilisateur peut avoir besoin a remplacer les valeurs
par défaut. La file d'attente est l'endroit où les avis sont conservés
sur le serveur pour chaque abonné.

[ queue|queue_name|qn <name>]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Par défaut, les composants créent un nom de file d’attente qui doit être unique. Le
queue_name par défaut créé par les composants et suit la convention suivante :

   **q_<brokerUser>.<programName>.<configName>.<random>.<random>** 

Ou:

* *brokerUser* est le nom d’utilisateur utilisé pour se connecter au courtier (souvent: *anonymous* )

* *programName* est le composant qui utilise la file d’attente (par exemple *sr_subscribe* )

* *configName* est le fichier de configuration utilisé pour régler le comportement des composants

* *random* n’est qu’une série de caractères choisis pour éviter les affrontements de plusieurs
  personnes qui utilisent les mêmes configurations

Les utilisateurs peuvent remplacer la valeur par défaut à condition qu’elle commence par **q_<brokerUser>**.

Lorsque plusieurs instances sont utilisées, elles utilisent toutes la même file d’attente, pour du multi-tasking simple.
Si plusieurs ordinateurs disposent d’un système de fichiers domestique partagé, le
queue_name est écrit à :

 ~/.cache/sarra/<programName>/<configName>/<programName>_<configName>_<brokerUser>.qname

Les instances démarrées sur n’importe quel nœud ayant accès au même fichier partagé utiliseront la
même file d’attente. Certains voudront peut-être utiliser l’option *queue_name* comme méthode plus explicite
de partager le travail sur plusieurs nœuds.

AMQP QUEUE BINDINGS
-------------------

Une fois qu'on a une file d'attente, elle doit être liée à un échange (exchange.)
Les utilisateurs ont presque toujours besoin de définir ces options. Une
fois qu'une file d'attente existe sur le courtier, il doit être lié (*bound*) à
une échange. Les liaisons (*bindings*) définissent ce que l'on entend par
les avis que le programme reçoit. La racine du thème
est fixe, indiquant la version du protocole et le type de l'arborescence.
(mais les développeurs peuvent l'écraser avec le **topic_prefix*.
option.)

Ces options définissent les messages (notifications URL) que le programme reçoit :

 - **exchange      <name>         (défaut: xpublic)**
 - **exchangeSuffix      <name>  (défaut: None)**
 - **topic_prefix  <amqp pattern> (défaut: 03 -- developer option)**
 - **subtopic      <amqp pattern> (pas de défaut, doit apparaitre apres exchange)**

subtopic <amqp pattern> (default: #)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dans les publications d’un échange, le paramètre de sous-thème restreint la sélection de produits.
Pour donner une valeur correcte au sous-thème, on a le choix de filtrer en utilisant **subtopic**
avec seulement le wildcard limité d’AMQP et à longueur limitée à 255 octets codés, ou l’expression
régulière la plus puissante basés sur les mécanismes  **accept/reject** décrits ci-dessous.
La différence étant que le Le filtrage AMQP est appliqué par le courtier lui-même, ce qui évite
que les avis ne soient livrés au client du tout. Les modèles **accept/reject** s’appliquent
aux messages envoyés par le courtier à l’abonné. En d’autres termes,  **accept/reject** sont
des filtres côté client, alors que **subtopic** est le filtrage côté serveur.

Il est préférable d'utiliser le filtrage côté serveur pour réduire le nombre
de avis envoyées au client à un petit sur-ensemble de ce qui est pertinent,
et n'effectuer qu'un réglage fin avec l'outil mécanismes côté client, économisant
la bande passante et le traitement pour tous.

topic_prefix est principalement d'intérêt pendant les transitions de version
de protocole, où l'on souhaite spécifier une version sans protocole par défaut
des messages auxquels s'abonner, ou bien pour manipuler des rapports de disposition,
au lieu d'avis.

Habituellement, l'utilisateur spécifie un échange et plusieurs options de sous-thèmes.
**subtopic** est ce qui est normalement utilisé pour indiquer les messages d'intérêt.
Pour utiliser le sous-thème pour filtrer les produits, faites correspondre la
chaîne de sous-thèmes avec le chemin relatif dans l´arborescence de répertoires sur le serveur.

Par exemple, en consommant à partir de DD, pour donner une valeur correcte au sous-thème, on peut
Parcourez notre site Web **http://dd.weather.gc.ca** et notez tous les annuaires.
d'intérêt.  Pour chaque arborescence de répertoires d'intérêt, écrivez un **subtopic**.
comme suit :

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#**

::

 ou:
       *                correspond a un seul nom de repertoire
       #                correspond à toute arborescence de répertoires restante

remarque:
  Lorsque les répertoires ont des wildcards, ou espaces dans leurs noms, ils
  seront encodé par l'URL ou ( '#' devient %23 ). Lorsque les répertoires ont
  des points dans leur nom, cela changera la hiérarchie des thèmes.

  FIXME: 
      les marques de hachage sont substituées à l’URL, mais n’ont pas vu le code pour les autres valeurs.
      Vérifiez si les astérisques dans les noms de répertoire dans les rubriques doivent être encodés par l'URL.
      Vérifiez si les points dans les noms de répertoire dans les rubriques doivent être encodés par l'URL.
 
On peut utiliser plusieurs liaisons à plusieurs échanges comme cela::

  exchange A
  subtopic directory1.*.directory2.#

  exchange B
  subtopic *.directory4.#

Cela va déclarer deux liaisons différentes à deux échanges différents et deux arborescences de fichiers différentes.
Alors que la liaison par défaut consiste à se lier à tout, certains courtiers pourraient ne pas permettre aux
clients à définir des liaisons, ou on peut vouloir utiliser des liaisons existantes.
On peut désactiver la liaison de file d’attente comme cela::

  subtopic None

(False, ou off marchera aussi.)





Client-side Filtering
---------------------

Nous avons sélectionné nos messages via **exchange**, **subtopic** et **subtopic**.
Le courtier met les messages correspondants dans notre file d'attente (*queue*).
Le composant télécharge ces messages.

Les clients Sarracenia implémentent un filtrage plus flexible côté client
en utilisant les expressions régulières.

Brief Introduction to Regular Expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les expressions régulières sont un moyen très puissant d'exprimer les correspondances de motifs.
Ils offrent une flexibilité extrême, mais dans ces exemples, nous utiliserons seulement un
petit sous-ensemble : Le point (.) est un joker qui correspond à n'importe quel caractère
unique. S'il est suivi d'un nombre d'occurrences, il indique le nombre de lettres
qui correspondent. Le caractère * (astérisque), signifie un nombre quelconque d'occurrences.
alors :

 - .* signifie n'importe quelle séquence de caractères de n'importe quelle longueur.
   En d'autres termes, faire correspondre n'importe quoi.
 - cap.* signifie toute séquence de caractères commençant par cap.
 - .*CAP.* signifie n'importe quelle séquence de caractères avec CAP quelque part dedans.
 - .*CAP signifie toute séquence de caractères qui se termine par CAP.
 - Dans le cas où plusieurs portions de la chaîne de caractères pourraient correspondre, la plus longue est sélectionnée.
 - .*?CAP comme ci-dessus, mais *non-greedy*, ce qui signifie que le match le plus court est choisi.
 - noter que l'implantaions de regexp en C n'inclu pas le *greediness*, alors certains expressions
   ne seront pas interpretés pareilles par les outils implanté en C: sr_cpost, sr_cpump, où libsrshim.

Veuillez consulter diverses ressources Internet pour obtenir de plus amples renseignements:

 - https://docs.python.org/3/library/re.html
 - https://en.wikipedia.org/wiki/Regular_expression
 - http://www.regular-expressions.info/ 


accept, reject and accept_unmatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **accept    <expression régulière (regexp)>  (facultatif)**
- **reject    <expression régulière (regexp)>  (facultatif)**
- **acceptUnmatched   <booléen> (par défaut: False)**
- **baseUrl_relPath   <booléen> (par défaut: False)**

Les options **accept** et **reject** traitent des expressions régulières (regexp).
La regexp est appliquée à l'URL du message pour détecter une correspondance.

Si l'URL du message d'un fichier correspond à un motif **reject**, on informe
le courtier que le message a été consommé et on abandonne son traitement.

Celui qui correspond à un motif **accept** est traité par le composant.

Dans de nombreuses configurations, les options **accept** et **reject**
sont spécifiés ensembles, et avec l'option **directory**.  Ils relient
ensuite les messages acceptés à la valeur **directory** sous laquelle
ils sont spécifiés.

Après que toutes les options **accept** / **reject** sont traitées normalement.
l'accusé de réception du message tel qu'il a été consommé et ignoré. Pour
outrepasser ce comportement de défaut, définissez **accept_unmatch** à True.

Les **accept/rejet** sont interprétés dans l'ordre qu´ils apparaissent
dans le fichier de configuration.  Chaque option est traitée en ordre
de haut en bas.  par exemple :

sequence #1::

  reject .*\.gif
  accept .*

sequence #2::

  accept .*
  reject .*\.gif


Dans la séquence #1, tous les fichiers se terminant par 'gif' sont rejetés.
Dans la séquence #2, l'option accept .* (regexp qui veut dire accepte tout) est
rencontré avant la déclaration de rejet, de sorte que le rejet n'a aucun effet.

Il est préférable d'utiliser le filtrage côté serveur pour réduire le nombre
de avis envoyées au composant à un petit sur-ensemble de ce qui est
pertinent, et n'effectuer qu'un réglage fin avec les mécanismes *accept/reject*
côté client, économisant la bande passante et le traitement pour tous.

Plus de détails sur la façon d’appliquer les directives suivent:

Normalement, le chemin d’accès relatif (baseUrl_relPath est False, ajouté au répertoire de base) pour
les fichiers téléchargés seront définis en fonction de l’en-tête relPath inclus
dans le message. Toutefois, si *baseUrl_relPath* est défini, le relPath du message va
être précédé des sous-répertoires du champ baseUrl du message.

Convention d´appellation de files d´attente
-------------------------------------------

Alors que dans la plupart des cas, une bonne valeur de nom de file d´attente (en anglais: queue) est 
générée par l'application, dans certains cas, c´est nécessaire de remplacer ces choix par une 
spécification utilisateur explicite. Pour ce faire, il faut connaître les règles de nommage des files d'attente :

1. les noms de file d'attente commencent par q\_.
2. ceci est suivi de <amqpUserName> (le propriétaire/utilisateur du nom d'utilisateur du courtier de la file d'attente).
3. suivi d'un deuxième tiret de soulignement ( _ )
4. suivi d'une chaîne de caractères au choix de l'utilisateur.

La longueur totale du nom de la file d'attente est limitée à 255 octets de caractères UTF-8.


PUBLICATION (POST)
==================

Comme de nombreux composants consomment un flux de messages, de nombreux composants
(souvent les mêmes) produisent également un flux de sortie de messages.  Pour créer des fichiers
disponible pour les abonnés, une affiche publie les annonces à un AMQP ou
Serveur MQTT, également appelé broker. L’option post_broker définit toutes les
informations d’identification pour se connecter au courtier de sortie **AMQP**.

**post_broker [amqp|mqtt]{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Une fois connecté au courtier de source AMQP, le programme génère des notifications après que
le téléchargement d’un fichier a eu lieu. Pour générer la notification et l’envoyer au
courtier au saut suivant, l’utilisateur définit ces options :

* **post_baseDir     <path>    (facultatif)**
* **post_topicPrefix <pfx> (par défaut: 'v03')**
* **post_exchange    <name>         (par défaut: xpublic)**
* **post_baseUrl     <url>     (OBLIGATOIRE)**

FIXME : Des exemples de ce à quoi ils servent, de ce qu’ils font...


Convention d´appellation des EXCHANGES
--------------------------------------

1. Les noms d’échange commencent par x
2. Les échanges qui se terminent par *public* sont accessibles (pour lecture) par tout utilisateur authentifié.
3. Les utilisateurs sont autorisés à créer des échanges avec le modèle: xs_<amqpUserName>_<whatever>. ces échanges ne peuvent être écrits que par cet utilisateur.
4. Le système (sr_audit ou administrateurs) crée l’échange de xr_<amqpUserName> comme un lieu d’envoi de rapports pour un utilisateur. Il n’est lisible que par cet utilisateur.
5. Les utilisateurs administratifs (rôles d’administrateur ou de feeder) peuvent publier ou s’abonner n’importe où.

Par exemple, xpublic n’a pas xs\_ et un modèle de nom d’utilisateur, de sorte qu’il ne peut être publié que par les utilisateurs administrateurs ou feeder.
Puisqu’il se termine en public, tout utilisateur peut s’y lier pour s’abonner aux messages publiés.
Les utilisateurs peuvent créer des échanges tels que xs_<amqpUserName>_public qui peuvent être écrits par cet utilisateur (selon la règle 3),
et lu par d’autres (selon la règle 2.) Une description du flux conventionnel de messages à travers les échanges sur une pompe.
Les abonnés se lient généralement à l’échange xpublic pour obtenir le flux de données principal. Il s’agit de la valeur par défaut dans sr_subscribe.

Un autre exemple, un utilisateur nommé Alice aura au moins deux échanges :

  - xs_Alice l’exhange où Alice poste ses notifications de fichiers et signale les messages (via de nombreux outils).
  - xr_Alice l’échange d’où Alice lit ses messages de rapport (via sr_shovel).
  - Alice peut créer un nouvel échange en publiant simplement dessus (avec sr3_post ou sr_cpost) s’il répond aux règles de nommage.

Habituellement, un sr_sarra exécuté par un administrateur de pompe lira à partir d’un échange tel que xs_Alice_mydata
pour récupérer les données correspondant au message *post* d’Alice, et les rendre disponibles sur la pompe,
en le ré-annonçant sur l’échange xpublic.


SONDAGE (POLLING)
=================

On peut faire le même travail que post, sauf que les fichiers sont sur un serveur distant.
Dans le cas d’un sondage (en anglais: poll), l’URL de la publication sera générée à partir de l´option *destination*,
avec le chemin d’accès du produit (*directory*/« fichier correspondant »).  Il y en a une publication
par fichier. La taille du fichier est prise dans le répertoire « ls »... mais sa somme
de contrôle ne peut pas être déterminée, lors la stratégie de calcul de est ¨cod¨ qui signifie
que ca devrait être calculé lors du transfert.

Par défaut, sr_poll envoie son message de publication au courtier avec l'échange par défaut
(le préfixe *xs_* suivi du nom d’utilisateur du courtier). Le *post_broker* est obligatoire.
Il peut être incomplet s’il est bien défini dans le fichier credentials.conf.

Référez `sr3_post(1) <../Reference/sr3_post.1.html>`_ - pour comprendre l’ensemble du processus de notification.
Référez `sr3_post(7) <../Reference/sr3_post.7.rst>`_ - pour comprendre le format complet de notification.

Ces options définissent les fichiers pour lesquels l’utilisateur souhaite être averti et où
 il sera placé, et sous quel nom.

- **directory <path>           (par défaut: .)**
- **accept    <regexp pattern> [rename=] (doit être défini)**
- **reject    <regexp pattern> (facultatif)**
- **permDefault     <integer>        (par défaut: 0o400)**
- **nodupe_fileAgeMax <duration>   (par défaut 30d)**


L’option *filename* peut être utilisée pour définir un changement de nom global pour les produits.
Ex.:

**filename  rename=/naefs/grib2/**

Pour tous les messages créés, l’option *rename* serait définie à '/naefs/grib2/filename'
parce que j’ai spécifié un répertoire (chemin qui se termine par /).

L’option *directory* définit où obtenir les fichiers sur le serveur.
Combiné avec les options **accept** / **reject**, l’utilisateur peut sélectionner
les fichiers d’intérêt et leurs répertoires de résidence.

Les options **accept** et **reject** utilisent des expressions régulières (regexp) pour trouver
une correspondance avec l’URL.
Ces options sont traitées séquentiellement.
L’URL d’un fichier qui correspond à un modèle **reject** n’est pas publiée.
Les fichiers correspondant à un modèle **accept** sont publiés.
Encore une fois, un *rename* peut être ajouté à l’option *accept*... les produits qui correspondent
a l'option *accept* seront renommé comme décrit... à moins que le *accept* corresponde à
un fichier, l’option *rename* doit décrire un répertoire dans lequel les fichiers
seront placé (en préfix au lieu de remplacer le nom du fichier).

Le répertoire peut avoir des modèles. Ces modèles pris en charge concernent la date/l’heure.
Ils sont fixes...

**${YYYY}         année actuelle**
**${MM}           mois actuel**
**${JJJ}          julian actuelle**
**${YYYYMMDD}     date actuelle**

**${YYYY-1D}      année actuelle   - 1 jour**
**${MM-1D}        mois actuel - 1 jour**
**${JJJ-1D}       julian actuelle - 1 jour**
**${YYYYMMDD-1D}  date actuelle   - 1 jour**

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

        directory /mylocaldirectory/${YYYYMMDD}/mydailies
        accept    .*observations.*

L’option **permDefault** permet aux utilisateurs de spécifier un masque d'autorisation octal numérique
de style Linux::

  permDefault 040

signifie qu’un fichier ne sera pas publié à moins que le groupe ait l’autorisation de lecture
(sur une sortie ls qui ressemble à : ---r-----, comme une commande chmod 040 <fichier> ).
Les options **permDefault** spécifient un masque, c’est-à-dire que les autorisations doivent être
au moins ce qui est spécifié.

Comme pour tous les autres composants, l’option **vip** peut être utilisée pour indiquer
qu’un poll doit être actif sur seulement un seul nœud d’un cluster. Notez que quand
d’autres nœuds participant au poll et wu’ils n’ont pas le vip, ils

les fichiers qui sont plus vieux que nodupe_fileAgeMax sont ignorés. Cela
peut être modifié à n’importe quelle limite de temps spécifiée dans les configurations en utilisant
l’option *nodupe_fileAgeMax <duration>*. Par défaut, dans les composants
autre que poll, cette option est désactivé en étant défini à zéro (0). Comme il s’agit d’une
option de durée, les unités sont en secondes par défaut, mais il est possible de definir l'option
en utilisant des minutes, heures, jours ou des semaines. Dans la composante de poll, nodupe_fileAgeMax
est défini à 30 jours par défaut.

Sondage avancé (Advanced Polling)
---------------------------------

Le poll intégré liste les répertoires distants et analyse les lignes renvoyées par les structures
paramiko.SFTPAttributes (similaires à os.stat) pour chaque fichier répertorié.
Il existe une grande variété de personnalisations disponibles car les ressources à poller
très différentes :

* on peut implémenter un rappel *sarracenia.flowcb* avec une routine *poll*
  pour prendre en charge ces services, ce qui remplace le poll par défaut.

* Certains serveurs ont des résultats non standard quand ils listent des fichiers, de sorte que l’on peut
  sur-classer un rappel sarracenia.flowcb.poll avec le point d’entrée **on_line** pour normaliser leurs
  réponses en utilisant quand même le flux de poll intégré.

* Il existe de nombreux serveurs http qui fournissent des formats très différents quand ils
  listent de fichiers, donc parfois, au lieu de reformater individuellement chaque ligne
  ligne, il faut refaire l’analyse de la page au complet. Le point d’entrée **on_html_page**
  dans sarracenia.flowcb.poll peut être modifié en la sur-classant également.

* Il existe d’autres serveurs qui fournissent des services différents qui ne sont pas inclus
  dans le poll par défaut. On peut implémenter une classe *sarracenia.transfer* supplémentaire
  pour mieux comprendre le poll.

La sortie d’un poll est une liste de messages créés à partir des noms de fichiers
et les enregistrements SFTPAttributes, qui peuvent ensuite être filtrés par éléments
après *gather* dans l’algorithme.

COMPOSANTS
==========

Tous les composants effectuent une combinaison de poll, de consommation et de publication.
avec des variations qui permettent soit la transmission d’annonces, ou soit aux
transferts de données. Les composants appliquent tous le seul même algorithme,
il suffit de commencer à partir de différents paramètres par défaut pour correspondre
à un cas d'utilisation commun.

CPUMP
-----

*cpump** est une implémentation du composant `shovel`_ en C.
Sur une base individuelle, il devrait être plus rapide qu’un seul téléchargeur python,
avec certaines limitations.

 - ne télécharge pas de données, ne fait que diffuser des messages. (pelle, et non abonné)
 - s’exécute en tant qu’instance unique (pas d’instances multiples).
 - ne prend en charge aucun plugin.
 - ne prend pas en charge vip pour la haute disponibilité.
 - différentes bibliothèques d’expressions régulières : POSIX vs python.
 - ne supporte pas regex pour la commande strip (pas de regex non-greedy).

Cela peut donc généralement, mais pas toujours, servir de substitution à l`shovel`_  et à `winnow`_.

L’implémentation C peut être plus facile à mettre à disposition dans des environnements spécialisés,
comme l'informatique de haute performance, car il y a beaucoup moins de dépendances que la version python.
Cela utilise également beaucoup moins de mémoire pour un rôle donné.  Normalement la version python
est recommandé, mais il y a des cas où l’utilisation de l’implémentation C est raisonnable.

**sr_cpump** se connecte à un *broker* (souvent le même que le courtier de post)
et s'abonne aux notifications d’intérêt. Si _suppress_duplicates_ est actif,
à la réception d’un message, il recherche le champ **integity** du message dans la cache.  Si le message est
trouvé, le fichier est déjà passé, de sorte que la notification est ignorée. Si ce n’est pas le cas, alors
le fichier est nouveau, et la **sum** est ajoutée à la cache et la notification est publiée.

POLL
----

**poll** est un composant qui se connecte à un serveur distant pour
vérifier divers répertoires pour certains fichiers. Lorsqu’un fichier est
présent, modifié, ou créé dans le répertoire distant, le programme
informe qu'il y a nouveau produit.

Le protocle de notification est défini ici `sr3_post(7) <../Reference/sr3_post.7.rst>`_

**poll** se connecte à un *broker*.  À toutes les secondes de *sleep*, il se connecte à
une *destination* (sftp, ftp, ftps). Pour chacun des *directory* définis, les contenus sont listés.
Le poll est seulement destinée à être utilisée pour les fichiers récemment modifiés.
L’option *nodupe_fileAgeMax* élimine les fichiers trop anciens. Lorsqu’un fichier correspondant
à un modèle donné est trouvé by *accept*, **poll** crée un message de notification pour ce produit.

Le message est ensuite verifié dans la cache dupliqué (limité en temps par l'option
nodupe_ttl) pour empêcher la publication de fichiers qui ont déjà été vus.

**poll** peut être utilisé pour acquérir des fichiers distants en conjonction avec un `sarra`_ qui est
abonné aux notifications d'un post, pour les télécharger et les republier à partir d’une pompe de données.

L’option de destination spécifie ce qui est nécessaire pour se connecter au serveur distant

**destination protocol://<user>@<server>[:port]**

::
      (par défaut : Aucun et il est obligatoire de le définir )

La *destination* doit être définie avec le minimum d’informations requises...
**sr_poll** utilise le paramètre *destination* non seulement lors du poll, mais aussi
dans messages sr3_post produits.

Par exemple, l’utilisateur peut définir :

**destination ftp://myself@myserver**

Et compléter les informations nécessaires dans le fichier d’informations d’identification (credentials) avec la ligne :

**ftp://myself:mypassword@myserver:2121  passive,binary**

Poll rassemble des informations sur les fichiers distants, pour créer des messages à leur sujet.
La méthode gather intégrée utilise les protocoles sarracenia.transfer. Actuellement sftp, ftp et http
sont implémentés.

Scans répétés et VIP
~~~~~~~~~~~~~~~~~~~~

Lorsque plusieurs serveurs coopèrent pour polller un serveur distant,
le paramètre *vip* est utilisé pour décider quel serveur il faut réellement poller.
Tous les serveurs participants s’abonnent à l’endroit où **poll** est publié,
et utilisent les résultats pour remplir la cache de suppression des doublons, afin que
que si l’adresse VIP se déplace, les serveurs alternatifs ont des indications actuelles
de ce qui a été affiché.

POST or WATCH
-------------

**sr3_post** affiche la disponibilité d’un fichier en créant une annonce.
Contrairement à la plupart des autres composants de sarracenia qui agissent comme des démons,
sr3_post est une invocation qui poste et se termine en une seul fois.
Pour mettre les fichiers à la disposition des abonnés, **sr3_post** envoie les annonces
à un serveur AMQP ou MQTT, également appelé broker.

Il existe de nombreuses options pour la détection des modifications dans les répertoires, pour
une discussion détaillée des options dans Sarracenia, voir `<DetectFileReady.rst>`_

Cette page de manuel concerne principalement l’implémentation de python,
mais il y a aussi une implémentation en C, qui fonctionne presque pareille.
Différences:

 - les plugins ne sont pas pris en charge dans l’implémentation C.
 - L’implémentation C utilise des expressions régulières POSIX, la grammaire python3 est légèrement différente.
 - lorsque l’option *sleep* (utilisée uniquement dans l’implémentation C) est définie sur > 0,
   cela transforme sr_cpost en un démon qui fonctionne comme un `watch`_.

Le composant *watch* est utilisé pour surveiller les répertoires à la recherche de nouveaux fichiers.
Cela est équivalent à poster (ou cpost) avec l’option *sleep* réglée sur >0.

L’option [*-pbu|--post_baseUrl url,url,...*] spécifie l’emplacement a partir d'ou
les abonnés pourront télécharger.  Il y a généralement un message par fichier.
Format de l’argument de l’option *post_baseUrl* ::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:

Lorsque plusieurs URL sont données sous forme de liste séparée par des virgules à *post_baseUrl*, les
url fournies sont utilisées dans le style round-robin, pour fournir une forme d’équilibrage de charge.

L’option [*-p|--path path1 path2 .. pathN*] spécifie le chemin d’accès des fichiers
à annoncer. Il y a généralement un message par fichier.
Format de l’argument de l’option *path* ::

       /absolute_path_to_the/filename
       or
       relative_path_to_the/filename

L’option *-pipe* peut être spécifiée pour que sr3_post lise les noms de chemin d’accès à partir de la norme
d’entrée également.

Exemple d’invocation de *sr3_post*::

 sr3_post -pb amqp://broker.com -pbu sftp://stanley@mysftpserver.com/ -p /data/shared/products/foo 

Par défaut, sr3_post lit le fichier /data/shared/products/foo et calcule sa somme de contrôle.
Il crée ensuite un message de publication, se connecte à broker.com en tant qu’utilisateur « invité »
(informations d’identification par défaut) et envoie la publication aux vhost '/' par défaut et à
l’échange par défaut. L’échange par défaut est le préfixe *xs_* suivi du nom d’utilisateur du courtier,
où la valeur par défaut 'xs_guest'. Un abonné peut télécharger le fichier /data/shared/products/foo en
s’authentifiant en tant qu’utilisateur stanley sur mysftpserver.com en utilisant le protocole sftp pour
broker.com en supposant qu’il dispose des informations d’identification appropriées.
La sortie de la commande est la suivante ::

 [INFO] Published xs_guest v03.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo' sum=d,82edc8eb735fd99598a1fe04541f558d parts=1,4574,1,0,0

Dans MetPX-Sarracenia, chaque article est publié sous un certain thème.
La ligne du journal commence par '[INFO]', suivie du **topic** du post.
Les thèmes dans *AMQP* sont des champs séparés par un point. Notez que les thèmes MQTT utilisent
une barre oblique (/) comme séparateur de thème.  Le thème complet commence par
a topicPrefix (voir option), version *v03*, suivi d’un sous-thème (voir option)
ici la valeur par défaut, et le chemin du fichier séparé par des points
*data.shared.products.foo*.

Le deuxième champ de la ligne du journal est l’avis de message.  Il se compose d’un horodatage
*20150813161959.854* et l’URL source du fichier dans les 2 derniers champs.

Le reste des informations est stocké dans des en-têtes de message AMQP, constitués de paires clé=valeur.
L’en-tête *sum=d,82edc8eb735fd99598a1fe04541f558d* donne l’empreinte du fichier (ou somme de contrôle).
Ici, *d* signifie la somme de contrôle md5 effectuée sur les données et *82edc8eb735fd99598a1fe04541f558d*
est la valeur de la somme de contrôle. Le *parts=1,4574,1,0,0* indique que le fichier est disponible en 1 partie de 4574 octets
(la taille du fichier.)  Le *1,0,0* restant n’est pas utilisé pour les transferts de fichiers avec une seule partie.

un autre exemple::

 sr3_post -pb amqp://broker.com -pbd /data/web/public_data -pbu http://dd.weather.gc.ca/ -p bulletins/alphanumeric/SACN32_CWAO_123456

Par défaut, sr3_post lit le fichier /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concaténation du chemin d’accès post_baseDir et relatif de l’URL source pour obtenir le chemin d’accès au fichier local)
et calcule sa somme de contrôle. Il crée ensuite un message de publication, se connecte à broker.com en tant qu’utilisateur « invité »
(informations d’identification par défaut) et envoie la publication aux hôtes par défaut '/' et échange 'xs_guest'.

Un abonné peut télécharger le fichier http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 à l’aide de http
sans authentification sur dd.weather.gc.ca.

Partitionnement de fichiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

l’utilisation de l’option *blocksize* n’a aucun effet dans sr3.  Il est utilisé pour faire le partitionnement de fichiers,
et il redeviendra efficace à l’avenir, avec la même sémantique.

SARRA
-----

**sarra** est un programme qui s'abonne aux notifications de fichiers,
acquiert les fichiers, et les réannonce à leurs nouveaux emplacements.
Le protocole de notification est défini ici `sr3_post(7) <../Reference/sr3_post.7.html>`_

**sarra** se connecte à un *broker* (souvent le même que le serveur de fichiers distant)
et s'abonne aux notifications d’intérêt. Il utilise les informations de la notification
permettant de télécharger le fichier sur le serveur local sur lequel il s’exécute.
Il publie ensuite une notification pour les fichiers téléchargés sur un courtier (généralement sur le serveur local).

**sarra** peut être utilisé pour acquérir des fichiers auprès de `sr3_post(1) <../Reference/sr3_post.1.html>`_
ou `watch`_ ou pour reproduire un dossier accessible sur le Web (WAF),
qui annoncent ses produits.

**sr_sarra** est un `sr_subscribe(1) <#subscribe>`_  aves les préréglages suivants::

   mirror True


Exigences spécifiques de consommation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si les messages sont postés directement à partir d’une source  l’échange utilisé est 'xs_<brokerSourceUsername>'.
Pour se protéger contre les utilisateurs malveillants, les administrateurs doivent définir *sourceFromExchange* à **True**.
Ces messages ne peuvent pas contenir un champ cluster ou source d’origine
ou un utilisateur malveillant peut définir les valeurs de manière incorrecte.

- **sourceFromExchange  <booléan> (défaut: False)**

À la réception, le programme définira ces valeurs dans la classe parente (ici
cluster est la valeur de l’option **cluster** tirée de default.conf) :

msg['source']       = <brokerUser>
msg['from_cluster'] = cluster

remplacer toutes les valeurs présentes dans le message. Ce paramètre
doit toujours être utilisé lors de l’ingestion de données provenant d’un
échange d’utilisateurs.

SENDER
------

**sender** est un composant dérivé de `subscribe`_
utilisé pour envoyer des fichiers locaux à un serveur distant à l’aide d’un protocole de transfert de fichiers, principalement SFTP.
**sender** est un consommateur standard, utilisant tous les paramètres AMQP normaux pour les courtiers, les échanges,
et toutes les files d'attente, et tout les filtres standard côté client avec accept, reject et after_accept.

Souvent, un courtier annoncera des fichiers à l’aide d’un protocole distant tel que HTTP,
mais pour l’expéditeur, il s’agit en fait d’un fichier local.  Dans de tels cas, on
voir un message : **ERROR: The file to send is not local.**
Un plugin after_accept convertira l’URL Web en un fichier local::

  baseDir /var/httpd/www
  flowcb sarracenia.flowcb.tolocalfile.ToLocalFile

Ce plugin after_accept fait partie des paramètres par défaut pour les expéditeurs, mais
doit encore spécifier baseDir pour qu’il fonctionne.

Si un **post_broker** est défini, **sender** vérifie si le nom du cluster est donné
par l’option **to** si elle se trouve dans l’un des clusters de destination du message.
Si ce n’est pas le cas, le message est ignoré.

CONFIGURATION 1 : RÉPLICATION POMPE À POMPE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour la réplication de la pompe, **mirror** est défini sur True (valeur par défaut).

**baseDir** fournit le chemin d’accès au répertoire qui, lorsqu’il est combiné avec le chemin relatif
dans la notification sélectionnée, donne le chemin absolu du fichier à envoyer.
La valeur par défaut est Aucun, ce qui signifie que le chemin d’accès dans la notification est le chemin absolu.

Dans un subscriber, baseDir représente le préfixe du chemin relatif en amont,
et est utilisé comme modèle pour se faire remplacer dans le répertoire de base actuellement sélectionné
(à partir d’une option *baseDir* ou *directory*) dans les champs de message : 'link', 'oldname', 'newname'
qui sont utilisés lors de la mise en miroir de liens symboliques ou de fichiers renommés.

La **destination** définit le protocole et le serveur à utiliser pour livrer les produits.
Sa forme est un url partiel, par exemple : **ftp://myuser@myhost**.
Le programme utilise le fichier ~/.conf/sarra/credentials.conf pour obtenir les détails restants
(mot de passe et options de connexion).  Les protocoles pris en charge sont ftp, ftps et sftp.
Si l’utilisateur doit implémenter un autre mécanisme d’envoi, il fournirait le script du plugin
par l’option **do_send**.

Sur le site distant, le **post_baseDir** sert à la même chose que le
**baseDir** sur ce serveur.  La valeur par défaut est None, ce qui signifie que le chemin d’accès livré
est l’absolu.

Maintenant, nous sommes prêts à envoyer le produit... par exemple, si la notification sélectionnée ressemble à ceci :

**20150813161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_product**

**sr_sender**  effectue la pseudo-livraison suivante :

Envoie le fichier locale [**baseDir**]/relative/path/to/IMPORTANT_product
à    **destination**/[**post_baseDir**]/relative/path/to/IMPORTANT_product
(**kbytes_ps** est supérieur à 0, le processus tente de respecter
cette vitesse de livraison... ftp,ftps,ou sftp)

À ce stade, une configuration de pompe à pompe doit envoyer la notification à distance...
(Si la post_broker n’est pas définie, il n’y aura pas d’affichage... juste la réplication des produits)

La notification sélectionnée contiennent toutes les bonnes informations
(attributs de thème et d’en-tête) à l’exception du champ url dans l'avis... dans notre exemple : **http://this.pump.com/**

Par défaut, **sr_sender** place la **destination** dans ce champ.
L’utilisateur peut l’écraser en spécifiant l’option **post_baseUrl**. Par exemple:

**post_baseUrl http://remote.apache.com**

L’utilisateur peut fournir un script **on_post**. Juste avant que le message ne soit
publié sur les **post_broker** et **post_exchange**, le
**on_post** script s’appelle... avec l’instance de classe **sr_sender** comme argument.
Le script peut effectuer ce que vous voulez... s’il renvoie False, le message ne sera pas
publié. Si la valeur est True, le programme poursuivra le traitement à partir de là.

FIXME : Exemple de configuration manquant.


CONFIGURATION DE DESTINATION 2 : DIFFUSION DE TYPE METPX-SUNDEW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dans ce type d’utilisation, nous n’aurions généralement pas reposté... mais si le
**post_broker** et **post_exchange** (**url**,**on_post**) sont définis,
le produit sera annoncé (avec son éventuel nouvel emplacement et son nouveau nom).
Réintroduisons les options dans un ordre différent
avec quelques nouveaux pour faciliter l’explication.

Il y a 2 différences avec le cas précédent :
les options **directory** et **filename**.

Le **baseDir** est le même, tout comme la
**destination** et les options **post_baseDir**.

L’option **répertoire** définit un autre « chemin relatif » pour le produit
à destination.  Il est marqué aux options **accept** définies après lui.
Si une autre séquence de **directory**/**accept** suit dans le fichier de configuration,
le deuxième répertoire est marqué pour les acceptations suivantes et ainsi de suite.

Les modèles **accept/reject** s’appliquent à l’URL de notification du message comme ci-dessus.
Voici un exemple, voici quelques options de configuration ordonnées :

::

  directory /my/new/important_location

  accept .*IMPORTANT.*

  directory /my/new/location/for_others

  accept .*

Si la notification sélectionnée est, comme ci-dessus, ceci :

**20150813161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_product**

Il a été sélectionné par la première option **accept**. Le chemin relatif distant devient
**/my/new/important_location** ... et **sr_sender**  effectue la pseudo-livraison suivante :

envoie le fichier local [**baseDir**]/relative/path/to/IMPORTANT_product
à    **destination**/[**post_baseDir**]/my/new/important_location/IMPORTANT_product


Habituellement, cette façon d’utiliser **sr_sender** n’exigerait pas l’affichage du produit.
Mais si **post_broker** and **post_exchange** sont fournis, et **url** , comme ci-dessus, est défini sur
**http://remote.apache.com**,  alors **sr_sender** reconstruirait :

Thème: **v03.my.new.important_location.IMPORTANT_product**

Notice: **20150813161959.854 http://remote.apache.com/ my/new/important_location/IMPORTANT_product**



SHOVEL
------

shovel copie les messages sur un courtier (donné par l’option *broker*) à
un autre (donné par l’option *post_broker*) soumis au filtrage
par (*exchange*, *subtopic*, et éventuellement, *accept*/*reject*.)

L’option *topicPrefix* doit être définie sur :

 - pour pelleter les messages `sr3_post(7) <../Reference/sr3_post.7.html>`_

shovel est un flux avec les préréglages suivants :
   
   no-download True
   suppress_duplicates off


SUBSCRIBE
---------

Subscribe est le composant de flux de téléchargement normal, qui se connectera à un courtier, télécharger
les fichiers configurés, puis transférer les messages avec une baseUrl modifiée.

WATCH
-----

Surveille un répertoire et publie des messages lorsque les fichiers dans le répertoire changent.
Ses arguments sont très similaires à `sr_post <sr_post <sr_post.1.rst>`_.
Dans la suite MetPX-Sarracenia, l'objectif principal est d'afficher la disponibilité et modifications
de ses dossiers. Les abonnés utilisent *sr_subscribe* pour consommer le message et télécharger les fichiers changés.

Les messages sont envoyés à un serveur AMQP, également appelé courtier, spécifié avec l'option [ *-pb|--post_broker broker_url* ].

The [*-post_baseUrl|--pbu|--url url*] option specifies the protocol, credentials, host and port to which subscribers
will connect to get the file.

Format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:


L'option[*-p|--chemin*] indique à *sr_watch* ce qu'il faut chercher.
Si le *path* spécifie un répertoire, *sr_watches* crée un message quand
un fichier dans ce répertoire qui est créé, modifié ou supprimé.
Si le *path* spécifie un fichier, *sr_watch* surveille uniquement ce fichier.
Dans l'avis, il est spécifié avec le *chemin* du produit.
Il y a généralement un message par fichier.


Un exemple d'une excution de *sr_watch* vérifiant un fichier::

 sr3 --post_baseUrl sftp://stanley@mysftpserver.com/ --path /data/shared/products/foo --post_broker amqp://broker.com start watch/myflow

Ici, *sr_watch* vérifie les événements sur le fichier /data/shared/products/foo.
Les paramètres par défaut des rapports d'événements si le fichier le fichier est modifié ou supprimé.
Lorsque le fichier est modifié, *sr_watch* lit le fichier /data/shared/products/foo.
et calcule sa somme de contrôle.  Il construit ensuite un message, se connecte à broker.com
en tant qu'utilisateur'guest' (informations d'identification par défaut).
et envoie le message aux valeurs par défaut vhost '/' et échange 'xs_stanley' (échange par défaut)

Un abonné peut télécharger le fichier /data/shared/products/foo en se connectant en tant qu'utilisateur stanley.
sur mysftpserver.com en utilisant le protocole sftp à broker.com en supposant qu'il a les informations d'identification appropriées.

La sortie de la commande est la suivante::

 [INFO] v03.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo'
       source=guest parts=1,256,1,0,0 sum=d,fc473c7a2801babbd3818260f50859de 

Dans MetPX-Sarracenia, chaque article est publié sous un certain thème.
Après le '[INFO]', l'information suivante donne le \fBtopic* du fichier
publié. Les thèmes dans *AMQP* sont un champ hierarchique, avec chaque sous-thème séparé par une points. Dans
MetPX-Sarracénie il est constitué d'un *topic_prefix* par défaut : version *V02*, d'une action *post*..,
suivi par *subtopic* par défaut : le chemin du fichier séparé par des points, ici, *data.shared.products.foo*.

Après la hiérarchie des thèmes vient le corps de l'avis.  Il se compose d'un temps *20150813161959.854*,
et l'url source du fichier dans les 2 derniers champs.

La ligne restante donne des informations qui sont placées dans l'en-tête du message amqp.
Ici, il se compose de *source=guest*, qui est l'utilisateur amqp, *parts=1,256,0,0,0,1*..,
qui proposent de télécharger le fichier en 1 partie de 256 octets (la taille réelle du fichier), suivi de 1,0,0,0.
donne le nombre de blocs, le nombre d'octets restants et le nombre d'octets actuel.
bloc.  *sum=d,fc473c7a2801babbd3818260f50859de* mentionne les informations de la somme de contrôle,
ici, *d* signifie la somme de contrôle md5 effectuée sur les données, et *fc473c7a2801babbd3818260f50859de*.
est la valeur de la somme de contrôle.  Lorsque l'événement sur un fichier est une suppression, sum=R,0 R
signifie de supprimer un fichier.

Un autre exemple avec un fichier::

 sr3 --post_baseDir /data/web/public_data --post_baseUrl http://dd.weather.gc.ca/ --path bulletins/alphanumeric/SACN32_CWAO_123456 -post_broker amqp://broker.com start watch/myflow

Par défaut, sr_watch vérifie le fichier /data/web/public_data/bulletins/alphanumériques/SACN32_CWAO_123456
(concaténer le répertoire base_dir et le chemin relatif de l'url source pour obtenir le chemin du fichier local).
Si le fichier change, il calcule sa somme de contrôle. Il construit ensuite un message, se connecte à broker.com en tant qu'utilisateur'guest'.
(informations d'identification par défaut) et envoie le message aux valeurs par défaut vhost'/' et exchange'sx_guest' (échange par défaut)

Un abonné peut télécharger le fichier http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_CWAO_123456 en utilisant http.
sans authentification sur dd.weather.gc.ca.

Un exemple de vérification d'un répertoire::

 sr3 -post_baseDir /data/web/public_data -post_baseUrl http://dd.weather.gc.ca/ --path bulletins/alphanumeric --post_broker amqp://broker.com start watch/myflow

Ici, sr_watch vérifie la création de fichiers (modification) dans /data/web/public_data/bulletins/alphanumérique.
(concaténer le répertoire base_dir et le chemin relatif de l'url source pour obtenir le chemin du répertoire).
Si le fichier SACN32_CWAO_123456 est créé dans ce répertoire, sr_watch calcule sa somme de contrôle.
Il construit ensuite un message, se connecte à broker.com en tant qu'utilisateur'guest'.
(informations d'identification par défaut) et envoie le message à exchange'amq.topic' (échange par défaut)

Un abonné peut télécharger le fichier créé/modifié http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_CWAO_123456 en utilisant http.
sans authentification sur dd.weather.gc.ca.

WINNOW
------

**winnow** est un programme qui s'abonne aux notifications de fichiers,
et réenregistre les notifications, en supprimant les notifications redondantes.

La méthode de décider quels messages d´annonce sont redondants varient selon le cas d´usage.
Normalement, les messages comprenned un champs *Integrity* qui avec une somme de contrôle
du ficher, tel que décrit dans `sr_post(7) <../Reference/sr_post.7.html>`_
Il y bien d´autres cas d´usage discutés dans `Supprimer les doublons <SupprimerLesDoublons.html>`_

**winnow** a les options suivante forcés::

   no-download True  
   suppress_duplicates on
   accept_unmatch True

La durée de vie des suppress_duplicates peut être ajustée, mais elle est toujours active.

**winnow** se connecte à un *broker* (souvent le même que le courtier d'affichage).
et souscrit aux notifications d'intérêt. Sur réception d´un avis, il cherche sa **sum**
dans son cache. s'il est trouvé, le fichier est déjà passé, de sorte que la notification
est ignorée. Si ce n'est pas le cas, le fichier est nouveau, et le **sum** est ajouté.
dans le cache et l'avis est affiché.

**winnow** peut être utilisé pour couper les messages de `sr3_post <../Reference/sr3_post.1.html>`_,
`sr_poll(1) <sr_poll.1.rst>`_ ou `sr_watch(1) <sr_watch.1.rst>`_ etc..... C'est
utilisé lorsqu'il y a plusieurs sources de données identiques, de sorte que les
clients ne téléchargent que le fichier une seule fois, à partir de la première
source qui les a publié.

**winnow** peut être utilisé pour couper les messages de post, `sr3_post <../Reference/sr3_post.1.html>`_,
sr3_cpost_, `poll`_ ou `watch`_ etc... C'est utilisé lorsqu'il y a plusieurs sources de
données identiques, de sorte que les clients ne téléchargent que le fichier une seule fois,
à partir de la première source qui les a publié.


Configurations
==============

Si on a une configuration prête à l'emploi appelée *q_f71.conf*, elle peut être
ajoutée à la liste des noms connus avec ::

  subscribe add q_f71.conf

Dans ce cas-ci, q_f71.conf est inclus avec les exemples fournis, donc *add* le trouve
dans les exemples et le copie dans le répertoire des configurations actives.
Chaque fichier de configuration gère les consommateurs pour une seule file
d'attente sur le courtier. Pour visualiser les configurations disponibles,
utilisez::

  $ subscribe list

    configuration examples: ( /usr/lib/python3/dist-packages/sarra/examples/subscribe ) 
              all.conf     all_but_cap.conf            amis.conf            aqhi.conf             cap.conf      cclean_f91.conf 
        cdnld_f21.conf       cfile_f44.conf        citypage.conf       clean_f90.conf            cmml.conf cscn22_bulletins.conf 
          ftp_f70.conf            gdps.conf         ninjo-a.conf           q_f71.conf           radar.conf            rdps.conf 
             swob.conf           t_f30.conf      u_sftp_f60.conf 
  
    user plugins: ( /home/peter/.config/sarra/plugins ) 
          destfn_am.py         destfn_nz.py       msg_tarpush.py 
  
    general: ( /home/peter/.config/sarra ) 
            admin.conf     credentials.conf         default.conf
  
    user configurations: ( /home/peter/.config/sarra/subscribe )
       cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf         ftp_f70.conf           q_f71.conf 
            t_f30.conf      u_sftp_f60.conf


On peut ensuite le modifier à l'aide de ::

  $ subscribe edit q_f71.conf

(La commande d'édition utilise la variable d'environnement EDITOR, si elle est présente.
Une fois les changements complétés, on peut démarrer la configuration avec ::


  $ subscibe foreground q_f71.conf

Que contiennent les fichiers ? Voir la section suivante :


* La barre oblique (/) est utilisée comme séparateur de chemin dans les fichiers de configuration Sarracenia sur tous les
  systèmes d’exploitation. L'utilisation de la barre oblique inverse comme séparateur (\) (tel qu’utilisé dans la
  cmd shell de Windows) risque de ne pas fonctionner correctement. Lorsque des fichiers sont lu dans Windows, le chemin d’accès
  est immédiatement converti en utilisant la barre oblique. Ceci est pour s'assurer que les options *reject*, *accept*, et
  *strip* peuvent filtrer des expressions correctement. C'est pour cela qu'il est toujours important d'utiliser la barre
  oblique (/) quand un séparateur est nécessaire.
  
Example::

    directory A
    accept X

Place les fichiers correspondant à X dans le répertoire A.

au lieu::
    accept X
    directory A

Place les fichiers correspondant à X dans le répertoire de travail actuel,
et le paramètre *directory A* ne fait rien par rapport à X.

Pour fournir une description non fonctionnelle de la configuration ou des
commentaires, utilisez des lignes commençant par **#**.  Toutes les options
sont sensibles aux majuscules et minuscules. **Debug** n'est pas le même
que **debug** ou **DEBUG**. Il s'agit de trois options différentes (dont deux
n'existent pas et n'auront aucun effet, mais devrait générer une
avertissement ´unknown option´).

Les options et les paramètres de ligne de commande sont équivalents.  Chaque
paramètre de ligne de commande a une version longue correspondante commençant
par'--'.  Par exemple, *-u* est la forme courte de *--url*. On peut
aussi spécifier cette option dans un fichier de configuration. Pour ce faire,
utilisez la forme longue sans le'--', suivi de sa valeur séparée par un
espace. Les éléments suivants sont tous équivalents :

  - **url <url>**
  - **-u <url>**
  - **--url <url>**

Les réglages sont interprétés dans l'ordre.  Chaque fichier est lu de haut en bas.
par exemple :

sequence #1::

  reject .*\.gif
  accept .*


sequence #2::

  accept .*
  reject .*\.gif


.. remarque::
   FIXME : est-ce que cela ne correspond qu'aux fichiers se terminant par'gif' ou devrions-nous y ajouter un $ ?
   correspondra-t-il à quelque chose comme.gif2 ? y a-t-il un .* supposé à la fin ?


Dans la séquence #1, tous les fichiers se terminant par 'gif' sont rejetés. Dans la séquence #2, le
accept .* (qui accepte tout) est lu avant la déclaration du rejet,
donc le rejet n’a aucun effet. Certaines options ont une portée globale, plutôt que d’être
interprété dans l’ordre. Dans ces cas, la dernière déclaration remplace celle qu'il y avait plus tôt dans le fichier..

Les options qui doivent être réutilié dans de fichier de config différents peuvent
être groupés dans des fichiers *include*:

  - **--include <includeConfigPath>**

The includeConfigPath would normally reside under the same config dir of its
master configs. If a URL is supplied as an includeConfigPATH, then a remote 
configuraiton will be downloaded and cached (used until an update on the server 
is detected.) See `Remote Configurations`_ for details.

Environment variables, and some built-in variables can also be put on the
right hand side to be evaluated, surrounded by ${..} The built-in variables are:
 
 - ${BROKER_USER} - le nom d’utilisateur pour l’authentification auprès du courtier (par exemple, anonyme)
 - ${PROGRAM}     - le nom du composant (subscribe, shovel, etc...)
 - ${CONFIG}      - le nom du fichier de configuration en cours d'exécution.
 - ${HOSTNAME}    - le hostname qui exécute le client.
 - ${RANDID}      - Un ID aléatoire qui va être consistant pendant la duration d'une seule invocation.

flowCallbacks
=============

Sarracenia utilise largement de petits extraits de code python qui personnalisent le
traitement appelé *flowCallback*. Flow_callbacks définit et utiliser des paramètres supplémentaires ::

  flowCallback sarracenia.flowcb.log.Log

Il existe également une forme plus courte pour exprimer la même chose::

  callback log

Quoi qu’il en soit, le module fait référence au fichier sarracenia/flowcb/msg/log.py dans le
package installé. Dans ce fichier, la classe Log est celle qui a été recherchée pour le point d'entré.
Le fichier log.py inclus dans le package est le suivant::

  from sarracenia.flowcb import FlowCB
  import logging

  logger = logging.getLogger( __name__ ) 

  class Log(Plugin):

    def after_accept(self,worklist):
        for msg in worklist.incoming:
            logger.info( "msg/log received: %s " % msg )
        return worklist

C’est une classe python normale, déclarée comme enfant de la classe sarracenia.flowcb.FlowCB.
Les méthodes (noms de fonction) dans le plugin décrivent quand
ces routines seront appelées. Pour plus de détails, consultez le
`Programmer's Guide <../Explanation/SarraPluginDev.rst>`_

Pour ajouter un traitement spécial des messages, créez un module en python
et faites-le inclure des points d’entrée.

Il existe également *flowCallbackPrepend* qui ajoute une classe flowCallback à l’avant
de la liste (qui détermine l’ordre d’exécution relatif entre les classes flowCallback.)


Options callback
----------------

les rappels livrés avec metpx-sr3 suivent la convention suivante :

* ils sont placés dans l’arborescence du répertoire sarracenia/flowcb.
* le nom de la classe principale est le même que le nom du fichier qui la contient.

nous fournissons donc le sucre syntaxique suivant::

  callback log    (is equivalent to *flowCallback sarracenia.flowcb.log.Log* )

Il y a de même un *callback_prepend* à remplir.

Importation d’extensions
------------------------

L’option *import* fonctionne d’une manière familière aux développeurs Python,
qui les rends disponibles pour une utilisation par le noyau Sarracenia, ou flowCallback.
Les développeurs peuvent ajouter des protocoles supplémentaires pour les messages ou
transfert de fichiers.  Par exemple::

  import torr

serait un nom raisonnable pour un protocole de transfert pour récupérer des
ressources avec le protocole bittorrent. Un squelette d’une telle chose
ressemblerait à ceci ::

  import logging

  logger = logging.getLogger(__name__)

  import sarracenia.transfer

  class torr(sarracenia.transfer.Transfer):
      pass

  logger.warning("loading")

Pour plus de détails sur la mise en œuvre des prolongations, consultez le
`Programmer's Guide <../Explanation/SarraPluginDev.rst>`_

Plugins v2 Obsolètes
--------------------

Il existe également un style de plugins plus ancien (v2). Qui sont généralement
précédé du nom du plugin ::

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

Un paramètre 'msg_to_clusters' est nécessaire par le plugin *msg_to_clusters*
référencés dans le *on_message* les plugins v2 sont un peu plus
encombrant à écrire. Ils sont inclus ici pour être complets, mais
les utilisateurs doivent utiliser la version 3 (flowCallback ou extensions)
discuté ensuite) lorsque cela est possible.

Raisons d’utiliser des plugins de style plus récents:

* La prise en charge de l’exécution des plugins v2 est réalisée à l’aide d’un flowcb
  appelé v2wrapper. Il effectue beaucoup de traitement pour conclure
  les structures de données v3 pour ressembler à celles de la v2, puis a
  pour propager les modifications. C’est un peu cher.

* les extensions de style plus récentes sont des modules python ordinaires, contrairement à
  v2 qui nécessitent des incantations magiques mineures.

* lorsqu’un module v3 (flowCallback ou importé) présente une erreur de syntaxe,
  tous les outils de l’interpréteur python s’appliquent, ce qui donne
  beaucoup plus de commentaires au codeur. Avec la v2, il
  dit seulement qu’il y a quelque chose qui ne va pas, beaucoup plus difficile à déboguer.

* l’api v3 est strictement plus puissante que la v2, car elle fonctionne
  sur des groupes de messages, plutôt que sur des messages individuels.

Environment Variables
---------------------

On peut aussi utiliser des variables d´environnement avec la syntax
*${ENV}* ou *ENV* est le nom d´une variable d´environnement. S´il faut
définir une variable d´environnement pour une utilisation par Sarracenia,
on peut l´indiquer dans un fichier de configuration::

  declare env HTTP_PROXY=localhost


Fichiers journal et Suivi
-------------------------

- debug
   L'option de déboggage **debug** est identique à l'utilisation de **loglevel debug**.

- logMessageDump  (défaut: off) booléen flag
  s’il est défini, tous les champs d’un message sont imprimés, plutôt qu’une simple référence url/chemin.

- logEvents ( défaut after_accept,after_work,on_housekeeping )
   émettre des messages de journal standard aux points donnés du traitement des messages.
   autres valeurs : on_start, on_stop, post, gather, ... etc...
  
- loglevel ( défaut: info )
   Le niveau de journalisation exprimé par la journalisation de python. Les valeurs possibles sont : critical, error, info, warning, debug.

- --logStdout ( défaut: False )  CAS D’UTILISATION EXPÉRIMENTAL POUR DOCKER

   *logStdout* désactive la gestion des journaux. Mieux utilisé sur la ligne de commande, car il y a
   certains risques de créer des fichiers stub avant que les configurations ne soient complètement analysées ::

       sr3 --logStdout start

   Tous les processus lancés héritent de leurs descripteurs de fichier du parent, donc toutes les sorties sont comme une session interactive.

   Cela contraste avec le cas normal, où chaque instance prend soin de ses journaux, en tournant et en purgeant périodiquement.
   Dans certains cas, on veut que d’autres logiciels s’occupent des logs, comme dans docker, où c’est préférable pour tous
   que la journalisation soie en sortie standard.

   Il n’a pas été mesuré, mais il y a une probabilité raisonnable que l’utilisation de *logStdout* avec de grandes configurations (des dizaines
   d'instances/processus configurés) entraînera soit une corruption des journaux, soit limitera la vitesse d’exécution de tous les processus
   à écrire à stdout.

- log_reject <True|False> ( défaut: False )
   afficher un ligne de journal pour chaque message rejeté.  Ceci peut produire des journeaux énorme.
   D’habitude utilisé uniquement lors du debogage.

- log <dir> ( défaut: ~/.cache/sarra/log ) (sur Linux)
   Répertoire dans lequel stocker les fichiers journaux.

- statehost <False|True> ( défaut: False )
   Dans les grands centres de données, l’annuaire de base peut être partagé entre des milliers de
   Nœuds. Statehost ajoute le nom du nœud après le répertoire de cache pour le rendre
   unique à chaque nœud. Ainsi, chaque nœud a ses propres fichiers d’état et journaux.
   Par exemple, sur un nœud nommé goofy, ~/.cache/sarra/log/ devient ~/.cache/sarra/goofy/log.

- logRotate <max_logs> ( défaut: 5 )
   Nombre maximal de journaux archivés.

- logRotate_interval <duration>[<time_unit>] ( défaut: 1 )
   La durée de l’intervalle avec une unité de temps optionnelle (c’est-à-dire 5m, 2h, 3d)

- permLog ( défaut: 0600 )
   Bits d’autorisation à définir sur les fichiers journaux.

Voir le `Subscriber Guide <../How2Guides/subscriber.rst>` pour une discussion plus détaillée sur les
options de journalisations et de techniques.

IDENTIFICATION (CREDENTIALS)
----------------------------

Normalement, on ne spécifie pas de mots de passe dans les fichiers de
configuration. Ils sont plutôt placés dans le fichier d´information d´identifcation::

   edit ~/.config/sr3/credentials.conf

Pour chaque url spécifié qui nécessite un mot de passe, on place une entrée
correspondante dans *credentials.conf*. L'option broker définit toutes les
informations d'identification pour se connecter au serveur **RabbitMQ**.

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (par défaut: amqps://anonymous:anonymous@dd.weather.gc.ca/ )

Pour tous les programmes de **sarracenia**, les parties confidentielles
des justificatifs d'identité sont stockées uniquement dans
~/.config/sarra/credentials.conf. Cela comprend les mots de passe pour la destination
et le courtier ainsi que les paramètres requis par les composants.  Une entrée par ligne.  Exemples :

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **amqps://usern:passwd@host/ login_method=PLAIN**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:De%3Aize@host  passive,binary,tls**
- **ftps://user8:%2fdot8@host:2121  active,ascii,tls,prot_p**
- **https://ladsweb.modaps.eosdis.nasa.gov/ bearer_token=89APCBF0-FEBE-11EA-A705-B0QR41911BF4**


Dans d'autres fichiers de configuration ou sur la ligne de commande, l'url
n'inclut pas le mot de passe ou spécification de clé.  L'url donné dans les
autres fichiers est utilisé comme clé de recherche pour credentials.conf.

Details d'Identifiants
~~~~~~~~~~~~~~~~~~~~~~

Vous devrez peut-être spécifier des options supplémentaires pour des entrées d’informations d’identification spécifiques.
Ces détails peuvent être ajoutés après la fin de l’URL, avec plusieurs détails séparés par des virgules (voir les exemples ci-dessus).

Détails pris en charge ::

- ``ssh_keyfile=<path>`` - (SFTP) Chemin d’accès au fichier de clés SSH
- ``passive`` - (FTP) Utiliser le mode passif
- ``active`` - (FTP) Utiliser le mode actif
- ``binary`` - (FTP) Utiliser le mode binaire
- ``ascii`` - (FTP) Utiliser le mode ASCII
- ``ssl`` - (FTP) Utiliser SSL/FTP standard
- ``tls`` - (FTP) Utiliser FTPS avec TLS
- ``prot_p`` - (FTPS) Utiliser une connexion de données sécurisée pour les connexions TLS (sinon, du texte clair est utilisé)
- ``bearer_token=<token>`` (or ``bt=<token>``) - (HTTP) Jeton de porteur pour l’authentification
- ``login_method=<PLAIN|AMQPLAIN|EXTERNAL|GSSAPI>`` - (AMQP) Par défaut, la méthode de connexion sera automatiquement déterminée. Cela peut être remplacé en spécifiant explicitement une méthode de connexion, ce qui peut être nécessaire si un courtier prend en charge plusieurs méthodes et qu’une méthode incorrecte est automatiquement sélectionnée.

Remarque::
 Les informations d’identification SFTP sont facultatives, car sarracenia cherchera dans le répertoire .ssh
 et utilisera les informations d’identification SSH normales qui s’y trouvent.

 Ces chaînes sont codées en URL, donc si un compte a un mot de passe avec un caractère spécial,
 son équivalent codé par l'URL peut être fourni.  Dans le dernier exemple ci-dessus,
 **%2f** signifie que le mot de passe réel est: **/dot8**
 L’avant-dernier mot de passe est : **De:olonize**. ( %3a étant la valeur codée url pour un caractère deux-points. )

TRAITEMENT PÉRIODIQUE
=====================

La plupart des traitements ont lieu à la réception d’un message, mais il y a une maintenance périodique
qui se produit à chaque intervalle *housekeeping* (la valeur par défaut est de 5 minutes.)  À chaque *housekeeping* tous les
les plugins *on_housekeeping* configurés sont exécutés. Par défaut, trois sont présents :

* log - imprime « housekeeping » dans le journal.
 * nodupe - vieillit les anciennes entrées dans le cache de réception, afin de minimiser sa taille.
 * memory - vérifie l’utilisation de la mémoire du processus et redémarre si elle est trop grande.

Le journal contiendra des messages des trois plugins à chaque intervalle de housekeeping, et
si un traitement périodique supplémentaire est nécessaire, l’utilisateur peut configurer d'autres
plugins à exécuter avec l’option *on_housekeeping*.

sanity_log_dead <interval> (défaut: 1.5*housekeeping)
-----------------------------------------------------

L’option **sanity_log_dead** définit la durée à prendre en compte avant de redémarrer
un composant.

nodup_ttl <off|on|999> (défaut: off)
------------------------------------

Le nettoyage des éléments expirés dans la store de suppression des doublons se produit à chaque housekeeping.

RÉCUPÉRATION D’ERREUR
=====================

Les outils sont conçus pour fonctionner bien sans surveillance, et donc lorsque des erreurs transitoires se produisent, ils
essayent de récupérer élégamment.  Il y a des délais d’attente sur toutes les opérations, et en cas de défaillance
détectée, le problème est noté pour une nouvelle tentative.  Des erreurs peuvent se produire à plusieurs reprises :

 * Établir une connexion avec le courtier.
 * perte d’une connexion avec le courtier
 * établir une connexion au serveur de fichiers pour un fichier (à télécharger).
 * perte d’une connexion au serveur.
 * pendant le transfert de données.

Initialement, les programmes essaient de télécharger (ou d’envoyer) un fichier un nombre de fois fixe (*tentatives*, par défaut: 3).
Si les trois tentatives de traitement du fichier échouent, le fichier est placé dans "réessayer".
Le programme poursuit ensuite le traitement des nouveaux éléments. Lorsqu’il n’y a pas de nouveaux éléments,
le programme recherche un fichier à traiter dans la file d’attente de nouvelles tentatives. Il vérifie ensuite si le fichier
est vieux, au-delà du *retry_expire* (par défaut : 2 jours). Si le fichier n’a pas expiré, alors
il déclenche une nouvelle série de tentatives de traitement du fichier. Si les tentatives échouent, il revient en arrière
dans la file d’attente de nouvelles tentatives.

Cet algorithme garantit que les programmes ne restent pas bloqués sur un seul mauvais produit qui empêche
le reste de la file d’attente en cours de traitement, et permet une récupération raisonnable et progressive,
permettant aux nouvelles données de circuler et en envoyant les anciennes données de manière opportuniste
lorsqu’il y a des lacunes.

Bien qu’un traitement rapide de bonnes données soit très souhaitable, il est important de ralentir en cas d’erreur.
Souvent, les erreurs sont liées à la charge, et une nouvelle tentative rapide ne fera qu’empirer les choses.
Sarracenia utilise le back-off exponentiel à de nombreux endroits pour éviter de surcharger un serveur lorsqu’il y a
des erreurs. Le back-off peut s’accumuler au point où les nouvelles tentatives peuvent être séparées d’une minute
ou deux. Une fois que le serveur recommence à répondre normalement, les programmes reviendront à la
vitesse normale de traitement.

EXEMPLES
========

Voici un court exemple complet de fichier de configuration ::

  broker amqps://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

Ce fichier ci-dessus se connectera au courtier dd.weather.gc.ca, se connectant en tant qu'anonyme
avec mot de passe anonyme (par défaut) pour obtenir des annonces a propos de fichiers dans le
répertoire http://dd.weather.gc.ca/model_gem_global/25km/grib2.
Tous les fichiers qui arrivent dans ce répertoire ou en dessous seront téléchargés
dans le répertoire actif (ou simplement imprimé en sortie standard si l'option -n
a été spécifié.)

Divers exemples de fichiers de configuration sont disponibles ici :

 `https://github.com/MetPX/sarracenia/tree/master/sarra/examples <https://github.com/MetPX/sarracenia/tree/master/sarra/examples>`_



QUEUES and MULTIPLE STREAMS
---------------------------

Lorsqu’il est exécuté, **subscribe** choisit un nom de file d’attente, ou il écrit
à un fichier nommé d’après le fichier de configuration donné comme argument pour **subscribe**
avec un suffixe .queue ( ."configfile".queue).
Si l’abonnement est arrêté, les messages publiés continuent de s’accumuler sur le
broker dans la file d’attente.  Lorsque le programme est redémarré, il utilise le nom de la file d’attente
stocké dans ce fichier pour se connecter à la même file d’attente et ne perd aucun message.

Les téléchargements de fichiers peuvent être parallélisés en exécutant plusieurs abonnements à l’aide de
la même file d’attente.  Les processus partageront la file d’attente et téléchargerons
une partie de ce qui a été sélectionné.  Il suffit de lancer plusieurs instances
d'abonnement dans le même utilisateur/répertoire à l’aide du même fichier de configuration.

Vous pouvez également exécuter plusieurs abonnements avec différents fichiers de configuration pour
avoir plusieurs flux de téléchargement dans le même répertoire,
et ce flux de téléchargement peut également être multi-flux.

.. REMARQUE::

  Alors que les courtiers gardent les files d’attente disponibles pendant un certain temps, les files d’attente prennent des ressources sur
  les courtiers, et sont nettoyés de temps en temps.  Une file d’attente à laquelle on n’accède pas pour
  une longue période (dépendante de la mise en œuvre) sera détruite.  Une file d’attente qui n’est pas
  accédé et ayant trop de fichiers (définis par l’implémentation) en file d’attente seront détruits.
  Les processus qui meurent doivent être redémarrés dans un délai raisonnable pour éviter la
  perte de notifications.

report et report_exchange
-------------------------

Pour chaque téléchargement, par défaut, un message de rapport amqp est renvoyé au broker.
Cela se fait avec l’option :

- **report <booléen>        (défaut: True)**
- **report_exchange <report_exchangename> (défaut: xreport|xs_*username* )**

Lorsqu’un rapport est généré, il est envoyé au *report_exchange* configuré. Les composants administratifs
publient directement sur *xreport*, tandis que les composants d'utilisateur publient sur le leur
échanges (xs_*nom d’utilisateur*). Les démons de rapport copient ensuite les messages dans *xreport* après validation.

Ces rapports sont utilisés pour le réglage de la livraison et pour les sources de données afin de générer des informations statistiques.
Définissez cette option sur **False**, pour empêcher la génération de rapports.

INSTANCES
---------

Parfois, une instance d’un composant et d’une configuration ne suffit pas pour traiter et envoyer toutes les notifications disponibles.

**instances      <integer>     (défaut:1)**

L’option d’instance permet de lancer plusieurs instances d’un composant et d’une configuration.
Lors de l’exécution de sender par exemple, un certain nombre de fichiers d’exécution sont créés.
Dans le répertoire ~/.cache/sarra/sender/configName ::

  A .sender_configname.state         est créé, contenant le nombre d’instances.
  A .sender_configname_$instance.pid est créé, contenant le PID du processus $instance.

Dans le répertoire ~/.cache/sarra/log::

  Un .sender_configname_$instance.log  est créé en tant que journal du processus $instance.

.. NOTE::
  Un bug connu dans l’interface de gestion '`sr <sr.8.rst>_` signifie que l’instance doit
  toujours être dans le fichier .conf (pas un .inc) et doit toujours être un nombre
  (pas une variable substituée ou une autre valeur plus complexe.

.. note::
  FIXME: indiquez également l’emplacement de Windows... fichiers dot sur Windows?


.. Note::
  Alors que les courtiers gardent les files d’attente disponibles pendant un certain temps, les files d’attente prennent des ressources sur les
  courtiers, et sont nettoyés de temps en temps.  Une file d’attente qui n’est pas
  accédé et ayant trop de fichiers en file d’attente (définis par l’implémentation) seront détruits.
  Les processus qui meurent doivent être redémarrés dans un délai raisonnable pour éviter la
  perte de notifications.  Une file d’attente à laquelle on n’accède pas pendant une longue période (dépendant de l’implémentation)
  sera détruite.

vip - ACTIVE/PASSIVE OPTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**sr3** peut être utilisé sur un seul nœud de serveur ou sur plusieurs nœuds.
pourrait partager la responsabilité. D'autres, configurés séparément, haute disponibilité
présente un **vip** (ip virtuel) sur le serveur actif. Si
le serveur tombe en panne, le **vip** est déplacé sur un autre serveur.
Les deux serveurs fonctionneraient **sr3**. Les options suivants contrôle
ce genre de comportement:

 - **vip          <string>          (None)**

Lorsque vous n'exécutez qu'un seul **sr3** sur un serveur, ces options ne
sont pas définies et sr3 fonctionnera en mode 'standalone'.

Dans le cas des courtiers en grappe, vous devez définir les options pour l'option
vip en mouvement.

**vip 153.14.126.3**

Lorsque **sr3** ne trouve pas le vip, il dort pendant 5 secondes et réessaie.
S´il possède le vip, il consomme et traite un message, puis revérifie le vip.


[--blocksize <value>] (default: 0 (auto))
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This **blocksize** option controls the partitioning strategy used to post files.
The value should be one of::

   0 - calcul automatique d'une stratégie de partitionnement appropriée (par défaut)
   1 - toujours envoyer des fichiers entiers en une seule partie.
   <blocksize> - utilisation d'une taille de partition fixe (exemple : 1M)

Les fichiers peuvent être publiés en plusieurs parties.  Chaque partie
a une somme de contrôle séparée. Les pièces et leurs sommes de contrôle sont
stockées dans le cache. Les cloisons peuvent traverser le réseau séparément,
et en parallèle.  Lorsque les fichiers changent, les transferts sont
optimisé en n'envoyant que des portions qui ont changé.

L'option *outlet*  permet la sortie finale d'être autre chose qu'un post.
Voir `sr3_cpump(1) <sr3_cpump.1.rst>`_ pour plus de détails.

[-pbd|--post_baseDir <path>] (facultatif)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option *post_baseDir* fournit le chemin du répertoire qui, lorsqu'il est
combiné (ou trouvé) dans le chemin d'accès donné, donne le chemin absolu local
vers le fichier de données à enregistrer. La *post_baseDir* du chemin sera
supprimée du avis. Pour sftp : url's il peut être approprié de spécifier un
chemin relatif à un compte utilisateur.  Un exemple de cette utilisation
serait :  -pbd ~user -url sftp:user@host
pour file : url's, baseDir n'est généralement pas approprié.  Pour publier
un chemin absolu, omettez le paramètre -pbd, et spécifiez simplement le chemin
complet en argument.

post_baseUrl <url> (OBLIGATOIRE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **post_baseUrl** définit comment obtenir le fichier.... il définit
le protocole, hôte, port, et optionnellement, l'utilisateur.  C'est une
bonne pratique de ne pas inclure les mots de passe dans l´URL.

post_exchange <name> (default: xpublic)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **post_exchange**, qui permet d'échanger la nouvelle notification.
sera publié.  Dans la plupart des cas, il s'agit d'un'xpublic'.

Chaque fois qu'une avis se produit pour un produit, un utilisateur peut
définir de déclencher un script. L'option **on_post** serait utilisée pour faire
une telle configuration.

post_exchangeSplit   <number>   (défaut: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **post_exchangeSplit** ajoute un suffixe à deux chiffres résultant d'une
division entière du dernier digit de la somme de contrôle, afin de répartir les
avis entre un certain nombre d'échanges, selon la valeur de leur somme de contrôle.
C'est utilisé dans les pompes à trafic élevé pour permettre des instances
multiples de winnow, ce qui ne peut pas être instancié de la manière normale. exemple::

    post_exchangeSplit 5
    post_exchange xwinnow

se traduira par l'envoi de messages à cinq échanges nommées xwinnow00, xwinnow01,
xwinnow02, xwinnow03 et xwinnow04, où chaque échange ne recevra qu'un cinquième du flux total.
xinnow01 recevra tous les messages dont la reste quand sa somme de contrôle est divisé par 5
est 1.

Remote Configurations
---------------------

On peut spécifier des URI comme fichiers de configuration, plutôt que des fichiers locaux. Exemple :

  - **--config http://dd.weather.gc.ca/alerts/doc/cap.conf**

Au démarrage, sr3 vérifie si le fichier local cap.conf existe dans le répertoire
répertoire de configuration local.  Si c'est le cas, alors le fichier sera lu pour trouver
une ligne comme ça :

  - **--remote_config_url http://dd.weather.gc.ca/alerts/doc/cap.conf**

Dans ce cas, il vérifiera l'URL distante et comparera le temps de modification.
du fichier distant contre le fichier local. Le fichier distant n'est pas plus récent ou ne peut pas être modifié.
est atteint, alors le composant continuera avec le fichier local.

Si le fichier distant est plus récent ou s'il n'y a pas de fichier local, il sera téléchargé,
et la ligne remote_config_url_config_url y sera pré-pendue, de façon à ce qu'elle continue
pour se mettre à jour à l'avenir.

Extensions
----------

On peut remplacer ou ajouter des fonctionnalités avec des scripts python.

Sarracenia est livré avec une variété d’exemples de plugins, et en utilise certains pour implémenter des fonctionnalités de base,
tels que la journalisation (implémentée par défaut en utilisant des plugins msg_log, file_log post_log)::

  
  $ sr3 list fcb
  Provided callback classes: ( /home/peter/Sarracenia/sr3/sarracenia ) 
  flowcb/filter/deleteflowfiles.py flowcb/filter/fdelay.py          flowcb/filter/pclean_f90.py      flowcb/filter/pclean_f92.py
  flowcb/gather/file.py            flowcb/gather/message.py         flowcb/line_log.py               flowcb/line_mode.py 
  flowcb/log.py                    flowcb/nodupe.py                 flowcb/pclean.py                 flowcb/post/message.py
  flowcb/retry.py                  flowcb/sample.py                 flowcb/script.py                 flowcb/v2wrapper.py
  flowcb/work/rxpipe.py            
  $ 

Les utilisateurs peuvent placer leurs propres scripts dans le sous-répertoire de script dans leur répertoire de configuration
( sur Linux, le ~/.config/sarra/plugins).

flowCallback et flowCallbackPrepend <class>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La directive flowCallback prend une classe à charger et peut analyser les points d’entrée comme argument ::

    flowCallback sarracenia.flowcb.log.Log
   
Avec cette directive dans un fichier de configuration, la classe Log trouvée dans le package installé sera utilisée.
Ce module enregistre les messages *after_accept* (après que les messages sont passé par les masques d’accept/reject)
et le *after_work* (après le téléchargement ou l’envoi du fichier). Voici le code source
pour cette classe de rappel ::

  import json
  import logging
  from sarracenia.flowcb import FlowCB

  logger = logging.getLogger(__name__)


  class Log(FlowCB):
    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)

    def after_accept(self, worklist):
        for msg in worklist.incoming:
            logger.info("accepted: %s " % msg_dumps(msg) )

    def after_work(self, worklist):
        for msg in worklist.ok:
            logger.info("worked successfully: %s " % msg.dumps() )

Si vous avez plusieurs rappels configurés, ils seront appelés dans le même ordre que dans
fichier de configuration. Les composants de sr3 sont souvent différenciés par les rappels configurés.
Par exemple, un *watch* est un flux avec la classe sarracenia.flowcb.gather.file.File qui
est utilisé pour analyser les répertoires. Un besoin courant lorsqu’une source de données n’est pas facilement accessible
avec les scripts python est d’utiliser le rappel de script::

   flowCallbackPrepend sarracenia.flowcb.script.Script

   script_gather get_weird_data.sh

En utilisant la variante *_prepend* de l’option *flowCallback*, le rappel de script aura le
point d’entrée de la classe, avant le rappel de fichier... Donc, un script sera exécuté, puis
le répertoire sera vérifié pour les nouveaux fichiers.  Voici une partie de la classe de rappel Script ::
    
    import logging
    from sarracenia.flowcb import FlowCB
    import subprocess
    
    logger = logging.getLogger(__name__)
    
    
    class Script(FlowCB):
    
       .
       .
       .
    
        def run_script( self, script ):
            try: 
                subprocess.run( self.o.script_gather, check=True )
            except Exception as err:
                logging.error("subprocess.run failed err={}".format(err))
                logging.debug("Exception details:", exc_info=True)
    
    
        def gather(self ):
            if hasattr( self.o, 'script_gather') and self.o.script_gather is not None :
                self.run_script( self.o.script_gather )
            return []
    
     
Integrity
---------

On peut utiliser la directive *import* pour ajouter de nouveaux algorithmes de somme de contrôle en sous-classant
sarracenia.integrity.Integrity.


Transfer 
--------

On peut ajouter la prise en charge de méthodes supplémentaires de téléchargement de données par sous-classification
sarracenia.transfer.Transfer.

Les scripts de protocole de transfert doivent être déclarés à l’aide de l’option **import**.
sauf pour les fonctions intégrées ciblées, un module **registered_as** qui définit
une liste des protocoles fournis par ces fonctions.  Exemple:

def registered_as(self) :
       return ['ftp','ftps']


Voir le `Programming Guide <../Explanation/SarraPluginDev.rst>`_ pour plus d’informations sur le développement d’extensions.



ROLES - feeder/admin/declare
----------------------------

*d’intérêt que pour les administrateurs*

Les options d'administration sont définies à l'aide de::

  edit ~/.config/sr3/admin.conf

L'option *feeder* spécifie le compte utilisé par défaut pour les transferts
système pour les composants tels que sr_shovel, sr_sarra et sr_sender (lors de publication).


-- **feeder amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>** (valeur par défaut : Aucun)
-- **admin <nom> (par défaut : Aucun)**

L’utilisateur administrateur est utilisé pour effectuer des opérations de maintenance sur la pompe, telles que la définition
des autres utilisateurs. La plupart des utilisateurs sont définis à l’aide de l’option *declare*. Le chargeur peut également être déclaré de cette
manière.

- **declare <role> <name>   (pas de défaut)**

subscriber
~~~~~~~~~~

  Un *subscriber* (abonné) est un utilisateur qui ne peut s'abonner qu'aux données
  et renvoyer des messages de rapport. Les abonnés ne sont pas autorisés à injecter des données.
  Chaque abonné a un central xs_<user>nommé sur la pompe, où si un utilisateur est
  nommé *Acme*, l'échange correspondant sera *xs_Acme*.  Cet échange
  est l'endroit où un processus sr_subscribe enverra ses messages de rapport.

  Par convention/défaut, l'utilisateur *anonyme* est créé sur toutes les pompes pour
  permettre l'abonnement sans un compte spécifique.

source
~~~~~~

  Un utilisateur autorisé à s’abonner ou à générer des données. Une source ne représente pas nécessairement
  une personne ou un type de données, mais plutôt une organisation responsable des données produites.
  Donc, si une organisation recueille et met à disposition dix types de données avec un seul contact,
  e-mail, ou numéro de téléphone, toute question sur les données et leur disponibilité par rapport aux
  activités de collecte peuvent alors utiliser un seul compte "source".

  Chaque source reçoit un échange xs_<utilisateur> pour l’injection de publications de données. Cela est comme un abonné
  pour envoyer des messages de rapport sur le traitement et la réception des données. La source peut également avoir
  un échange xl_<utilisateur> où, selon les configurations de routage des rapports, les messages de rapport des
  consommateurs seront envoyés.

feeder
~~~~~~
  
  Un utilisateur autorisé à écrire à n’importe quel échange. Une sorte d’utilisateur de flux administratif, destiné à pomper
  des messages lorsque aucune source ou abonné ordinaire n’est approprié pour le faire. Doit être utilisé de
  préférence au lieu de comptes d’administrateur pour exécuter des flux.


Les informations d’identification de l’utilisateur sont placées dans le `credentials.conf <sr3_credentials.7.html>`_
et *sr3 --users declare* mettra à jour le courtier pour accepter ce qui est spécifié dans ce fichier, tant que le
mot de passe de l'administrateur est déjà correct.


FICHIERS DE CONFIGURATION
-------------------------

Alors qu'on peut gérer les fichiers de configuration à l'aide de la fonction *add*, *remove*,
*list*, *edit*, *disable*, et *enable* actions, on peut aussi tout faire.
des mêmes activités manuellement en manipulant les fichiers dans les paramètres.
dans l'annuaire de l'entreprise.  Les fichiers de configuration pour une configuration sr_subscribe.
appelé *myflow* serait ici :

 - linux : ~/.config/sarra/subscribe/myflow.conf (selon : `XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.rst>`_ )

 - Windows : %AppDir%/science.gc.ca/sarra/myflow.conf, cela pourrait être :
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\sarra\myflow.conf

 - MAC : FIXME.

Le sommet de l'arborescence a *~/.config/sarra/default.conf* qui contient les paramètres suivants
sont lus par défaut pour tout composant au démarrage. Dans le même répertoire,
*~/.config/sarra/credentials.conf* contient des informations d'identification
(mots de passe) à utiliser par sarracenia (`CREDENTIALS`_ pour plus de détails. ).

On peut également définir la variable d'environnement XDG_CONFIG_HOME pour remplacer
le placement par défaut, ou bien Les fichiers de configuration individuels peuvent
être placés dans n'importe quel répertoire et invoqués avec la commande chemin complet.
Lorsque des composants sont invoqués, le fichier fourni est interprété comme un fichier
(avec un suffixe.conf conf supposé.) S'il n'est pas trouvé comme chemin d'accès au
fichier, alors l'option recherchera dans le répertoire de configuration du
composant ( **config_dir** / **component**) pour un fichier.conf correspondant.

S'il n'est toujours pas trouvé, il le recherchera dans le répertoire de configuration du site.
(linux : /usr/share/default/sarra/**component**).

Enfin, si l'utilisateur a défini l'option **remote_config** sur True et s'il
dispose de sites web configurés où l'on peut trouver des configurations
(option **remote_config_config_url**), Le programme essaiera de télécharger
le fichier nommé à partir de chaque site jusqu'à ce qu'il en trouve un.
En cas de succès, le fichier est téléchargé dans **config_dir/Downloads** et
interprété par le programme à partir de là.  Il y a un processus similaire
pour tous les *plugins* qui peuvent être interprété et exécuté à l'intérieur
des composantes de la Sarracenia.  Les composants chercheront en premier lieu
dans le répertoire *plugins* dans l'arbre de configuration des
utilisateurs, puis dans le site, puis dans le paquet sarracenia lui-même,
et finalement il regardera à distance.



OPTIONS DE COMPATIBILITÉ SUNDEW
-------------------------------

Pour la compatibilité avec Sundew, il existe des options de livraison supplémentaires qui peuvent être spécifiées.


destfn_script <script> (défaut:None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cette option définit un script à exécuter lorsque tout est prêt
pour la livraison du produit. Le script reçoit une instance de la classe sender.
Le script prends le parent comme argument, et par exemple, une
modification de **parent.msg.new_file** changera le nom du fichier écrit localement.

filename <mots-clé> (défaut:WHATFN)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

De **MetPX Sundew**, le support de cette option donne toutes sortes de possibilités
pour définir le nom de fichier distant. Certains **keywords** sont basés sur le fait que
les noms de fichiers **MetPX Sundew** ont cinq (à six) champs de chaîne de caractères séparés par des deux-points.

La valeur par défaut sur Sundew est NONESENDER, mais dans l’intérêt de décourager l’utilisation
de la séparation par des deux-points dans les fichiers, le défaut dans Sarracenia est WHATFN.

Les mots-clés possibles sont :

**WHATFN**
 - la première partie du nom de fichier Sundew (chaîne de caractères avant le premier : )

**HEADFN**
 - Partie EN-TETE du nom de fichier Sundew

**SENDER**
 - le nom de fichier Sundew peut se terminer par une chaîne SENDER=<string> dans ce cas,
   la <string> sera le nom de fichier distant

**NONE**
 -  livrer avec le nom du fichier Sundew complet (sans :SENDER=...)

**NONESENDER**
 -  livrer avec le nom de fichier Sundew complet (avec :SENDER=...)

**TIME**
 - horodatage ajouté au nom de fichier. Exemple d’utilisation : WHATFN:TIME

**DESTFN=str**
 - déclaration str direct du nom de fichier

**SATNET=1,2,3,A**
 - Paramètres d’application satnet interne cmc

**DESTFNSCRIPT=script.py**
 - appeler un script (identique à destfn_script) pour générer le nom du fichier à écrire

**accept <regexp pattern> [<keyword>]**

Keyword peut être ajouté à l’option **accept**. Le keyword est une des options **filename**.
Un message qui correspond au modèle accept regexp aura son remote_file
appliqué à cette option de mot-clé.  Ce mot-clé a la priorité sur le précédent **nom de fichier**.

Le **regexp pattern** peut être utilisé pour définir des parties du répertoire si une partie du message est placée
entre parenthèses. **sender** peut utiliser ces parties pour générer le nom du répertoire.
Les chaînes de parenthèses entre les guillemets rst remplaceront le mot-clé **${0}** dans le nom du répertoire...
le second **{1} $ ** etc.

Exemple d’utilisation ::


      filename NONE

      directory /this/first/target/directory

      accept .*file.*type1.*

      directory /this/target/directory

      accept .*file.*type2.*

      accept .*file.*type3.*  DESTFN=file_of_type3

      directory /this/${0}/pattern/${1}/directory

      accept .*(2016....).*(RAW.*GRIB).*


Un message sélectionné par le premier *accept* sera remis inaltérée dans le premier répertoire.

Un message sélectionné par le deuxième *accept* sera remis inaltérée dans deuxième répertoire.

Un message sélectionné par le troisième *accept sera renommé « fichier_de_type3 » dans le deuxième répertoire.

Un message sélectionné par le quatrième *accept* sera remis inaltérée à un répertoire.

Ça sera appelé  */ce/20160123/modèle/RAW_MERGER_GRIB/répertoire* si la notice du message ressemble à cela:

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**




Field Replacements
~~~~~~~~~~~~~~~~~~

Dans MetPX Sundew, le format de la nomination de fichier est beaucoup plus
stricte, et est spécialisée pour une utilisation aves les données du World Meteorological Organization (WMO).
Notez que la convention du format des fichiers est antérieure, et n’a aucun rapport avec la convention de
dénomination des fichiers de WMO actuellement approuvée, et est utilisé strictement comme format interne. Les fichiers sont
séparés en six champs avec deux points. Le premier champ, DESTFN, est le "Abbreviated Header Line (AHL)" de WMO
(style 386) ou les blancs sont remplacé avec des traits de soulignement ::

   TTAAii CCCC YYGGGg BBB ...  

(voir le manuel de WMO pour plus de détails) suivis de chiffres pour rendre le produit unique (cela est vrai en
théorie, mais pas en pratique vu qu'il existe un grand nombre de produits qui ont les mêmes identifiants).
La signification du cinquième champ est une priorité, et le dernier champ est un horodatage.
La signification des autres champs varie en fonction du contexte. Exemple de nom de fichier ::

   SACN43_CWAO_012000_AAA_41613:ncp1:CWAO:SA:3.A.I.E:3:20050201200339

Si un fichier est envoyé à Sarracenia et qu’il est nommé selon les conventions de Sundew,
les champs de substitution suivants seront disponibles::

  ${T1}    remplacer par le bulletin T1
  ${T2}    remplacer par le bulletin T2
  ${A1}    remplacer par le bulletin A1
  ${A2}    remplacer par le bulletin A2
  ${ii}    remplacer par le bulletin ii
  ${CCCC}  remplacer par le bulletin CCCC
  ${YY}    remplacer par le bulletin YY   (obs. jour)
  ${GG}    remplacer par le bulletin GG   (obs. heure)
  ${Gg}    remplacer par le bulletin Gg   (obs. minute)
  ${BBB}   remplacer par le bulletin bbb
  ${RYYYY} remplacer par l'année de réception
  ${RMM}   remplacer par le mois de réception
  ${RDD}   remplacer par le jour de réception
  ${RHH}   remplacer par l'heure de réception
  ${RMN}   remplacer par la minute de réception
  ${RSS}   remplacer par la seconde de réception

Les champs 'R' proviennent du sixième champ, et les autres viennent du premier champ.
Lorsque des données sont injectées dans Sarracenia à partir de Sundew, l’en-tête du message *sundew_extension*
fournira la source de ces substitions même si ces champs ont été supprimés des fichiers livrés.

