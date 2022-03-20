
=========
 SR_Sarra
=========

---------------------------------------------------------
Selectionner, acquérir et renvoyer récursivement a autrui
---------------------------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite

.. contents::


SYNOPSIS
========

**sr_sarra** foreground|start|stop|restart|reload|status configfile

**sr_sarra** cleanup|declare|setup configfile


DESCRIPTION
===========


**sr_sarra** est un programme qui s'abonne aux notifications de fichiers,
Acquiert les fichiers et les annonce à leurs nouveaux emplacements.
Le protocole de notification est défini ici `sr_post(7) <sr_post.7.rst>`_

**sr_sarra** se connecte à un *broker* (souvent le même que le serveur de fichiers distant)
) et s´abonne aux notifications d'intérêt. Il utilise l'avis des informations 
pour télécharger les fichier au serveur local.  Il envoie ensuite un avis pour les 
fichiers téléchargés sur un courtier (généralement aussi sur le serveur local).

**sr_sarra** peut être utilisé pour acquérir des fichiers à partir de `sr_post(1) <sr_post.1.rst>`_
ou `sr_watch(1) <sr_watch.1.rst>`_ ou pour réproduire un dossier accessible sur le Web (WAF),
qui annoncent ses produits.

Le **sr_sarra** est un `sr_subscribe(1) <sr_subscribe.1.rst>`_ avec les presets suivants::

   mirror True



Besoins spécifiques de consommation
-----------------------------------

Si les messages sont affichés directement à partir d'une source,
l'échange utilisé est'xs_<brokerSourceUsername>_<xxz>'.  Un tel message 
peut ne pas contenir une source ni une grappe d'origine, ou un utilisateur 
malveillant peut régler les valeurs incorrectement. Pour se protéger contre 
les paramètres malveillants, les administrateurs doit 
setté *sourceFromExchange* à **True**.

- **sourceFromExchange <booléen> (par défaut : False)**.

Lors de la réception, le programme réglera les valeurs suivantes
dans la classe mère (ici le cluster est la valeur de
option **cluster** extraite du fichier default.conf) :

self.msg.headers['source'] = <brokerUser>User>.
self.msg.headers['from_cluster'] = cluster

Ceux-ci prime sur les valeurs présentes dans le message.  Ce réglage
devrait toujours être utilisé lors de l'ingestion de données provenant d'une
échange d'un utilisateur.

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
