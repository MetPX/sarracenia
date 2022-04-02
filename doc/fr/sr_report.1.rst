
=========
SR_Report 
=========

---------------------------------
traiter les rapport de télémétrie
---------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite

.. contents::

SYNOPSIS
========

 **sr_report** foreground|start|stop|restart|reload|status configfile

 **sr_report** cleanup|declare|setup configfile


DESCRIPTION
===========

sr_report est un programme pour traiter efficacement les rapports de transferts de fichiers 
à partir de Sarracenia. Le format des rapports est indiqué dans le *man page* `sr_report(7) <sr_report.7.rst>`_
Lorsque les clients téléchargent un message à partir d'un site de Sarracenia, ils publient 
un message d´information sur leur succès à le faire.

La commande **sr_report** prend deux arguments : un fichier de configuration décrit ci-dessous,
suivi d'une action, l'une des actions suivantes : start|stop|restart|reload|reload|status ou foreground..... (auto-décrit).
sr_report est sr_subscribe avec les paramètres suivants modifiés: :

  no_download On
  topic-prefix v02.report
  cache       off
  accept_unmatch On
  report off

L'action **foreground** est différente. Il est utilisé lors de la construction d'une configuration.
ou déboguer des choses, quand l'utilisateur veut exécuter le programme et son fichier de configuration.
interactivement... L'instance **foreground** n'est pas concernée par d'autres actions, mais 
si les instances configurées sont en cours d'exécution, il partage la même file d'attente 
de messages (configurée). 

Les actions **cleanup**, **declare**, **setup**, **setup** peuvent être utilisées pour gérer les ressources sur
le serveur rabbitmq. Les ressources sont soit des files d'attente, soit des échanges. **declare** crée
les ressources. **setup** crée et fait en plus les liaisons des files d'attente.


CONFIGURATION
=============

En général, les options de cette composante sont décrites dans le manuel de l
`sr_subscribe(1) <sr_sr_subscribe.1.rst>`_ page qui doit être lue en premier.
Il explique en détail la langue de configuration de l'option, et comment trouver
les paramètres de l'option.


EXEMPLES
--------

Voici un court exemple complet de fichier de configuration:: 

  broker amqps://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

Celui-ci se connectera au courtier dd.weather.gc.ca, en tant que
anonymous avec mot de passe anonymous (par défaut) pour obtenir des annonces à propos de
dans le répertoire http://dd.weather.gc.ca/model_gem_global/25km/grib2.
Tous les rapports de téléchargements de ces fichiers présents sur la pompe sera
accepté pour traitement par sr_report.




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




