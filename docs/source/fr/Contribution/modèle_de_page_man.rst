==========
 SR3_TITRE
==========

--------
sr_titre
--------

:Manual section: 1 
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**sr_titre** foreground|start|stop|restart|reload|status configfile
**sr_titre** cleanup|declare|setup configfile

DESCRIPTION
===========

**sr_title** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do 
eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea 
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat 
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
est laborum. `sr_subscribe(7) <sr3.1.rst#subscribe>`_ 
avec des limitations.

 - ne télécharge pas de données, ne fait circuler que des messages de notification.
 - s’exécute en tant qu’instance unique (pas plusieurs instances).
 - ne supporte aucun plugin.
 - Ne prend pas en charge de VIP pour la haute disponibilité.
 - bibliothèque d’expressions régulières différente: POSIX vs python.
 - Ne prend pas en charge regex pour la commande strip (pas de regex non-greedy).


Il peut donc servir de remplaçant pour :

   `sr_report(1) <sr3.1.rst#report>`_ - Traiter les messages de notification de rapport.

   `sr_shovel(8) <sr3.1.rst#shovel>`_ - Traiter les messages de notification de shovel.

   `sr_winnow(8) <sr3.1.rst#winnow>`_ - Traiter les messages de notification de winnow.

La commande **sr_cpump** prend deux arguments : une action start|stop|restart|reload|status... (auto-décrit)
suivi d’un fichier de configuration.

L’action **foreground** est utilisée lors du débogage d’une configuration, lorsque l’utilisateur souhaite
exécutez le programme et son fichier de configuration de manière interactive...   L’instance **foreground**
n’est pas concerné par d’autres actions.  L’utilisateur cesserait d’utiliser l’instance **foreground**
en utilisant simplement <ctrl-c> sur Linux ou en utilisant d’autres moyens pour envoyer SIGINT ou SIGTERM au processus.


Les actions **cleanup**, **declare**, **setup** peuvent être utilisé pour gérer les ressources sur
le serveur RabbitMQ. Les resources sont des files d’attente ou des échanges. **declare** Crée
les ressources. **setup** crée et effectue en en plus les liaisons des files d’attente.

Les actions **add**, **remove**, **edit**, **list**, **enable**, **disable** agissent
sur des configurations.

CONFIGURATION
=============

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium 
doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore 
veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim
ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia
consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque
porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, 
adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore 
et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis 
nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid 
ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea
voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem
eum fugiat quo voluptas nulla pariatur?"




VARIABLES D'ENVIRONMENT
=======================

Si la variable SR_CONFIG_EXAMPLES est définie, la directive *add* peut être utilisée
pour copier des exemples dans le répertoire de l’utilisateur à des fins d’utilisation et/ou de personnalisation.

Une entrée dans le fichier ~/.config/sarra/default.conf (créée via sr_subscribe edit default.conf )
pourrait être utilisé pour définir la variable ::


  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/examples

La valeur doit être disponible à partir de la sortie d’une commande list de l’implémentation python.

VOIR AUSSI
==========

`sr3_report(7) <sr3.1.rst#report>`_ - Format des messages de rapport.

`sr3_report(1) <sr3.1.rst#report>`_ - Traiter les messages de rapport.

`sr3_post(1) <sr3_post.1.rst>`_ - Publier des messages de notification de fichiers spécifiques.

`sr3_post(7) <sr_post.7.rst>`_ - Format des messages de notification.

`sr3_subscribe(1) <sr3.1.rst#subscribe>`_ - le client de téléchargement.

`sr3_watch(1) <sr3.1.rst#watch>`_ - Le démon de surveillance du répertoire.
