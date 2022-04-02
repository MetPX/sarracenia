
==============
 SR_Shovel 
==============

----------------------------------------------
Copier de avis (pas les fichiers) entre pompes 
----------------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite

.. contents::


SYNOPSIS
========

 **sr_shovel** foreground|start|stop|restart|reload|status configfile

 **sr_shovel** cleanup|declare|setup configfile

DESCRIPTION
===========

sr_shovel copie les messages sur un courtier (donné par l'option *broker*) pour
une autre (donnée par l'option *post_broker*) soumise au filtrage.
par (*exchange*, *subtopic*, et optionnellement, *accept*/*reject*).

L'option *topic_prefix* doit être définie sur :

 **v02.post** pour pelleter des avis `sr_post(7) <sr_post.7.rst>`_ 
 **v02.log** to shovel des rapports `sr_report(7) <sr_report.7.rst>`_ 

Il n'y a pas de défaut.  Au démarrage, le composant sr_shovel prend deux éléments
argument :
une action start|stop|restart|reload|reload|status..... (auto-explicatif.) et
un fichier de configuration décrit ci-dessous.

Les actions **cleanup**, **declare**, **setup**, **setup** peuvent être utilisées pour gérer les ressources sur
le serveur rabbitmq. Les ressources sont soit des files d'attente, soit des échanges. **Declare** crée
les ressources. **setup** crée et fait en plus les liaisons des files d'attente.

sr_shovel est un sr_subscribe avec les presets suivants::
  
   no-download True
   suppress_duplicates off



CONFIGURATION
=============

En général, les options de cette composante sont décrites dans le manuel de l
`sr_subscribe(1) <sr_sr_subscribe.1.rst>`_ page qui doit être lue en premier.
Il explique en détail la langue de configuration de l'option, et comment trouver
les paramètres de l'option.



OPTIONS DE PUBLICATION
======================

Il n'y a pas d'option requise pour l'affichage des messages.
Par défaut, le programme publie le message consommé sélectionné avec son échange.
sur le cluster courant, avec le compte feeder.

L'utilisateur peut écraser les valeurs par défaut avec les options :

- **post_broker    amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>**
- **post_exchange   <name>        (défaut: aucun)**
- **post_exchangeSplit <number> (défaut: 0)**
- **on_post         <script_name> (optionelle)**


L'option post_broker définit les informations d'authentification pour se connecter à l'application
sortie **RabbitMQ** serveur. La valeur par défaut est la valeur de l'option **feeder**.
dans default.conf.

L'option **post_exchange** définit un nouvel échange pour les messages sélectionnés.
Le défaut est de publier sous l'échange qu'il a été consommé.

Le **post_exchangeSplit** est documenté dans sr_subscribe.

Avant la publication d'un message, un utilisateur peut définir le déclenchement d'un script.
L'option **on_post** serait utilisée pour faire une telle configuration.
Le message n'est publié que si le script renvoie True.

QUEUE Save/Restore
==================

Si une file d'attente s'accumule sur un courtier parce qu'un abonné n'est pas en mesure de traiter 
ses messages, la performance globale du courtier en souffrira, alors laisses des files d'attente traîner
est un problème. En tant qu'administrateur, on pourrait conserver une configuration comme celle-ci
autour de::

  % more ~/tools/save.conf
  broker amqp://tfeed@localhost/
  topic_prefix v02.post
  exchange xpublic

  post_rate_limit 50
  on_post post_rate_limit
  post_broker amqp://tfeed@localhost/

La configuration repose sur l'utilisation d'un compte d'administrateur ou d'alimentation.
notez la file d'attente qui contient des messages, dans ce cas q_tsub.sr_subscribe.t.99524171.43129428.  
Invoquer la pelle en mode de sauvegarde des messages des consommateurs de la file d'attente.
et les sauvegarder sur disque::

  % cd ~/tools
  % sr_shovel -save -queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf


  2017-03-18 13:07:27,786 [INFO] sr_shovel start
  2017-03-18 13:07:27,786 [INFO] sr_sarra run
  2017-03-18 13:07:27,786 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:07:27,788 [WARNING] non standard queue name q_tsub.sr_subscribe.t.99524171.43129428
  2017-03-18 13:07:27,788 [INFO] Binding queue q_tsub.sr_subscribe.t.99524171.43129428 with key v02.post.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:07:27,790 [INFO] report to tfeed@localhost, exchange: xreport
  2017-03-18 13:07:27,792 [INFO] sr_shovel saving to /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save for future restore
  2017-03-18 13:07:27,794 [INFO] sr_shovel saving 1 message topic: v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:07:27,795 [INFO] sr_shovel saving 2 message topic: v02.post.hydrometric.doc.hydrometric_StationList.csv
          .
          .
          .
  2017-03-18 13:07:27,901 [INFO] sr_shovel saving 188 message topic: v02.post.hydrometric.csv.ON.hourly.ON_hourly_hydrometric.csv
  2017-03-18 13:07:27,902 [INFO] sr_shovel saving 189 message topic: v02.post.hydrometric.csv.BC.hourly.BC_hourly_hydrometric.csv

  ^C2017-03-18 13:11:27,261 [INFO] signal stop
  2017-03-18 13:11:27,261 [INFO] sr_shovel stop

  % wc -l /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  189 /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  % 


Les messages sont écrits dans un fichier dans le répertoire de mise en cache pour 
une utilisation future, avec les éléments suivants: le nom du fichier étant basé sur le nom 
de configuration utilisé. le fichier est dans le répertoire format json, un message par 
ligne (les lignes sont très longues) et donc filtrage avec d'autres outils.
permet de modifier la liste des messages enregistrés.  Notez qu'un seul fichier de sauvegarde par fichier
la configuration est automatiquement définie, de sorte que pour sauvegarder plusieurs 
files d'attente, il faudrait une configuration par file d'attente à enregistrer. Une fois 
que l'abonné est de nouveau en service, on peut renvoyer les messages.
enregistré dans un fichier dans la même file d'attente::



  % sr_shovel -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf

  2017-03-18 13:15:33,610 [INFO] sr_shovel start
  2017-03-18 13:15:33,611 [INFO] sr_sarra run
  2017-03-18 13:15:33,611 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:15:33,613 [INFO] Binding queue q_tfeed.sr_shovel.save with key v02.post.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:15:33,615 [INFO] report to tfeed@localhost, exchange: xreport
  2017-03-18 13:15:33,618 [INFO] sr_shovel restoring 189 messages from save /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 
  2017-03-18 13:15:33,620 [INFO] sr_shovel restoring message 1 of 189: topic: v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:15:33,620 [INFO] msg_log received: 20170318165818.878 http://localhost:8000/ observations/swob-ml/20170318/CPSL/2017-03-18-1600-CPSL-AUTO-swob.xml topic=v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml lag=1034.74 sundew_extension=DMS:WXO_RENAMED_SWOB:MSC:XML::20170318165818 source=metpx mtime=20170318165818.878 sum=d,66f7249bd5cd68b89a5ad480f4ea1196 to_clusters=DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM parts=1,5354,1,0,0 toolong=1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß from_cluster=DD atime=20170318165818.878 filename=2017-03-18-1600-CPSL-AUTO-swob.xml 
     .
     .
     .
  2017-03-18 13:15:33,825 [INFO] post_log notice=20170318165832.323 http://localhost:8000/hydrometric/csv/BC/hourly/BC_hourly_hydrometric.csv headers={'sundew_extension': 'BC:HYDRO:CSV:DEV::20170318165829', 'toolong': '1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß', 'filename': 'BC_hourly_hydrometric.csv', 'to_clusters': 'DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM', 'sum': 'd,a22b2df5e316646031008654b29c4ac3', 'parts': '1,12270407,1,0,0', 'source': 'metpx', 'from_cluster': 'DD', 'atime': '20170318165832.323', 'mtime': '20170318165832.323'}
  2017-03-18 13:15:33,826 [INFO] sr_shovel restore complete deleting save file: /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 


  2017-03-18 13:19:26,991 [INFO] signal stop
  2017-03-18 13:19:26,991 [INFO] sr_shovel stop
  % 

Tous les messages enregistrés sont renvoyés au *return_to_queue* nommé. Notez que l'utilisation 
de la limite *post_rate_limit* qui empêche la file d'attente d'être inondée de centaines de 
messages par seconde. La limite de taux d'utilisation aura besoin de d'être accordé dans la pratique.

par défaut, le nom du fichier de sauvegarde est choisi dans ~/.cache/sarra/shovel/<config>_<instance>.save.
Pour choisir une destination différente, l'option *save_file* est disponible::

  sr_shovel -save_file `pwd`/here -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 ./save.conf foreground

créera les fichiers de sauvegarde dans le répertoire courant nommé here_000x.save où x est le 
numéro d'instance (0 pour le premier plan).


AUSSI VOIR
==========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés.

`sr_shovel(8) <sr_shovel.8.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(8) <sr_winnow.8.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - messages de rapport de processus.

`sr_post(1) <sr_post.1.rst>`_ - publier les avis de fichiers.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Outil pour S´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.





