
==========
 SR_CPUMP 
==========

-----------------
sr_shovel en C
-----------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::

SYNOPSIS
========

**sr_cpump** foreground|start|stop|restart|reload|status configfile
**sr_cpump** cleanup|declare|setup configfile

DESCRIPTION
===========

sr_cpump** est une implémentation alternative de `sr_subscribe(7) <sr_sr_subscribe.1.rst>`_ 
avec quelques limitations.

 - ne télécharge pas les données, mais ne fait que diffuser les messages.
 - fonctionne comme une seule instance (pas d'instances multiples).
 - ne supporte pas les plugins.
 - ne prend pas en charge vip pour une haute disponibilité.
 - différentes bibliothèques d'expressions régulières : POSIX vs. python.
 - ne supporte pas le regex pour la commande strip (pas de regex non-vorace).

Il peut donc agir comme un substitut facile pour:

 `sr_shovel(8) <sr_shovel.8.rst>`_ - copier des avis (pas les fichiers).

 `sr_winnow(8) <sr_winnow.8.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

 `sr_report(1) <sr_report.1.rst>`_ - consommateur de rapports.

L´implémention en C peut être plus facile à rendre disponible dans des environnements spécialisés,
comme le High Performance Computing, car il a beaucoup moins de dépendances que la version python.
Il utilise aussi beaucoup moins de mémoire pour un rôle donné. Normalement la version python
est recommandé, mais il y a des cas où l'utilisation de l'implémentation C est raisonnable.

**sr_cpump** se connecte à un *broker* (souvent le même que le courtier d'affichage).
et s´abonne aux notifications d'intérêt. Sur réception d´un avis, il cherche sa **sum** dans
son cache. s'il est trouvé, le fichier est déjà passé, de sorte que la notification 
est ignorée. Si ce n'est pas le cas, le fichier est nouveau, le **sum** est ajouté.
dans le cache et l'avis est affiché.

**sr_cpump** peut être utilisé, comme `sr_winnow(1) <sr_winnow.1.rst>`_, pour vanner 
les avis de `sr_post(1) <sr_post.1.rst>`_, `sr_poll(1) <sr_poll.1.html>`_, ou 
`sr_watch(1) <sr_watch.1.rst>`_ Il est utilisé lorsqu'il y a plusieurs sources
des mêmes données, de sorte que les clients ne téléchargent les données qu'une seule 
fois, à partir de la première source qui l'a publié.

La commande **sr_cpump** prend deux arguments : une action start|stop|restart|reload|reload|status
 (auto-décrit) suivi d'un fichier de configuration.  L'action **foreground** est utilisée lors du 
débogage d'une configuration, lorsque l'utilisateur souhaite exécuter le programme et son 
fichier de configuration de manière interactive.   L'instance **foreground** instance n'est 
pas concerné par d'autres actions. L'utilisateur peut terminer une session **foreground**
par <ctrl-c-c> simplement sur linux ou utiliser d'autres moyens pour envoyer SIGINT ou SIGTERM au processus.

Les actions **cleanup**, **declare**, **setup**, peuvent être utilisées pour gérer les ressources sur
le serveur rabbitmq. Les ressources sont soit des files d'attente, soit des échanges. **declare** crée
les ressources. **setup** crée et fait en plus les liaisons des files d'attente.

Les actions **add**, **remove**, **edit**, **list**, **enable**, **disable** agissent
sur les configurations pour les: ajouter, enlever, editer, lister, activer our désactiver.


CONFIGURATION
=============

En général, les options de cette composante sont décrites dans le manuel de l
`sr_subscribe(1) <sr_sr_subscribe.1.rst>`_ page qui doit être lue en premier.
Il explique en détail la langue de configuration de l'option, et comment trouver
les paramètres de l'option.

**NOTE** : La bibliothèque d'expressions régulières utilisée dans l'implémentation 
est la bibliothèque POSIX , et la grammaire est légèrement différente de 
l'implémentation python. Certains des ajustements peuvent être nécessaires.


VARIABLES D'ENVIRONNEMENT
=========================

Dans l'implémentation C (sr_cpost), si la variable SR_CONFIG_EXAMPLES est
définie, alors la directive *add* peut être utilisée pour copier des exemples
dans le répertoire de l'utilisateur à des fins d'utilisation et/ou de personnalisation.

Une entrée dans le fichier ~/.config/sarra/default.conf (créé via sr_subscribe
edit default.conf) pourrait être utilisé pour définir la variable::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/exemples

la valeur est disponible à partir de la sortie d'une commande *sr_post list*
( de la version en python. )


AUSSI VOIR
==========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés. (page principale de référence.)

`sr_shovel(8) <sr_shovel.8.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(8) <sr_winnow.8.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - traiter les rapport de télémétrie.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Outil pour s´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.





