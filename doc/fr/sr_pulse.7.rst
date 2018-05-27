
=========
sr_pulse
=========

--------------------------------------------------
Format/Protocol de message pulse de Sarracenia v02
--------------------------------------------------

:Date: @Date@
:Version: @Version@
:Manual section: 7
:Manual group: MetPX-Sarracenia


.. contents::


SYNOPSIS
========

**AMQP Topic: <version>.pulse.[tick|message]**

**Body:** *<message>*



DESCRIPTION
===========

Les messages Sr_pulse sont envoyés périodiquement (par défaut chaque minute) de 
sorte que les abonnés dont la fréquence de avis recus par abonnement est très faible.
maintiendront une connexion à travers les pare-feu. Les consommateurs peuvent vérifier 
chaque battement de coeur (10 minutes par défaut) s'ils ont reçu les pouls.  Si 
aucune impulsion n'a été reçue, le consommateur peut essayer une opération sur le 
canal pour confirmer la connexion avec le courtier.  S'il n'y a pas de connexion, 
les consommateurs doivent démonter et reconstruire la connexion.


AMQP TOPIC
==========

Le thème d'un message d'impulsion est préfixé par v02.pulse.  Le sous-sujet est 
l'un ou l'autre : *tick* pour un message keep-alive ordinaire,
ou *message* pour un message administrateur destiné à tous les abonnés.


THE BODY
========

Le corps du message dans un *tick* est l'horodatage standard (comme dans 
un `sr_post(7) <sr_post.7.rst>`_ message).

Format : *YYYYYYMMDDHHHMMHMMSS.(Remarque : l'horodatage est toujours dans le fuseau horaire UTC.*

Dans le cas d'un message avec la rubrique *v02.pulse.message*.  Le corps est 
un message à afficher dans les journaux de tous les abonnés.


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







