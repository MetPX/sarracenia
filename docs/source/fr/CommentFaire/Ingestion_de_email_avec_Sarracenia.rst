====================================
Ingestion par e-mail avec Sarracenia
====================================

Le courrier électronique est un moyen facile d’acheminer les données entre les serveurs. Utilisation du protocole POP3 (Post Office Protocol) et
Protocole IMAP (Internet Message Access Protocol), les fichiers e-mail peuvent être diffusés via Sarracenia
en étendant les fonctions du poll et de téléchargement.

Polling
-------


Extending Polling Protocols
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Prêt à l’emploi, Sarracenia prend en charge les destinations de poll avec les protocoles HTTP/HTTPS et SFTP/FTP.
D’autres protocoles peuvent être pris en charge en sous-classant la classe sarracenia.flowcb.poll.Poll.
Heureusement, il existe un plugin de poll par courrier, qui invoque un plugin.
commencez par énumérer les exemples disponibles ::

   fractal% sr3 list examples | grep poll
   cpump/cno_trouble_f00.inc        poll/airnow.conf                 
   poll/aws-nexrad.conf             poll/mail.conf                   
   poll/nasa-mls-nrt.conf           poll/noaa.conf                   
   poll/soapshc.conf                poll/usgs.conf                   
   fractal% 

Ajoutant la configuration::

   fractal% sr3 add poll/mail.conf
   add: 2022-03-10 15:59:48,266 2785187 [INFO] sarracenia.sr add copying: /home/peter/Sarracenia/sr3/sarracenia/examples/poll/mail.conf to /home/peter/.config/sr3/poll/mail.conf 
   fractal% 

Qu’avons-nous obtenu?::

   fractal% cat ~/.config/sr3/poll/mail.conf
   #
   # Sample poll config, used to advertise availability of new emails using either POP3/IMAP protocols.
   # To use, make sure rabbitmq is running as described in the Dev.rst documentation,
   # and a tsource user/xs_tsource exchange exist, with FLOWBROKER set to the hostname
   # rabbitmq is running on (e.g. export FLOWBROKER='localhost')
   #
   # The destination is in RFC 1738 format, e.g. <scheme>://<user>@<host>:<port>/ where your full credentials,
   # <scheme>://<user>:<password>@<host>:<port>/ would be contained in your ~/.config/sarra/credentials.conf.
   # Valid schemes are pop/pops/imap/imaps, where the s denotes an SSL connection. If a port isn't 
   # specified, the default port associated with the scheme will be used (IMAPS -> 993, POPS -> 995,
   # IMAP -> 143, POP -> 110).
   #
   
   post_broker amqp://tsource@${FLOWBROKER}
   post_exchange xs_tsource
   
   sleep 60
   
   destination <scheme>://<user>@<host>:<port>/
   
   callback poll.mail
   
   fractal% 

Maintenant, lorsque l’instance de poll est démarrée avec ce plugin,

Mise en œuvre de POP/IMAP
~~~~~~~~~~~~~~~~~~~~~~~~~
Avec les modules *poplib* et *imaplib* de Python, la destination peut être analysée et le serveur de messagerie
peut être connecté selon le schéma spécifié. Sarracenia peut extraire les informations d’identification de la destination
grâce à ses classes intégrées, aucun mot de passe n’a donc besoin d’être stocké dans le fichier de configuration pour se connecter. Pop3
utilise un indicateur de lecture interne pour déterminer si un message a été vu ou non. Si un message n’est pas lu, après
en le récupérant avec POP3, il sera marqué comme lu et il ne sera pas repris sur d’autres poll.
POP3 offre d’autres options comme la suppression du fichier après sa lecture, mais IMAP offre plus d'options de gestion
de courrier telles que le déplacement entre les dossiers et la génération de requêtes plus complexes. IMAP permet également
à plusieurs clients de se connecter à une boîte aux lettres en même temps, et prend en charge les indicateurs de message de suivi tels que
si le message est lu/non lu, répondu/pas encore répondu, ou supprimé/toujours dans la boîte de réception. L'exemple
de plugin de poll,
`poll_email_ingest.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_email_ingest.py>`_
récupère uniquement les e-mails non lus dans la boîte de réception et les marque comme non lus après les avoir récupérés, dans les deux cas suivants :
Versions POP et IMAP. Ce paramètre peut être facilement modifié selon les intentions de l’utilisateur final. S’il y a
s’il y a de nouveaux messages de la dernière fois qu’un client POP/IMAP s’est connecté, il publiera alors le fichier
en fonction de l’objet et d’un horodatage, où une instance sr_subscribe peut recevoir le message publié,
connectez-vous individuellement au serveur et téléchargez le message pour le sortir dans un fichier localement. Un exemple
de configuration qui a été inclus sous **exemples** en tant que
`pollingest.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollingest.conf>`_.
Une fois que vous avez modifié/fourni les variables d’environnement requises pour le
config pour travailler, ouvrir un nouveau terminal et exécuter ::

	[aspymap:~]$ sr_poll foreground pollingest.conf

Si les informations d’identification ont été incluses correctement et que toutes les variables ont été définies, la sortie doit ressembler à ceci ::

	[aspymap:~/sarra_test_output]$ sr_poll foreground pollingest.conf 
	2018-10-03 15:24:58,611 [INFO] poll_email_ingest init
	2018-10-03 15:24:58,617 [INFO] sr_poll pollingest startup
	2018-10-03 15:24:58,617 [INFO] log settings start for sr_poll (version: 2.18.07b3):
	2018-10-03 15:24:58,617 [INFO]  inflight=unspecified events=create|delete|link|modify use_pika=False
	2018-10-03 15:24:58,617 [INFO]  suppress_duplicates=1200 retry_mode=True retry_ttl=Nonems
	2018-10-03 15:24:58,617 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-10-03 15:24:58,617 [INFO]  heartbeat=300 default_mode=400 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-10-03 15:24:58,617 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-10-03 15:24:58,617 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report=True
	2018-10-03 15:24:58,617 [INFO]  post_base_dir=None post_base_url=pops://dfsghfgsdfg24@hotmail.com@outlook.office365.com:995/ sum=z,d blocksize=209715200 
	2018-10-03 15:24:58,617 [INFO]  Plugins configured:
	2018-10-03 15:24:58,617 [INFO]          on_line: Line_Mode 
	2018-10-03 15:24:58,617 [INFO]          on_html_page: Html_parser 
	2018-10-03 15:24:58,617 [INFO]          do_poll: Fetcher 
	2018-10-03 15:24:58,617 [INFO]          on_message: 
	2018-10-03 15:24:58,617 [INFO]          on_part: 
	2018-10-03 15:24:58,618 [INFO]          on_file: File_Log 
	2018-10-03 15:24:58,618 [INFO]          on_post: Post_Log 
	2018-10-03 15:24:58,618 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse 
	2018-10-03 15:24:58,618 [INFO]          on_report: 
	2018-10-03 15:24:58,618 [INFO]          on_start: 
	2018-10-03 15:24:58,618 [INFO]          on_stop: 
	2018-10-03 15:24:58,618 [INFO] log_settings end.
	2018-10-03 15:24:58,621 [INFO] Output AMQP broker(localhost) user(tsource) vhost(/)
	2018-10-03 15:24:58,621 [INFO] Output AMQP exchange(xs_tsource)
	2018-10-03 15:24:58,621 [INFO] declaring exchange xs_tsource (tsource@localhost)
	2018-10-03 15:24:59,452 [INFO] post_log notice=20181003192459.452392 pops://dfsghfgsdfg24@hotmail.com@outlook.office365.com:995/ sarra%20demo20181003_15241538594699_452125 headers={'parts': '1,1,1,0,0', 'sum': 'z,d', 'from_cluster': 'localhost', 'to_clusters': 'ALL'}
	^C2018-10-03 15:25:00,355 [INFO] signal stop (SIGINT)
	2018-10-03 15:25:00,355 [INFO] sr_poll stop


Téléchargement
--------------
Les messages électroniques, une fois récupérés, sont formatés au format MIME (Multipurpose Internet Mail Extensions) 1.0 brut,
comme indiqué dans le premier en-tête du fichier. Les métadonnées de l’e-mail sont transmises dans une série d’en-têtes, dont une
par ligne, dans le format nom:valeur. Cela peut être analysé pour les pièces jointes, les corps de message, les méthodes de codage, etc. Un
*do_download* plugin peut implémenter la récupération du message à sortir dans un fichier en enregistrant le protocole
dans un module séparé, comme dans le plugin *do_poll*. Une fois qu’un message est reçu avec l’utilisateur/hôte
publié, il peut ensuite se connecter au serveur de messagerie en utilisant la destination et les informations d’identification spécifiées
dans ~/.config/sarra/credentials.conf et récupére le message localement. Un exemple de plugin qui fait cela
peut être trouvé sous **plugins** comme
`download_email_ingest.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_email_ingest.py>`_.

Décodage du contenu
~~~~~~~~~~~~~~~~~~~
Une fois le message électronique téléchargé, un plug-in *on_file* peut analyser le fichier au format MIME et extraire
la pièce jointe, généralement indiquée par l’en-tête Content-Disposition ou les champs corps/objet/adresse du message, à enregistrer en tant que
nouveau fichier pour affiner davantage les données. Un exemple de plugin qui fait cela peut être trouvé sous **plugins** comme
`file_email_decode.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/file_email_decode.py>`_.
Un exemple de configuration incorporant ce type de traitement de fichiers est inclus sous **exemples** en tant que
`downloademail.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/downloademail.conf>`_.
Une fois que les variables d’environnement ont été fournies et que le serveur rabbitmq est correctement configuré, ouvrez un nouveau
terminal et exécutez::

	[aspymap~]$ sr_subscribe foreground downloademail.conf

Si tout a été fourni correctement, la sortie devrait ressembler à ceci::

	[aspymap:~/sarra_output_test]$ sr_subscribe foreground downloademail.conf 
	2018-10-03 15:24:57,153 [INFO] download_email_ingest init
	2018-10-03 15:24:57,159 [INFO] sr_subscribe downloademail start
	2018-10-03 15:24:57,159 [INFO] log settings start for sr_subscribe (version: 2.18.07b3):
	2018-10-03 15:24:57,159 [INFO]  inflight=.tmp events=create|delete|link|modify use_pika=False
	2018-10-03 15:24:57,159 [INFO]  suppress_duplicates=False retry_mode=True retry_ttl=300000ms
	2018-10-03 15:24:57,159 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-10-03 15:24:57,159 [INFO]  heartbeat=300 default_mode=000 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-10-03 15:24:57,159 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-10-03 15:24:57,159 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report=True
	2018-10-03 15:24:57,159 [INFO]  Plugins configured:
	2018-10-03 15:24:57,159 [INFO]          do_download: Fetcher 
	2018-10-03 15:24:57,159 [INFO]          do_get     : 
	2018-10-03 15:24:57,159 [INFO]          on_message: 
	2018-10-03 15:24:57,159 [INFO]          on_part: 
	2018-10-03 15:24:57,159 [INFO]          on_file: File_Log Decoder 
	2018-10-03 15:24:57,159 [INFO]          on_post: Post_Log 
	2018-10-03 15:24:57,159 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse RETRY 
	2018-10-03 15:24:57,159 [INFO]          on_report: 
	2018-10-03 15:24:57,159 [INFO]          on_start: 
	2018-10-03 15:24:57,159 [INFO]          on_stop: 
	2018-10-03 15:24:57,159 [INFO] log_settings end.
	2018-10-03 15:24:57,159 [INFO] sr_subscribe run
	2018-10-03 15:24:57,160 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
	2018-10-03 15:24:57,164 [INFO] Binding queue q_tsource.sr_subscribe.downloademail.64168876.31529683 with key v02.post.# from exchange xs_tsource on broker amqp://tsource@localhost/
	2018-10-03 15:24:57,166 [INFO] reading from to tsource@localhost, exchange: xs_tsource
	2018-10-03 15:24:57,167 [INFO] report to tsource@localhost, exchange: xs_tsource
	2018-10-03 15:24:57,167 [INFO] sr_retry on_heartbeat
	2018-10-03 15:24:57,172 [INFO] No retry in list
	2018-10-03 15:24:57,173 [INFO] sr_retry on_heartbeat elapse 0.006333
	2018-10-03 15:25:00,497 [INFO] download_email_ingest downloaded file: /home/ib/dads/map/.cache/sarra/sarra_doc_test/sarra demo20181003_15241538594699_452125
	2018-10-03 15:25:00,500 [INFO] file_log downloaded to: /home/ib/dads/map/.cache/sarra/sarra_doc_test/sarra demo20181003_15241538594699_452125
	^C2018-10-03 15:25:03,675 [INFO] signal stop (SIGINT)
	2018-10-03 15:25:03,675 [INFO] sr_subscribe stop


Cas d'utilisation
-----------------
Les plugins d’ingestion d’e-mails ont été développés pour le cas d’utilisation des données en rafale courte, où l’information
arrive dans les pièces jointes des messages. Auparavant, les e-mails étaient téléchargés avec un script fetchmail et un
cronjob s’exécuterait de temps en temps pour détecter et décoder les nouveaux fichiers et leurs pièces jointes,
à utiliser pour un traitement ultérieur des données. Sarracenia prend désormais en charge toutes les étapes du routage des données,
et permet à ce processus d’être plus parallélisable.

