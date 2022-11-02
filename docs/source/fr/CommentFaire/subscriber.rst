
==================
 Guide de l’abonné
==================

---------------------------------------------------------------------
Réception de données à partir d’une pompe de données MetPX-Sarracenia
---------------------------------------------------------------------


Enregistrement de révision
--------------------------


:version: |release|
:date: |today|


Introduction
------------
Une pompe de données Sarracenia est un serveur Web avec des notifications
pour que les abonnés sachent rapidement, quand de nouvelles données sont arrivées.
Pour savoir quelles données sont déjà disponibles sur une pompe, il faut
afficher l’arborescence avec un navigateur Web.
Pour des besoins immédiats simples, on peut télécharger des données en utilisant le
navigateur lui-même, ou un outil standard tel que wget.
L’intention habituelle est que sr_subscribe
télécharge automatiquement les données souhaitées dans un répertoire sur une
machine d'un abonné où d’autres logiciels peuvent les traiter.  Veuillez noter:

- l’outil est entièrement piloté par ligne de commande (il n’y a pas d’interface graphique). Plus précisément,
  il est principalement piloté par fichier de configuration.
  La plupart de l'*interface* implique l’utilisation d’un éditeur de texte pour modifier les fichiers de configuration.
- lorsqu’il est écrit pour être compatible avec d’autres environnements,
  l’accent est mis sur l’utilisation de Linux.
- l’outil peut être utilisé soit comme un outil d’utilisateur final, soit comme un moteur de transfert à l’échelle du système.
  Ce guide est axé sur le cas de l’utilisateur final.
- Des documents de référence plus détaillés sont disponibles à l’adresse suivante :
  page de manuel sr_subscribe(1) traditionnelle,
- Toute la documentation du paquet est disponible
  à https://github.com/MetPX

Alors que Sarracenia peut fonctionner avec n’importe quel arbre Web, ou n’importe quelle URL
que les sources choisissent de poster, il y a une mise en page conventionnelle.
Le serveur Web d’une pompe de données exposera simplement des dossiers accessibles sur le Web
et la racine de l’arbre est la date, dans le format AAAAMMJJ.
Ces dates ne représentent rien sur les données autres que
quand elles ont été mis dans le réseau de pompage, et puisque Sarracenia
utilise toujours le temps coordonné universel, les dates peuvent ne pas correspondre à
la date/heure actuelle à l’emplacement de l’abonné::

  Index of /

  Name                    Last modified      Size  Description
  Parent Directory                             -   
  20151105/               2015-11-27 06:44    -   
  20151106/               2015-11-27 06:44    -   
  20151107/               2015-11-27 06:44    -   
  20151108/               2015-11-27 06:44    -   
  20151109/               2015-11-27 06:44    -   
  20151110/               2015-11-27 06:44    -  


Un nombre variable de jours sont stockés sur chaque pompe de données, et pour ceux qui mettent
l’accent sur une livraison fiable en temps réel, le nombre de jours sera plus court.
Pour les autres pompes, où les pannes à long terme doivent être tolérées, plus de jours
seront conservés.


Sous le premier niveau d’arbres de date, il y a un répertoire
par source.  Une source dans Sarracenia est un compte utilisé pour injecter des
données dans le réseau de pompage.  Les données peuvent traverser de nombreuses pompes sur son
chemin vers celles qui sont visibles::

  Index of /20151110
  
  Name                    Last modified      Size  Description
  Parent Directory                             -   
  UNIDATA-UCAR/           2015-11-27 06:44    -   
  NOAAPORT/               2015-11-27 06:44    -   
  MSC-CMC/                2015-11-27 06:44    -   
  UKMET-RMDCN/            2015-11-27 06:44    -   
  UKMET-Internet/         2015-11-27 06:44    -   
  NWS-OPSNET/             2015-11-27 06:44    -  
  
Les données sous chacun de ces répertoires ont été obtenues à partir de la
source. Dans ces exemples, il est en fait injecté par DataInterchange
et les noms sont choisis pour représenter l’origine des données.

Pour lister les configurations disponibles avec *sr_subscribe list* ::

  $ sr3 list examples
    Sample Configurations: (from: /usr/lib/python3/dist-packages/sarracenia/examples )
    cpump/cno_trouble_f00.inc        poll/aws-nexrad.conf             poll/pollingest.conf             poll/pollnoaa.conf               poll/pollsoapshc.conf            
    poll/pollusgs.conf               poll/pulse.conf                  post/WMO_mesh_post.conf          sarra/wmo_mesh.conf              sender/ec2collab.conf            
    sender/pitcher_push.conf         shovel/no_trouble_f00.inc        subscribe/WMO_Sketch_2mqtt.conf  subscribe/WMO_Sketch_2v3.conf    subscribe/WMO_mesh_CMC.conf      
    subscribe/WMO_mesh_Peer.conf     subscribe/aws-nexrad.conf        subscribe/dd_2mqtt.conf          subscribe/dd_all.conf            subscribe/dd_amis.conf           
    subscribe/dd_aqhi.conf           subscribe/dd_cacn_bulletins.conf subscribe/dd_citypage.conf       subscribe/dd_cmml.conf           subscribe/dd_gdps.conf           
    subscribe/dd_ping.conf           subscribe/dd_radar.conf          subscribe/dd_rdps.conf           subscribe/dd_swob.conf           subscribe/ddc_cap-xml.conf       
    subscribe/ddc_normal.conf        subscribe/downloademail.conf     subscribe/ec_ninjo-a.conf        subscribe/hpfx_amis.conf         subscribe/local_sub.conf         
    subscribe/pitcher_pull.conf      subscribe/sci2ec.conf            subscribe/subnoaa.conf           subscribe/subsoapshc.conf        subscribe/subusgs.conf           
    sender/ec2collab.conf            sender/pitcher_push.conf         watch/master.conf                watch/pitcher_client.conf        watch/pitcher_server.conf        
    watch/sci2ec.conf


Chaque section de la liste affiche le contenu du répertoire entre parenthèses.
Pour utiliser un exemple comme point de départ ::

  $ sr3 add subscribe/dd_amis.conf
    add: 2021-01-26 01:13:54,047 [INFO] sarracenia.sr add copying: /usr/lib/python3/dist-packages/sarracenia/examples/subscribe/dd_amis.conf to /home/peter/.config/sr3/subscribe/dd_amis.conf 


Maintenant, les fichiers dans  `.config/` peut être utilisé directement::
 
  $ sr3 list
    User Configurations: (from: /home/peter/.config/sr3 )
    subscribe/dd_amis.conf           admin.conf                       credentials.conf                 default.conf                     
    logs are in: /home/peter/.cache/sr3/log


Pour afficher une configuration, donnez-la à `sr_subscribe list` comme argument::

  $ sr3 list subscribe/dd_amis.conf
    # il s’agit d’un flux de bulletin wmo (un ensemble appelé AMIS dans les temps anciens)
    
    broker amqps://dd.weather.gc.ca/
    
    # instances: nombre de processus de téléchargement à exécuter à la fois.  la valeur par défaut est 1. Pas assez pour ce cas
    instances 5
    
    # expire, en utilisation opérationnelle, devrait être plus longue que l’interruption prévue
    expire 10m
    
    subtopic bulletins.alphanumeric.#
    
    accept .*


Pour supprimer une configuration::

  $ sr3 remove subscribe/dd_amis
    2021-01-26 01:17:24,967 [INFO] root remove FIXME remove! ['subscribe/dd_amis']
    2021-01-26 01:17:24,967 [INFO] root remove removing /home/peter/.config/sr3/subscribe/dd_amis.conf 


Ressources côté serveur allouées aux abonnés
--------------------------------------------

Chaque configuration entraîne la déclaration des ressources correspondantes sur le courtier.
Lors de la modification des paramètres *subtopic* ou *queue*, ou lorsque l’on s’attend à ne pas utiliser
une configuration pour une période prolongée, il est préférable de::

  sr3 cleanup subscribe/swob.conf

qui désallouera la fil d’attente (et ses liaisons) sur le serveur.

Pourquoi? Chaque fois qu’un abonné est démarré, une fil d’attente est créée sur la pompe de données, avec
les liaisons de rubrique définies par le fichier de configuration. Si l’abonné est arrêté,
la fil d’attente continue de recevoir des messages de notification tels que définis par la sélection de subtopic, et lorsque le
l’abonné redémarre, les messages de notification en fil d’attente sont transférés au client.
Ainsi, lorsque l’option *subtopic* est modifiée, puisqu’elle est déjà définie sur le
serveur, on finit par ajouter une liaison plutôt que de la remplacer.  Par exemple
si l’un d’eux a un subtopic qui contient SATELLITE, puis arrête l’abonné,
modifier le fichier et maintenant le topic ne contient que RADAR, lorsque l’abonné est
redémarré, non seulement tous les fichiers satellites en fil d’attente seront envoyés au consommateur,
mais le RADAR est ajouté aux fixations, plutôt que de les remplacer, de sorte que l’abonné
obtiendra à la fois les données SATELLITE et RADAR même si la configuration
ne contient plus l'ancien.

De plus, si l’on expérimente et qu’une fil d’attente doit être arrêtée pendant très longtemps
elle peut accumuler un grand nombre de messages de notification. Le nombre total de messages de notification
sur une pompe de données a un effet sur les performances de la pompe pour tous les utilisateurs. C’est donc
conseillé de demander à la pompe de désaffecter les ressources lorsqu’elles ne seront pas nécessaires
pendant de longues périodes ou lors de l’expérimentation de différents paramètres.

Utilisation de plusieurs configurations
---------------------------------------

Placez tous les fichiers de configuration, avec le suffixe .conf, dans un répertoire
standard : ~/.config/sr3/subscribe/. Par exemple, s’il y a deux fichiers dans
ce répertoire : CMC.conf et NWS.conf, on pourrait alors exécuter ::

  peter@idefix:~/test$ sr3 start subscribe/CMC.conf 
  2016-01-14 18:13:01,414 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] sr_subscribe CMC 0001 starting
  2016-01-14 18:13:01,418 [INFO] sr_subscribe CMC 0002 starting
  2016-01-14 18:13:01,419 [INFO] sr_subscribe CMC 0003 starting
  2016-01-14 18:13:01,421 [INFO] sr_subscribe CMC 0004 starting
  2016-01-14 18:13:01,423 [INFO] sr_subscribe CMC 0005 starting
  peter@idefix:~/test$ 

pour démarrer la configuration de téléchargement CMC. On peut utiliser
la commande sr pour démarrer/arrêter plusieurs configurations à la fois.
La commande sr passera par les répertoires par défaut et démarrera
toutes les configurations qu’y si trouve ::

  peter@idefix:~/test$ sr3 start
  2016-01-14 18:13:01,414 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] sr_subscribe CMC 0001 starting
  2016-01-14 18:13:01,418 [INFO] sr_subscribe CMC 0002 starting
  2016-01-14 18:13:01,419 [INFO] sr_subscribe CMC 0003 starting
  2016-01-14 18:13:01,421 [INFO] sr_subscribe CMC 0004 starting
  2016-01-14 18:13:01,423 [INFO] sr_subscribe CMC 0005 starting
  2016-01-14 18:13:01,416 [INFO] sr_subscribe NWS 0001 starting
  2016-01-14 18:13:01,416 [INFO] sr_subscribe NWS 0002 starting
  2016-01-14 18:13:01,416 [INFO] sr_subscribe NWS 0003 starting
  peter@idefix:~/test$ 

démarrera certains processus sr3 tels que configurés par CMC.conf et d’autres
pour correspondre à NWS.conf. Sr3 stop fera également ce que vous attendez. Tout comme le sr3 status.
Notez qu’il existe 5 processus sr_subscribe commencent par le CMC
et 3 NWS. Ce sont des *instances* et partagent les mêmes
fil d’attentes de téléchargement.

Livraison hautement prioritaire
-------------------------------

Bien que le protocole Sarracenia ne fournisse pas de hiérarchisation explicite, l’utilisation
de plusieurs files d’attentes offre des avantages similaires. Résultats de chaque configuration
dans une déclaration de fil d’attente côté serveur. Regroupez les produits à la même priorité dans
une fil d’attente en les sélectionnant à l’aide d’une configuration commune. Plus les regroupements sont petits,
plus le délai de traitement est faible. Alors que toutes les files d’attente sont traitées avec la même priorité,
les données passent plus rapidement dans des files d’attente plus courtes. On peut résumer par :

  **Utiliser plusieurs configurations pour établir la priorité**

Pour rendre le conseil concret, prenons l’exemple des données d’Environnement Canada
( dd.weather.gc.ca ), qui distribue des binaires quadrillés, des images satellite GOES,
plusieurs milliers de prévisions urbaines, des observations, des produits RADAR, etc...
Pour la météo en temps réel, les avertissements et les données RADAR sont la priorité absolue. À certaines
heures de la journée, ou en cas d’arriérés, plusieurs centaines de milliers de produits
peut retarder la réception de produits hautement prioritaires si une seule fil d’attente est utilisée.

Pour assurer un traitement rapide des données dans ce cas, définissez une configuration pour vous abonner
aux avertissements météorologiques (qui sont un très petit nombre de produits), une seconde pour les RADARS
(un groupe plus grand mais encore relativement petit), et un troisième (groupe le plus important) pour toutes
les autres données. Chaque configuration utilisera une fil d’attente distincte. Les avertissements seront
traités le plus rapidement, les RADARS feront la queue les uns contre les autres et auront
plus de retard, et d’autres produits partageront une seule fil d’attente et seront soumis à plus de
retard dans les cas d’arriéré.

https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/examples/subscribe/ddc_hipri.conf::

  broker amqps://dd.weather.gc.ca/
  mirror
  directory /data/web
  subtopic alerts.cap.#
  accept .*

https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/examples/subscribe/ddc_normal.conf::

  broker amqps://dd.weather.gc.ca/
  subtopic #
  reject .*alerts/cap.*
  mirror
  directory /data/web
  accept .*

Là où vous voulez le miroir du data mart qui commence à /data/web (vraisemblablement il y a un
serveur web configuré pour afficher ce répertoire.)  Probablement, la configuration *ddc_normal*
connaîtra beaucoup de files d’attente, car il y a beaucoup de données à télécharger.  Le *ddc_hipri.conf* est
uniquement abonné aux avertissements météorologiques au format Common Alerting Protocol, il y aura donc
peu ou pas de fil d’attente pour ces données.

Affiner la sélection
--------------------

.. Avertissement::
  **FIXME**: Faire une photo, avec un:

  - courtier à une extrémité, et le subtopic s’y applique.
  - client à l’autre extrémité, et l'accept/reject s’appliquent là.


Choisissez *subtopics* (qui sont appliquées sur le broker sans téléchargement de message de notification) pour affiner
le nombre de messages de notification qui traversent le réseau pour accéder aux processus clients sarracenia.
Les options *reject* et *accept* sont évaluées par les processus sr_subscriber eux-mêmes,
qui fourni un filtrage basé sur l’expression régulière des messages qui sont transférés.
*accept* fonctionne sur le chemin réel (enfin, l'URL), indiquant quels fichiers dans
le flux de notification reçu doit en fait être téléchargé. Regardez dans les *Downloads*
du fichier journal pour des exemples de ce chemin d’accès transformé.

.. Remarque:: Brève introduction aux expressions régulières

  Les expressions régulières sont un moyen très puissant d’exprimer les correspondances de motifs.
  Elles offrent une flexibilité extrême, mais dans ces exemples, nous n’utiliserons qu’un
  sous-ensemble très basique : le . est un caractère générique correspondant à n’importe quel caractère unique. Si c’est
  suivi d’un nombre d’occurrences, il indique combien de lettres correspondront au motif. le caractère * (astérisque) signifie n’importe quel nombre d’occurrences.
  ainsi:

  - .* désigne toute séquence de caractères de n’importe quelle longueur. En d’autres termes, faites correspondre n’importe quoi.
  - cap.* désigne toute séquence de caractères commençant par cap.
  - .*CAP.* désigne toute séquence de caractères avec CAP quelque part dedans.
  - .*cap désigne toute séquence de caractères qui se termine par CAP. Dans le cas où plusieurs parties de la chaîne
    peuvent correspondre, la plus longue est sélectionnée.
  - .*?cap comme ci-dessus, mais *non-greedy*, ce qui signifie que le match le plus court est choisi.

  Veuillez consulter diverses ressources Internet pour plus d’informations sur l’ensemble
  de variété de correspondance possible avec les expressions régulières :

  - https://docs.python.org/3/library/re.html
  - https://en.wikipedia.org/wiki/Regular_expression
  - http://www.regular-expressions.info/ 

retour aux exemples de fichiers de configuration :

Notez ce qui suit ::

$ sr3 edit subscribe/swob

  broker amqps://anonymous@dd.weather.gc.ca
  accept .*/observations/swob-ml/.*

  #écrire tous les SWOBS dans le répertoire de travail actuel
  #MAUVAIS : CE N’EST PAS AUSSI BON QUE L’EXEMPLE PRÉCÉDENT
  #     NE PAS avoir de "subtopic" et filtrer avec "accept" SIGNIFIE QUE DES NOTIFICATIONS EXCESSIVES sont traitées.

Cette configuration, du point de vue de l’abonné,  livrera probablement
les mêmes données que l’exemple précédent. Toutefois, le subtopic par défaut étant
un caractère générique signifie que le serveur transférera toutes les notifications pour le
serveur (probablement des millions d’entre eux) qui sera ignoré par le processus de l’abonné qui
applique la clause d’acceptation. Il consommera beaucoup plus de CPU et de
bande passante sur le serveur et le client. Il faut choisir les subtopics appropriés
pour minimiser les notifications qui seront transférées uniquement pour être ignorées.
Les modèles *accept* (et *reject*) sont utilisés pour affiner davantage *subtopic* plutôt
que de le remplacer.

Par défaut, les fichiers téléchargés seront placés dans le répertoire actuel
lors du démarrage de sr_subscribe. Cela peut être remplacé à l’aide de
l’option *directory*.

Si vous téléchargez une arborescence de répertoires et que l’intention est de mettre en miroir l’arborescence,
alors l’option miroir doit être définie::

$ sr3 edit subscribe/swob

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  directory /tmp
  mirror True
  accept .*
  #
  # au lieu d’écrire dans le répertoire de travail actuel, écrivez dans /tmp.
  # dans /tmp. Mirror: créer une hiérarchie comme celle du serveur source.

On peut également intercaler les directives *directory* et *accept/reject* pour construire
une hiérarchie arbitrairement différente de ce qui se trouvait sur la pompe de données de source.
Le fichier de configuration est lu de haut en bas, alors sr_subscribe
trouve un paramètre d’option ''directory'', seulement les clauses ''accept'' après
celles la entraîneront le placement de fichiers par rapport à ce répertoire ::

$ sr3 edit subscribe/ddi_ninjo_part1.conf 

  broker amqps://ddi.cmc.ec.gc.ca/
  subtopic ec.ops.*.*.ninjo-a.#

  directory /tmp/apps/ninjo/import/point/reports/in
  accept .*ABFS_1.0.*
  accept .*AQHI_1.0.*
  accept .*AMDAR_1.0.*

  directory /tmp/apps/ninjo/import/point/catalog_common/in
  accept .*ninjo-station-catalogue.*

  directory /tmp/apps/ninjo/import/point/scit_sac/in
  accept .*~~SAC,SAC_MAXR.*

  directory /tmp/apps/ninjo/import/point/scit_tracker/in
  accept .*~~TRACKER,TRACK_MAXR.*

Dans l’exemple ci-dessus, les données du catalogue ninjo-station sont placées dans le
catalog_common/in, plutôt que dans l'hiérarchie des données ponctuelles
utilisée pour stocker les données qui correspondent aux trois premiers
clauses d'accept.

.. Remarque::
  Notez que .* dans la directive de subtopic, où
  cela signifie "correspondre à un topic" (c’est-à-dire qu’aucun caractère de point n’est autorisé dans un nom
  de sujet) a une signification différente de celle qui est dans une clause accept,
  où cela signifie correspondre à n’importe quelle chaîne.

  Oui, c’est déroutant.  Non, on ne peut pas l’aider.

Performance
-----------

Si les transferts vont trop lentement, les étapes sont les suivantes:


Optimiser la sélection des fichiers par processus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Souvent, les utilisateurs spécifient # comme subtopic, ce qui signifie que les accept/reject
  font tout le travail. Dans de nombreux cas, les utilisateurs ne sont intéressés que par une petite fraction des
  fichiers publiés.  Pour de meilleures performances, **Rendez *suntopic* aussi spécifique que possible** pour
  minimiser l’envoi de messages de notification envoyés par le courtier et qui arrivent sur l’abonné uniquement pour
  se faire rejetés. (utilisez l’option *log_reject* pour trouver de tels produits.)

* **Placez les instructions *reject* le plus tôt possible dans la configuration**. Comme le rejet enregistre
  le traitement de tous les regex ultérieurs dans la configuration.

* **Avoir peu de clauses d’acceptation/rejet** : parce qu’il s’agit d’une expression régulière
  les clauses de correspondance, accept/reject sont coûteuses, mais l’évaluation d’un
  regex n’est pas beaucoup plus cher qu’un seul, il est donc préférable d’en avoir
  quelques un plus compliqués que beaucoup de simples.  Exemple::

          accept .*/SR/KWAL.*
          accept .*/SO/KWAL.*

  fonctionnera à la moitié de la vitesse (ou le double de la surcharge du processeur) par rapport à ::

         accept .*/S[OR]/KWAL.*

* **Utilisez suppress_duplicates**.  Dans certains cas, il y a un risque que le même fichier
  se fassent annoncer plus d’une fois.  Habituellement, les clients ne veulent pas de copies redondantes
  des fichiers transférés.  L’option *suppress_duplicates* configure un cache de
  les sommes de contrôle des fichiers qui sont passés et empêche leur traitement
  encore.

* Si vous transférez de petits fichiers, le traitement de transfert intégré est tout à fait
  bon, mais **s’il y a des fichiers volumineux** dans le mélange, alors un chargement sur un binaire en C
  va aller plus vite. **Utilisez des plugins tels que accel_wget, accel_sftp,
  accel_cp** (pour les fichiers locaux.) Ces plugins ont des paramètres de seuil de sorte que
  les méthodes optimal python transfer sont toujours utilisées pour les fichiers plus petits que le
  seuil.

* **l’augmentation du prefetch** peut réduire la latence moyenne (amortie sur
  le nombre de messages de notification prélus.) Les performances peuvent être amélioré sur une longue
  distances ou taux de messages de notification élevés au sein d’un centre de données.

* Si vous contrôlez l’origine d’un flux de produits, et les consommateurs voudront une
  très grande proportion des produits annoncés, et les produits sont petits
  (quelques K au plus), envisagez de combiner l’utilisation de v03 avec l’inlining pour un
  transfert optimal de petits fichiers. Remarque, si vous avez une grande variété d’utilisateurs
  qui veulent tous des ensembles de données différents, l’inlining peut être contre-productif. Ceci
  entraînera également des messages de notification plus importants et signifiera une charge beaucoup plus élevée sur le courtier.
  Ca peut optimiser quelques cas spécifiques, tout en ralentissant le courtier dans l’ensemble.


Utiliser des instances
~~~~~~~~~~~~~~~~~~~~~~

Une fois que vous avez optimisé ce qu’un seul abonné peut faire, si ce n’est pas assez rapide,
utilisez l’option *instances* pour que davantage de processus participent au
traitement.  Avoir 10 ou 20 instances n’est pas un problème du tout.  Le maximum
nombre d’instances qui augmenteront les performances plafonnera à un moment donné
qui varie en fonction de la latence à négocier, de la vitesse de traitement des instances de
chaque fichier, la prélecture en cours d’utilisation, etc...  Il faut expérimenter.

En examinant les journaux d’instance, s’ils semblent attendre les messages de notification pendant une longue période,
ne faisant aucun transfert, alors on aurait pu atteindre la saturation de la fil d’attente.
Cela se produit souvent à environ 40 à 75 instances. Rabbitmq gère une seule fil d’attente
avec un seul processeur, et il y a une limite au nombre de messages de notification qu’une fil d’attente peut traiter
dans une unité de temps donnée.

Si la fil d’attente devient saturée, nous devons partitionner les abonnements
dans plusieurs configurations. Chaque configuration aura une fil d’attente distincte,
et les files d’attente auront leurs propres processeurs (CPU). Avec un tel partitionnement, nous sommes allés
à une centaine d’instances et pas vu de saturation. Nous ne savons pas quand nous courons
hors performance.

Nous n’avons pas encore eu besoin de faire évoluer le courtier lui-même.


Suppression des doublons haute performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Une mise en garde à l’utilisation de *instances* est que *suppress_duplicates* est inefficace
car les différentes occurrences d’un même fichier ne seront pas reçues par les même
instances, et donc avec n instances, environ n-1/n doublons passeront à travers.

Afin de supprimer correctement les messages de notification de fichiers en double dans les flux de données
qui ont besoin de plusieurs instances, on utilise le winnowing avec *post_exchangeSplit*.
Cette option envoie des données à plusieurs échanges post-exchange en fonction de la somme de contrôle des données,
de sorte que tous les fichiers en double seront acheminés vers le même processus winnow.
Chaque processus winnow exécute la suppression normale des doublons utilisée dans des instances uniques,
puisque tous les fichiers avec la même somme de contrôle se retrouvent avec le même winnow, cela fonctionne.
Les processus winnow sont ensuite postés sur l’échange utilisé par des piscines de traitement réels.

Pourquoi la suppression des doublons haute performance est-elle une bonne chose ? Parce que
le modèle de disponibilité de Sarracenia est d’avoir des piles d’applications individuelles
qui produisent aveuglément des copies réductrices de produits. Il ne nécessite aucun ajustement
d’application d’un seul nœud à la participation à un cluster. Sarracenia
sélectionne le premier résultat que nous recevons pour le transfert. Cela évite tout tri
du protocole de quorum, une source d’une grande complexité en haute disponibilité
et en mesurant en fonction de la production, minimise le potentiel des
systèmes à apparaître, lorsqu’ils ne sont pas complètement fonctionnels. Les
applications n’ont pas besoin de savoir qu’il existe une autre pile produisant le même
produit, ce qui les simplifie également.

Plugins
-------

Le traitement des fichiers par défaut est souvent correct, mais il existe également des personnalisations prédéfinies qui
peuvent être utilisé pour modifier le traitement effectué par les composants. La liste des plugins prédéfinis est
dans un répertoire 'plugins' où que le paquet soit installé (consultable avec *sr_subscribe list*)
exemple de sortie::

   $ sr3 list help
   blacklab% sr3 list help
   Valid things to list: examples,eg,ie flow_callback,flowcb,fcb v2plugins,v2p

   $ sr3 list fcb
      
      
   Provided callback classes: ( /home/peter/Sarracenia/sr3/sarracenia ) 
   flowcb/accept/delete.py          flowcb/accept/downloadbaseurl.py 
   flowcb/accept/hourtree.py        flowcb/accept/httptohttps.py     
   flowcb/accept/longflow.py        flowcb/accept/posthourtree.py    
   flowcb/accept/postoverride.py    flowcb/accept/printlag.py        
   flowcb/accept/rename4jicc.py     flowcb/accept/renamedmf.py       
   flowcb/accept/renamewhatfn.py    flowcb/accept/save.py            
   flowcb/accept/speedo.py          flowcb/accept/sundewpxroute.py   
   flowcb/accept/testretry.py       flowcb/accept/toclusters.py      
   flowcb/accept/tohttp.py          flowcb/accept/tolocal.py         
   flowcb/accept/tolocalfile.py     flowcb/accept/wmotypesuffix.py   
   flowcb/filter/deleteflowfiles.py flowcb/filter/fdelay.py          
   flowcb/filter/pclean_f90.py      flowcb/filter/pclean_f92.py      
   flowcb/filter/wmo2msc.py         flowcb/gather/file.py            
   flowcb/gather/message.py         flowcb/housekeeping/hk_police_queues.py 
   flowcb/housekeeping/resources.py flowcb/line_log.py               
   flowcb/log.py                    flowcb/mdelaylatest.py           
   flowcb/nodupe/data.py            flowcb/nodupe/name.py            
   flowcb/pclean.py                 flowcb/poll/airnow.py            
   flowcb/poll/mail.py              flowcb/poll/nasa_mls_nrt.py      
   flowcb/poll/nexrad.py            flowcb/poll/noaa_hydrometric.py  
   flowcb/poll/usgs.py              flowcb/post/message.py           
   flowcb/retry.py                  flowcb/sample.py                 
   flowcb/script.py                 flowcb/send/email.py             
   flowcb/shiftdir2baseurl.py       flowcb/v2wrapper.py              
   flowcb/wistree.py                flowcb/work/delete.py            
   flowcb/work/rxpipe.py            
   $ 

Les plugins peuvent être inclus dans les configurations en ajoutant des lignes 'flow_callback' comme::

   flowcb work.rxpipe

qui ajoute le rappel donné à la liste des rappels à appeler.
Il y a aussi::

   flowcb_prepend work.rxpipe

qui ajoutera ce rappel à la liste, de sorte qu’il est appelé avant
ceux qui ne sont pas prépendés.

Les plugins sont tous écrits en python, et les utilisateurs peuvent créer les leurs et les placer dans ~/.config/sr3/plugins.
Pour plus d’informations sur la création de nouveaux plug-ins personnalisés, reportez-vous à la section `Writing Flow Callbacks <FlowCallbacks.rst>`_


Pour récapituler :

* Pour voir les plugins actuellement disponibles sur le système *sr3 list fcb*
* Pour afficher le contenu d’un plugin: * liste sr3 <plugin>*
* Les plugins peuvent avoir des paramètres d’option, tout comme ceux intégrés
* Pour les définir, placez les options dans le fichier de configuration avant que le plugin ne s’appelle lui-même
* Pour créer vos propres plugins, créez-les dans ~/.config/sr3/plugins.

file_rxpipe
-----------

Le plugin file_rxpipe pour sr_subscribe permet à toutes les instances d’écrire les noms
des fichiers téléchargés sur un canal nommé. La configuration de cette configuration nécessitait deux lignes dans
un fichier de configuration sr_subscribe ::

$ mknod /home/peter/test/.rxpipe p
$ sr3 edit subscribe/swob 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  rxpipe_name /home/peter/test/.rxpipe

  callback work/rxpipe

  directory /tmp
  mirror True
  accept .*
  # rxpipe est un plugin on_file intégré qui écrit le nom du fichier reçu dans
  # un canal nommé '.rxpipe' dans le répertoire de travail actuel.

Avec rxpipe, chaque fois qu’un transfert de fichiers est terminé et est prêt pour
post-traitement, son nom est écrit sur le canal linux (nommé .rxpipe.)


.. REMARQUE::

   Dans le cas où un grand nombre d’instances d’abonnement fonctionnent
   Sur la même configuration, il y a une légère probabilité que les notifications
   peuvent se corrompre mutuellement dans le canal nommé.

   **FIXME** Nous devrions probablement vérifier si cette probabilité est négligeable ou non.

Analyse d'antivirus
-------------------

Un autre exemple d’utilisation facile d’un plugin est de réaliser une analyse antivirus.
En supposant que ClamAV-daemon est installé, ainsi que le python3-pyclamd
package, alors on peut ajouter ce qui suit à un
fichier de configuration d'un abonné::

  broker amqps://dd.weather.gc.ca
  topicPredix v02.post
  batch 1
  callback clamav
  subtopic observations.swob-ml.#
  accept .*

Pour que chaque fichier téléchargé soit analysé av. Exemple d’exécution ::

    $ sr3 foreground subscribe//dd_swob.conf 

    blacklab% sr3 foreground subscribe/dd_swob
    2022-03-12 18:47:18,137 [INFO] 29823 sarracenia.flow loadCallbacks plugins to load: ['sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'sarracenia.flowcb.clamav.Clamav', 'sarracenia.flowcb.log.Log']
    clam_scan on_part plugin initialized
    2022-03-12 18:47:22,865 [INFO] 29823 sarracenia.flowcb.log __init__ subscribe initialized with: {'after_work', 'on_housekeeping', 'after_accept'}
    2022-03-12 18:47:22,866 [INFO] 29823 sarracenia.flow run options:
    _Config__admin=amqp://bunnymaster:Easter1@localhost/ None True True False False None None, _Config__broker=amqps://anonymous:anonymous@dd.weather.gc.ca/ None True True False False None None,
    _Config__post_broker=None, accel_threshold=0, acceptSizeWrong=False, acceptUnmatched=False, action='foreground', attempts=3, auto_delete=False, baseDir=None, baseUrl_relPath=False, batch=100, bind=True,
    bindings=[('xpublic', ['v02', 'post'], ['observations.swob-ml.#'])], bufsize=1048576, bytes_per_second=None, bytes_ps=0, cfg_run_dir='/home/peter/.cache/sr3/subscribe/dd_swob', config='dd_swob',
    configurations=['subscribe/dd_swob'], currentDir=None, dangerWillRobinson=False, debug=False, declare=True, declared_exchanges=['xpublic', 'xcvan01'],
   .
   .
   .
    022-03-12 18:47:22,867 [INFO] 29823 sarracenia.flow run pid: 29823 subscribe/dd_swob instance: 0
    2022-03-12 18:47:30,019 [INFO] 29823 sarracenia.flowcb.log after_accept accepted: (lag: 140.22 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/COGI/2022-03-12-2344-COGI-AUTO-minute-swob.xml 
   .
   .
   .  # bonnes entrées...

    22-03-12 19:00:55,347 [INFO] 30992 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2347-CVPX-AUTO-minute-swob.xml
    2022-03-12 19:00:55,353 [INFO] 30992 sarracenia.flowcb.clamav avscan_hit part_clamav_scan took 0.00579023 seconds, no viruses in /tmp/dd_swob/2022-03-12-2347-CVPX-AUTO-minute-swob.xml
    2022-03-12 19:00:55,385 [INFO] 30992 sarracenia.flowcb.log after_accept accepted: (lag: 695.46 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/COTR/2022-03-12-2348-COTR-AUTO-minute-swob.xml 
    2022-03-12 19:00:55,571 [INFO] 30992 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2348-COTR-AUTO-minute-swob.xml
    2022-03-12 19:00:55,596 [INFO] 30992 sarracenia.flowcb.clamav avscan_hit part_clamav_scan took 0.0243611 seconds, no viruses in /tmp/dd_swob/2022-03-12-2348-COTR-AUTO-minute-swob.xml
    2022-03-12 19:00:55,637 [INFO] 30992 sarracenia.flowcb.log after_accept accepted: (lag: 695.71 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/CWGD/2022-03-12-2348-CWGD-AUTO-minute-swob.xml 
    2022-03-12 19:00:55,844 [INFO] 30992 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2348-CWGD-AUTO-minute-swob.xml
  
    .
    .
    . # mauvaises entrées.

    2022-03-12 18:50:13,809 [INFO] 30070 sarracenia.flowcb.log after_work downloaded ok: /tmp/dd_swob/2022-03-12-2343-CWJX-AUTO-minute-swob.xml 
    2022-03-12 18:50:13,930 [INFO] 30070 sarracenia.flowcb.log after_accept accepted: (lag: 360.72 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/CAJT/2022-03-12-2343-CAJT-AUTO-minute-swob.xml 
    2022-03-12 18:50:14,104 [INFO] 30070 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2343-CAJT-AUTO-minute-swob.xml
    2022-03-12 18:50:14,105 [ERROR] 30070 sarracenia.flowcb.clamav avscan_hit part_clamav_scan took 0.0003829 not forwarding, virus detected in /tmp/dd_swob/2022-03-12-2343-CAJT-AUTO-minute-swob.xml

    .
    . # chaque intervalle de heartbeat, un petit résumé:
    .
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.clamav on_housekeeping files scanned 121, hits: 5


Journalisation et débogage
--------------------------

Comme les composants sr3 s’exécutent généralement en tant que démon (sauf s’ils sont appelés en mode *foreground*)
on examine normalement son fichier journal pour savoir comment se déroule le traitement.  Lorsque seulement
une seule instance est en cours d’exécution, on peut afficher le journal du processus en cours d’exécution comme suit::

   sr3 log subscribe/*myconfig*

FIXME: pas implémenté correctement. normalement utiliser la commande "foreground" à la place.

Où *myconfig* est le nom de la configuration en cours d’exécution. Les fichiers journaux
sont placés conformément à la spécification XDG Open Directory. Il y aura un fichier journal
pour chaque *instance* (processus de téléchargement) d’un processus sr_subscribe exécutant la configuration myflow ::

   in linux: ~/.cache/sarra/log/sr_subscribe_myflow_01.log

On peut remplacer le placement sur Linux en définissant la variable d’environnement XDG_CACHE_HOME, comme
par: `XDG Open Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_
Les fichiers journaux peuvent être très volumineux pour les configurations à volume élevé, de sorte que la journalisation est très configurable.

Pour commencer, on peut sélectionner le niveau de journalisation dans l’ensemble de l’application en utilisant
logLevel et logReject :

- debug
   Définir l’option de debug est identique à utiliser **logLevel debug**

- logLevel ( par défaut: info )
   Niveau de journalisation exprimé par la journalisation de python. Les valeurs possibles sont les suivantes:  critical, error, info, warning, debug.

- log_reject <True|False> ( par défaut: False )
   imprimer un message de journal lors du *rejet* des messages de notification (en choisissant de ne pas télécharger les fichiers correspondants)

   Les messages de rejet indiquent également la raison du rejet.

À la fin de la journée (à minuit), ces fichiers de journalisations sont pivotées automatiquement par
les composants, et l’ancien journal obtient un suffixe de date. Le répertoire dans lequel
les journaux sont stockés peut être remplacé par l’option **log**, le nombre
de journaux pivotés à conserver sont définis par le paramètre **logRotate**. Le journal le plus ancien
est supprimé lorsque le nombre maximal de journaux a été atteint et que cela
poursuit pour chaque rotation. Un intervalle prend une durée de l’intervalle et
cela peut prendre un suffixe d’unité de temps, tel que 'd\|D' pour les jours, 'h\|H' pour les heures,
ou 'm\|M' pour les minutes. Si aucune unité n’est fournie, les journaux tourneront à minuit.
Voici quelques paramètres pour la gestion des fichiers journaux :

- log <dir> ( par défaut: ~/.cache/sarra/log ) (sur Linux)
   Répertoire dans lequel stocker les fichiers journaux.

- statehost <False|True> ( par défaut: False )
   Dans les grands centres de données, l’annuaire de base peut être partagé entre des milliers de
   nœuds. Statehost ajoute le nom du nœud après le répertoire de la cache pour le rendre
   unique à chaque nœud. Ainsi, chaque nœud a ses propres fichiers d’état et journaux.
   Par exemple, sur un nœud nommé goofy, ~/.cache/sarra/log/ devient ~/.cache/sarra/goofy/log.

- logRotate <max_logs> ( par défaut: 5 , alias: lr_backupCount)
   Nombre maximal de journaux archivés.

- logRotate_interval <duration>[<time_unit>] ( par défaut: 1, alias: lr_interval)
   La durée de l’intervalle avec une unité de temps optionnelle (ex. 5m, 2h, 3d)

- permLog ( par défaut: 0600 )
   Bits d’autorisation à définir sur les fichiers journaux.



Réglage du débogage flowcb/log.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
En plus des options d’application, il existe un flowcb qui est utilisé par défaut pour la journalisation, qui
a des options supplémentaires:

- logMessageDump (par défaut : off) indicateur booléen
  S’ils sont définis, tous les champs d’un message de notification sont imprimés, à chaque événement, plutôt qu’une simple référence url/chemin.

- logEvents ( after_accept par défaut,after_work,on_housekeeping )
   émettre des messages de journal standard à certains points durant le traitement des messages.
   autres valeurs : on_start, on_stop, post, gather, ... etc...

etc... On peut également modifier les plugins fournis, ou en écrire de nouveaux pour changer complètement la journalisation.


Réglage du débogage moth
~~~~~~~~~~~~~~~~~~~~~~~~
L’activation de logLevel pour déboguer l’ensemble de l’application entraîne souvent des fichiers journaux excessivement volumineux.
Par défaut, la classe parent Messages Organized into Topic Hierarchies (Moth) pour les protocoles de messagerie,
ignore l’option de débogage à l’échelle de l’application.  Pour activer le débogage de la sortie de ces classes, il y a
des paramètres supplémentaires.

On peut définir explicitement l’option de débogage spécifiquement pour la classe de protocole de messagerie::

    set sarracenia.moth.amqp.AMQP.logLevel debug
    set sarracenia.moth.mqtt.MQTT.logLevel debug

cela va rendra la couche de messagerie très verbeuse.
Parfois, lors des tests d’interopérabilité, il faut voir les messages de notification bruts, avant de décoder par classes de Moth ::

    messageDebugDump

L’une ou l’autre de ces options ou les deux feront de très gros journaux et sont mieux utilisées judicieusement.

Métrique Housekeeping
---------------------
Les rappels de flux peuvent implémenter un point d’entrée on_housekeeping.  Ce point d’entrée est généralement
une possibilité pour les rappels d’imprimer périodiquement des métriques.  Le journal intégré et
les rappels de surveillance des ressources, par exemple, donnent des lignes dans le journal comme suit ::

    2022-03-12 19:00:55,114 [INFO] 30992 sarracenia.flowcb.housekeeping.resources on_housekeeping Current Memory cpu_times: user=1.97 system=0.3
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.housekeeping.resources on_housekeeping Memory threshold set to: 161.2 MiB
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.housekeeping.resources on_housekeeping Current Memory usage: 53.7 MiB / 161.2 MiB = 33.33%
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.clamav on_housekeeping files scanned 121, hits: 0 
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.log housekeeping_stats messages received: 242, accepted: 121, rejected: 121  rate:    50%
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.log housekeeping_stats files transferred: 0 bytes: 0 Bytes rate: 0 Bytes/sec
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.log housekeeping_stats lag: average: 778.91, maximum: 931.06 
  

Réception de fichiers redondants
--------------------------------

Dans les environnements où une grande fiabilité est requise, plusieurs serveurs
sont souvent configurés pour fournir des services. L’approche Sarracenia pour
la haute disponibilité est ´Active-Active´ en ce sens que toutes les sources sont en ligne
et la production de données en parallèle. Chaque source publie des données,
et les consommateurs les obtiennent de la première source qui les rend disponible,
en utilisant des sommes de contrôle pour déterminer si la référence donnée a été obtenue
ou pas.

Ce filtrage nécessite la mise en œuvre d’une pompe locale sans données avec
sr_winnow. Consultez le Guide de l’administrateur pour plus d’informations.

Proxys Web
----------

La meilleure méthode pour travailler avec des proxys Web est de mettre ce qui suit
dans le fichier default.conf::

   declare env HTTP_PROXY http://yourproxy.com
   declare env HTTPS_PROXY http://yourproxy.com

La mise en place de default.conf garantit que tous les abonnés utiliseront
le proxy, pas seulement une seule configuration.

Plus d’informations
-------------------

L3 `sr3(1) <../Reference/sr3.1.html>`_ est la source de référence informative définitive
sur les options de configuration. Pour plus d’informations,
consulter: `Sarracenia Documentation <https://metpx.github.io/sarracenia>`_


