================================================================
Utilisation de plugins pour récupérer des données hydrométriques
================================================================

Plusieurs sites Web de données environnementales utilisent des API pour communiquer des données. Afin de faire de la publicité pour la
disponibilité de nouveaux fichiers et les intégrer de manière transparente dans la pile Sarracenia, quelques plugins sont
nécessaire pour étendre la fonctionnalité de polling.


Protocoles de polling pris en charge en mode natif
--------------------------------------------------
Prêt à l’emploi, Sarracenia prend en charge l’interrogation des sources HTTP / HTTPS et SFTP / FTP où le nom de fichier
est ajouté à la fin de l’URL de base. Par exemple, si vous essayez d’accéder les données de niveau de l’eau
du réservoir du lac Ghost près de Cochrane en Alberta, auxquelles on peut accéder en naviguant jusqu’à
`http://environment.alberta.ca/apps/Basins/data/figures/river/abrivers/stationdata/L_HG_05BE005_table.json`,
l’URL de base dans ce cas serait considérée comme le
`http://environment.alberta.ca/apps/Basins/data/figures/river/abrivers/stationdata/`
et la partie du nom de fichier `L_HG_05BE005_table.json`. Étant donné que l’URL de base ne
contient pas un bon répertoire avec tous les fichiers JSON, si vous vouliez vérifier si les nouvelles
données de niveau d’eau ont a été ajouté au localisateur ci-dessus, puisqu’il s’agit d’un fichier
JSON, vous pouvez vérifier l’en-tête modifié en dernier pour
voir s’il a été modifié depuis votre dernier poll. À partir de là, vous devrez définir le *new_baseurl* sur la
première partie, et le *new_file* réglé sur la seconde, et une instance sr_subscribe saurait assembler
pour localiser le fichier et le télécharger.

Extension des protocoles de poll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Si la source de données ne respecte pas cette convention (voir `NOAA CO-OPS API`_ et `USGS Instantaneous Values
Web Service`_ pour des exemples de deux sources de données qui ne le font pas), un module **registered_as**
peut être inclus en bas d’un fichier plugin pour définir la liste des protocoles en cours
d’extension ou d’implémentation ::

	def registered_as(self):
		return ['http','https']

Ca surchargerait alors la méthode de transfert et utiliserait celle décrite dans le plugin.

Exemples d’intégration d’API dans des plugins
---------------------------------------------
API NOAA CO-OPS
~~~~~~~~~~~~~~~
Le département des marées et des courants de National Oceanic and Atmospheric Administration publie son
programme coopératif données d’observations et de prédictions de stations via un service Web GET RESTful,
disponible à l’adresse `the NOAA Tides et le site Web de Currents <https://tidesandcurrents.noaa.gov/api/>`_.
Par exemple, si vous souhaitez accéder aux données de température de l’eau de la dernière heure à Honolulu,
vous pouvez naviguer vers `https://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv`.
Une nouvelle observation est enregistrée toutes les six minutes, donc si vous vouliez annoncer uniquement de nouvelles données via
Sarracenia, vous configureriez une instance sr_poll pour vous connecter à l’API, mettre en veille toutes les heures et leur construire
une requête GET à annoncer à chaque fois qu’il se réveille (cela fonctionne sous l’hypothèse potentiellement erronée
que la source de données maintienne son accord). Pour télécharger ce nouveau fichier, vous devez vous connecter
à un sr_subscribe au même échange sur lequel il a été annoncé, et il récupérerait l’URL, qu’un *do_download*
plugin pourrait alors prendre et télécharger. Un exemple de plugin de poll qui saisit toute la température et le niveau d’eau
de la dernière heure de toutes les stations CO-OPS et les publient, sont incluses sous *plugins* comme
`poll_noaa.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_noaa.py>`_.

Un plugin *do_download* qui correspond à une une instance sarra pour télécharger ce fichier est inclus
comme `download_noaa.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_noaa.py>`_.
Des exemples de configurations pour sr_poll et sr_subscribe sont inclus sous
*exemples*, nommés `pollnoaa.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollnoaa.conf>`_
et `subnoaa.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/subnoaa.conf>`_.
Pour exécuter, ajoutez à la fois des plugins et des configurations à l’aide de l’action :code:`add`, modifiez les
variables appropriées dans la config (le flowbroker, et la destination entre autres. Si vous exécutez à partir
d’un serveur RabbitMQ local, de la documentation sous `doc/Dev.rst <https://github.com/MetPX/sarracenia/blob/master/doc/Dev.rst>`_
sur la façon de configurer le serveur peut être utile). Si tout a été configuré correctement, la sortie doit
ressemblez à quelque chose comme ceci::

	[aspymap:~]$ sr_poll foreground pollnoaa.conf 
	2018-09-26 15:26:57,704 [INFO] sr_poll pollnoaa startup
	2018-09-26 15:26:57,704 [INFO] log settings start for sr_poll (version: 2.18.07b3):
	2018-09-26 15:26:57,704 [INFO]  inflight=unspecified events=create|delete|link|modify use_pika=False
	2018-09-26 15:26:57,704 [INFO]  suppress_duplicates=False retry_mode=True retry_ttl=Nonems
	2018-09-26 15:26:57,704 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-09-26 15:26:57,705 [INFO]  heartbeat=300 default_mode=400 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-09-26 15:26:57,705 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-09-26 15:26:57,705 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report=True
	2018-09-26 15:26:57,705 [INFO]  post_base_dir=None post_base_url=http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station={0:}&product={1:}&units=metric&time_zone=gmt&application=web_services&format=csv/ sum=z,d blocksize=209715200 
	2018-09-26 15:26:57,705 [INFO]  Plugins configured:
	2018-09-26 15:26:57,705 [INFO]          on_line: Line_Mode 
	2018-09-26 15:26:57,705 [INFO]          on_html_page: Html_parser 
	2018-09-26 15:26:57,705 [INFO]          do_poll: NOAAPoller 
	2018-09-26 15:26:57,705 [INFO]          on_message: 
	2018-09-26 15:26:57,705 [INFO]          on_part: 
	2018-09-26 15:26:57,705 [INFO]          on_file: File_Log 
	2018-09-26 15:26:57,705 [INFO]          on_post: Post_Log 
	2018-09-26 15:26:57,705 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse 
	2018-09-26 15:26:57,705 [INFO]          on_report: 
	2018-09-26 15:26:57,705 [INFO]          on_start: 
	2018-09-26 15:26:57,706 [INFO]          on_stop: 
	2018-09-26 15:26:57,706 [INFO] log_settings end.
	2018-09-26 15:26:57,709 [INFO] Output AMQP broker(localhost) user(tsource) vhost(/)
	2018-09-26 15:26:57,710 [INFO] Output AMQP exchange(xs_tsource)
	2018-09-26 15:26:57,710 [INFO] declaring exchange xs_tsource (tsource@localhost)
	2018-09-26 15:26:58,403 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv
	2018-09-26 15:26:58,403 [INFO] post_log notice=20180926192658.403634 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv CO-OPS__1611400__wt.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	2018-09-26 15:26:58,554 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND
	2018-09-26 15:26:58,554 [INFO] post_log notice=20180926192658.554364 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND CO-OPS__1611400__wl.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	2018-09-26 15:26:58,691 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv
	2018-09-26 15:26:58,691 [INFO] post_log notice=20180926192658.691466 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv CO-OPS__1612340__wt.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	2018-09-26 15:26:58,833 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND
	2018-09-26 15:26:58,834 [INFO] post_log notice=20180926192658.833992 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND CO-OPS__1612340__wl.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	^C2018-09-26 15:26:58,965 [INFO] signal stop (SIGINT)
	2018-09-26 15:26:58,965 [INFO] sr_poll stop

pour le polling et::

	[aspymap:~]$ sr_subscribe foreground subnoaa.conf 
	2018-09-26 15:26:53,473 [INFO] sr_subscribe subnoaa start
	2018-09-26 15:26:53,473 [INFO] log settings start for sr_subscribe (version: 2.18.07b3):
	2018-09-26 15:26:53,473 [INFO]  inflight=.tmp events=create|delete|link|modify use_pika=False
	2018-09-26 15:26:53,473 [INFO]  suppress_duplicates=False retry_mode=True retry_ttl=300000ms
	2018-09-26 15:26:53,473 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-09-26 15:26:53,473 [INFO]  heartbeat=300 default_mode=000 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-09-26 15:26:53,473 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-09-26 15:26:53,473 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report=False
	2018-09-26 15:26:53,473 [INFO]  Plugins configured:
	2018-09-26 15:26:53,473 [INFO]          do_download: BaseURLDownloader 
	2018-09-26 15:26:53,473 [INFO]          do_get     : 
	2018-09-26 15:26:53,473 [INFO]          on_message: 
	2018-09-26 15:26:53,474 [INFO]          on_part: 
	2018-09-26 15:26:53,474 [INFO]          on_file: File_Log 
	2018-09-26 15:26:53,474 [INFO]          on_post: Post_Log 
	2018-09-26 15:26:53,474 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse RETRY 
	2018-09-26 15:26:53,474 [INFO]          on_report: 
	2018-09-26 15:26:53,474 [INFO]          on_start: 
	2018-09-26 15:26:53,474 [INFO]          on_stop: 
	2018-09-26 15:26:53,474 [INFO] log_settings end.
	2018-09-26 15:26:53,474 [INFO] sr_subscribe run
	2018-09-26 15:26:53,474 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
	2018-09-26 15:26:53,478 [INFO] Binding queue q_tsource.sr_subscribe.subnoaa.90449861.55888967 with key v02.post.# from exchange xs_tsource on broker amqp://tsource@localhost/
	2018-09-26 15:26:53,480 [INFO] reading from to tsource@localhost, exchange: xs_tsource
	2018-09-26 15:26:53,480 [INFO] report suppressed
	2018-09-26 15:26:53,480 [INFO] sr_retry on_heartbeat
	2018-09-26 15:26:53,486 [INFO] No retry in list
	2018-09-26 15:26:53,488 [INFO] sr_retry on_heartbeat elapse 0.007632
	2018-09-26 15:26:58,751 [INFO] download_noaa: file noaa_20180926_1926_1611400_TP.csv
	2018-09-26 15:26:58,751 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1611400__wt.csv
	2018-09-26 15:26:58,888 [INFO] download_noaa: file noaa_20180926_1926_1611400_WL.csv
	2018-09-26 15:26:58,889 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1611400__wl.csv
	2018-09-26 15:26:59,026 [INFO] download_noaa: file noaa_20180926_1926_1612340_TP.csv
	2018-09-26 15:26:59,027 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1612340__wt.csv
	2018-09-26 15:26:59,170 [INFO] download_noaa: file noaa_20180926_1926_1612340_WL.csv
	2018-09-26 15:26:59,171 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1612340__wl.csv
	^C2018-09-26 15:27:00,597 [INFO] signal stop (SIGINT)
	2018-09-26 15:27:00,597 [INFO] sr_subscribe stop

pour le téléchargement.

Service Web SHC SOAP
~~~~~~~~~~~~~~~~~~~~
Un service Web SOAP (Simple Object Access Protocol) utilise un système de messagerie XML pour fournir les données demandées
données sur un réseau. Le client peut spécifier des paramètres pour une opération prise en charge (par exemple une recherche) sur
le service Web, noté avec une extension de fichier wdsl, et le serveur renverra une réponse SOAP au format XML.
Le Service Hydrographique du Canada (SHC) utilise ce service Web comme API pour obtenir des données hydrométriques.
données en fonction des paramètres envoyés.
Il ne prend en charge qu’une seule opération, la recherche, qui accepte les éléments suivants
paramètres : dataName, latitudeMin, latitudeMax, longitudeMin, longitudeMax, depthMin, depthMax, dateMin,
dateMax, start, end, tailleMax, metadata, metadataSelection, order. Par exemple, une recherche renverra toutes les
données sur le niveau d’eau disponibles à Acadia Cove au Nunavut le 1er septembre 2018 si votre recherche contient
les paramètres suivants : 'wl', 40.0, 85.0, -145.0, -50.0, 0.0, 0.0, '2018-09-01 00:00:00',
'2018-09-01 23:59:59', 1, 1000, 'true', 'station_id=4170, 'asc'.

La réponse peut ensuite être convertie en un fichier et vidé, qui peut être publié, ou les paramètres peuvent
être annoncés eux-mêmes dans le rapport. Remarquez, qu’un plugin sarra *do_download* pourrait ensuite déchiffrer
et traiter les données dans un fichier côté utilisateur. Afin de ne publier que de nouvelles données à partir de SHC, \
une instance de poll peut être configurée pour se mettre en veille toutes les 30 minutes,
et un plugin *do_poll* pourrait définir la plage de début-fin sur la dernière demi-heure avant de former la demande.
Chaque demande est renvoyée avec un message d’état confirmant s’il s’agissait d’un appel de fonction valide. Le plugin pourrait
ensuite vérifier que le message d’état est correct avant de publier le message annonçant de nouvelles données sur l’échange.
Un plugin *do_download* prend ces paramètres passés dans le message, forme une requête SOAP avec eux, et
extrait les données/les enregistre dans un fichier. Des exemples de plugins qui effectuent ces deux étapes peuvent être trouvés sous
*plugins*, nommés `poll_shc_soap.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_shc_soap.py>`_
et `download_shc_soap.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_shc_soap.py>`_.
Des exemples de configurations pour l’exécution des deux sont inclus sous *exemples*, nommés
`pollsoapshc.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollsoapshc.conf>`_ et
`subsoapshc.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/subsoapshc.conf>`_. 

Service Web de valeurs instantanées USGS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Le United States Geological Survey publie ses données sur l’eau par son Service Web des valeurs instantanées RESTful
, qui utilise des requêtes HTTP GET pour filtrer leurs données. Il renvoie les données dans les fichiers XML une fois
demandé, et peut prendre en charge plus d’un argument d’ID de station à la fois (téléchargement de données en bloc). Plus d’infos sur
le service peut être consulté `sur le site Web des services de l’eau <https://waterservices.usgs.gov/rest/IV-Service.html>`_.
Ils ont une longue liste de paramètres à spécifier en fonction du type de données sur l’eau que vous souhaitez récupérer,
qui est passé par l’argument parameterCd. Par exemple, si vous vouliez aller chercher l’évacuation de l’eau, nivelez
les données de température des trois dernières heures de North Fork Vermilion River près de Bismarck, IL, vous utiliseriez
l’URL suivante :
https://waterservices.usgs.gov/nwis/iv/?format=waterml,2.0&indent=on&site=03338780&period=PT3H&parameterCd=00060,00065,00011.
Une liste de codes de paramètres à utiliser pour personnaliser vos résultats peut être trouvée
`ici <https://help.waterdata.usgs.gov/code/parameter_cd_query?fmt=rdb&inline=true&group_cd=%25>`_.
Les plugins pour n’importe quel service Web GET peuvent être généralisés pour utilisation, de sorte que les plugins
utilisés pour l’API NOAA CO-OPS peuvent également être réutilisés dans ce contexte. Par défaut, les ID de station
à transmettre sont différents, ainsi que le méthode de les passer, de sorte que le code de plug-in qui détermine les
ID de station à utiliser diffère, mais la méthode conceptuellement, c’est toujours la même chose. Vous transmettez
une version généralisée de l’URL comme destination dans la config, par exemple
 https://waterservices.usgs.gov/nwis/iv/?format=waterml,2.0&indent=on&site={0}&period=PT3H&parameterCd=00060,00065,00011

et dans le plugin, vous remplaceriez le '{0}' (Python rend cela facile avec le formatage de chaîne) par les sites qui
vous intéressent, et si d’autres paramètres doivent être modifiés, ils peuvent être remplacés de la même manière.
Si un fichier d’ID de site de station n’a pas été transmis en tant qu’option de configuration de plug-in,
le plug-in saisit par défaut tout les identifiants de site enregistrés à partir de
`the USGS website <https://water.usgs.gov/osw/hcdn-2009/HCDN-2009_Station_Info.xlsx>`_.
Le service Web IV prend en charge les requêtes avec plusieurs ID de site spécifiés (séparés par des virgules).
Si l’option plugin *poll_usgs_nb_stn* a été spécifié à la taille du bloc dans la configuration, il faudra des
groupes de données de stations en fonction du nombre passé (cela réduit les requêtes Web et accélère
la collecte de données en cas de collecte en bloc).

Pour exécuter cet exemple, les configs et les plugins se trouvent sous *plugins*
(`poll_usgs.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_usgs.py>`_ 
et `download_usgs.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_usgs.py>`_)
et *examples* (`pollusgs.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollusgs.conf>`_
et `subusgs.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/subusgs.conf>`_).

Cas d'utilisation
-----------------
Les plug-ins hydrométriques ont été développés pour le cas d’utilisation canhys d’Environnement Canada, où les fichiers
contenant les métadonnées de la station seraient utilisées comme données d’entrée pour recueillir les données
hydrométriques. Chaque plugin fonctionne également en générant tous les identifiants de station valides de l’autorité
de l’eau elle-même et le branchement de ces entrées. Cette option alternative peut être a basculé en omettant la
variable de configuration du plug-in qui spécifierait autrement le fichier de métadonnées de la station.
Les plugins de téléchargement renomment également le fichier selon la convention spécifique de ce cas d’utilisation.

La plupart de ces sources ont des avertissements que ces données ne sont pas de qualité assurée, mais elles sont rassemblées en soft
en temps réel (annoncées a la secondes/minutes à partir du moment où elles ont été enregistré).

