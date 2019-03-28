
===================================
 Guide de Programmation Sarracenia
===================================

[ `version anglaise <../Prog.rst>`_ ] 

------------------------
 Programmer des Plugins
------------------------


Revision Record
---------------

:version: @Version@
:date: @Date@


Audience
--------

Les lecteurs de ce manuel devraient être à l'aise avec les scripts légers en
python version 3.  Sarracenia comprend un certain nombre de points où le
traitement peut être personnalisé par les moyens suivants de petits fragments
de code fourni par l'utilisateur, connus sous le nom de plugins.  Les plugins
eux-mêmes sont attendus d'être concis, et une connaissance élémentaire de
python devrait suffire à construire de nouveaux plugins de manière 
copier/coller, avec de nombreux exemples à lire.


Idées de plugin
---------------

Exemples de choses qui seraient amusantes à faire avec les plugins.

- Common Alerting Protocol ou CAP, est un format XML qui fournit un avertissement.
  pour de nombreux types d'événements, en indiquant la zone de couverture.  Il y 
  a un *polygone* dans l'avertissement, que la source pourrait ajouter aux 
  messages à l'aide de la commande un plugin on_post. Les abonnés auraient
  accès à l'en-tête 'polygone' par l'utilisation d'un plugin on_message, ce
  qui leur permet de déterminer si l'option a affecté une zone d'intérêt
  sans télécharger la totalité de l'avertissement.

- Une source qui applique la compression aux produits avant de les poster,
  pourrait ajouter un tel que'uncompressed_size' et'uncompressed_sum' pour
  permettre l'utilisation de avec un plugin on_message pour comparer un fichier
  qui a été enregistré localement non compressé en un fichier amont offert
  sous forme compressée.
  

------------
Introduction
------------

Une pompe de données Sarracenia est un serveur web avec des notifications
pour les abonnés à savoir, rapidement, quand de nouvelles données sont
arrivées. Pour savoir quelles sont les données qui existent déjà disponible
sur une pompe, visualiser l'arbre avec un navigateur web. Pour une
utilisation simple et immédiate on peut télécharger les données en utilisant
le navigateur lui-même ou un outil standard comme wget. L'intention habituelle
est que sr_subscribe télécharge automatiquement les données voulus dans un
répertoire sur une machine d'abonné où d'autres logiciels peut le traiter.

Souvent, le but du téléchargement automatisé est de le subir à un traitement
ultérieur. Plutôt que d'avoir a sonder le répertoire avec un autre processus,
on peut insérer des traitements personnalisés.

Des exemples sont disponibles à l'aide de la commande list::


  blacklab% sr_subscribe list
  
  packaged plugins: ( /home/peter/src/sarracenia/sarra/plugins ) 
        bad_plugin1.py       bad_plugin2.py       bad_plugin3.py                cp.py     destfn_sample.py 
        download_cp.py       download_dd.py      download_scp.py     download_wget.py          file_age.py 
         file_check.py          file_log.py       file_rxpipe.py        file_total.py           harness.py 
           hb_cache.py            hb_log.py         hb_memory.py          hb_pulse.py         html_page.py 
           line_log.py         line_mode.py               log.py         msg_2http.py        msg_2local.py 
     msg_2localfile.py     msg_auditflow.py     msg_by_source.py       msg_by_user.py         msg_delay.py 
         msg_delete.py      msg_download.py          msg_dump.py        msg_fdelay.py msg_filter_wmo2msc.py 
   msg_from_cluster.py     msg_hour_tree.py           msg_log.py     msg_print_lag.py   msg_rename4jicc.py 
     msg_rename_dmf.py msg_rename_whatfn.py       msg_renamer.py msg_replace_new_dir.py          msg_save.py 
       msg_skip_old.py        msg_speedo.py msg_sundew_pxroute.py    msg_test_retry.py   msg_to_clusters.py 
          msg_total.py        part_check.py  part_clamav_scan.py        poll_pulse.py       poll_script.py 
     post_hour_tree.py          post_log.py    post_long_flow.py     post_override.py   post_rate_limit.py 
         post_total.py         watch_log.py              wget.py 
  
  configuration examples: ( /home/peter/src/sarracenia/sarra/examples/subscribe ) 
              all.conf     all_but_cap.conf            amis.conf            aqhi.conf             cap.conf 
       cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf        citypage.conf       clean_f90.conf 
             cmml.conf cscn22_bulletins.conf         ftp_f70.conf            gdps.conf         ninjo-a.conf 
            q_f71.conf           radar.conf            rdps.conf            swob.conf           t_f30.conf 
       u_sftp_f60.conf 
  user plugins: ( /home/peter/.config/sarra/plugins ) 
          destfn_am.py         destfn_nz.py       msg_tarpush.py              wget.py 
  
  general: ( /home/peter/.config/sarra ) 
            admin.conf     credentials.conf         default.conf
  
  
  user configurations: ( /home/peter/.config/sarra/subscribe )
       cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf         ftp_f70.conf 
            q_f71.conf           t_f30.conf      u_sftp_f60.conf 
  
  blacklab% 

Les plugins *de série* sont montrés dans le premier groupe des plugins disponibles. 
Beaucoup d'entre eux ont des arguments qui sont documentés via *list*. Une exemple
de plugin de base:

.. code:: python


  blacklab% sr_subscribe list msg_log.py
  #!/usr/bin/python3

  """
    the default on_msg handler for subscribers.  Prints a simple notice.
  
  """

  class Msg_Log(object):  # Mandatory: declare a class, with a capital letter in it.

      def __init__(self,parent):  # Mandatory: declare a constructor.
          parent.logger.debug("msg_log initialized")

      def on_message(self,parent):  # Mandatory: Declare an function to be called when messages are accepted.
          msg = parent.msg
          parent.logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % \
             tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
          return True

  msg_log = Msg_Log(self)   # Mandatory: Declare a variable of the class.

  self.on_message = msg_log.on_message # Mandatory: assign the function to the entry point.

  blacklab%


Pour le modifier, copiez-le à partir du répertoire examples installé dans le
cadre du paquet vers la préférence éditable::


  blacklab% sr_subscribe add msg_log.py


And then modify it for the purpose::

  blacklab% sr_subscribe edit msg_log.py

Le plugin msg_log.py ci-dessus est un plugin à entrée unique. Pour les plugins
avec une seule fonction, consultez bad_plugins1, 2 et 3  pour identifier les
éléments obligatoires. Comme on pourrait l'imaginer, tous les plugins qui 
commencent par msg\_sont pour les événements *on_msg*.  Similairement, file\_ 
sont des exemples de *on_file*, etc... pour les autres types de plugins à 
entrée unique.

Si un plugin n'a pas un tel préfixe, il y a une deuxième forme de plugins
appelée simplement un *plugin*, où un groupe de routines pour mettre en 
œuvre une fonction globale. Examinez les routines *log.py* et *wget.py* pour
des exemples de ce format.

On peut aussi voir quels plugins sont actifs dans une configuration en 
regardant les messages au démarrage::

   blacklab% sr_subscribe foreground clean_f90
   2018-01-08 01:21:34,763 [INFO] sr_subscribe clean_f90 start

   .
   .
   .

   2018-01-08 01:21:34,763 [INFO]  Plugins configured:
   2018-01-08 01:21:34,763 [INFO]      do_download: 
   2018-01-08 01:21:34,763 [INFO]      on_message: Msg_FDelay Msg_2LocalFile Msg_AuditFlow Msg_Delete 
   2018-01-08 01:21:34,764 [INFO]      on_part: 
   2018-01-08 01:21:34,764 [INFO]      on_file: File_Log 
   2018-01-08 01:21:34,764 [INFO]      on_post: Post_Log 
   2018-01-08 01:21:34,764 [INFO]      on_heartbeat: Hb_Log Hb_Memory Hb_Pulse 
   .
   .
   .
   blacklab% 


---------------------
Plugin Exemple Simple
---------------------

Un exemple, du format *plugin*, on peut configurer l'utilisation de
file_noop.py dans une configuration comme suit::

 
  plugin file_noop

Le contenu du fichier à placer (sous Linux) dans ~/.config/sarra/plugins serait :

.. code:: python

  # MUST: declare a class with Upper case characters in it.

  class File_Noop(object):
      def __init__(self,parent):
          parent.declare_option( 'file_string' )  # declare options to avoid 'unknown option' messages being logged.

      def on_start(self,parent):
          if not hasattr(parent,'file_string'):  # set default values here, if necessary.
             parent.file_string='hello world'
      
      def on_file(self,parent):
          parent.logger.info("file_noop: I have no effect but adding a log line with %s in it" % parent.file_string )
          return True

  self.plugin = 'File_Noop'   # MUST: set the value of the plugin variable to the name of the class.


Il y a une partie d'initialisation qui s'exécute lorsque le composant est démarré,
une section d'exécution qui doit être invoquée sur l'événement approprié.  
le plugin nécessite les deux dernières lignes magiques dans le plugin sample, où 
la dernière ligne doit refléter le type de plugin (on_file pour un plugin 
on_file, on_message, pour un message on_message, etc....)

Le seul argument que le script reçoit est **parent**, qui a toutes les options.
des fichiers de configuration et de la ligne de commande en tant qu'attributs.  Par exemple,
si un réglage comme::

  msg_speedo_interval 10

est défini dans un fichier de configuration, alors le script du plugin aura
*parent.msg_speedo_speedo_interval* comme variable définie à '10' (la 
chaîne, pas le nombre.) Par convention lors de l'invention de nouveaux 
paramètres de configuration, le nom de l'élément le plugin est utilisé 
comme préfixe (dans cet exemple, msg_speedo)

En plus des options de ligne de commande, il y a aussi un logger disponible.
comme indiqué dans l'échantillon ci-dessus.  Le *logger* est un objet logger
python3, tel que documenté.  
ici : https://docs.python.org/3/library/logging.html.   Pour permettre aux 
utilisateurs d'accorder la fonction verbosité des journaux, utiliser une 
méthode spécifique pour classer les messages::

  logger.debug - beaucoup de détail pour dévéloppement ou dépistage.
  logger.info  - messages informatifs 
  logger.warn  - avertissement de ce qui est probablement une problème.
  logger.error - une erreur.

Dans le message ci-dessus, logger.info est utilisé, indiquant un message 
informatif. Un autre attribut utile disponible dans parent, est'msg', qui a
tous les attributs du message en cours de traitement. Tous les en-têtes du
message, tels que définis dans le fichier de configuration 
`sr_post(1) <sr_post.1.rst>`, sont disponibles pour le plugin, tel que la
somme de contrôle des messages comme *parent.msg.headers.headers.sum*.
Consulter les `Variables disponibles`_ pour une liste exhaustive.  En
général, il est préférable de ne sortir que le journal de débogage dans la
routine __init__ pour un plugin, parce qu'il est exécuté à chaque fois qu'un
fichier La commande *sr status* est exécutée, ce qui peut rapidement
devenir difficile à lire.

Si l'un de ces scripts renvoie False, le traitement du message/fichier.
s'arrêtera là et un autre message sera consommé par le courtier.


Variables populaires dans Plugins
---------------------------------

Une variable populaire dans les plugins on_file et on_part est :
*parent.msg.new_file*, en donnant le nom du fichier dans lequel le produit
téléchargé a été écrit. Lorsque le la même variable est modifiée dans un plugin
on_message, elle change le nom de le fichier à télécharger. De même, une autre
variable souvent utilisée est *parent.new_dir*, qui agit sur le répertoire dans
lequel le fichier sera téléchargé.

Il y a aussi *parent.msg.urlstr* qui est l'URL de téléchargement complet du 
fichier, et *parent.msg.url,* qui est l'url équivalente après avoir été
analysée avec urlparse (voir la documentation python3 de urlparse pour 
l'utilisation détaillée) à, par exemple *parent.msg.msg.url.hostname* pour
l'hôte distant à partir duquel un fichier doit être obtenu, ou 
*parent.msg.msg.url.username* pour le compte à utiliser, parent.url.path
donne le chemin sur le fichier hôte distant.

D'autres champs populaires sont les en-têtes (AMQP) définis pour un fichier,
accessibles en tant que fichier *parent.msg.headers[ 'headername' ]*

Notez que les en-têtes sont limités par le protocole AMQP à 255 octets, et seront tronqués si
crée des valeurs plus longues que cela.

Ce sont les variables qui sont le plus souvent d'intérêt, mais bien d'autres encore.
est disponible.  Voir la section `Variables disponibles`_ pour plus de détails.
discussion.

--------------------------------
Meilleure réception des fichiers
--------------------------------

Par exemple, plutôt que d'utiliser le système de fichiers, sr_subscribe
pourrait indiquer quand chaque fichier est prêt en écrivant à une pipe nommée::


  blacklab% sr_subscribe edit dd_swob.conf 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  file_rxpipe_name /local/home/peter/test/rxpipe

  on_file file_rxpipe
  directory /tmp
  mirror True
  accept .*
  # rxpipe is a builtin on_file script which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.


Avec l'option *on_file*, on peut spécifier une option de traitement telle que
rxpipe. Avec rxpipe, chaque fois qu'un transfert de fichier est terminé et
prêt pour le post-traitement, son nom est écrit au *pipe linux* (nommé .rxpipe)
dans le répertoire de travail courant. Donc le code pour le post-traitement
devient::

  do_something <.rxpipe


Aucun sondage des répertoires de travail par l'utilisateur n'est nécessaire, 
et l'ingestion de fichiers partiels est nécessaire. 

.. NOTE::
   Dans le cas où un grand nombre d'instances sr_subscribe fonctionnent
   sur la même configuration, il y a une légère probabilité que les 
   notifications peuvent se corrompre l'un l'autre dans le tuyau nommé.
   Nous devrions probablement vérifier si cette probabilité est négligeable
   ou non.

Réception avancée des fichiers
------------------------------

Alors que la directive *on_file* spécifie le nom d'une action à effectuer 
à la réception d'un fichier, ces actions ne sont pas corrigées, mais simplement
de petits scripts fournis avec la commande et personnalisable par les
utilisateurs finaux. Le module rxpipe n'est qu'un exemple  inclu avec
Sarracenia::

  class File_RxPipe(object):

      def __init__(self,parent):
          parent.declare_option( 'file_rxpipe_name' ):

      def on_start(self,parent):
          if not hasattr(parent,'file_rxpipe_name'):
              parent.logger.error("Missing file_rxpipe_name parameter")
              return
          self.rxpipe = open( parent.file_rxpipe_name[0], "w" )

      def on_file(self, parent):
          self.rxpipe.write( parent.msg.new_file + "\n" )
          self.rxpipe.flush()
          return None

  self.plugin = 'File_RxPipe'

Avec ce fragment de python, lorsque sr_subscribe est appelé pour la première
fois, un *pipe linux* nommé npipe dans le répertoire spécifié est ouvert par
la fonction __init__.  Puis, chaque fois que une réception de fichier est 
terminée, l'attribution de *self.on_file* permet de s'assurer que
la fonction rx.on_file est appelée.

La fonction rxpipe.on_file ne fait qu'écrire le nom du fichier téléchargé au
*pipe linux.*  L'utilisation du tube nommé rend la réception des données
asynchrone. Comme indiqué dans l'exemple précédent, on peut alors démarrer
une seule tâche *do_something* qui traite la liste des fichiers alimentés.
comme entrée standard, à partir d'un *pipe linux* nommé.

Dans les exemples ci-dessus, la réception et le traitement des fichiers sont
entièrement séparés. S'il y a est un problème de traitement, les répertoires
de réception de fichiers se rempliront, potentiellement et causant de
nombreuses difficultés pratiques. Lorsqu'un plugin tel que comme on_file est
utilisé, le traitement de chaque fichier téléchargé est exécuté avant de
continuer au fichier suivant.

Si le code dans le script on_file est modifié pour effectuer le travail 
detraitement réel, alors plutôt que d'être asynchrone, le traitement va 
fournir une contre-pression au télećhargement pour refleter le rhythme
de transformation.  Si le traitement est bloqué, alors l'abonné sr_subscriber
arrêtera le téléchargement, et la file d'attente sera sur le serveur, 
au lieu de créer un énorme répertoire local sur le client.  Différents 
modèles s'appliquent dans différentes situations.

Un point supplémentaire est que si le traitement des fichiers est inclu
dans le plugin, c´est très simple de parralèliser, avec les *instances*.

Authentification dans les plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour mettre en œuvre le support des protocoles additionnels, il faudrait écrire
a **_do_download** script. les scripts accèdent aux informations d'identification.
dans le script avec le code :

- **ok, details = parent.credentials.get(msg.urlcred)**
- **if details  : url = details.url**

Les options de détails sont des éléments de la classe de détails (hardcode) :

- **print(details.ssh_keyfile)**
- **print(details.passive)**
- **print(details.binary)**
- **print(details.tls)**
- **print(details.prot_p)**

Pour le justificatif d'identité qui définit le protocole de téléchargement
de la connexion, qui, une fois ouverte, est maintenue ouverte. Il est 
réinitialisé (fermé et rouvert) lorsque le nombre de téléchargements
atteint le nombre donné par l'option **batch** (par défaut 100)

Toutes les opérations de téléchargement (upload) utilisent une mémoire 
tampon. La taille, en octets de la mémoire tampon utilisée est donnée par
l'option **bufsize** (par défaut 8192)


Variables disponibles
---------------------

Sans consulter le code source python de Sarracenia, il est difficile 
de connaître quelles sont les variables disponibles pour les scripts de 
plugin. Comme un tricheur pour sauver les développeurs d'avoir à comprendre
le code source, un plugin de diagnostic pourrait être utile.

Si l'on met **on_message msg_dump** dans une configuration, l'ensemble de
l'application La liste des variables disponibles sera affichée dans un 
fichier journal. 

Faire du fichier ci-dessus un script on_file (ou autre trigger) dans une 
configuration, démarrer un récepteur (et s'il est occupé, alors arrêtez-le
immédiatement, car il crée de très gros messages de rapport pour chaque 
message reçu.)  Essentiellement, tout l'état du programme est disponible pour
les plugins.

Un exemple de sortie est montré (reformaté pour la lisibilité) est donné 
ci-dessous. Pour chaque champ *xx* indiqué, un script de plugin peut y 
accéder sous la forme *parent.xx* (par exemple *parent.queue_name*)::


  peter@idefix:~/test$ sr_subscribe foreground dd.conf 
  ^C to stop it immediately after the first message.
  peter@idefix:~/test$ tail -f ~/.cache/sarra/log/sr_subscribe_dd_0001.log

  # the following is reformatted to look reasonable on a page.
  2016-01-14 17:13:01,649 [INFO] {
  'kbytes_ps': 0,
  'queue_name': None,
  'flatten': '/',
  'exchange': 'xpublic',
  'discard': False,
  'report_back': True,
  'source': None,
  'pidfile': '/local/home/peter/.cache/sarra/.sr_subscribe_dd_0001.pid',
  'event': 'IN_CLOSE_WRITE|IN_ATTRIB|IN_MOVED_TO|IN_MOVE_SELF',
  'basic_name': 'sr_subscribe_dd',
  'cluster_aliases': [],
  'expire': None,
  'currentRegexp': re.compile('.*'),
  'handler': <logging.handlers.TimedRotatingFileHandler
  object at 0x7f4fcdc4d780>,
  'accept_unmatch': False,
  'reconnect': False,
  'isrunning': False,
  'on_line': None,
  'masks': [('.*/grib2/.*', '/local/home/peter/test/dd', None, re.compile('.*/grib2/.*'), False),
  ('.*grib2.tar.*', '/local/home/peter/test/dd', None, re.compile('.*grib2.tar.*'), False),
  ('.*', '/local/home/peter/test/dd', None, re.compile('.*'), True)],
  'logrotate': 5,
  'pid': 14079,
  'consumer': <sarra.sr_consumer.sr_consumer object at 0x7f4fcdc489b0>,
  'post_document_root': None,
  'manager': None,
  'publisher': <sarra.sr_amqp.Publisher object at 0x7f4fcdbdae48>,
  'post_broker': ParseResult(scheme='amqp',
  netloc='guest:guest@localhost',
  path='/',
  params='',
  query='',
  fragment=''),
  'currentPattern': '.*',
  'partflg': '1',
  'notify_only': False,
  'program_dir': 'subscribe',
  'on_part': None,
  'to_clusters': None,
                                        'site_data_dir': '/usr/share/ubuntu/sarra',
  'source_from_exchange': False,
  'new_url': ParseResult(scheme='file', netloc='',
  path='/local/home/peter/test/dd/bulletins/alphanumeric/20160114/SA/CYVT/22/SACN62_CYVT_142200___11878',
  params='', query='', fragment=''),
  'sumflg': 'd',
  'user_log_dir': '/local/home/peter/.cache/sarra/log',
  'topic_prefix': 'v02.post',
  'on_post': None,
  'do_poll': None,
  'message_ttl': None,
  'user_scripts_dir': '/local/home/peter/.config/sarra/scripts',
  'appname': 'sarra',
  'debug': False,
  'chmod': 775,
  'destination': None,
  'subtopic': None,
  'events': 'IN_CLOSE_WRITE|IN_DELETE',
  'document_root': '/local/home/peter/test/dd',
  'inplace': True,
  'last_nbr_instances': 6,
  'config_name': 'dd',
  'instance_str': 'sr_subscribe dd 0001',
  'randomize': False,
  'vip': None,
  'parts': '1',
  'inflight': '.tmp',
  'cache_url': {},
  'queue_share': True,
  'overwrite': True,
  'appauthor': 'science.gc.ca',
  'no': 1,
  'url': None,
  'bindings': [('xpublic', 'v02.post.#')],
  'blocksize': 0,
  'cluster': None,
  'rename': None,
  'user_config_dir': '/local/home/peter/.config/sarra',
  'users': {},
  'currentDir': '/local/home/peter/test/dd',
  'instance': 1,
  'sleep': 0,
  'user_cache_dir': '/local/home/peter/.cache/sarra',
  'report_clusters': {},
  'strip': 0,
  'msg': <sarra.sr_message.sr_message object at 0x7f4fcdc54518>,
  'site_config_dir': '/etc/xdg/xdg-ubuntu/sarra',
  'program_name': 'sr_subscribe',
  'on_file': <bound method Transformer.perform of <sarra.sr_config.Transformer object at 0x7f4fcdc48908>>,
  'cwd': '/local/home/peter/test',
  'nbr_instances': 6,
  'credentials': <sarra.sr_credentials.sr_credentials object at 0x7f4fcdc911d0>,
  'on_message': None,
  'currentFileOption': None,
  'user_config': 'dd.conf',
  'lpath': '/local/home/peter/.cache/sarra/log/sr_subscribe_dd_0001.log',
  'bufsize': 8192,
  'do_download': None,
  'post_exchange': None,
  'report_exchange': 'xlog',
  'new_path': '/local/home/peter/test/dd/bulletins/alphanumeric/20160114/SA/CYVT/22/SACN62_CYVT_142200___11878',
  'instance_name': 'sr_subscribe_dd_0001',
  'statefile': '/local/home/peter/.cache/sarra/.sr_subscribe_dd.state',
  'use_pattern': True,
  'admin': None,
  'gateway_for': [],
  'interface': None,
  'logpath': '/local/home/peter/.cache/sarra/log/sr_subscribe_dd_0001.log',
  'recompute_chksum': False,
  'user_queue_dir': '/local/home/peter/.cache/sarra/queue',
  'mirror': True,
  'broker': ParseResult(scheme='amqp', netloc='anonymous:anonymous@dd.weather.gc.ca', path='/', params='', query='', fragment=''),
  'durable': False,
  'logger': <logging.RootLogger object at 0x7f4fcdc48a20>,
  'user_data_dir': '/local/home/peter/.local/share/sarra',
  'flow': None}

On n'a pas encore réfléchi à la compatibilité des plug_in entre les versions.
On ne sait pas très bien dans quelle mesure le cet état variera au fil du 
temps. Comme pour les paramètres de configuration du programme, tous les champs
impliqués dans le traitement des messages individuels sont disponibles dans 
l'objet parent.msg. Une dump vers ce qui précède est ici (par exemple, les
scripts python peuvent utiliser *parent.msg.partsr* ...), 
et/ou *parent.msg.header.parts* dans leur code.)::

 2016-01-14 17:13:01,649 [INFO] message =
 {'partstr': '1,78,1,0,0',
 'suffix': '.78.1.0.0.d.Part',
 'subtopic': 'alphanumeric.20160617.CA.CWAO.12',
 'in_partfile': False,
 'notice': '20160617120454.820 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
 'checksum': 'ab1ba0020e91119fb024a2c115ccd908',
 'pub_exchange': None,
 'local_checksum': None,
 'chunksize': 78,
 'time': '20160617120454.820',
 'path': 'bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
 'report_exchange': 'xs_anonymous',
 'part_ext': 'Part',
 'topic_prefix': 'v02.post',
 'current_block': 0,
 'tbegin': 1466165094.82,
 'remainder': 0,
 'to_clusters': ['DD', 'DDI.CMC', 'DDI.EDM'],
 'local_offset': 0,
 'mtype': 'post',
  'user': 'anonymous',
  'bufsize': 8192, 'new_url':
  ParseResult(scheme='file', netloc='', path='/home/peter/test/dd/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919', params='', query='', fragment=''), 'exchange': 'xpublic', 'url': ParseResult(scheme='http', netloc='dd2.weather.gc.ca', path='/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919', params='', query='', fragment=''),
 'onfly_checksum': 'ab1ba0020e91119fb024a2c115ccd908',
  'host': 'blacklab',
  'filesize': 78,
  'block_count': 1,
 'sumalgo': <sarra.sr_util.checksum_d object at 0x7f77554234e0>,
 'headers': {
      'sum': 'd,ab1ba0020e91119fb024a2c115ccd908',
      'parts': '1,78,1,0,0',
      'filename': 'CACN00_CWAO_171133__WAR_00919',
      'to_clusters': 'DD,DDI.CMC,DDI.EDM',
      'source': 'metpx',
      'rename': '/home/peter/test/dd/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
      'from_cluster': 'DD'},
 'hdrstr': 'parts=1,78,1,0,0 sum=d,ab1ba0020e91119fb024a2c115ccd908 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/home/peter/test/dd/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919 message=Downloaded ',
  'report_notice': '20160617120454.820 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919 201 blacklab anonymous 3.591402',
  'version': 'v02',
  'parent': <sarra.sr_subscribe.sr_subscribe object at 0x7f775682b4a8>,
  'length': 78,
  'topic': 'v02.post.bulletins.alphanumeric.20160617.CA.CWAO.12',
  'inplace': True,
  'urlcred': 'http://dd2.weather.gc.ca/',
  'sumstr': 'd,ab1ba0020e91119fb024a2c115ccd908',
  'report_topic': 'v02.report.bulletins.alphanumeric.20160617.CA.CWAO.12',
  'publisher': None,
  'code': 201,
  'urlstr': 'http://dd2.weather.gc.ca/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
  'lastchunk': True,
  'sumflg': 'd',
  'offset': 0,
  'partflg': '1',
  'report_publisher': <sarra.sr_amqp.Publisher object at 0x7f77551c7518>}


----------------------
Débogage on\_ Scripts
----------------------

Lors du développement initial d'un script de plugin, il peut être 
laboriieux de l'exécuter dans le framework complet.  Si on tente d'exécuter
même le plugin trivial ci-dessus::

   blacklab% python noop.py
   Traceback (most recent call last):
     File "noop.py", line 25, in <module>
       filenoop  = File_Noop(self)
   NameError: name 'self' is not defined
   blacklab%

Pour le travail syntaxique de base, on peut ajouter des échafaudages de débogage.  En prenant le code ci-dessus, ajoutez simplement::


    class File_Noop(object):
          def __init__(self,parent):
              parent.declare_option( 'file_string' )

          def on_start(self,parent):
              if not hasattr(parent,'file_string'): # prior to 2.18.1a4, include on_start code in __init__
                 parent.file_string='hello world'

          def on_file(self,parent):
              logger = parent.logger

              logger.info("file_noop: I have no effect but adding a log line with %s in it" % parent.file_string )

              return True

    # after > 2.18.4
    self.plugin = 'File_Noop'
    
    # prior to sarra 2.18.4
    #file_noop=File_Noop(self)
    #self.on_file=file_noop.on_file

    ## DEBUGGING CODE START

    class TestLogger:
        def silence(self,str):
            pass

        def __init__(self):
            self.debug   = self.silence
            self.error   = print
            self.info    = self.silence
            self.warning = print

    class TestParent(object):
        def __init__(self):
            self.logger=TestLogger()
            pass

    testparent=TestParent()

    filenoop  = File_Noop(testparent)
    testparent.on_file = filenoop.on_file


Il peut donc maintenant être invoqué avec::


    blacklab% python noop.py
    blacklab%

Ce qui confirme qu'il n'y a au moins aucune erreur de syntaxe. Il faudra 
ajouter d'autres échafaudages en fonction de la complexité du plugin. On
peut ajouter une invocation du plugin au test script, comme ça::


   self.on_file(self)

et puis la routine s'exécutera. Plus le plugin est complexe, plus 
l´échafaudage est élaboré. Une fois ce type d'essai de base terminé, 
il suffit d'enlever l'échafaudage. Pour des tests plus compliqués, il 
suffit d'ajouter plus de code de test::


  cat >fifo_test.py <<EOT
  #!/usr/bin/python3

  """
  when a file is downloaded, write the name of it to a named pipe called .rxpipe
  at the root of the file reception tree.

  """
  import os,stat,time

  class Transformer(object):

      def __init__(self):
          pass

      def on_file(self,parent):
          msg    = parent.msg

          # writing filename in pipe
          f = open('/users/dor/aspy/mjg/mon_fifo','w')
          f.write(parent.new_file)
          f.flush()
          f.close()

          # resume process as usual ?
          return True

  transformer=Transformer()
  #self.on_file = transformer.on_file


  """
  for testing outside of a sr_ component plugin environment,
  we comment out the normal activiation line of the script above
  and insert a little wrapper, so that it can be invoked
  at the command line:
         python3  fifo_test.py

  """
  class TestLogger():
      def silence(self,str):
          pass

      def __init__(self):
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print

  class TestMessage() :
      def __init__(self):
          self.headers = {}

  class TestParent(object):
      def __init__(self):
          self.new_file = "a string"
          self.msg = TestMessage()
          self.logger = TestLogger()
          pass

  testparent=TestParent()

  transformer.on_file(testparent)

La partie qui suit la ligne #self.on_file n'est qu'un harnais de test.
On crée un objet d'appel avec les champs nécessaires pour tester l'application.
que le plugin utilisera dans les classes TestParent et TestMessage.
Consultez également le plugin harness.py disponible pour inclure ce qui précède.
pour le test des plugins.


-------------------------
Avise sans téléchargement
-------------------------

Si la pompe de données existe dans un environnement partagé de grande 
taille, tel que un centre de supercalcul avec un système de fichiers de 
site, le fichier pourrait être disponible sans téléchargement. Donc, 
l'obtention de l´avis est suffisant pour déclencher sa lecture pour
transformation:: 

  blacklab% sr_subscribe edit dd_swob.conf 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  document_root /data/web/dd_root
  no_download
  on_message msg_2local
  on_message do_something

  accept .*

on_message est un crochet de scripting, exactement comme on_file, qui permet
un traitement spécifique à effectuer à la réception d'un message. Un message
correspondent habituellement à un fichier, mais pour les gros fichiers, il y
en aura un message par bloc. On peut utiliser le fichier parent.msg.partstr
pour trouver quelle pièce vous avez (Voir `sr_post.1 <sr_post.1.rst>`_ pour
plus de détails sur l'encodage de partstr.

Assurez-vous que le plugin on_message renvoie'False' pour éviter le 
téléchargement.


... avertissement: :
   **FIXME** : peut-être montrer un moyen de vérifier l'en-tête des pièces à
   avec une instruction if afin de n'agir que sur la première partie du message.
   pour les longs fichiers.


----------
do_scripts
----------

Dans le cas où de gros fichiers sont téléchargés, et que l'on veut le faire 
rapidement, les méthodes intégrées de Sarracenia sont intrinsèquement un peu 
limitées au niveau de performance.  Bien que sont raisonnablement efficaces, 
on pourrait soutenir que lorsque des fichiers volumineux doivent être 
téléchargés, un téléchargeur efficace et dédié écrit dans un langage de 
bas niveau comme C est plus efficace. Ces exemples sont inclus avec chaque 
installation de sarracenia, et peut être modifié pour être utilisé avec
d'autres outils.

Voici un exemple de mise en œuvre de l'utilisation conditionnelle d'une 
méthode de téléchargement plus efficace.  Commencez par un script 
on_message qui évalue la condition pour déterminer s'il faut invoquer le
téléchargeur personnalisé:

.. include:: ../../sarra/plugins/msg_download.py 
   :code:

Ainsi, on "invente" un nouveau schéma d'URL qui fait référence au
téléchargeur alternatif. Dans ce cas, les URLs qui sont à télécharger à
l'aide d'un autre outil, obtenez leur 'http:' remplacé par 'download:'.
Dans l'exemple ci-dessus, si le fichier est plus gros qu´une valeur seuil 
(10 mégaoctets par défaut) seront marqués pour le téléchargement avec 
une autre méthode en faisant modifier leur URL.

Ce plugin on_message msg_download doit être couplé avec l'utilisation d'un 
plugin do_download.  Lorsque le schéma alternatif est rencontré, le
composant invoquera ce plugin. Exemple de ce plugin:


.. include:: ../../sarra/plugins/download_wget.py
   :code:

-------------------------------------
Pourquoi *import* ne fonctionne pas ?
-------------------------------------

Il y a un problème où l'endroit dans le code où les plugins sont lus 
est différent à partir de laquelle les routines du plugin sont exécutées,
et donc les importations au niveau de la classe ne fonctionnent pas comme
prévu.


.. code:: python

    #!/usr/bin/python3

    import os,sys,stat,time,datetime,string,socket
    from ftplib import FTP

    class Renamer(object):
        def __init__(self):
            pass

        def perform(self,parent):
            infile = parent.local_file
            Path = os.path.dirname(infile)
            Filename = os.path.basename(infile)

            # FTP upload
            def uploadFile(ftp, upfile):
                ftp.storbinary('STOR ' + upfile, open(upfile, 'rb'), 1024)
                ftp.sendcmd('SITE CHMOD 666 ' + upfile)

            # ftp = FTP('hoho.haha.ec.gc.ca')
            ftp = FTP('127.272.44.184')
            logon = ftp.login('px', 'pwgoeshere')
            path = ftp.cwd('/apps/px/rxq/ont2/')
            os.chdir( Path )
            uploadFile(ftp, Filename)
            ftp.quit()

    renamer=Renamer()
    self.on_file = renamer.perform


Lorsque le code est exécuté, cela se produit::


  2018-05-23 20:57:31,958 [ERROR] sr_subscribe/run going badly, so sleeping for 0.01 Type: <class 'NameError'>, Value: name 'FTP' is not defined,  ...
  2018-05-23 20:57:32,091 [INFO] file_log downloaded to: /apps/urp/sr_data/TYX_N0S:NOAAPORT2:CMC:RADAR_US:BIN:20180523205529
  2018-05-23 20:57:32,092 [INFO] confirmed added to the retry process 20180523205531.8 http://ddi1.cmc.ec.gc.ca/ 20180523/UCAR-UNIDATA/RADAR_US/NEXRAD3/N0S/20/TYX_N0S:NOAAPORT2:CMC:RADAR_US:BIN:20180523205529
   
  2018-05-23 20:57:32,092 [ERROR] sr_subscribe/run going badly, so sleeping for 0.02 Type: <class 'NameError'>, Value: name 'FTP' is not defined,  ...
  2018-05-23 20:57:32,799 [INFO] file_log downloaded to: /apps/urp/sr_data/CXX_N0V:NOAAPORT2:CMC:RADAR_US:BIN:20180523205533
  2018-05-23 20:57:32,799 [INFO] confirmed added to the retry process 20180523205535.46 http://ddi2.cmc.ec.gc.ca/ 20180523/UCAR-UNIDATA/RADAR_US/NEXRAD3/N0V/20/CXX_N0V:NOAAPORT2:CMC:RADAR_US:BIN:20180523205533
  2018-05-23 20:57:32,799 [ERROR] sr_subscribe/run going badly, so sleeping for 0.04 Type: <class 'NameError'>, Value: name 'FTP' is not defined,  ...


La solution est de déplacer l'importation à l'intérieur de la routine 
d'exécution comme la première ligne, comme suit::


    .
    .
    .

        def perform(self,parent):
            from ftplib import FTP
            infile = parent.local_file
            Path = os.path.dirname(infile)
    .
    .
    .












