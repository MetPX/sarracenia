
=================
 Guide D´abonnés
=================

-------------------------------------------------
Recevoir des données d´une pompe MetPX-Sarracenia
-------------------------------------------------

.. warning::
  **FIXME**: Missing sections are highlighted by **FIXME**.  What is here should be accurate!

.. contents::

Revision Record
---------------

:version: @Version@
:date: @Date@


Introduction
------------

Une pompe de données Sarracenia est un serveur web avec des avis publiés
quand les fichiers servi changent.  Pour savoir quelles données sont déjà 
disponibles sur une pompe, on peut visualiser l'arbre à l'aide d'un 
furreteur web. Pour des besoins immédiats simples, on peut télécharger 
des données à l'aide du fureteur lui-même, ou un outil standard tel que wget.
L'intention habituelle est d´utiliser sr_subscribe pour automatiquement
télécharger les données souhaitées sur une base régulière et automatisé,
et permettre traitement par d´autre logiciels. Noter:

- L'outil est entièrement piloté en ligne de commande (il n'y a pas d'interface graphique) 
  Plus précisément, il est principalement piloté par des fichiers de configuration.
  la plupart de l´*interface* implique l'utilisation d'un éditeur de texte pour 
  modifier les fichiers de configuration.
- tout en étant écrit pour être compatible avec d'autres environnements,
  l'accent est mis sur l'utilisation en Linux.
- l'outil peut être utilisé soit comme outil de l'utilisateur final, soit 
  comme moteur de transfert à l'échelle du système.
- Ce guide est axé sur le cas de l'utilisateur final.
- Des documents de référence plus détaillés sont disponibles à l'adresse suivante
  `sr_subscribe(1) <sr_subscribe.1.rst>`_ 
- Toute la documentation du paquet est disponible.
  à l'adresse https://github.com/MetPX

Alors que Sarracénie peut fonctionner avec n'importe quelle arborescence web, 
ou n'importe quelle URL que les sources choisissent d'afficher, il y a une mise 
en page conventionnelle.  Le serveur Web d'une pompe de données ne fera 
qu'exposer les dossiers accessibles sur le Web et la racine de l'arbre 
est la date, au format AAAAMMJJJ. Ces dates ne représentent quand il a 
été mis dans le réseau de pompage, et sarracénie utilise toujours le 
temps universel coordonné, les dates peuvent ne pas correspondre à
la date et l'heure actuelles dans la localité de l'abonné::

  Index of /

  Icon  Name                    Last modified      Size  Description
  [PARENTDIR] Parent Directory                             -   
  [DIR] 20151105/               2015-11-27 06:44    -   
  [DIR] 20151106/               2015-11-27 06:44    -   
  [DIR] 20151107/               2015-11-27 06:44    -   
  [DIR] 20151108/               2015-11-27 06:44    -   
  [DIR] 20151109/               2015-11-27 06:44    -   
  [DIR] 20151110/               2015-11-27 06:44    -  

Un nombre variable de jours est stocké sur chaque pompe de données. 
Les pompes qui mettent l'accent sur la fiabilité de la livraison en temps réel,
aura moins de jours en ligne. Pour d'autres pompes, lorsque des pannes de 
plus longue durée sont nécessaires à tolérer, plus de jours seront conservés.

Sous le premier niveau de l'arborescence par dates, il y a un répertoire
par source.  Une Source en Sarracenia est un compte utilisé pour ajouter de donnée
dans le réseau de pompes. Les données peuvent traverser de nombreuses pompes sur leur
chemin vers celui qui est visible pour un abonné en particulier::


  Index of /20151110
  
  Icon  Name                    Last modified      Size  Description
  [PARENTDIR] Parent Directory                             -   
  [DIR] UNIDATA-UCAR/           2015-11-27 06:44    -   
  [DIR] NOAAPORT/               2015-11-27 06:44    -   
  [DIR] MSC-CMC/                2015-11-27 06:44    -   
  [DIR] UKMET-RMDCN/            2015-11-27 06:44    -   
  [DIR] UKMET-Internet/         2015-11-27 06:44    -   
  [DIR] NWS-OPSNET/             2015-11-27 06:44    -  
  
Les données de chacun de ces répertoires ont été obtenues à partir de 
la base de données nommée source. Dans ces exemples, il est en fait 
injecté par la groupe DataInterchange de Services Partagés Canada, et les noms 
sont choisis pour représenter l'origine des données.

Vous devriez pouvoir lister les configurations disponibles avec *sr_subscribe list* ::


  blacklab% sr_subscribe list
  
  packaged plugins: ( /usr/lib/python3/dist-packages/sarra/plugins ) 
           __pycache__     destfn_sample.py       download_cp.py       download_dd.py 
       download_scp.py     download_wget.py          file_age.py        file_check.py 
           file_log.py       file_rxpipe.py        file_total.py          hb_cache.py 
             hb_log.py         hb_memory.py          hb_pulse.py         html_page.py 
           line_log.py         line_mode.py         msg_2http.py        msg_2local.py 
     msg_2localfile.py     msg_auditflow.py     msg_by_source.py       msg_by_user.py 
          msg_delay.py        msg_delete.py      msg_download.py          msg_dump.py 
         msg_fdelay.py msg_filter_wmo2msc.py  msg_from_cluster.py     msg_hour_tree.py 
            msg_log.py     msg_print_lag.py   msg_rename4jicc.py    msg_rename_dmf.py 
  msg_rename_whatfn.py       msg_renamer.py msg_replace_new_dir.py          msg_save.py 
       msg_skip_old.py        msg_speedo.py msg_sundew_pxroute.py    msg_test_retry.py 
    msg_to_clusters.py         msg_total.py        part_check.py  part_clamav_scan.py 
         poll_pulse.py       poll_script.py    post_hour_tree.py          post_log.py 
     post_long_flow.py     post_override.py   post_rate_limit.py        post_total.py 
          watch_log.py 
  configuration examples: ( /usr/lib/python3/dist-packages/sarra/examples/subscribe ) 
              all.conf     all_but_cap.conf            amis.conf            aqhi.conf 
              cap.conf      cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf 
         citypage.conf           clean.conf       clean_f90.conf            cmml.conf 
  cscn22_bulletins.conf         ftp_f70.conf            gdps.conf         ninjo-a.conf 
            q_f71.conf           radar.conf            rdps.conf            swob.conf 
            t_f30.conf      u_sftp_f60.conf 
  
  user plugins: ( /home/peter/.config/sarra/plugins ) 
          destfn_am.py         destfn_nz.py       msg_tarpush.py 
  
  general: ( /home/peter/.config/sarra ) 
            admin.conf     credentials.conf         default.conf
  
  user configurations: ( /home/peter/.config/sarra/subscribe )
       cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf 
          ftp_f70.conf           q_f71.conf           t_f30.conf      u_sftp_f60.conf 
  
  blacklab% 

Chaque section de la liste montre le contenu du répertoire entre parenthèses.  
il suffit d'éditer les fichiers dans les répertoires directement, ou de les modifier 
autrement, car la commande list existe seulement pour des raisons de commodité.  Il y a quatre sections:

 * plugins système : routines python que l'on peut appeler à partir de la configuration de l'abonné.
 * plugins utilisateur : routines python écrites par l'utilisateur du même type.
 * général : fichiers de configuration qui sont référencés par d'autres fichiers de configuration.
 * configurations utilisateur : ce sont celles définies par l'utilisateur et le plus souvent d'intérêt.

Pour visualiser une configuration particulière, donnez à sr_subscribe la liste des fichiers en argument:: 


    blacklab% sr_subscribe list msg_log.py

.. code:: python

    #!/usr/bin/python3

    """
      the default on_msg handler for sr_log.
      prints a simple notice.
    
    """

    class Msg_Log(object):

        def __init__(self,parent):
            parent.logger.debug("msg_log initialized")

        def on_message(self,parent):
            msg = parent.msg
            parent.logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % \
               tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
            return True


    msg_log = Msg_Log(self) # required: Make instance of class whose name is lower case version of class.

    self.on_message = msg_log.on_message  # assign self.on_message to corresponding function.

    blacklab%


Un premier exemple
-------------------

L'arbre décrit ci-dessus est l'arbre *conventionnel* que l'on trouve sur la plupart des 
pompes de données, mais la pompe de données originale, dd.weather.gc.ca, est antérieure 
à la convention.  Indépendamment de l'arbre, on peut le parcourir pour trouver les 
données d'intérêt. Sur dd.weather.gc.ca, on peut naviguer jusqu'à http://dd.weather.gc.ca/observations/swob-ml/
pour trouver l'arbre de toutes les observations météorologiques au format SWOB
publié récemment par n'importe quel bureau de prévision d'Environnement Canada.

Initialisez d'abord le fichier de stockage des informations d'identification::

  blacklab% sr_subscribe edit credentials.conf

  amqp://anonymous:anonymous@dd.weather.gc.ca

La commande *edit* appelle simplement l'éditeur configuré de l'utilisateur.
sur le fichier à créer au bon endroit.  Pour créer
une configuration pour obtenir les fichiers swob::

  blacklab% sr_subscribe edit swob.conf

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  accept .*

  blacklab% 
  blacklab% sr_subscribe status swob
  2017-12-14 06:54:54,010 [INFO] sr_subscribe swob 0001 is stopped
  blacklab% 


NOTE :

  Ce qui précède écrira les fichiers dans le répertoire de travail courant, et ils 
  arriveront rapidement. Il peut être plus avantageux de créer un répertoire dédié 
  et d'utiliser l'option *directory* pour y placer les fichiers.  par exemple :
  mkdir /tmp/swob_downloads_downloads
  *directory /tmp/swob_downloads* 

Sur la première ligne, *broker* indique l'endroit où se connecter pour obtenir le service
de notifications. Le terme *broker* est tiré de l'AMQP (http://www.amqp.org),
qui est le protocole utilisé pour transférer les notifications.
Les notifications qui seront reçues ont toutes des thèmes ( *topic* ) qui correspondent 
au chameni relatif du fichier annoncé.

Démarrez maintenant un abonné (supposons que le fichier de configuration s'appelait dd_swob.conf)::

  blacklab% sr_subscribe start dd_swob
  2015-12-03 06:53:35,268 [INFO] user_config = 0 ../dd_swob.conf
  2015-12-03 06:53:35,269 [INFO] instances 1 
  2015-12-03 06:53:35,270 [INFO] sr subscribe dd swob 0001 started

on peut surveiller l'activité avec la commande *log*::


  blacklab% sr_subscribe log dd_swob
  
  2015-12-03 06:53:35,635 [INFO] Binding queue q_anonymous.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqp://anonymous@dd.weather.gc.ca/
  2015-12-03 17:32:01,834 [INFO] user_config = 1 ../dd_swob.conf
  2015-12-03 17:32:01,835 [INFO] sr_subscribe start
  2015-12-03 17:32:01,835 [INFO] sr_subscribe run
  2015-12-03 17:32:01,835 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2015-12-03 17:32:01,835 [INFO] AMQP  input :    exchange(xpublic) topic(v02.post.observations.swob-ml.#)
  2015-12-03 17:32:01,835 [INFO] AMQP  output:    exchange(xs_anonymous) topic(v02.report.#)
  
  2015-12-03 17:32:08,191 [INFO] Binding queue q_anonymous.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqp://anonymous@dd.weather.gc.ca/
  blacklab% 
  
Le sr_subscribe obtiendra la notification et téléchargera le fichier dans le répertoire
répertoire de travail actuel. Comme le démarrage est normale, cela signifie que l'option
l'information d'authentification était bonne.  Les mots de passe sont stockés dans le répertoire
le fichier ~/.config/sarra/credentials.conf.  Le format n'est qu'un url complet sur chaque ligne. 
L'exemple ci-dessus serait::
  
  amqp://anonymous:anonymous@dd.weather.gc.ca/

Le mot de passe est situé après le :, et avant le @ dans l'URL comme c'est la norme.
la pratique. Ce fichier credentials.conf doit être privé (permissions octales linux : 0600).
De même, si un fichier.conf est placé dans le répertoire ~/.config/sarra/subscribe, alors
sr_subscribe le trouvera sans avoir à donner le chemin complet.

Un téléchargement normal ressemble à ceci:: 

  2015-12-03 17:32:15,031 [INFO] Received topic   v02.post.observations.swob-ml.20151203.CMED
  2015-12-03 17:32:15,031 [INFO] Received notice  20151203223214.699 http://dd2.weather.gc.ca/ \
         observations/swob-ml/20151203/CMED/2015-12-03-2200-CMED-AUTO-swob.xml
  2015-12-03 17:32:15,031 [INFO] Received headers {'filename': '2015-12-03-2200-CMED-AUTO-swob.xml', 'parts': '1,3738,1,0,0', \
        'sum': 'd,157a9e98406e38a8252eaadf68c0ed60', 'source': 'metpx', 'to_clusters': 'DD,DDI.CMC,DDI.ED M', 'from_cluster': 'DD'}
  2015-12-03 17:32:15,031 [INFO] downloading/copying into ./2015-12-03-2200-CMED-AUTO-swob.xml 

Donnant toutes les informations contenues dans la notification.  Voici un échec::

  2015-12-03 17:32:30,715 [INFO] Downloads: http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml  into ./2015-12-03-2200-CXFB-AUTO-swob.xml 0-6791
  2015-12-03 17:32:30,786 [ERROR] Download failed http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml
  2015-12-03 17:32:30,787 [ERROR] Server couldn't fulfill the request. Error code: 404, Not Found

Notez que ce message n'est pas toujours un échec, car sr_subscribe retries
quelques fois avant d'abandonner. Quoi qu'il en soit, après quelques minutes, 
voici ce qui suit le répertoire courant ressemble à::

  blacklab% ls -al | tail
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
  blacklab% 


Ressources côté serveur allouées aux abonnés
--------------------------------------------

Chaque configuration a pour résultat que les ressources correspondantes sont déclarées sur le broker.
Quand on change les paramètres *subtopic* ou *queue*, ou quand on s'attend à ne pas utiliser
une configuration pour une période de temps prolongée, il est préférable de faire::

  sr_subscribe cleanup swob.conf

qui dé-alloue la file d'attente (et ses liaisons) sur le serveur.  Pourquoi ? Chaque fois qu'un 
abonné est démarré, une file d'attente est créée sur la pompe de données.  Les liens de 
thème définis par le fichier de configuration. Si l'abonné est arrêté, la file d'attente 
continue à recevoir des messages tels que définis par la sélection de sous-thèmes, et lorsque 
la commande de l'abonné repart, les messages en file d'attente sont transmis au client.

Ainsi, lorsque l'option *subtopic* est modifiée, puisqu'elle est déjà définie dans le fichier
on finit par ajouter une liaison plutôt que de la remplacer.  Par exemple,
si l'on a un sous-thème ( *subtopic* ) qui contient SATELLITE, puis arrête l'abonné,
éditer le fichier et maintenant le thème ( *topic* ) ne contient plus que RADAR, lorsque l'abonné est
non seulement tous les fichiers satellites en file d'attente seront envoyés au consommateur,
mais le RADAR est ajouté aux fixations, plutôt que de les remplacer.
l'abonné obtiendra les données SATELLITE et RADAR, même si la configuration
ne contient plus le premier.

Aussi, si l'on expérimente et qu'une file d'attente doit être arrêtée pour une très longue durée
Dans le temps, il peut accumuler un grand nombre de messages. Le nombre total de messages
sur une pompe de données a un effet sur les performances de la pompe pour tous les utilisateurs. Il est donc
Il est conseillé de demander à la pompe de décharger les ressources lorsqu'elles ne seront pas nécessaires.
pendant des périodes prolongées, ou lors d'expériences avec différents réglages.


