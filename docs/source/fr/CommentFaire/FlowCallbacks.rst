

================================
Écriture de plugins FlowCallback
================================

Tous les composants de Sarracenia implémentent l’algorithme *Flow*.
La classe principale de Sarracenia est *sarracenia.flow* et
la fonctionnalité de base est implémentée à l’aide de la classe créée pour ajouter un
traitement personnalisé à un flux, la classe flowcb (flow callback).

Pour une discussion détaillée de l’algorithme de flux elle-même, jetez un coup d’œil
sur le manuel `Concepts <../Explanation/Concepts.rst>`_. Pour tout flux, on peut
ajouter un traitement personnalisé à divers moments au cours du traitement en sous-classant
la classe `sarracenia.flowcb <../../sarracenia/flowcb/__init__.py>`_.

En bref, l’algorithme comporte les étapes suivantes :

* **gather** -- collecter passivement les messages de notification à traiter.
* **poll** -- collecter activement les messages de notification à traiter.
* **filter** -- appliquer des correspondances d’expression régulière accept/reject à la liste des messages de notification.

  * *after_accept* point d’entré de callback

* **work** -- effectuer un transfert ou une transformation sur un fichier.

  * *after_work* point d’entrée de callback

* **post**  -- publier le résultat du travail effectué pour l’étape suivante.

Un *flowcallback*, est une classe python construite avec des routines nommées pour
indiquer quand le programmeur veut qu’elles soient appelés.
Il y a plusieurs exemples de class python *flowcallback* inclus avec Sarracenia,
qu'on peut voir (en anglais) dans `Flowcallback Reference <../../Reference/flowcb.html>`_
qui peuvent servir comment modèle pour partir de nouvelles classes.

Ce guide décrit les éléments nécessaire pour façonner des classes flowcb à partir de zéro.

Entrées de fichier de configuration pour utiliser Flow_Callbacks
----------------------------------------------------------------

Pour ajouter un callback à un flux, une ligne est ajoutée au fichier de configuration ::

    flowcb sarracenia.flowcb.log.Log

Si vous suivez la convention et que le nom de la classe est une
version en majuscules (Log) du nom de fichier (log), un raccourci est disponible ::

   callback log

Le constructeur de classe accepte un objet de classe sarracenia.config.Config,
appelées options, qui stockent tous les paramètres à utiliser par le flux en cours d’exécution.
Options est utilisé pour remplacer le comportement par défaut des flux et des callbacks.
L’argument du flowcb est une classe python standard qui doit être
dans le chemin python normal pour l'*import* python, et le dernier élément
est le nom de la classe dans le fichier qui doit être instancié
en tant qu’instance flowcb.

un paramètre pour un callback est déclaré comme suit ::

    set sarracenia.flowcb.filter.log.Log.logLevel debug

(le préfixe du paramètre correspond à la hiérarchie de types dans flowCallback)

lorsque le constructeur du callback est appelé, son argument options contiendra::

    options.logLevel = 'debug'

Si aucune substitution spécifique au module n’est présente, le paramètre le plus global est utilisé.


Worklists
---------

Outre l'option, l’autre argument principal pour les routines de callbacks after_accept et after_work
est worklist. Worklist est donnée aux points d’entrée qui se produisent pendant le traitement de message de
notification, et est un certain nombre de worklist de messages de notification::

    worklist.incoming --> messages de notification à traiter (nouveaux ou nouvelles tentatives).
    worklist.ok       --> traité avec succès
    worklist.rejected --> les messages de notification ne doivent pas être traités ultérieurement.
    worklist.failed   --> messages de notification pour lesquels le traitement a échoué.
                          les messages de notification ayant échoué seront réessayés.

Initialement, tous les messages de notification sont placés dans worklists.incoming.
si un plugin décide :

- un message de notification n’est pas pertinent, déplacé vers la worklist rejetée.
- aucun traitement supplémentaire du message de notification n’est nécessaire, déplacez-le vers worklist ok.
- une opération a échoué et elle doit être réessayée plus tard, passez à la worklist échouée.

Ne supprimez pas de toutes les listes, déplacez uniquement les messages de notification entre les worklists.
Il est nécessaire de placer les messages de notification rejetés dans la worklist appropriée
afin qu’ils soient reconnus comme reçus. Les messages ne peuvent être supprimés qu'une
fois que l’accusé de réception a été pris en charge.

Journalisation
--------------

Python a une excellente journalisation intégrée, et il faut simplement utiliser le module
d’une manière normale, pythonique, avec::

  import logging

Après toutes les importations dans votre fichier source python, définissez un enregistreur
pour le fichier source ::

  logger = logging.getLogger(__name__)

Comme c’est normal avec le module de journalisation Python, les messages de notification peuvent alors
être affiché dans le journal ::

  logger.debug('got here')

Chaque message de notification dans le journal sera précédé de la classe et de la
routine émettant le message de notification du journal, ainsi que de la date/heure.

On peut également implémenter un remplacement par module pour les niveaux de journalisation.
Voir sarracenia/moth/amqp.py comme exemple. Pour ce module,
le niveau de journalisation des messages de notification est porté à l’avertissement par défaut.
On peut le remplacer par un paramètre de fichier de configuration::

   set sarracenia.moth.amqp.AMQP.logLevel info
 
dans la fonction *__init__(self,options)* du callback,
inclure les lignes::

   me = "%s.%s" % ( __class__.__module__ , __class__.__name__ )
   if 'logLevel' in self.o['settings'][me]:
                logger.setLevel( self.o['logLevel'].upper() )



Initialisation et paramètres
----------------------------

L’étape suivante consiste à déclarer une classe ::

  class Myclass(FlowCB):

en tant que sous-classe de FlowCB.  Les principales routines de la classe sont les points d’entrée
qui seront appelés au moment où leur nom l’indique. S’il manque un point d’entrée donné à votre classe,
elle ne sera tout simplement pas appelée. La classe __init__() est utilisée pour
initialiser des éléments pour la classe de callback::

    def __init__(self, options):

        super().__init__(options,logger)

        self.o.add_option( 'myoption', 'str', 'usuallythis')

Les lignes de configuration de la journalisation dans __init__ permettent de définir un niveau de journalisation spécifique
pour cette classe flowCallback. Une fois la journalisation passe-partout est terminée,
la routine add_option pour définir les paramètres de la classe.
les utilisateurs peuvent les inclure dans les fichiers de configuration, tout comme les options intégrées ::

        myoption IsReallyNeeded

Le résultat d’un tel réglage est que le *self.o.myoption = 'IsReallyNeeded'*.
Si aucune valeur n’est définie dans la configuration, *self.o.myoption* sera par défaut *'usuallyThis'*
Il existe différents *types* d’options, où le type déclaré modifie l’analyse::
           
   'count'    type de nombre entier.
   'duration' un nombre à virgule flottante indiquant une quantité de secondes (0,001 est 1 miliseconde)
              modifié par un suffixe unitaire ( m-minute, h-heure, w-semaine )
   'flag'     option booléen (True/False).
   'list'     une liste de valeurs de chaîne, chaque occurrence suivante se caténates au total.
              toutes les options de plugin v2 sont déclarées de type list.
   'size'     taille entière. Suffixes k, m et g pour les multiplicateurs kilo, mega et giga (base 2).
   'str'      une valeur de chaîne arbitraire, comme tous les types ci-dessus,
              chaque occurrence suivante remplace la précédente.

Points d’entrée
---------------
Autres entry_points, extraits de sarracenia/flowcb/__init__.py ::

    def name(self):
        Task: return the name of a plugin for reference purposes. (automatically there)

    def ack(self,messagelist):
        Task: acknowledge notification messages from a gather source.

    def gather(self):
        Task: gather notification messages from a source... return a list of notification messages.
              can also return tuple (keep_going, new_messages) where keep_going is a flag 
              that when False stops processing of further gather routines.
        return []

    """
      application of the accept/reject clauses happens here, so after_accept callbacks
      run on a filtered set of notification messages.

    """

    def after_accept(self,worklist):
        """
         Task: just after notification messages go through accept/reject masks,
               operate on worklist.incoming to help decide which notification messages to process further.
               and move notification messages to worklist.rejected to prevent further processing.
               do not delete any notification messages, only move between worklists.
        """
    def do_poll(self):
        Task: build worklist.incoming, a form of gather()

    def on_data(self,data):
        Task:  return data transformed in some way.

        return new_data

    def after_work(self,worklist):
        Task: operate on worklist.ok (files which have arrived.)

    def post(self,worklist):
         Task: operate on worklist.ok, and worklist.failed. modifies them appropriately.
               notification message acknowledgement has already occurred before they are called.

    def on_housekeeping(self):
         do periodic processing.

    def on_html_page(self,page):
         Task: modify an html page.

    def on_line(self,line):
         used in FTP polls, because servers have different formats, modify to canonical use.

         Task: return modified line.

    def on_start(self):
         After the connection is established with the broker and things are instantiated, but
         before any notification message transfer occurs.

    def on_stop(self):

new_* Champs
------------

Pendant le traitement des messages de notification, les valeurs des champs standard d'origine restent généralement inchangées (telles que lues).
Pour modifier les champs des messages de notification transmis aux consommateurs en aval, on modifie plutôt new_field
de celui du message, car l'original est nécessaire pour une récupération réussie en amont
:

* msg['new_baseUrl'] ... baseUrl à transmettre aux consommateurs en aval.

* msg['new_dir'] ... le répertoire dans lequel un fichier sera téléchargé ou envoyé.

* msg['new_file'] .... nom final du fichier à écrire.

* msg['new_inflight_path'] ... nom calculé du fichier temporaire à écrire avant de le renommer en msg['new_file'] ... ne pas modifier manuellement.

* msg['new_relPath'] ... calculé à partir de 'new_baseUrl', 'post_baseDir', 'new_dir', 'new_file'... ne pas modifier manuellement. 

* msg['post_version'] ... le format d'encodage du message à poster (à partir des paramètres)

* msg['new_subtopic'] ... la hiérarchie des sous-thèmes qui sera codée dans le message de notification destiné aux consommateurs en aval.

Les champs override
-------------------

Pour modifier le traitement des messages, on peut définir des remplacements pour modifier le fonctionnement des algorithmes intégrés.
Par exemple:

* msg['nodupe_override'] = { 'key': ..., 'path': ... } modifie le fonctionnement de la détection des doublons.
* msg['topic'] ... définit le sujet d'un message publié (au lieu d'être calculé à partir d'autres champs.)
* msg['exchangeSplitOverride'] = int ... change la façon dont post_ExchangeSplit choisit parmi plusieurs postExchanges


Personnalisation de la suppression des doublons
---------------------------------

Le traitement intégré des doublons consiste à utiliser le champ d'identité comme clé et à stocker le chemin (path) comme valeur.
Ainsi, si un fichier est reçu avec la même clé et que le path est déjà présent, il est alors considéré comme un doublon.
et laissé tomber.

Dans certains cas, nous pouvons souhaiter que seul le nom du fichier soit utilisé, donc si un fichier portant le même nom est reçu deux fois,
quel que soit le contenu, il doit alors être considéré comme un doublon et supprimé. Ceci est utile lorsque plusieurs systèmes
produisent les mêmes produits, mais ils ne sont pas identiques au niveau des bits. Le flowcb intégré qui implémente
cette fonctionnalité est ci-dessous ::


   import logging
   from sarracenia.flowcb import FlowCB

   logger = logging.getLogger(__name__)


   class Name(FlowCB):
       """
         Remplacez la comparaison afin que les fichiers portant le même nom, quel que soit 
         le répertoire dans lequel ils se trouvent, sont considérés comme identiques.
         Ceci est utile lors de la réception de données provenant de deux sources différentes 
         (deux arbres différents) et vanner entre eux.
       """
       def after_accept(self, worklist):
           for m in worklist.incoming:
               if not 'nodupe_override' in m:
                   m['_deleteOnPost'] \|= set(['nodupe_override'])
                   m['nodupe_override'] = {}

               m['nodupe_override']['path'] = m['relPath'].split('/')[-1]
               m['nodupe_override']['key'] = m['relPath'].split('/')[-1]



Personnalisation de post_exchangeSplit
-------------------------------

La fonction ExchangeSplit permet à un seul flux d'envoyer des sorties à différents échanges,
numérotés 1...n pour assurer la répartition de la charge. Le traitement intégré le fait de manière
manière fixe basée sur le hachage du champ d'identification. Le but d'exchangeSplit est de
permettre à un ensemble commun de chemins en aval de recevoir un sous-ensemble du flux total, et pour
les produits avec un « routage » similaire atterrissent sur le même nœud en aval. Par exemple, un fichier
avec une somme de contrôle donnée, pour que le vannage fonctionne, il doit atterrir sur le même nœud en aval.

Il se pourrait que, plutôt que d'utiliser une somme de contrôle, on préfère utiliser une autre somme de contrôle.
méthode pour décider quel échange est utilisé::


  import logging
  from sarracenia.flowcb import FlowCB
  import hashlib
  logger = logging.getLogger(__name__)


  class Distbydir(FlowCB):
    """
      Remplacer l'utilisation du champ d'identité afin que les produits puissent 
      être regroupés par répertoire dans le relPath. Cela garantit que tous les produits 
      reçus du même répertoire sont publiés dans le même exchange lorsque post_exchangeSplit est actif.
    """
    def after_accept(self, worklist):
        for m in worklist.incoming:
            m['_deleteOnPost'] |= set(['exchangeSplitOverride'])
            m['exchangeSplitOverride'] = int(hashlib.md5(m['relPath'].split(os.sep)[-2]).hexdigest()[0])



Exemple de sous-classe Flowcb
-----------------------------

Il s’agit d’un exemple de fichier de classe de callback (gts2wis2.py) qui accepte les fichiers dont
les noms commencent par ceux d’AHL et renomme l’arborescence des répertoires selon une norme différente,
celui en évolution pour le WIS 2.0 de WMO (pour plus d’informations sur ce module :
https://github.com/wmo-im/GTStoWIS2) ::

  import json
  import logging
  import os.path

  from sarracenia.flowcb import FlowCB
  import GTStoWIS2

  logger = logging.getLogger(__name__)


  class GTS2WIS2(FlowCB):

    def __init__(self, options):

        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)
        self.topic_builder=GTStoWIS2.GTStoWIS2()
        self.o = options


    def after_accept(self, worklist):

        new_incoming=[]

        for msg in worklist.incoming:

            # fix file name suffix.
            type_suffix = self.topic_builder.mapAHLtoExtension( msg['new_file'][0:2] )
            tpfx=msg['subtopic']
    
            # input has relpath=/YYYYMMDD/... + pubTime
            # need to move the date from relPath to BaseDir, adding the T hour from pubTime.
            try:
                new_baseSubDir=tpfx[0]+msg['pubTime'][8:11]
                t='.'.join(tpfx[0:2])+'.'+new_baseSubDir
                new_baseDir = msg['new_dir'] + os.sep + new_baseSubDir
                new_relDir = 'WIS' + os.sep + self.topic_builder.mapAHLtoTopic(msg['new_file'])
                msg['new_dir'] = new_baseDir + os.sep + new_relDir
                msg.updatePaths( self.o, new_baseDir + os.sep + new_relDir, msg['new_file'] )

            except Exception as ex:
                logger.error( "skipped" , exc_info=True )
                worklist.failed.append(msg)
                continue
    
            msg['_deleteOnPost'] |= set( [ 'from_cluster', 'sum', 'to_clusters' ] )
            new_incoming.append(msg)

        worklist.incoming=new_incoming 

La routine *after_accept* est l’une des deux plus courantes en cours d’utilisation.La routine *after_accept* est l’une des deux plus courantes en cours d’utilisation.

La routine after_accept a une boucle externe qui parcourt l’ensemble de la
liste des messages de notification entrants. Le traitement normal est qu’il construit une nouvelle liste de
messages de notification entrants, en ajoutant tous les messages rejetés à *worklist.failed.* La
liste est juste une liste de messages de notification, où chaque message de notification est un dictionnaire python avec
tous les champs stockés dans un message de notification au format v03. Dans le message de notification, il y a,
par exemple, les champs *baseURL* et *relPath* :

* baseURL - baseURL de la ressource à partir duquel un fichier serait obtenu.
* relPath - le chemin d’accès relatif à ajouter à baseURL pour obtenir l’URL de téléchargement complet.

Cela se produit avant que le transfert (téléchargement ou envoi, ou traitement) du fichier
se soit produit, de sorte que l’on peut changer le comportement en modifiant les champs dans le message de notification.
Normalement, les chemins de téléchargement (appelés new_dir et new_file) refléteront l’intention
pour faire un mirroir à l’arborescence de source d’origine. Donc si vous avez *a/b/c.txt* sur l’arborescence source, et
vous téléchargez dans le répertoire *mine* sur le système local, la new_dir serait
*mine/a/b* et new_file serait *c.txt*.

Le plugin ci-dessus modifie la mise en page des fichiers à télécharger, en fonction de la classe
`GTStoWIS <https://github.com/wmo-im/GTStoWIS>`_, qui prescrit une arborescence de répertoires
différente en sortie.  Il y a beaucoup de champs à mettre à jour lors de la modification de placement de fichier,
il est donc préférable d’utiliser::

   msg.updatePaths( self.o, new_dir, new_file )

pour mettre à jour correctement tous les champs nécessaires dans le message de notification. Cela mettra à jour
'new_baseURL', 'new_relPath', 'new_subtopic' à utiliser lors de l’affichage.

La partie try/except de la routine traite le cas ou un fichier pourrait arriver
avec un nom à partir duquel une arborescence de topic ne peut pas être générée, puis une exception
peut se produire et le message de notification est ajouté à la liste de travail ayant échoué et ne sera pas
traité par des plugins ultérieurs.

Autres exemples
---------------

La sous-classification de Sarracenia.flowcb est utilisée en interne pour effectuer beaucoup de travail de base.
C’est une bonne idée de regarder le code source de sarracenia lui-même. Par exemple:

* sr3 list fcb est une commande pour répertorier toutes les classes de rappel incluses dans le package metpx-sr3.

* *sarracenia.flowcb* jetez un coup d’œil dans le fichier __init__.py qui s’y trouve,
  qui fournit ces informations sur un format plus succinct.

* *sarracenia.flowcb.gather.file.File* est une classe qui implémente la publication de fichiers
  et la surveillance de répertoires, dans le sens d’un callback qui implémente le point d’entrée
  *gather*, en lisant un système de fichiers et en créant une liste de messages de notification à traiter.

* *sarracenia.flowcb.gather.message.Message* est une classe qui implémente la réception des messages
  de notification à partir des flux de protocole de fil d’attente de messages.

* *sarracenia.flowcb.nodupe.NoDupe* Ce module supprime les doublons des flux de messages en fonction
  des sommes de contrôle d’intégrité.

* *sarracenia.flowcb.post.message.Message* est une classe qui implémente la publication de messages
  de notification dans les flux de protocole de fil d’attente de messages

* *sarracenia.flowcb.retry.Retry* lorsque le transfert d’un fichier échoue, Sarracenia doit conserver
  le message de notification correspondant dans un fichier d’état pour une période ultérieure lorsqu’il
  pourra être réessayé. Cette classe implémente cette fonctionnalité.


Modification de fichiers en transit
-----------------------------------

La classe *sarracenia.transfer* inclu un point d'entrée *on_data* qui permet de transformer
des données durant un transfer::


    def on_data(self, chunk) -> bytes:
        """
            transform data as it is being read. 
            Given a buffer, return the transformed buffer. 
            Checksum calculation is based on pre transformation... likely need
            a post transformation value as well.
        """
        # modify the chunk in this body...
        return chunk

   def registered_as():
        return ['scr' ]

   # copied from sarracenia.transfer.https

   def connect(self):

        if self.connected: self.close()

        self.connected = False
        self.sendTo = self.o.sendTo.replace('scr', 'https', 1)
        self.timeout = self.o.timeout

        if not self.credentials(): return False

        return True
        
Pour effectuer la modification des données en vol, on peut sous-classer la classe de transfert pertinente.
Une telle classe (scr - strip retour chariot) peut être ajoutée en mettant un import dans la configuration
dossier::

   import scr.py

alors les messages où l'url de récupération est définie pour utiliser le schéma de récupération *scr* utiliseront ce
protocole de transfert personnalisé.


flots modifiés
--------------

Si aucun des composants intégrés ( poll, post, sarra, shovel, subscribe, watch, winnow ) n'a le
comportement souhaité, on peut créer un composant personnalisé pour faire ce qu'il faut en sous-classant le flux.

Copiez l'une des sous-classes de sarracenia.flow à partir du code source et modifiez-la à votre goût. Dans la configuration
fichier, ajoutez la ligne ::

   flowMain MaComposant

pour que le flux utilise le nouveau composant.

