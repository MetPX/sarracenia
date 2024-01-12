==========
 SR_CPUMP 
==========

-----------------
sr_shovel en C
-----------------

:Manual section: 1 
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**sr_cpump** foreground|start|stop|restart|reload|status configfile
**sr_cpump** cleanup|declare configfile

DESCRIPTION
===========

**sr_cpump** est une implémentation alternative du composant *shovel* de `sr3(1) <sr3.1.html>`_
avec quelques limites.

  - ne télécharge pas de données, ne fait que diffuser des publications.
  - fonctionne comme une seule instance (pas d'instances multiples).
  - ne supporte aucun plugin.
  - ne prend pas en charge vip pour une haute disponibilité.
  - différentes bibliothèques d'expressions régulières : POSIX vs python.
  - ne prend pas en charge les regex pour la commande strip (pas de regex non gourmand).

Il peut donc agir comme un remplacement direct pour :

    `sr3 shovel <sr3.1.rst>`_ - traite les messages shovel.

    `sr3 winnow <sr3.1.rst>`_ - traite les messages winnow.

L'implémentation C peut être plus facile à mettre à disposition dans des environnements spécialisés,
comme le calcul haute performance, car il a beaucoup moins de dépendances que la version python.
Il utilise également beaucoup moins de mémoire pour un rôle donné. Normalement la version python
est recommandé, mais il y a des cas où l'utilisation de l'implémentation C est judicieuse.

**sr_cpump** se connecte à un *courtier* (broker) (souvent le même que le courtier de publication)
et s'abonne aux notifications d'intérêt. A la réception d'une annonce,
il recherche sa **sum** dans son cache. S'il est trouvé, le fichier est déjà arrivé,
la notification est donc ignorée. Si ce n'est pas le cas, le fichier est nouveau et la **sum** est ajoutée
dans le cache et la notification est publiée.

**sr_cpump** peut être utilisé, comme `sr3 winnow(1) <sr3.1.rst>`_, pour couper les messages
de `sr3_post(1) <sr3_post.1.rst>`_, `sr3 poll(1) <sr3.1.rst>`_
ou `sr3 watch (1) <sr3.1.rst>`_ etc... Il est utilisé lorsqu'il y a plusieurs
sources des mêmes données, de sorte que les clients ne téléchargent les données source qu'une seule fois à partir de
la première source qui l'a posté.

La commande **sr3_cpump** prend deux arguments: une action start|stop|restart|reload|status... (autodécrit)
suivi d'un fichier de configuration.

L'action **foreground** est utilisée lors du débogage d'une configuration, lorsque l'utilisateur veut
exécuter le programme et son fichier de configuration de manière interactive... L'instance **foreground**
n'est pas concerné par d'autres actions. L'utilisateur cesserait d'utiliser l'instance **foreground**
en simplement <ctrl-c> sous linux ou utilisez d'autres moyens pour envoyer SIGINT ou SIGTERM au processus.

Les actions **cleanup**, **declare**, peuvent être utilisées pour gérer les ressources sur
le serveur rabbitmq. Les ressources sont soit des files d'attente, soit des échanges. **déclarer** crée
les ressources. 

Les actions **ajouter**, **supprimer**, **modifier**, **lister**, **activer**, **désactiver** agissent
sur les configurations.

CONFIGURATION
=============

En général, les options de ce composant sont décrites par
la page `sr3_options(7) <sr3_options.7.html>`_ qui doit être lue en premier.
Elle explique en détail la langue de configuration des options et comment trouver
les paramètres des options.

**REMARQUE**: La bibliothèque d'expressions régulières utilisée dans l'implémentation C est celle POSIX
et la grammaire est légèrement différente de l'implémentation de python. Quelques
ajustements peuvent être nécessaires.

VARIABLES ENVIRONNEMENTALES
===========================

Si la variable SR_CONFIG_EXAMPLES est définie, la directive *add* peut être utilisée
pour copier des exemples dans le répertoire de l'utilisateur à des fins d'utilisation et/ou de personnalisation.

Une entrée dans ~/.config/sarra/default.conf (créé via sr_subscribe edit default.conf )
pourrait être utilisé pour définir la variable::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/examples

La valeur doit être disponible à partir de la sortie d'une commande de liste à partir de
l'implémentation python.


VOIR AUSSI
==========


**User Commands:**

`sr3(1) <sr3.1.html>`_ - Interface de ligne de commande principale de Sarracenia.

`sr3_post(1) <sr3_post.1.rst>`_ - publication des annonces de fichiers (implémentation Python.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - publication des annonces de fichiers (implémentation C.)

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - le format des informations d'authentification. 

`sr3_options(7) <sr3_options.7.html>`_ - liste de toute les options dans la langue de configuration.

`sr3_post(7) <sr3_post.7.rst>`_ - le format des annonces

**Page d'acceuil:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: une boîte à outils de gestion du partage de données pub/sub en temps réel

                                     
