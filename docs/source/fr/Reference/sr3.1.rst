=====
 SR3 
=====

------------------
sr3 Sarracenia CLI
------------------

:Manual section: 1 
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia


SYNOPSIS
========

**sr3** *options* *action* [ *composant/config* ... ]

DESCRIPTION
===========
Sr3 est un outil pour gérer une flotte de démons, ou les résultats/sortie du programme est principalement
dans les fichiers logs. Sr3 permet à l'utilisateur de commencer, arrêter, et se renseigner sur
le statut d'un flux de sarracenia déjà configuré. C'est le point d'entrée principal de la ligne de commande pour
Sarracenia 3 ( https://metpx.github.io/sarracenia/ )

Lorsque sr3 est démarré, l’intégralité des configurations sont lu et on peut faire une requête sur l’état
de tous les flux, avec *sr3 status* par exemple. Lorsque *composant/config* est utilisé, sr3 doit
fonctionner sur un sous-ensemble de toutes les configurations présentes.

* Si vous êtes déjà familier avec Sarracenia et que vous cherchez de l'information spécifique par rapport a des
  options ou des directives, il vaut mieux regarder `sr3 Options (7) <sr3_options.7.html>`_
* Pour commencer plus facilement, jetez un coup d’œil sur `the Subscriber Guide on GitHub <../How2Guides/subscriber.html>`_
* Pour un guide général de l’interface : voir le `Command Line Guide <../Explication/CommandLineGuide.html>`_

La ligne de commande a trois éléments importants:
* options
* action
* composant/config

Un flux est un groupe de processus qui roule en utilisant un composant/config commun.

OPTIONS
=======
La majorité des options son stockés dans des fichiers de configuration. Ceci est dénoté
par *compsant/config* indiqué par le nom du fichier, mais de temps en temps, on peut utiliser la ligne
de commande pour remplacer une valeur dans le fichier de configuration. Les options sont défini
`Sr3 Options (7) <sr3_options.7.html>`_ Reportez-vous à cette page de manuel pour une discussion complète.
Il y a une exception ::

   -h (or --help)


L'option d'aide est seulement disponible sur la ligne de commande. Elle est utilisée pour obtenir
une description d'une sélection d'options disponible pour remplacer les valeurs du fichier
de configuration.

ACTIONS
=======
Les types d'actions disponible. Une seule parmi:

 - add:           copier a la liste de configurations disponible.
 - cleanup:       supprimer les ressources des composants sur le serveur.
 - convert:       copie et mets à jour une configuration de v2 dans le répertoire sr3.
 - declare:       crée les ressources d'un composant sur le serveur.
 - disbale:       marquer une configuration comme non-éligible à exécuter.
 - edit:          modifier une configuration existante.
 - enable:        marquer une configuration comme éligible à exécuter.
 - foreground:    rouler une seule instance avec le mode foreground avec des logs sur stderr
 - liste:          lister toutes les configurations disponible.
 - liste plugins:  lister tout les plugins disponible.
 - list examples: lister tout les examples disponible.
 - remove:        supprimer une configuration.
 - run:           comme *start* mais on attend que les sous-processus reviennent.
 - restart:       arrêter et ensuite commencer une configuration.
 - sanity:        cherche des instances qui sont perdus/coincées/en panne et les redémarres.
 - show           afficher une version interprétée d’un fichier de configuration.
 - start:         partir l'execution d'une ensemble de configurations
 - status:        vérifier si une configuration est en train de rouler.
 - stop:          arrêter une configuration en cours d'exécution.



COMPOSANTS
==========

`The Flow Algorithme <../Explication/Concepts.html#the-flow-algorithm>`_ est ce qui est exécuté
par tout les processus de sr3. Le comportement de l'algorithme du flux est adaptable aves les options,
dont certaines contrôlent des modules optionnels (flowcallbacks). Chaque composant possède de
différents ensembles de paramètres d’options par défaut pour couvrir un cas d’utilisation courant.


* `cpump <../Explication/CommandLineGuide.html#cpump>`_ - copier un message d'annonce d'une pompe a une deuxième pompe (une implémentation C d'un shovel.)
* `flow <../Explication/CommandLineGuide.html#flow>`_ - flux générique, pas de valeurs par défaut, bonne base pour convenir à la construction personnalisée les flux
* `poll <../Explication/CommandLineGuide.html#poll>`_ - poller une page web non-sarracenia ou des fichiers sur un serveur pour créer des messages d'annonce pour un traitement.
* `post|sr3_post|sr_cpost|watch <../Explication/CommandLineGuide.html#post-or-watch>`_ - créer es messages d'annonce pour les fichiers qui doivent être traités.
* `sarra <../Explication/CommandLineGuide.html#sarra>`_ - télécharger un fichier d’un serveur distant vers un serveur local et les republier pour les autres.
* `sender <../Explication/CommandLineGuide.html#sender>`_ - envoyer des fichiers d’un serveur local à un serveur distant.
* `shovel <../Explication/CommandLineGuide.html#shovel>`_ - copier seulement des messages d'annonce et non des fichiers.
* `watch <../Explication/CommandLineGuide.html#watch>`_ - crée un message d'annonce pour chaque nouveau fichier qui arrive dans un répertoire.
* `winnow <../Explication/CommandLineGuide.html#winnow>`_ - copier des messages d'annonce et supprime les doublons.


CONFIGURATIONS
==============

Quand une paire de *composant/configuration* et spécifiée sur la ligne de commande,
la configuration se fait construire a partir de:

 1. default.conf

 2. admin.conf

 3. <component>.conf (subscribe.conf, audit.conf, etc...)

 4. <component>/<config>.conf

Les paramètres d'un fichier .conf sont lu après le fichier default.conf,
et les valeurs initiales choisi par défaut peuvent éventuellement être replacer.
Les options spécifiées sur la ligne de commande remplacent les options spécifiées dans le
fichier de configuration.

Les fichiers de configurations peuvent être gérer en utilisant les actions *add*, *remove*,
*list*, *edit*, *disable*, et *enable*. Il est également possible de faire
les mêmes activités manuellement en manipulant les fichiers dans le répertoire des paramètres.
Les fichiers de configuration pour une configuration de sr3 appelé *myflow*
se trouverait ici:

 - linux: ~/.config/sarra/subscribe/myflow.conf (selon: `XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.rst>`_ )

 - Windows: %AppDir%/science.gc.ca/sarra/myflow.conf , ca pourrait être:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\myflow.conf

 - MAC: FIXME.

A la base, le répertoires *~/.config/sarra/default.conf* contient des paramètres
qui sont lus par défaut pour tout composant au démarrage. Dans le même répertoire,
*~/.config/sarra/credentials.conf*, il y a les identifiants (mots de passe) qui doivent
être utilisé par sarracenia ( `CREDENTIALS <sr3_credentials.7.rst>`_ pour plus de détails ).

Il est également possible de définir la valeur de la variable XDG_CONFIG_HOME pour remplacer
le répertoire de base, ou sinon un fichier de configuration peut être placé dans n'importe quel
répertoire est peut être invoqué en utilisant le chemin du fichier au complet.
Quand un composant est invoqué, le fichier fourni est interprété en tant que chemin de fichier
(il est assumé que l'extension .conf est employé.) Si le chemin du fichier est introuvable,
le composant va regarder dans le répertoire de configuration du composant
( **repertoire_config** / **composant** ) pour un fichier .conf correspondant.

Si il est toujours introuvable, il le recherchera dans le répertoire de configuration du site
(linux : /usr/share/default/sarra/**composant**).

Finalement, si l’utilisateur a défini l’option **remote_config** a True et si il y a des
sites Web configurés où les configurations peuvent être trouvées (option **remote_config_url**),
le programme essaiera de télécharger le fichier à partir de chaque site jusqu’à ce qu’il en trouve un.


En cas de succès, le fichier est téléchargé sur **repertoire_config/Téléchargements** et interprété
par le programme à partir de là.  Il existe un processus similaire pour tous les *plugins* qui peuvent
être interprétés et exécutés dans les composants de sarracenia.  Les composants vont d’abord
regarder dans le répertoire *plugins* dans l’arborescence de configuration des utilisateurs, puis dans le site,
ensuite dans le paquet sarracenia lui-même, et enfin il regardera à distance.


Configurations a Distance
-------------------------

Il est possible de spécifier des URI en tant que fichiers de configuration, plutôt que des fichiers locaux. Exemple:

  - **--config http://dd.weather.gc.ca/alerts/doc/cap.conf**

Au démarrage, sr3 vérifie si le fichier local cap.conf existe dans le
répertoire de configuration local.  Si c’est le cas, le fichier sera lu pour trouver
une ligne comme celle-ci :

  - **--remote_config_url http://dd.weather.gc.ca/alerts/doc/cap.conf**

Dans ce cas, il vérifiera l’URL distant et comparera le temps de modification
du fichier distant par rapport au fichier local. Si le fichier distant n’est pas plus récent ou ne peut pas
être atteint, le composant continuera avec le fichier local.

Si le fichier distant est plus récent ou s’il n’y a pas de fichier local, le fichier distant sera téléchargé,
et la ligne remote_config_url sera rajouté, de sorte qu’elle continuera
de se mettre à jour automatiquement à l’avenir.


Logs
----

Pour les fichiers de logs, il faut regarder dans ~/.cache/sr3/logs (pour linux. Cela va varier sur d'autres
plateformes.) Pour les trouver sur n'importe quel plateforme::

    fractal% sr3 list
    User Configurations: (from: /home/peter/.config/sr3 )
    admin.conf                       credentials.conf                 default.conf
    logs are in: /home/peter/.cache/sr3/log

La dernière ligne indique le répertoire.



EXEMPLES
========

Voici un exemple complet de fichier de configuration::

  broker amqps://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

Ce fichier se connectera au broker dd.weather.gc.ca en tant qu'anonyme avec mot de passe
anonyme (par défaut) pour obtenir des annonces à propos des fichiers dans le répertoire
http://dd.weather.gc.ca/model_gem_global/25km/grib2.
Tous les fichiers qui arrivent dans ce répertoire ou en dessous seront téléchargés
dans le répertoire courant (ou simplement imprimé en sortie standard si l'option -n
a été spécifié.)

Divers exemples de fichiers de configuration sont disponibles ici :

 `https://github.com/MetPX/sarracenia/tree/main/sarra/examples <https://github.com/MetPX/sarracenia/tree/main/sarra/examples>`_



VOIR AUSSI
==========


**Commande de l'utilisateur:**

`sr3_post(1) <sr3_post.1.html>`_ - poste des annoncements de fichiers (implémentation en Python.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - poste des annoncements de fichiers (implémentation en C.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - copie les messages d'annonce ( implémentation en C du composant shovel. )

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - Convertir les lignes du fichier log au format .save pour le rechargement/le renvoi.

`sr3_options(7) <sr3_options.7.html>`_ -  Convertir les lignes du fichier log au format .save pour le rechargement/le renvoi.

`sr3_post(7) <sr3_post.7.html>`_ - Format des messages d’annonce.

**Page d'acceuil:**


`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia : une boîte à outils de gestion du partage de données pub/sub en temps réel
