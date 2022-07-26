
==================================
 Guide de programmation Sarracenia
==================================

---------------------------
Travailler avec des plugins
---------------------------

Enregistrement de révision
--------------------------

:version: |release|
:date: |today|

Audience
--------

Les lecteurs de ce manuel doivent être à l’aise avec les scripts légers dans Python version 3.
Alors qu’une grande partie de la compatibilité v2 est incluse dans Sarracenia version 3,
le remplacement des interfaces de programmation est une grande partie de ce qui se trouve dans la version 3.
S’ils travaillent avec la version 2, les programmeurs doivent se référer au Guide du programmeur de la version 2,
car le contenu ici est très différent.

Introduction
------------
Sarracenia v3 comprend un certain nombre de points où le traitement peut être personnalisé par
de petits extraits de code fourni par l’utilisateur, appelés flowCallbacks. Les flowCallbacks eux-mêmes
sont censés être concis, et une connaissance élémentaire de Python devrait suffire à
en construire de nouveaux de manière copier/coller, avec de nombreux exemples disponibles à la lecture.



Il existe d’autres façons d’étendre Sarracenia v3 en sous-classant :

* Sarracenia.Transfer pour ajouter plus de protocoles de transfert de données
* Sarracenia.integrity pour ajouter plus de méthodes de somme de contrôle.
* Sarracenia.moth pour ajouter la prise en charge de plus de protocoles de messagerie.
* Sarracenia.flow pour créer de nouveaux flux.
* Sarracenia.flowcb pour personnaliser les flux.
* Sarracenia.flowcb.poll pour personnaliser les flux de sondage.

Cela sera discuté après que les rappels auront été traités.

Il y a une courte démonstration interactive de tous ces sujets dans
`Jupyter Notebooks <../../jupyter>`_ inclus avec Sarracenia.

Introduction
------------

Une pompe de données Sarracenia est un serveur Web avec des notifications pour les abonnés à
savoir, rapidement, quand de nouvelles données sont arrivées. Pour savoir quelles données sont déjà
disponible sur une pompe, visualisez l’arbre avec un navigateur web.  Pour de besoins simple et immédiats,
on peut télécharger des données en utilisant le navigateur lui-même ou via un outil standard
comme wget. L’intention habituelle est que sr_subscribe télécharge automatiquement
les données dans un répertoire sur une machine d'abonnée où d’autres logiciels
peuvent les traiter.

Souvent, le but du téléchargement automatisé est d’avoir d’autres codes qui ingerent
les fichiers et effectuent un traitement ultérieur. Plutôt que d’avoir un
processus qui regarde un fichier dans un répertoire, on peut insérer un
traitement personnalisé à différents points du flux.

Des exemples sont disponibles à l’aide de la commande list ::

    fractal% sr3 list fcb
    Provided plugins: ( /home/peter/Sarracenia/v03_wip/sarra ) 
    flowcb/gather/file.py            flowcb/gather/message.py         flowcb/line_log.py               flowcb/line_mode.py
    flowcb/filter/deleteflowfiles.py flowcb/filter/fdelay.py          flowcb/filter/log.py             flowcb/nodupe.py
    flowcb/post/log.py               flowcb/post/message.py           flowcb/retry.py                  flowcb/v2wrapper.py
    fractal%
    fractal% fcbdir=/home/peter/Sarracenia/v03_wip/sarra

Listes de travail (Worklist)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La structure de données de liste de travail est un ensemble de listes de messages.  Il y en a quatre :

  * worklist.incoming - messages à traiter. (construit par gather)
  * worklist.rejected -- message qui ne doit pas être traité ultérieurement. (généralement par filtrage.)
  * worklist.ok - messages qui ont été traités avec succès. (généralement par work.)
  * worklist.failed : messages pour lesquels le traitement a été tenté, mais qui a échoué.

La liste de travail est transmise aux plugins *after_accept* et *after_work* comme détaillé dans la section suivante.


~~~~~~~~~~~~~~~~~~~~

Tous les composants (post, subscribe, sarra, sender, shovel, watch, winnow)
partagent du code substantiel et ne diffèrent que par les paramètres de défaut.  L’algorithme de flux est :

* Rassemblez une liste de messages, à partir d’un fichier ou d’une source de messages en amont (une pompe de données).
  placer de nouveaux messages dans _worklist.incoming_

* Filtrez-les avec des clauses accept/reject, les messages rejetés sont déplacés vers _worklist.rejected_ .
  Les callbacks after_accept manipulent davantage les listes de travail après le filtrage initial d’accept/reject.

* Travailler sur les messages entrants restants, en effectuant le téléchargement, l’envoi ou tout autre travail qui crée de nouveaux fichiers.
  lorsque le travail d’un message réussit, le message est déplacé vers _worklist.ok_ .
  Si le travail pour un message échoue, le message est déplacé vers _worklist.failed_ .

* (facultatif) Publiez le travail accompli (messages sur _worklist.ok_) pour le prochain flux à consommer.

Rappels de Flux (Flow Callbacks)
--------------------------------

Avec les nombreuses façons d’étendre les fonctionnalités, la plus courante est l’ajout de rappels
pour faire circuler les composants. Tous les composants de Sarracenia sont implémentés à l’aide de
la classe sarra.flow. Il existe une classe parent sarra.flowcb pour les implémenter.
Les plugins du paquet sont affichés dans le premier groupe de ceux disponibles. Beaucoup d’entre eux ont des arguments qui
sont documentés en les énumérant. Dans un fichier de configuration, on peut avoir la ligne::

    flowCallback sarracenia.flowcb.log.Log

Cette ligne amène Sarracenia à regarder dans le chemin de recherche Python une classe comme :

.. code:: python

  blacklab% cat sarra/flowcb/msg/log.py

  from sarracenia.flowcb import FlowCB
  import logging

  logger = logging.getLogger(__name__)

  class Log(FlowCB):
    def after_accept(self, worklist):
        for msg in worklist.incoming:
            logger.info("received: %s " % msg)

    def after_work(self, worklist):
        for msg in worklist.ok:
            logger.info("worked successfully: %s " % msg)

Le module imprimera chaque message accepté, et chaque message après avoir travaillé dessus
quand il est terminé (ou le téléchargement a eu lieu, par exemple). Pour modifier la classe de callback,
copiez-la à partir du répertoire répertorié dans la commande *list fcb* vers un endroit dans le
PYTHONPATH de l’environnement, puis modifiez-la aux fins prévues.

On peut également voir quels plugins sont actifs dans une configuration en regardant les messages au démarrage::

   blacklab% sr3 foreground subscribe/clean_f90
   2018-01-08 01:21:34,763 [INFO] sr_subscribe clean_f90 start

   .
   .
   .

   2020-10-12 15:20:06,250 [INFO] sarra.flow run callbacks loaded: ['sarra.flowcb.retry.Retry', 'sarra.flowcb.msg.log.Log', 'file_noop.File_Noop', 'sarra.flowcb.v2wrapper.V2Wrapper', 'sarra.flowcb.gather.message.Message'] 2
   .
   .
   .
   blacklab% 

L’utilisation de l’option *flowCallbackPrepend* aura la classe chargée au début de la liste, plutôt que
à la fin.


Paramètres
----------

Souvent, lors de l’écriture d’extensions via la sous-classification, des options supplémentaires doivent être définies.
La classe sarracenia.config effectue analyse d'options a partir de la ligne de commande et de fichier de configuration.
Il y a une routine qui peut être appelée à partir du nouveau code
pour définir des paramètres supplémentaires, généralement à partir de la routine __init__, dans les classes intégrées
ou flowcb accepte comme paramètre _options_ dans leurs routines __init__() ::

      somewhere in the __init__(self, options):

      options.add_option('accel_wget_command', 'str', '/usr/bin/wget')


      def add_option(self, option, kind='list', default_value=None):
           
      """
           options can be declared in any plugin. There are various *kind* of options, where the declared type modifies the parsing.
           
           'count'      integer count type. 
           'duration'   a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
                        modified by a unit suffix ( m-minute, h-hour, w-week ) 
           'flag'       boolean (True/False) option.
           'list'       a list of string values, each succeeding occurrence catenates to the total.
                        all v2 plugin options are declared of type list.
           'size'       integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.
           'str'        an arbitrary string value, as will all of the above types, each succeeding occurrence overrides the previous one.
           
      """

L’exemple ci-dessus définit une option "accel\_wget\_command"
comme étant de type chaîne, avec la valeur par défaut _/usr/bin/wget_ .

Paramètres hiérarchiques
~~~~~~~~~~~~~~~~~~~~~~~~

On peut également créer des paramètres spécifiques pour les classes de rappel individuelles à l’aide du _set_
et en identifiant la classe exacte à laquelle le paramètre s’applique. Par exemple
parfois, tourner le logLevel en débogage peut entraîner des fichiers journaux très volumineux, et on pourrait
activer uniquement la sortie de débogage pour certaines classes de rappel. Cela peut être fait via::

    set sarracenia.flowcb.gather.file.File.logLevel debug

La commande _set_ peut également être utilisée pour définir des options à transmettre à n’importe quel plugin.

Affichage de tous les paramètres
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utilisez la commande _sr3_ _show_ pour afficher tous les paramètres actifs résultant d’un fichier de configuration ::

    fractal% sr3 show sarra/download_f20.conf
    
    Config of sarra/download_f20: 
    _Config__admin=amqp://bunnymaster@localhost, _Config__broker=amqp://tfeed@localhost, _Config__post_broker=amqp://tfeed@localhost, accel_threshold=100.0,
    accept_unmatch=True, accept_unmatched=False, announce_list=['https://tracker1.com', 'https://tracker2.com', 'https://tracker3.com'], attempts=3,
    auto_delete=False, baseDir=None, batch=1, bind=True, bindings=[('v03', 'xsarra', '#')], bufsize=1048576, bytes_per_second=None, bytes_ps=0,
    cfg_run_dir='/home/peter/.cache/sr3/sarra/download_f20', chmod=0, chmod_dir=509, chmod_log=384, config='download_f20', currentDir=None, debug=False,
    declare=True, declared_exchanges=['xpublic', 'xcvan01'], declared_users="...rce', 'anonymous': 'subscriber', 'ender': 'source', 'eggmeister': 'subscriber'}",
    delete=False, destfn_script=None, directory='/home/peter/sarra_devdocroot', documentRoot=None, download=False, durable=True, exchange=['xflow_public'],
    expire=25200.0, feeder=amqp://tfeed@localhost, filename=None, fixed_headers={}, flatten='/', hostdir='fractal', hostname='fractal', housekeeping=60.0,
    imports=[], inflight=None, inline=False, inlineEncoding='guess', inlineByteMax=4096, instances=1,
    logFormat='%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s', logLevel='info', log_reject=True, lr_backupCount=5, lr_interval=1,
    lr_when='midnight', masks="...nia/insects/flakey_broker', None, re.compile('.*'), True, True, 0, False, '/')]", message_count_max=0, message_rate_max=0,
    message_rate_min=0, message_strategy={'reset': True, 'stubborn': True, 'failure_duration': '5m'}, message_ttl=0, mirror=True, notify_only=False,
    overwrite=True, plugins=['sample.Sample', 'sarracenia.flowcb.log.Log'], post_baseDir='/home/peter/sarra_devdocroot', post_baseUrl='http://localhost:8001',
    post_documentRoot=None, post_exchange=['xflow_public'], post_exchanges=[], prefetch=1, preserve_mode=True, preserve_time=False, program_name='sarra',
    pstrip=False, queue_filename='/home/peter/.cache/sr3/sarra/download_f20/sarra.download_f20.tfeed.qname',
    queue_name='q_tfeed_sarra.download_f20.65966332.70396990', randid='52f9', realpath_post=False, report=False, report_daemons=False, reset=False,
    resolved_exchanges=['xflow_public'], resolved_qname='q_tfeed_sarra.download_f20.65966332.70396990', settings={}, sleep=0.1, statehost=False, strip=0,
    subtopic=None, suppress_duplicates=0, suppress_duplicates_basis='path', timeout=300, tlsRigour='normal', topicPrefix='v03',
    undeclared=['announce_list'], users=False, v2plugin_options=[], v2plugins={}, vhost='/', vip=None
    
    fractal% 



Contrôle de la journalisation
-----------------------------

La méthode de compréhension de l’activité de flux sr3 consiste à examiner ses journaux.
La journalisation peut être assez lourde dans sr3, il existe donc de nombreuses façons de l’affiner.

logLevel
~~~~~~~~

le logLevel normal est utilisé dans les classes Log de python intégrées. Il a les
niveaux : *debug, info, warning, error,* et *critical,* où level indique
le message de priorité la plus basse à imprimer.  La valeur par défaut est *info*.

Parce qu’un simple commutateur binaire du logLevel peut entraîner d’énormes journaux, pour
exemple lors de l’interrogation (poll), où chaque fois que chaque ligne est interrogée peut générer une ligne de journal.
La surveillance des protocoles MQP peut être également détaillée, donc par défaut ni l’un ni l’autre
d’entre eux sont en fait mis en mode débogage par le paramètre logLevel global.
certaines classes n’honorent pas le cadre global et demandent une activation:

set sarracenia.transfer.Transfer.logLevel debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Peut contrôler le logLevel utilisé dans les classes de transfert, pour le définir plus bas ou plus haut
que le reste de sr3.

set sarracenia.moth.amqp.AMQP.logLevel debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Imprimez les messages de débogage spécifiques à la file d’attente de messages AMQP (classe sarracenia.moth.amqp.AMQP).
utilisé uniquement lors du débogage avec le MQP lui-même, pour traiter les problèmes de connectivité du courtier par exemple.
diagnostic et test d’interopérabilité.

set sarracenia.moth.mqtt.MQTT.logLevel debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Imprimez les messages de débogage spécifiques à la file d’attente de messages MQTT (classe sarracenia.moth.mqtt.MQTT).
utilisé uniquement lors du débogage avec le MQP lui-même, pour traiter les problèmes de connectivité du courtier par exemple.
diagnostic et test d’interopérabilité.

logEvents
~~~~~~~~~

valeur par défaut : *after_accept, after_work, on_housekeeping*
disponible: after_accept, after_work, all, gather, on_housekeeping, on_start, on_stop, post

implémenté par la classe *sarracenia.flowcb.log.Log*, on peut sélectionner les événements qui génèrent le journal
Messages. caractère générique : *all* génère des messages de journal pour chaque événement connu de la classe *Log*.

logMessageDump
~~~~~~~~~~~~~~

mis en œuvre par sarracenia.flowcb.log, à chaque événement de journalisation, imprimer le contenu actuel
du message en cours de traitement.

logReject
~~~~~~~~~

imprimer un message de journal pour chaque message rejeté (normalement ignoré silencieusement).

messageDebugDump
~~~~~~~~~~~~~~~~

Implémenté dans des sous-classes de moth, imprime les octets réellement reçus ou envoyés
pour le protocole MQP utilisé.

Extension des classes
---------------------

On peut ajouter des fonctionnalités supplémentaires à Sarracenia en créant des sous-classes.

* sarra.moth - Messages organisés en hiérarchies de thèmes. (existants : rabbitmq-amqp)

* sarra.integrity - algorithmes de somme de contrôle (existants: md5, sha512, arbitraires, aléatoires)

* sarra.transfer - protocoles de transport supplémentaires (https, ftp, sftp )

* sarra.flow - création de nouveaux composants au-delà des composants intégrés. (post, sarra, shovel, etc...)

* sarra.flowcb - personnalisation des flux de composants à l’aide de rappels.

* sarra.flowcb.poll - personnalisation du rappel de poll pour les sources non standard.

On commencerait par l’une des classes existantes, on la copierait ailleurs dans le chemin python,
et on construirez notre extension. Ces classes sont ajoutées à Sarra à l’aide de l’option *import*
dans les fichiers de configuration. les fichiers __init__ dans les répertoires sources sont les bons
pour rechercher des informations sur l’API de chaque classe.

The Simplest Flow_Callback
--------------------------



Sample Extensions
-----------------

Vous trouverez ci-dessous une classe d’exemple flowCallback minimale, qui se trouverait dans un sample.py.
Le fichier est placé dans n’importe quel répertoire du PYTHONPATH::

    import logging
    import sarracenia.flowcb

    # this logger declaration  must be after last import (or be used by imported module)
    logger = logging.getLogger(__name__)

    class Sample(sarracenia.flowcb.FlowCB):

        def __init__(self, options):

            self.o = options

            # implement class specific logging priority.
            logger.setLevel(getattr(logging, self.o.logLevel.upper()))

            # declare a module specific setting.
            options.add_option('announce_list', list )

        def on_start(self):

            logger.info('announce_list: %s' % self.o.announce_list )

Tout ce qu’il fait est d’ajouter un paramètre appelé 'announce-list' à la configuration.
puis imprimer la valeur au démarrage.

Dans un fichier de configuration, on s’attendrait à voir ::

   flowCallback sample.Sample

   announce_list https://tracker1.com
   announce_list https://tracker2.com
   announce_list https://tracker3.com

Et au démarrage, le message de journalisation s’imprimerait::

   021-02-21 08:27:16,301 [INFO] sample on_start announce_list: ['https://tracker1.com', 'https://tracker2.com', 'https://tracker3.com']



Les développeurs peuvent ajouter des protocoles de transfert supplémentaires pour les messages ou
transport de données à l’aide de la directive *import* pour que la nouvelle classe soit
disponible::

  import torr

serait un nom raisonnable pour que le protocole de transfert récupère les
ressources avec le protocole bittorrent.  *import* peut également être utilisé
pour importer des modules python arbitraires à utiliser par des rappels.

Champs dans les Messages
------------------------

les rappels reçoivent le paramètre sarracenia.options déjà analysé.
self est le message en cours de traitement. variables les plus utilisées :

*msg['exchange']*
  Échange par lequel le message est posté ou consommé.

*msg['isRetry']*
  S’il s’agit d’une tentative ultérieure d’envoi ou de téléchargement d’un message.

*msg['new_dir']*
  Le répertoire qui contiendra *msg['new_file']*

*msg['new_file']*
  Une variable populaire dans les plugins on_file et on_part est : *msg['new_file]*,
  en donnant le nom de fichier dans lequel le produit téléchargé a été écrit.  Lorsque
  la même variable est modifiée dans un plugin on_message, elle change le nom du
  fichier à télécharger. De même, une autre variable souvent utilisée est
  *parent.new_dir*, qui fonctionne sur le répertoire dans lequel le fichier
  sera téléchargé.

*msg['new_inflight_file']*
  dans les rappels de téléchargement et d’envoi, ce champ sera défini avec le nom temporaire
  d’un fichier utilisé pendant le transfert.  Une fois le transfert terminé,
  le fichier doit être renommé à qui se trouve dans *msg['new_file']*.

*msg['pubTime']*
  Heure à laquelle le message a été inséré dans le réseau (premier champ d’un avis).

*msg['baseUrl']*
  racine URL de l’arborescence de publication à partir de laquelle les chemins relatifs sont construits.

*msg['relPath']*
  Chemin d’accès relatif à partir de l’URL de base du fichier.
  la concaténation des deux donne l’URL complète.

*msg['integrity']*
  La structure de somme de contrôle, un dictionnaire python avec les champs 'méthode' et 'valeur'.

*msg['subtopic']*
  liste des chaînes (avec le préfixe de thème supprimé)

Ce sont les champs de message qui sont le plus souvent d’intérêt, mais beaucoup d’autres
peuvent être consulté par les éléments suivants dans une configuration ::

   logMessageDump True
   callback log

Ce qui garantit que la classe log flowcb est active et active le paramètre
pour imprimer des messages bruts pendant le traitement.

Accès aux options
-----------------

Les paramètres résultant de l’analyse des fichiers de configuration sont également facilement disponibles.
Les plugins peuvent définir leurs propres options en appelant::

   FIXME: api incomplete.
   Config.add_option( option='name_of_option', kind, default_value  )

Les options ainsi déclarées deviennent simplement des variables d’instance dans les options transmises à init.
Par convention, les plugins définissent self.o pour contenir les options passées au moment de l’initialisation, de sorte que
toutes les options intégrées sont traitées de la même manière.  En consultant le `sr_subscribe(1) <../Reference/sr3.1.html#subscribe>`_,
la plupart des options auront une variable d’instance corrélative.

Quelques exemples :

*self.o.baseDir*
  le répertoire de base de l’emplacement des fichiers lors de la consommation d’une publication.

*self.o.suppress_duplicates*
  Valeur numérique indiquant la durée de vie de la mise en cache (l’âge des entrées avant qu’elles ne vieillissent).
  La valeur 0 indique que la mise en cache est désactivée.

*self.o.inflight*
  Le paramètre actuel de *inflight* (voir `Delivery Completion <FileCompletion.rst>`_)

*self.o.overwrite*
  qui contrôle si les fichiers déjà téléchargés doivent être remplacés sans condition.

*self.o.discard*
  Si les fichiers doivent être supprimés après leur téléchargement.

Points de rappel de flux
------------------------
Sarracenia interprétera les noms des fonctions comme des heures d'indication dans le de traitement lorsque
une routine donnée devrait être appelée.

Voir le `FlowCB source <https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/__init__.py>`_
pour des informations détaillées sur les signatures d’appel et les valeurs de retour, etc.

+---------------------+----------------------------------------------------+
|  Name               | Quand/Pourquoi il est appelé                       |
+=====================+====================================================+
|  ack                | accuser réception des messages d’un courtier.      |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | très fréquemment utilisé.                          |
|                     |                                                    |
|                     | peut modifier les messages dans worklist.incoming  |
|                     | ajout d’un champ ou modification d’une valeur.     |
|                     |                                                    |
|                     | Déplacez les messages entre les listes de messages |
| after_accept        | dans worklist. pour rejeter un message, il est     |
| (self,worklist)     | déplacé de worklist.incoming -> worklist.rejected. |
|                     | (sera reconnu et rejeté.)                          |
|                     |                                                    |
|                     | Pour indiquer qu’un message a été traité, déplacez |
|                     | worklist.incoming -> worklist.ok                   |
|                     | (sera reconnu et rejeté.)                          |
|                     |                                                    |
|                     | Pour indiquer l’échec du traitement, déplacez :    |
|                     | worklist.incoming -> worklist.failed               |
|                     |ira dans la file d’attente pour réessayer plus tard |
|                     |                                                    |
|                     | Exaeples: msg_* dans le répertoire exemples        |
|                     |                                                    |
|                     | msg_delay - assurez-vous que les messages sont     |
|                     | anciens avant de les traiter.                      |
|                     |                                                    |
|                     | msg_download - modifier les messages pour utiliser |
|                     | différent téléchargeurs en fonction de la taille du|
|                     | fichier (intégré pour les petits, téléchargeurs    |
|                     | binaires pour les fichiers volumineux.)            |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | appelé après qu’un transfert a été tenté.          |
| after_work          |                                                    |
| (self,worklist)     | A ce point, tous les messages sont reconnus.       |
|                     | worklist.ok contient des transferts réussis        |
|                     | worklist.failed contient des transferts échoué     |
|                     | worklist.rejected contient des transferts rejetés  |
|                     | pendant le transfert.                              |
|                     |                                                    |
|                     | généralement à propos de faire quelque chose avec  |
|                     | le fichier après que le téléchargement est terminé.|
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | changer msg['new_file'] a son gout                 |
| destfn_script       | appelé lors du changement de nom du fichier en vol |
|                     | son nom permanent                                  |
|                     |                                                    |
|                     | NOT IMPLEMENTED? FIXME?                            |
+---------------------+----------------------------------------------------+
| download(self,msg)  | remplacer le téléchargeur intégré, retourner true  |
|                     | pour un succès. Prends un messafe comme argument.  |
+---------------------+----------------------------------------------------+
| gather(self)        | Rassembler les messages a la source, retourne une  |
|                     | une liste de messages.                             |
+---------------------+----------------------------------------------------+
|                     | Appelé à chaque intervalle housekeeping (minutes). |
|                     | utilisé pour nettoyer le cache, vérifier les       |
|                     | problèmes occasionnels. Gérer les files d'attentes |
| on_housekeeping     |                                                    |
| (self)              | retourne False pour abandonner le traitement       |
|                     | ultérieur. Retourne True pour continuer.           |
|                     |                                                    |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | Quand un composant (e.g. sr_subscribe) est démarré.|
| on_start(self)      | Peut être utlisé pour lire l'état a partir d'un    |
|                     | fichier.                                           |
|                     | fichier d'état dans self.o.user_cache_dir          |
|                     |                                                    |
|                     | valeur retourné ignoré                             |
|                     |                                                    |
|                     | exemple: file_total_save.py [#]_                   |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     |Quand un composant (e.g. sr_subscribe) est arrêté.  |
| on_stop(self)       | peut être utilisé pour conserver l’état.           |
|                     |                                                    |
|                     | fichier d'état dans self.o.user_cache_dir          |
|                     |                                                    |
|                     |valeur retourné ignoré                              |
|                     |                                                    |
+---------------------+----------------------------------------------------+
| poll(self)          | remplace la méthode d’interrogation (poll) intégrée|
|                     | retourne une liste de messages.                    |
+---------------------+----------------------------------------------------+
| post(self,worklist) | remplacez la routine de publication (post) intégrée|
|                     |                                                    |
+---------------------+----------------------------------------------------+
| send(self,msg)      | remplacez la routine d’envoi (send) intégrée       |
|                     |                                                    |
+---------------------+----------------------------------------------------+

Personnalisation du Callback de Flux de Poll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Une sous-classe intégrée de flowcb, sarracenia.flowcb.poll.Poll implémente la majorité du
sondage (poll) sr3. Il existe de nombreux types de ressources à interroger, et
tant d’options pour les personnaliser sont nécessaires. La personnalisation est accomplie
avec la sous-classification, de sorte que le haut d’un tel rappel ressemble à::

   ...
   from sarracenia.flowcb.poll import Poll
   ....

   class Nasa_mls_nrt(Poll):

Plutôt que d’implémenter une classe flowcb, on sous-classe la classe
flowcb.poll.Poll.  Voici les sous classes commune du sondage avec des
points d’entrée spécifiques généralement implémentés dans les sous-classes :

+-------------------+----------------------------------------------------+
|                   | dans sr_poll si vous souhaitez uniquement modifier |
| handle_data       | la façon dont l’URL html téléchargée est analysée  |
|                   | remplacez ceci.                                    |
|                   | action:                                            |
|                   | analyser parent.entries pour faire self.entries    |
|                   |                                                    |
|                   | Exemples:  html_page* dans le répertoire exemples  |
|                   |                                                    |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | dans sr_poll si les sites ont des formats distants |
|                   | différents, appelé pour analyser chaque ligne dans |
| on_line           | parent.entries.                                    |
|                   | Travaille sur parent.line                          |
|                   |                                                    |
|                   | retourner False pour abandonner le traitement      |
|                   | retourner True pour continuer                      |
|                   |                                                    |
|                   | Exemples:  line_* dans le répertoire exemples      |
|                   |                                                    |
+-------------------+----------------------------------------------------+

Voir les classes intégrés `flowcb Poll <https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/__init__.py>`_
est utile.

.. [#] voir `smc_download_cp <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/smc_download_cp.py>`_
.. [#] voir `Issue 74 <https://github.com/MetPX/sarracenia/issues/74>`_
.. [#] voir `part_clanav_scan.py  <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/part_clanav_scan.py>`_
.. [#] voir `file_total_save.py  <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/file_total_save.py>`_
.. [#] voir `poll_email_ingest.py  <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_email_ingest.py>`_

--------------------------------
Meilleure réception des fichiers
--------------------------------

Par exemple, plutôt que d’utiliser le système de fichiers, sr_subscribe pourrait indiquer quand chaque fichier est prêt
en écrivant dans un canal nommé ::

  blacklab% sr_subscribe edit dd_swob.conf 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  flowcb sarracenia.flowcb.work.rxpipe.RxPipe
  rxpipe_name /tmp/dd_swob.pipe

  directory /tmp/dd_swob
  mirror True
  accept .*

  # rxpipe is a builtin on_file script which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.

Avec l’option *flowcb*, on peut spécifier une option de traitement telle que rxpipe. Avec rxpipe,
chaque fois qu’un transfert de fichier est terminé et est prêt pour le post-traitement, son nom est écrit
au canal Linux (nommé .rxpipe) dans le répertoire de travail actuel. Donc le code pour le post-traitement
devient::

  do_something <.rxpipe

Aucun filtrage des fichiers de travail par l’utilisateur n’est requis, et l’ingestion de fichiers partiels est
complètement évité.

.. REMARQUE::
   Dans le cas où un grand nombre d’instances sr_subscribe fonctionnent
   sur la même configuration, il y a une légère probabilité que les notifications
   peuvent se corrompre mutuellement dans le canal nommé.
   Nous devrions probablement vérifier si cette probabilité est négligeable ou non.

Réception avancée des fichiers
------------------------------

Le point d’entrée *after_work* dans une classe *sarracenia.flowcb* est une action à effectuer
après réception d’un fichier (ou après l’envoi, dans un sender.) Le module RxPipe en est un exemple
fourni avec sarracenia::

  import logging
  import os
  from sarracenia.flowcb import FlowCB

  logger = logging.getLogger(__name__)

  class RxPipe(FlowCB):

      def __init__(self,options):

          self.o=options
          logger.setLevel(getattr(logging, self.o.logLevel.upper()))
          self.o.add_option( option='rxpipe_name', kind='str' )

      def on_start(self):
          if not hasattr(self.o,'rxpipe_name') and self.o.file_rxpipe_name:
              logger.error("Missing rxpipe_name parameter")
              return
          self.rxpipe = open( self.o.rxpipe_name, "w" )

      def after_work(self, worklist):

          for msg in worklist.ok:
              self.rxpipe.write( msg['new_dir'] + os.sep + msg['new_file'] + '\n' )
          self.rxpipe.flush()
          return None


Avec ce fragment de Python, lorsque sr_subscribe est appelé pour la première fois, il s’assure que
un canal nommé npipe est ouvert dans le répertoire spécifié en exécutant
la fonction __init__ dans la classe python RxPipe déclarée.  Puis, chaque fois qu'une
réception de dossier est terminée, l’attribution de *self.on_file* assure que
la fonction rx.on_file est appelée.

La fonction rxpipe.on_file écrit simplement le nom du fichier téléchargé dans
le canal nommé.  L’utilisation du canal nommé rend la réception des données asynchrone
du traitement des données. Comme le montre l’exemple précédent, on peut alors
démarrer une seule tâche *do_something* qui traite la liste des fichiers alimentés
en tant qu’entrée standard, à partir d’un canal nommé.

Dans les exemples ci-dessus, la réception et le traitement des fichiers sont entièrement séparés. S’il y a
un problème de traitement, les répertoires de réception de fichiers se rempliront, potentiellement
atteignant une taille encombrante et causent de nombreuses difficultés pratiques. Quand un plugin comme
on_file est utilisé, le traitement de chaque fichier téléchargé est exécuté avant de continuer
au fichier suivant.

Si le code du script on_file est modifié pour effectuer du traitement réel, alors
plutôt que d’être indépendant, le traitement pourrait fournir une contre-pression au
mécanisme de livraison des données.  Si le traitement est bloqué, le sr_subscriber
arrêtera le téléchargement et la file d’attente sera sur le serveur, plutôt que de créer
un énorme répertoire local sur le client.  Différents modèles s’appliquent dans différents
Situations.

Un point supplémentaire est que si le traitement des fichiers est appelé
dans chaque cas, fournissant un traitement parallèle très facile construit
dans sr_subscribe.

Utilisation des Identifiants dans les Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour mettre en œuvre la prise en charge de protocoles supplémentaires, il faut souvent des informations d’identification
dans le script avec le code :

- **ok, details = self.o.credentials.get(msg.urlcred)**
- **if details  : url = details.url**

Le détails des options sont des éléments de la classe de détails (hardcoded) :

- **print(details.ssh_keyfile)**
- **print(details.passive)**
- **print(details.binary)**
- **print(details.tls)**
- **print(details.prot_p)**

Pour les informations d’identification qui définissent le protocole de téléchargement (upload),
la connexion, une fois ouverte, reste ouverte. Il est réinitialisé
(fermé et rouvert) uniquement lorsque le nombre de téléchargements (uploads)
atteint le nombre donné par l’option **batch** (100 par défaut).

Toutes les opérations de téléchargement (upload) utilisent un buffer. La taille, en octets,
du buffer utilisé est donné par l’option **bufsize** (8192 par défaut).

Pourquoi l’API v3 doit être utilisée dans la mesure du possible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* utilise importlib de python, un moyen beaucoup plus standard d’enregistrer des plugins.
  maintenant les erreurs de syntaxe seront détectées comme n’importe quel autre module python importé,
  avec un message d’erreur raisonnable.

* pas de décoration étrange à la fin des plugins (self.plugin = , etc... juste du python ordinaire.)
  Modules python entièrement standard, uniquement avec des méthodes/fonctions connues

* Le choix étrange de *parent* comme lieu de stockage des paramètres est déroutant pour les gens.
  La variable d’instance *parent* devient *options*, *self.parent* devient *self.o*

* les rappels d’événements pluriels remplacent les rappels singuliers.  after_accept remplace on_message

* les messages ne sont que des dictionnaires python. champs définis par json.loads( format de charge utile v03 )
  les messages ne contiennent que les champs réels, pas de paramètres ou d’autres choses...
  données simples.

* ce qu’on appelait autrefois les plugins, ne sont plus qu’un type de plugins, appelés flowCallbacks.
  Ils déplacent maintenant les messages entre les listes de travail.

Avec cette API, traiter différents nombres de fichiers d’entrée et de sortie devient beaucoup
plus naturel, lors du décompression d’un fichier tar, des messages pour les fichiers décompressés peuvent être ajoutés
à la liste ok, de sorte qu’ils seront affichés lorsque le flux arrivera là-bas.
De même, un grand nombre de petits fichiers peuvent être regroupés pour en créer un
fichier volumineux, donc plutôt que de transférer tous les fichiers entrants vers la liste,
seul le seau de tar résultant sera placé dans ok.

Le mécanisme d’importation *import* décrit ci-dessous fournit un moyen simple
d’étendre Sarracenia en créant des enfants des classes principales

* moth (messages organisés en hiérarchies de thèmes) pour traiter les nouveaux protocoles de message.
* transfert ... pour ajouter de nouveaux protocoles pour les transferts de fichiers.
* flux .. nouveaux composants avec un flux différent de ceux intégrés.

Dans la v2, il n’y avait pas de mécanisme d’extension équivalent et l’ajout de protocoles
aurait nécessité une refonte du code de base de manière personnalisée pour chaque ajout.

-------------------------------------------
Notification de fichier sans téléchargement
-------------------------------------------

Si la pompe de données existe dans un environnement partagé de grande taille, tel qu'un
centre de supercalcul avec un système de fichiers de site,
le fichier peut être disponible sans téléchargement.  Donc, juste
obtenir la notification de fichier et le transformer en fichier local est suffisant ::

  blacklab% sr_subscribe edit dd_swob.conf 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  document_root /data/web/dd_root
  download off
  flowcb msg_2local.Msg2Local
  flowcb do_something.DoSomething

  accept .*
  
Il devrait y avoir deux fichiers dans le PYTHONPATH quelque part contenant des
classes dérivées de FlowCB avec des routines after_accept  déclarées.
Le traitement dans ces routines se fera à la réception d’un lot
de messages.  Un message correspondra à un fichier.

les routines after_accept acceptent une liste de travail comme argument.

.. avertissement::
   **FIXME**: peut-être montrer un moyen de vérifier l’en-tête des pièces
   avec une instruction afin d’agir uniquement sur le message de première partie
   pour les fichiers longs.

Idées d’extension
-----------------

Exemples de choses qui seraient amusantes à faire avec les plugins:

- Common Alerting Protocol (CAP), est un format XML qui fournit des avertissements
  pour de nombreux types d’événements, en indiquant la zone de couverture.  Il y a un
  champ 'polygone' dans l’avertissement, que la source pourrait ajouter aux messages en utilisant
  un plugin on_post.  Les abonnés auraient accès à l’en-tête 'polygone'
  grâce à l’utilisation d’un plugin on_message, leur permettant de déterminer si l’avertissement
  affecté une zone d’intérêt sans télécharger l’intégralité de l’avertissement.

- Une source qui applique la compression aux produits avant de poster, pourrait ajouter un
  en-tête tel que 'uncompressed_size' et 'uncompressed_sum' pour permettre aux
  abonnés avec un plugin on_message de comparer un fichier qui a été localement
  non compressé dans un fichier en amont proposé sous forme compressée.

- ajouter Bittorrent, S3, IPFS comme protocoles de transfert (sous-classification Transfer)

- ajouter des protocoles de message supplémentaires (sous-classification Moth)

- des sommes de contrôle supplémentaires, sous-classification de l’intégrité. Par exemple, pour obtenir des données GOES DCP
  provenant de sources telles que l’USGS Sioux Falls, les rapports ont une remorque
  qui montre quelques statistiques d’antenne du site de réception.  Donc, si l’un d’entre eux
  reçoit GOES DCP de Wallops, par exemple, la bande-annonce sera différente.
  Ainsi, la somme de contrôle de l’ensemble du contenu aura des résultats différents pour le
  même rapport.

-------
Polling
-------

Pour implémenter un sondage personnalisé, déclarez-le en tant que sous-classe de Sondage
(sarracenia.flowcb.poll.Poll), et seulement la routine nécessaire (dans ce cas
l’analyse html « handle_data ») doit être écrite pour remplacer le comportement fourni
par la classe parente.

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/__init__.py )

Le plugin a une routine principale « parse », qui appelle la classe html.parser, dans laquelle
le data_handler est appelé pour chaque ligne, construisant progressivement les self.entries
dictionnaire où chaque entrée à une structure SFTPAttributes décrivant un fichier en cours d’interrogation.

Donc, le travail dans handle_data est juste de remplir une structure paramiko.SFTPAttributes.
Étant donné que le site Web ne fournit pas réellement de métadonnées, il est simplement rempli avec des données raisonnables
par défaut, qui fournissent suffisamment d’informations pour créer un message et l’exécuter au travers de la
suppression des doublons.

Voici le rappel complet du poll::

    import logging
    import paramiko
    import sarracenia
    from sarracenia import nowflt, timestr2flt
    from sarracenia.flowcb.poll import Poll
    
    logger = logging.getLogger(__name__)
    
    class Nasa_mls_nrt(Poll):
    
        def handle_data(self, data):
    
            st = paramiko.SFTPAttributes()
            st.st_mtime = 0
            st.st_mode = 0o775
            st.filename = data
    
            if 'MLS-Aura' in data:
                   logger.debug("data %s" %data)
                   self.entries[data]=st
    
                   logger.info("(%s) = %s" % (self.myfname,st))
            if self.myfname == None : return
            if self.myfname == data : return


Le fichier est ici:

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/nasa_mls_nrt.py )

et le fichier de configuration correspondant fourni ici :

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/examples/poll/nasa-mls-nrt.conf )






-------------------------------------
Accès aux messages à partir de Python
-------------------------------------

Jusqu’à présent, nous avons présenté des méthodes d’écriture de personnalisations de traitement Sarracenia,
où l’on écrit des extensions, via des rappels ou une extension
pour modifier ce que font les instances de flux de sarracénia.

Certains peuvent ne pas vouloir utiliser le langage de Sarracenia et des configurations.
Ils peuvent avoir du code existant, à partir duquel ils veulent appeler une sorte de code d’ingestion de données.
On peut appeler des fonctions liées à sarracenia directement à partir de programmes python existants.

Pour l’instant, il est préférable de consulter le `Jupyter Notebooks <../../jupyter>`_  inclus avec Sarracenia,
qui ont quelques exemples d’une telle utilisation.

.. avertissement::
    **FIXME**, lien vers amqplib ou liaisons java, et pointeur vers les pages de manuel sr_post et sr_report section 7.


