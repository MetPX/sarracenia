
==========
 SR_Winnow 
==========

-----------------------------
Supprimer des avis redondants
-----------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::

SYNOPSIS
========

**sr_winnow** foreground|start|stop|restart|reload|status configfile
**sr_winnow** cleanup|declare|setup configfile

DESCRIPTION
===========


sr_winnow** est un programme qui s'abonne aux notifications de fichiers,
et réenregistre les notifications, en supprimant les notifications redondantes en comparant leurs données
L'en-tête **sum** mémorise l'empreinte digitale d'un fichier comme décrit ci-dessus.
dans la page de manuel `sr_post(7) <sr_post.7.rst>`_ 

**sr_winnow** est un `sr_subscribe(1) <sr_subscribe.1.rst>`_ avec les options suivantes forcées::

   no-download True  
   suppress_duplicates on
   accept_unmatch True

La durée de vie des suppress_duplicates peut être ajustée, mais elle est toujours active.

**sr_winnow** se connecte à un *courtier* (souvent le même que le courtier d'affichage).
et souscrit aux notifications d'intérêt. Sur réception d´un avis, il cherche sa **sum** 
dans son cache. s'il est trouvé, le fichier est déjà passé, de sorte que la notification 
est ignorée. Si ce n'est pas le cas, le fichier est nouveau, et le **sum** est ajouté.
dans le cache et l'avis est affiché.

**sr_winnow** peut être utilisé pour couper les messages de `sr_post(1) <sr_post.1.rst>`_,
`sr_poll(1) <sr_poll.1.rst>`_ ou `sr_watch(1) <sr_watch.1.rst>`_ etc..... C'est
utilisé lorsqu'il y a plusieurs sources de données identiques, de sorte que les 
clients ne téléchargent que le fichier une seule fois, à partir de la première 
source qui les a publié.

La commande **sr_winnow** prend deux arguments : une action 
start|stop|stop|restart|reload|status..... (auto-descriptif?)
suivi d'un fichier de configuration décrit ci-dessous.

Le **foreground** est utilisé lors du débogage d'une configuration, lorsque 
l'utilisateur souhaite exécuter le programme et son fichier de configuration de 
manière interactive.

Les actions **cleanup**, **declare**, **setup**, **setup** peuvent être utilisées pour 
gérer les ressources sur le serveur rabbitmq. Les ressources sont soit des files 
d'attente, soit des échanges. **declare** crée les ressources. **setup** crée et 
fait en plus les liaisons des files d'attente. 

CONFIGURATION
=============

En général, les options de cette composante sont décrites dans le manuel de l
`sr_subscribe(1) <sr_subscribe.1.rst>`_ page qui doit être lue en premier.
Il explique en détail la langue de configuration de l'option, et comment trouver
les paramètres de l'option.



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








