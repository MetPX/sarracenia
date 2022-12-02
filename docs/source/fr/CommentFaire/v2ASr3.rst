
===============================
Portage des plugins V2 vers Sr3
===============================

Ceci est un guide pour porter des plugins de Sarracenia version 2.X (metpx-sarracenia) vers
Sarracenia version 3.x (metpx-sr3)

.. Contenu ::

.. note :: Si vous êtes nouveau sur Sarracenia, et que vous n’avez aucune expérience ou besoin de regarder les plugins v2,
   ne lisez pas ceci. cela ne fera que vous confondre. **Ce guide s’adresse à ceux qui ont besoin de prendre des
   Plugins v2 et les porter à Sr3.** Vous feriez mieux d’obtenir un nouveau regard en regardant le
   `jupyter notebook examples <../Tutorials>`_ qui fournissent une introduction à la v3 sans
   les références déroutantes à la v2.

.. note :: Même si vous avez réellement besoin de porter des plugins v2 vers sr3, vous devriez toujours être
   familier avec les plugins sr3 avant d'essayer d'en porter un. Ressources pour cela :

   `Guide de Programmation <../Explication/SarraPluginDev.html>`_

    Les `exemples de jupyter notebook <.. /Tutorials>`_ sont probablement un bon pré-requis pour tout 
    le monde, pour comprendre comment fonctionnent les plugins Sr3, avant d’essayer de porter ceux de la v2.

`Exemple de plugin Sr3 <../Reference/flowcb.html#module-sarracenia.flowcb.log>`_

D’une manière générale, les plugins v2 ont été rajouté sur le code existant pour permettre certaines modifications
de comportement. Les plugins V2 de première génération n’avaient que des routines uniques déclarées
(par exemple *on_message*), alors que ceux de la deuxième génération utilisaient des classes entières
(par exemple *plugin*) ont été déclarés, mais toujours sur pilotis.

Les plugins Sr3 sont des éléments de conception de base, composés ensemble pour implémenter une partie de
Sarracenia. Les plugins V3 devraient être plus faciles à implémenté et à déboguer pour les programmeurs Python,
et sont plus flexibles et puissants que le mécanisme de v2.

 * v3 utilise la syntaxe standard de python, pas l’étrange *self.plugins*, *parent.logger*, de la v2,
   et oh gee pourquoi *import* ne fonctionne-t-il pas?
 * Importations python standard; Les erreurs de syntaxe sont détectées et signalées *de la manière normale*
 * Les classes v3 sont conçues pour être utilisables en dehors de l’interface de ligne de commande elle-même
   (voir les exemples de jupyter notebook)
   appelable par les programmeurs d’applications dans leur propre code, comme toute autre bibliothèque python.
 * Les classes v3 peuvent être sous-classées pour ajouter des fonctionnalités de base, comme un nouveau message
   de notification ou un protocole de transport de fichier.

.. astuce::
  Il existe également quelques vidéos pas à pas sur Youtube montrant des ports simples v2 -> v3:
   - `Sender (10 min) <https://www.youtube.com/watch?v=rUazjoGzPac>`_
   - `Poll (20 min) <https://www.youtube.com/watch?v=P20M9ojn_Zw>`_

Placement de Fichier
--------------------

v2 place les fichier de configuration sous ~/.config/sarra, et les fichiers d'état sous ~/.cache/sarra

v3 place les fichier de configuration sous ~/.config/sr3, et les fichiers d'état sous ~/.cache/sr3

v2 a une implémentation C de sarra appelée sarrac. L’implémentation C pour v3, est appelée sr3c,
et est identique à celui de la v2, sauf qu’il utilise les emplacements de fichiers v3.

Différence de ligne de commande
-------------------------------

En bref, le point d’entrée sr3 est utilisé pour démarrer / arrêter / évaluer les choses::

  v2:  sr_*component* start config

  v3:  sr3 start *component*/config

Dans sr3, on peut également utiliser des spécifications de style de globbing de fichier pour demander qu'une commande
soit invoqué sur un groupe de configurations, alors que dans la v2, on ne pouvait fonctionner que sur une à la fois.

.. caution::
  **sr3_post** est une exception à ce changement parce qu'il fonctionne comme sr_post de la v2, étant
  un outil d’affichage interactif.

Ce qui fonctionnera sans changement
-----------------------------------

La première étape du portage d’une configuration subscribe/X vers v3, consiste simplement à copier le
fichier de configuration de ~/.config/sarra à l’emplacement correspondant dans ~/.config/sr3 et essayez::

   sr3 show subscribe/X

La commande *show* est nouvelle dans sr3 et permet d’afficher la configuration après
avoir été analysé. La plupart d’entre eux devraient fonctionner, sauf si vous avez des plugins do_*.

Exemples de choses qui devraient fonctionner:

* tous les paramètres des fichiers de configuration v2 doivent être reconnus par l’analyseur d’options v3 et convertis
  aux équivalents v3, c’est-à-dire :

  ========================== ===============
  Option v2                  Option v3
  ========================== ===============
  accept_scp_threshold       accel_threshold
  heartbeat                  housekeeping
  chmod_log                  permLog
  loglevel                   logLevel
  post_base_url              post_baseUrl
  post_rate_limit            messageRateMax
  cache, suppress_duplicates nodupe_ttl
  topic_prefix               topicPrefix 
  ========================== ===============

  Pour la liste complète, consultez le `Release Notes <UPGRADING.html>`_

  Le topic_prefix dans la v2 est 'v02.post' dans la v3, la valeur par défaut est 'v03'. Si topic_prefix est omis
  vous devrez ajouter la ligne *topicPrefix v02.post* pour obtenir le même comportement que la v2. Pourrais
  être également placé dans ~/.config/sr3/default.conf si le cas est trop courant.
  Il se peut que l’on doive remplacer de la même manière la valeur par défaut sr3 pour post_topicPrefix.

* toutes les routines on_message, on_file, on_post, on_heartbeat, fonctionneront, par sr3 en utilisant
  le plugin flowcb/v2wrapper.py qui sera automatiquement appelé lorsque les plugins v2 sont
  lu dans le fichier de configuration.

.. Note:: Idéalement, v2wrapper est utilisé comme béquille pour permettre d’avoir une configuration fonctionnelle
  rapidement. Il y a un succès de performance à l’utilisation de v2wrapper.


Ce qui ne fonctionnera pas sans changement
------------------------------------------

* do_* ils sont juste fondamentalement différents dans la v3.

Si vous avez une configuration avec un plugin do_*, vous avez besoin de ce guide, à partir du jour 1.
pour définir une configuration pour utiliser un plugin, dans la v2 on utilisait l’option *plugin* ::

   plugin <pluginName>

L’équivalent de celui de la v3 est *callback*::

   callback <pluginName>

Pour que ce raccourci fonctionne, il devrait y avoir un fichier nommé <pluginName>.py quelque part dans le
PYTHONPATH (~/.config/plugins est ajouté pour plus de commodité.) et ce fichier source python a besoin
qu’une classe <PluginName> y soit déclarée (identique au nom du fichier mais avec la première lettre en majuscule).
Si vous devez le nommer différemment, il existe un formulaire plus long qui permet de violer la
convention dans v3::

  flowCallback <pluginName>.MyFavouriteClass

les déclarations de plugins de routine individuelles on_message, on_file, etc... ne sont pas un moyen de
faire les choses dans la v3. Vous déclarez des rappels et leur demandez de contenir les points d’entrée dont vous avez besoin.

* DESTFNSCRIPT fonctionne de manière similaire dans v3 à v2, mais l’API est faite pour correspondre v3 flowCallbacks,
les nouvelles routines, ou on renvoie le nouveau nom de fichier en sortie, au lieu de modifier un champ
dans le message de notification.


Différences de codage entre les plugins dans v2 vs Sr3
------------------------------------------------------

L’API pour ajouter ou personnaliser des fonctionnalités dans sr3 est très différente de la v2.
En général, les plugins v3:

* **sont généralement sous-classés à partir de sarracenia.flowcb.FlowCB.**

  Dans la v2, on déclarerait::

      class Msg_Log(object): 

  Les plugins v3 sont des fichiers sources python normaux (pas de magie à la fin.)
  ils sont sous-classés à partir de sarracenia.flowcb::

      from sarracenia.flowcb import FlowCB

      class MyPlugin(FlowCB):
        ...le reste de la classe de plugin..
        
         def after_accept(self, worklist):
           ...code à exécuter dans callback...

  Pour créer un plugin *after_accept* dans la classe *MyPlugin*, définissez une fonction
  avec ce nom et la signature appropriée.

* Les plugins v3 **sont pythoniques, pas bizarres** :
  Dans la v2, vous avez besoin que la dernière ligne pour inclure quelque chose comme ::

     self.plugin = 'Msg_Delay'

  ceux de la première génération à la fin avaient quelque chose comme ceci pour attribuer explicitement des points d’entrée::

      msg_2localfile = Msg_2LocalFile(None)
      self.on_message = msg_2localfile.on_message

  Quoi qu’il en soit, une partie python naïve du fichier échouerait invariablement sans qu’une sorte de
  harnais de test ne soit enroulée autour d’elle.

  .. Astuce:: Dans la v3, supprimez ces lignes (généralement situées au bas du fichier)

  Dans la v2, il y avait des problèmes étranges avec les importations, ce qui a entraîné la mise en place
  d'importer des instructions à l’intérieur des fonctions. Ce problème est résolu dans la v3, vous pouvez
  vérifier votre syntaxe d’importation en faisant *import X* dans n’importe quel interpréteur python.

  .. Astuce:: Placez les importations nécessaires au début du fichier, comme tout autre module python
           **et supprimez les importations situées dans les fonctions lors du portage**.

* **Les plugins v3 peuvent être utilisés par les programmeurs d’applications.** Les plugins ne sont pas
  boulonné, mais un élément central, implémentant la suppression de doublon, réception et transmission de messages
  de notification, surveillance de fichiers, etc.. comprendre les plugins v3 donne aux gens des indices
  importants pour être capable de travailler sur sarracénia.

  Les plugins v3 peuvent être *importés* dans des applications existantes pour ajouter la possibilité
  d'interagir avec les pompes sarracenia sans utiliser l’interface de ligne de commande Sarracenia.
  voir les tutoriels jupyter.

* Les plugins v3 utilisent maintenant **la journalisation python standard** ::

      import logging
  
  Assurez-vous que la déclaration d’enregistreur suivante se trouve après le **last _import_** en haut du plugin v3 ::

      logger = logging.getLogger(__name__)

      # To log a notification message:
      logger.debug( ... )
      logger.info( ... )
      logger.warning( ... )
      logger.error( ... )
      logger.critical( ... )
      
  Lors du portage des plugins v2 -> v3 : *logger.x* remplace *parent.logger.x*.
  Parfois, il y a aussi self.logger x... je ne sais pas pourquoi... ne demandez pas.
  
  .. Astuce:: Dans vi, vous pouvez utiliser le remplacement global pour effectuer un travail rapide lors du portage::
  
             :%s/parent.logger/logger/g

* En v2, **parent** est un gâchis. L'objet *self* variait en fonction des points d'entrée
  appelé. Par exemple, *self* dans __init__ n'est pas identique à *self* dans on_message. En conséquence, tous les 
  variables d´états doivent être stocké dans le parent. l'objet parent contient des options, des paramètres et 
  les variable d´instance de la classe qui appelle le plugin.

  Pour les attributs réels, sr3 fonctionne désormais comme les programmeurs python s'y attendent : self, 
  est le même self, dans __init__() et tous les autres points d'entrée, donc on peut définir des variables
  d'état pour le plugin en utilisant les attributs self.x dans le code du plugin.

* Les plugins v3 *ont des options comme argument pour le __init__ (self, options): routine* plutôt
  que dans la v2 où ils se trouvaient dans l’objet parent. Par convention, dans la plupart des modules, la
  fonction __init__ comprend un::

       self.o = options
       self.o.add_option('OptionName', Type, DefaultValue)
       
  .. Astuce:: Dans VI, vous pouvez utiliser le remplacement global::
  
             :%s/parent/self.o/g


* **vous pouvez voir quelles options sont actives en démarrant un composant avec la commande 'show'** ::

      sr3 show subscribe/myconf

  ces paramètres sont accessibles à partir de self.o

* Dans les paramètres sr3, **recherchez le remplacement de nombreux traits de soulignement par le camelCase**
  
  
  correspondre à l’intention.  ainsi:
    *  custom_setting_thing -> customSettingThing
    *  post_base_dir -> post_baseDir
    *  post_broker est inchangé.
    *  post_base_url -> post_baseUrl

* Dans la v2, *parent.msg* stockait les messages, avec certains champs comme attributs intégrés et d'autres comme en-têtes.
  Dans la v3 **les messages de notification sont maintenant des dictionnaires python** , donc un `msg.relpath` v2 devient `msg['relPath']` dans la v3.

  plutôt que d'être transmis via le parent, il existe une option *worklist* transmise aux points d'entrée du plugin qui manipulent
  messages. par exemple, un *on_message(self,parent)* dans un plugin v2 devient un *after_accept(self,worklist)* dans sr3.
  la liste de travail.incoming contient tous les messages qui ont passé le filtrage d'acceptation/rejet et seront traités
  (pour télécharger, envoyer ou publier) donc la logique ressemblera à ::


     for msg in worklist.incoming:
         do the same logic as in the v2 plugin. 
         for one message at a time in the loop.

  les mappages de tous les points d'entrée sont décrits dans `Mappage des points d'entrée v2 aux rappels v3`_
  section plus loin dans ce document

  Chaque message de notification v3 agit comme un dictionnaire python. Ci-dessous un mappage de table
  champs de la représentation sarra v2 à celle de sr3 :

  ================ =================== ===========================================================
  v2               sr3                 Notes
  ================ =================== ===========================================================
  msg.pubtime      msg['pubTime']      quand le message a été initialement publié 
  msg.baseurl      msg['baseUrl']      racine de l'arborescence url du fichier annoncé.
  msg.relpath      msg['relPath']      chemin relatif concaténé à baseUrl pour le chemin canonique
  *no equivalent*  msg['retPath']      chemin opaque pour remplacer le chemin canonique.
  msg.notice       pas disponible      calculé à partir d'un autre champ sur l'écriture v2
  msg.new_subtopic msg['new_subtopic'] à éviter en sr3, champ calculé à partir de relPath
  msg.new_dir      msg['new_dir']      nom de répertoire où le fichier sera écrite.
  msg.new_file     msg['new_file']     nom de fichier à écrire en new_dir.
  msg.headers      msg                 pour les champs variables/optionnels. 
  msg.headers['x'] msg['x']            un message est un dict python
  msg.message_ttl  msg['message_ttl']  le même option de réglage.
  msg.exchange     msg['exchange']     le canal sur lequel le message à été reçu.
  msg.logger       logger              les journeaux fonctionnent ¨normalement" pour python
  msg.parts        msg['size']         oublie ca, utilise une constructeur de sarracenia.Message
  msg.sumflg       msg['integrity']    oublie ca, utilise une constructeur de sarracenia.Message
  parent.msg       worklist.incoming   sr3 traite des groupe des messages, pas individuelement
  ================ =================== ===========================================================

* pubTime, baseUrl, relPath, retPath, size, integrity, sont tous des champs de message standard
  mieux décrit dans `sr_post(7) <../Reference/sr_post.7.html>`_

* si l'on a besoin de stocker par état de message, alors on peut déclarer des champs temporaires dans le message,
  qui ne seront pas transmis lors de la publication du message. Il y a un champ défini *msg['_deleteOnPost']* ::

      msg['my_new_field'] = my_new_value
      msg['_deleteOnPost'] |= set(['my_new_field'])

  Sarracenia supprimera le champ donné du message avant de le publier pour les consommateurs en aval.

* dans les anciennes versions de v2 (<2.17), il y avait msg.local_file, et msg.remote_file, certains anciens plugins peuvent contenir
  ce. Ils représentaient la destination dans les cas d'abonnement et d'expéditeur, respectivement.
  les deux ont été remplacés par new_dir concaténé avec new_file pour couvrir les deux cas.
  la séparation du répertoire et du nom de fichier a été considérée comme une amélioration.

* dans la v2 *parent* était l'objet sr_subscribe, qui avait toutes ses variables d'instance, dont aucune
  étaient destinés à être utilisés par des plugins. Dans les fonctions du plugin __init__(), elles 
  peuvent être référencées en tant que *soi* plutôt que *parent* :

  ====================== ===================== ===================================================
  v2                     sr3                   Notes
  ====================== ===================== ===================================================
  parent.currentDir      msg['new_dir'] ?      répertoire *courant*... ca dépend... 
  parent.masks           *none*                valeur interne de la class sr_subscribe
  parent.program_name    self.o.program_name   nom de la programme qui execute e.g. 'sr_subscribe'
  parent.consumer        *none*                ivaleur interne de la class sr_consumer
  parent.publisher       *none*                instance de Publisher de sr_amqp.py
  parent.post_hc         *none*                instance de HostConnect class from sr_amqp.py
  parent.cache           *none*                cache pour mémoriser les fichiers traités.
  parent.retry           *none*                fil d´attente pour les ressais.
  ====================== ===================== ===================================================

  Il existe des dizaines (des centaines ?) de ces attributs qui étaient destinés à servir de données internes au
  sr_subscribe et ne devrait pas vraiment être disponible pour les plugins.
  La plupart d'entre eux n'apparaissent pas, mais si un développeur a trouvé quelque chose, il peut être présent.
  Difficile de prédire ce qu'un développeur de plugin utilisant l'une de ces valeurs attendait.

* Dans la v3 **les messages de notification sont maintenant des dictionnaires python** , donc `msg.relpath` dans v2
  devient `msg['relPath']` dans la v3. Les messages de notification v3, car les dictionnaires sont la
  représentation interne par défaut.

* Dans la v3 **les plugins fonctionnent sur des lots de messages de notification**. v2 *on_message* obtient parent
  comme paramètre, et le message de notification se trouve dans parent.message. Dans la v3, *after_accept* a worklist
  comme option, qui est la liste python des messages, la longueur maximale étant fixée par l'option
  *batch*. Donc, l’organisation générale pour after_accept, et after_work est::

      new_incoming=[]
      for message in old_list:
          if good:
             new_incoming.append(message)
          if bad:
             worklist.rejected.append(message)
      worklist.incoming=new_incoming


  .. Note:: les plugins doivent être déplacés du répertoire /plugins vers le répertoire /flowcb,
            et plus précisément, les plugins on_message qui se transforment en plugins after_accept devraient être
            placé dans le répertoire flowcb/accept (afin que les plugins similaires puissent être regroupés).

  Dans *after_work*, le remplacement de *on_file* dans v2, les opérations sont sur :

  * worklist.ok (transfert réussi.)
  * worklist.failed (transferts ayant échoué.)

  Dans le cas de la réception d’un fichier .tar et de l’extension à des fichiers individuels,
  la routine *after_work* modifierait le fichier worklist.ok pour qu’il contienne des messages de notification pour
  les fichiers individuels, plutôt que les .tar collectifs d’origine.

  .. Note:: les plugins on_file qui deviennent des plugins after_work doivent être placés dans le
            répertoire /flowcb/after_work

* v3 a **pas besoin de définir des champs de message de notification dans les plugins**
  dans la v2, il faudrait définir partstr, et sumstr pour les messages de notification v2 dans les plugins.
  Cela nécessitait une compréhension excessive des formats de message de notification et signifiait que la
  modification des formats de message de notification demande de modifier les plugins (le format de message de
  notification v03 est non pris en charge par la plupart des plugins v2, par exemple). 

 La manipulation de ces champs manuellement est activement contre-productif.
 La somme de contrôle est déjà effectuée lorsque le nouveau message de notification est généré, donc très probablement
 tous les champs de message tels que **sumalgo** et d'autres champs **algo** peuvent être ignorés.

  Pour créer un message de notification à partir d’un fichier local dans un plugin v3 ::

     import sarracenia

     m = sarracenia.Message.fromFileData(sample_fileName, self.o, os.stat(sample_fileName) )

  juste a regarder `do_poll -> poll`_

* les plugins v3 **impliquent rarement la sous-classification des classes de Moth ou de Transfer.**
  La classe sarracenia.moth implémente un support pour les protocoles de mise en fil d’attente
  des messages de notification qui prennent en charge les abonnements basés sur la hiérarchie des topics.
  Il y a actuellement deux sous-classes de Moth: amqp (pour rabbitmq) et mqtt.  Ce serait
  idéal pour quelqu’un d’ajouter un amq1 (pour le support qpid amqp 1.0.)

  Il peut être raisonnable d’y ajouter une classe SMTP pour l’envoi d’e-mails,
  Pas sûr.

  Les classes sarracenia.transfer incluent http, ftp et sftp aujourd’hui.
  Elles sont utilisés pour interagir avec des services distants qui fournissent une interface de fichier
  (prise en charge de choses comme la liste des fichiers, le téléchargement et / ou l'envoi.)
  D’autres sous-classes telles que S3, IPFS ou webdav, seraient des ajouts excellents.

Fichiers de configuration
-------------------------

Dans la v2, l’option de configuration principale pour déclarer un plugin est ::

   plugin X

D’une manière générale, il devrait y avoir un fichier plugins/x.py
avec une classe X.py dans ce fichier dans ~/.config/plugins
ou dans le répertoire sarra/plugins dans le paquet lui-même.
Il s’agit déjà d’un style de déclaration de plugin de deuxième génération
dans Sarracenia. La version originale, une personne déclare des points d’entrée individuels ::

    on_message, on_file, on_post, on_..., do_... 

Dans Sr3, les entrées ci-dessus sont considérées comme des demandes pour des plugins de v2,
et doit être utilisé que pour des raisons de continuité.
Idéalement, on devrait appeler les plugins v3 comme suit::

   callback x

Où x sera une sous-classe de sarracenia.flowcb, qui
contiendra une classe X (première lettre en majuscule) dans le
fichier x.py quelque part dans le chemin de recherche python, ou dans le répertoire
*sarracenia/flowcb* qui est inclus dans le package.
Il s’agit en fait d’une version abrégée de l’importation python.
Si vous devez déclarer un rappel qui n’obéit pas à cette
convention, on peut aussi utiliser un manière plus flexible mais plus longue::

  flowcb sarracenia.flowcb.x.X

les deux ci-dessus sont équivalents. La version flowcb peut être utilisée pour importer des classes
qui ne correspondent pas à la convention du x.X (un fichier nommé x.py contenant une classe appelée X)

Mise à niveau de la configuration
---------------------------------

Une fois qu’un plugin est porté, on peut également faire en sorte que l’analyseur d’options v3 reconnaisse une
invocation de plugin de v2 et la remplace par une invocation v3. En regardant dans /sarracenia/config.py#L144,
il existe une structure de données *convert_to_v3*.  Voici un exemple d’entrée ::

    .
    .
    .
    'on_message' : {
             'msg_delete': [ 'flowCallback': 'sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles' ]
    .
    .
    .


Un fichier de configuration v2 contenant une ligne *on_message msg_delete* sera remplacé par l’analyseur avec ::

    flowCallback sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles




Options
-------

Dans la v2, on déclarerait les paramètres à utiliser par un plugin dans la routine __init__, avec
le *declare_option*.::

    parent.declare_option('poll_usgs_stn_file')

Les valeurs sont toujours de type *list*, donc généralement, on utilise la valeur en choisissant la première valeur::

    parent.poll_usgs_stn_file[0]

Dans la v3, cela serait remplacé par ::

    self.o.add_option( option='poll_usgs_stn_file', kind='str', default_value='hoho' )

Dans la v3 il y a maintenant des types (comme on le voit dans le fichier sarracenia/config.py#L777) et le paramètre
de valeur par défaut est inclus sans code supplémentaire. Il serait mentionné dans d’autres routines comme celle-ci::

    self.o.poll_usgs_stn_file

Mappage des points d’entrée v2 aux Callbacks v3
-----------------------------------------------

Pour un aperçu complet des points d’entrée v3, jetez un coup d’œil :
https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/__init__.py

pour plus de détails.

on_message, on_post --> after_accept
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
v2 : reçoit un message de notification, renvoie True/False

v3: reçoit worklist
    modifie worklist.incoming
    transfert des messages de notification rejetés vers worklist.rejected ou worklist.failed.

Flux d’échantillon::

  def after_accept(self, worklist):

     ...

     new_incoming=[]
     for m in worklist.incoming:

          if message is useful to us:
             new_incoming.append(m)
          else
             worklist.rejected.append(m)        
 
     worklist.incoming = new_incoming



exemples:
  v2: plugins/msg_gts2wistopic.py
  v3: flowcb/wistree.py


on_file --> after_work
~~~~~~~~~~~~~~~~~~~~~~

v2 : reçoit un message de notification, renvoie True/False

v3: reçoit worklist
    modifie worklist.ok (transfer has already happenned.)
    transfert des messages de notification rejetés vers worklist.rejected ou worklist.failed.

    peut également être utilisé pour travailler sur worklist.failed (la logique de retry le fait.)

exemples:

.. Danger:: IL N’Y A PAS D’EXEMPLES?!?!
            TODO: ajouter quelques exemples


on_heartbeat -> on_housekeeping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

v2: reçoit le parent comme argument.
    fonctionnera inchangé.

v3: ne reçoit que self (qui devrait avoir self.o qui remplaçe le parent)

exemples:

  * v2: hb_cache.py -- nettoie la cache (références sr_cache.)
  * v3: flowcb/nodupe.py -- implémente toute la routine de mise en cache.



do_poll -> poll
~~~~~~~~~~~~~~~

v2: appelez do_poll à partir du plugin.

 * le protocole d’utilisation de la routine do_poll est identifié par le point d’entrée registered_as()
    qui est obligatoire à fournir.
 * nécessite la construction manuelle de champs pour les messages de notification, est-ce que la vérification du message de notification est spécifique,
   (ne prennent généralement pas en charge les messages de notification v03.)
 * appelle explicitement les points d’entrée du poll.
 * fonctionne, il faut s’inquiéter de savoir si on a le vip ou non pour décider quel traitement
   à faire dans chaque plugin.
 * paramètre poll_without_vip disponible.


v3: définir poll dans une classe flowcb.

 * le sondage n’est exécuté que lorsque has_vip est true.

 * le point d’entrée registered_as() est discutable

 * toujours rassembler les exécutions, et est utilisé pour s’abonner à post effectuée par le nœud qui a le vip,
   permettant a la cache nodupe d’être maintenu à jour.

 * API définie pour créer des messages de notification à partir de données de fichier, quel que soit le format du message de notification.

 * renvoie une liste de messages de notification à filtrer et à publier.

Pour créer un message de notification, sans fichier local, utilisez fromFileInfo sarracenia.message factory::

  
     import dateparser
     import paramiko
     import sarracenia

     gathered_messages=[]

     m = sarracenia.Message.fromFileInfo(sample_fileName, cfg)

génère un message de notification à partir de zéro.

On peut également construire et fournir un enregistrement de statistiques simulé à partir de l’usine fromFileInfo,
en utilisant la classe *paramiko.SfTPAttributes()*. Par exemple, en utilisant
les routines dateparser pour convertir. Toutefois, le serveur distant répertorie également la date et l’heure, et
détermine la taille du fichier et les autorisations en vigueur ::

     pollmtime = dateparser.parse( ... , settings={ ... TO_TIMEZONE='utc' } )
     mtimestamp = time.mktime( pollmtime.timetuple() )

     fsize = info_from_poll #about the size of the file to download
     st = paramiko.SFTPAttributes()
     st.st_mtime=mtimstamp
     st.st_atime=mtimestamp
     st.st_size=fsize
     st.st_mode=0o666 
     m = sarracenia.Message.fromFileInfo(sample_fileName, cfg, st)

Il faut remplir l’enregistrement *SFTPAttributes* si possible, puisque le doublon
de cache utilise les métadonnées si elles sont disponibles. Plus les métadonnées sont bonnes, le mieux est la
détection des modifications apportées aux fichiers existants.

Une fois le message de notification généré, ajoutez-le à la liste ::

     gathered_messages.append(m) 
  
et à la fin::

     return gathered_messages


Traitement IP virtuel dans le poll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dans la v2, si vous avez une séléction de vIP, tous les nœuds participants pollent le serveur en amont
et maintiennent la liste des fichiers actuels, ils ne publient tout simplement pas le résultat.
Donc, si vous avez 8 serveurs partageant un vIP, les huit sont des poll, un peu triste.
Il y a aussi le paramètre poll_no_vip, et les plugins doivent souvent vérifier s’ils
ont le vIP ou non.

Dans la v3, seul le serveur avec le vIP peux poller. Les plugins n’ont pas besoin de vérifier.
Les autres serveurs participants s’abonnent à l’endroit où le sondage est publié,
pour mettre à jour leur cache recent_files.

exemples:
 * flowcb/poll/airnow.py

on_html_page -> sous-classement de flowcb/poll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Voici un plugin v2 nsa_mls_nrt.py:

.. code-block:: python

    #!/usr/bin/env python3                                                                                                                          
                                                  
    class Html_parser():                                                                                                                            
                                                  
        def __init__(self,parent):                                                                                                                  
                                                  
            parent.logger.debug("Html_parser __init__")
            import html.parser
    
            self.parent = parent
            self.logger = parent.logger
    
            self.parser = html.parser.HTMLParser()
            self.parser.handle_starttag = self.handle_starttag
            self.parser.handle_data     = self.handle_data
    
    
        def handle_starttag(self, tag, attrs):
            for attr in attrs:
                c,n = attr
                if c == "href" and n[-1] != '/':
                   self.myfname = n.strip().strip('\t')
    
        def handle_data(self, data):
            import time
    
            if 'MLS-Aura' in data:
                   self.logger.debug("data %s" %data)
                   self.entries[self.myfname] = '-rwxr-xr-x 1 101 10 ' +'_' + ' ' + 'Jan 1 00:01' + ' ' + data
                   self.logger.debug("(%s) = %s" % (self.myfname,self.entries[self.myfname]))
            if self.myfname == None : return
            if self.myfname == data : return
            ''' 
            # at this point data is a filename like
            name = data.strip().strip('\t')
    
            parts = name.split('_')
            if len(parts) != 3 : return
    
            words = parts[1].split('.')
            sdate  = ' '.join(words[:4])
            t      = time.strptime(sdate,'%Y %j %H %M')
    
            # accept file if 1 month old in sec  60 sec* 60min * 24hr * 31days
    
            epochf = time.mktime(t)
            now    = time.time()
            elapse = now - epochf
    
            if elapse > self.month_in_secs : return
    
            # build an ls line from date in file ... size set to 0  since not provided
    
            mydate = time.strftime('%b %d %H:%M',t)
     
            mysize = '_'
     
            self.entries[self.myfname] = '-rwxr-xr-x 1 101 10 ' + mysize + ' ' + mydate + ' ' + data
            self.logger.debug("(%s) = %s" % (self.myfname,self.entries[self.myfname]))
            '''
    
        def parse(self,parent):
            self.logger.debug("Html_parser parse")
            self.entries = {}
            self.myfname = None
    
            self.logger.debug("data %s" % parent.data)
            self.parser.feed(parent.data)
            self.parser.close()
    
            parent.entries = self.entries
    
            return True
    
    html_parser = Html_parser(self)
    self.on_html_page = html_parser.parse

Le plugin a une routine principale "parse", qui appelle la classe html.parser, où data_handler
est appelé pour chaque ligne, en construisant progressivement le dictionnaire self.entries où chaque entrée est
une chaîne construite pour ressembler à une ligne de sortie de commande *ls*.

Ce plugin est une copie presque exacte du plugin html_page.py utilisé par défaut.
Le point d’entrée on_html_page pour les plugins est remplacé par un mécanisme complètement différent.
La plus grande partie de la logique du poll de v2 dans sr3 est dans la nouvelle  class sarracenia.FlowCB.Poll.
La logique des plugins/html_page.py v2, utilisés par défaut, fait désormais partie de cette
nouvelle classe Poll, sous-classée à partir de flowcb, de sorte que l’analyse HTML de base est intégrée.

Un autre changement par rapport à la v2 est qu’il y avait beaucoup plus de manipulation de chaînes dans l’ancienne
version. Dans les poll sr3, la plupart des maniupulations de chaînes ont été remplacées par le remplissage d’une
structure paramiko.SFTPAttribute dès que possible.

Donc, la façon de remplacer on_html_page dans sr3 est de sous-classer Poll. Voici une
version sr3 du même plugin (nasa_mls_nrt.py):

.. code-block:: python

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
                   #self.entries[self.myfname] = '-rwxr-xr-x 1 101 10 ' +'_' + ' ' + 'Jan 1 00:01' + ' ' + data
                   self.entries[data]=st
    
                   logger.info("(%s) = %s" % (self.myfname,st))
            if self.myfname == None : return
            if self.myfname == data : return

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/nasa_mls_nrt.py )
et le fichier de configuration correspondant fourni ici :
( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/examples/poll/nasa-mls-nrt.conf )

La nouvelle classe est déclarée comme une sous-classe de Poll, et seule la classe nécessaire
de routine HTML (handle_data) doit être écrite pour remplacer le comportement
fourni par la classe parente.

Cette solution est inférieure à la moitié de la taille de celle de la v2 et permet
toutes sortes de flexibilité en permettant le remplacement de tout ou une seule partie des éléments
de la classe de poll.

on_line -> sous-classement de poll
----------------------------------

Comme on_html_page ci-dessus, toutes les utilisations de on_line dans la version précédente
concernaient le reformatage des lignes pour qu’elles puissent être analysées. La routine on_line peut être
sous-classé de la même manière pour le remplacer.  Il fallait modifier la chaîne parent.line
pour qu'elle soit analysable par l’analyse de ligne de style *ls* intégrée.

Dans sr3, on_line devrait renvoyer un  champ paramiko.SFTPAttributes rempli, similaire
à la façon dont on_html_page fonctionne (mais seulement un seul au lieu d’un dictionnaire d’entre eux.)
Avec l’analyse de date plus flexible dans sr3, il n’y a pas le besoin d'identifié de on_line
sur lequel construire un exemple.

do_send -> send:
----------------

v2 : do_send peut être une routine autonome ou associée à un type de protocole

* basé sur registered_as() afin que la destination détermine si elle est utilisée ou non.

* accepte parent comme argument.

* renvoie True en cas de réussite, False en cas d’échec.

* aura généralement un point d’entrée registered_as() pour indiquer les protocoles pour lesquels utiliser un sender.

v3: send(self,msg)

* utilisez le msg fourni pour effectuer l’envoi.

* renvoie True en cas de réussite, False en cas d’échec.

* registered_as n’est plus utilisé, peut être supprimé.

* Le entry_point d’envoi remplace tous les envois et n’est pas spécifique au protocole.
  Pour ajouter la prise en charge de nouveaux protocoles, il faut sous-classer sarracenia.transfer à la place.

exemples:
  * flowcb/send/email.py


do_download -> download:
------------------------
créer une classe flowCallback avec un point d’entrée *download*.

* accepte un seul message de notification comme argument.

* renvoie la valeur True si le téléchargement réussit.

* s’il renvoie False, la logique de nouvelle tentative s’applique (le téléchargement sera appelé à nouveau
  puis placé dans la fil d’attente de nouvelles tentatives, retry queue.)

* utiliser msg['new_dir'], msg['new_file'], msg['new_inflight_path']
  pour respecter les paramètres tels que *inflight* et placer le fichier correctement.
  (à moins que changer cela soit la motivation du plugin.)

* peut être une bonne idée de vérifier la somme de contrôle des données téléchargées.
  Si la somme de contrôle du fichier téléchargé n’est pas en accord avec ce qui se trouve dans
  le message de notification, la suppression des doublons échoue et ca boucle.

* un cas de téléchargement est lorsque retrievalURL n’est pas un téléchargement de fichier normal.
  Dans v03, il existe des champs retPath pour exactement ce cas. Cette nouvelle fonctionnalité
  peut être utilisé pour éliminer le besoin de plugins de téléchargement.  Exemple:

  Dans la v2:

      * https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/poll_noaa.py 

      * https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/download_noaa.py

  est porté sur sr3 :

      * https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/noaa_hydrometric.py

  Le résultat porté définit le nouveau champ *retPath* (chemin de récupération) au lieu de new_dir et new_file
  et le traitement normal du champ *retPath* dans le message de notification fera un bon téléchargement, aucun
  plugin est requis.

DESTFNSCRIPT
~~~~~~~~~~~~

DESTFNSCRIPT est refondu en tant que point d’entrée flowcb, où la directive est maintenant formatée d'une manière
similaire au flowcallback dans la configuration

configuration V2::

    accept .*${HOSTNAME}.*AWCN70_CWUL.*       DESTFNSCRIPT=sender_renamer_add_date.py

Code du plugin v2::

    import sys, os, os.path, time, stat

    # this renamer takes file name like : AACN01_CWAO_160316___00009:cmcin:CWAO:AA:1:Direct:20170316031754 
    # and returns :                       AACN01_CWAO_160316___00009_20170316031254

    class Renamer(object):

      def __init__(self) :
          pass

      def perform(self,parent):
 
          path = parent.new_file
          tok=path.split(":")

          datestr = time.strftime('%Y%m%d%H%M%S',time.gmtime())
          #parent.logger.info('Valeur_path: %s' % datstr)

          new_path=tok[0] + '_' + datestr
          parent.new_file = new_path
          return True 

    renamer=Renamer()
    self.destfn_script=renamer.perform


Se transforme en sr3

configuration SR3::

   accept .*${HOSTNAME}.*AWCN70_CWUL.*       DESTFNSCRIPT=sender_renamer_add_date.Sender_Renamer_Add_Date
 
In sr3, as for any flowcallback invocation, one needs to use a traditional python class invocation
and add to it the name of the class within the file.  This notation is equivalent to python *from*
statement *from sender_renamer_add_date import Sender_Renamer_Add_Date*

Dans sr3, comme pour tout appel flowcallback, il faut utiliser un appel de classe python traditionnel
et ajouter le nom de la classe dans le fichier. Cette notation est équivalente à l'instruction python *from*,
*from sender_renamer_add_date import Sender_Renamer_Add_Date*

code du flow callback::

   import logging,time

   from sarracenia.flowcb import FlowCB

   logger = logging.getLogger(__name__)

   class Sender_Renamer_Add_Date(FlowCB):

      def __init__(self,options):
          self.o = options
          pass

      def destfn(self,msg) -> str:

          logger.info('before: m=%s' % msg )
          relPath = msg["relPath"].split('/')
          datestr = time.strftime('%Y%m%d%H%M%S',time.gmtime())
          return relPath[-1] + '_' + datestr

Exemple de débogage des fonctions destfn sr3 ::
    fractal% python3
    Python 3.10.4 (main, Jun 29 2022, 12:14:53) [GCC 11.2.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from sender_renamer_add_date import Sender_Renamer_Add_Date
    >>> fb=Sender_Renamer_Add_Date(None)
    >>> msg = { 'relPath' : 'relative/path/to/file.txt' }
    >>> fb.destfn(msg)
    'file.txt_20220725130328'
    >>> 




v3 seulement: post,gather
------------------------

Le polling/posting est en fait effectuée dans des classes de rappel de flux (flowcb).
Le statut de sortie n’a pas d’importance, toutes ces routines seront appelées dans l’ordre.

Le retour d’un gather est une liste de messages de notification à ajouter à worklist.incoming

Le retour d'un post n’est pas défini. Le but est de créer un effet secondaire
qui affecte un autre processus ou serveur.


exemples:
 * flowcb/gather/file.py - lire des fichiers à partir du disque (pour le post et watch)
 * flowcb/gather/message.py - comment les messages de notification sont reçus par tous les composants
 * flowcb/post/message.py - comment les messages de notification sont publiés par tous les composants.
 * flowcb/poll/nexrad.py - cela poll le serveur AWS de la NOAA pour les données.
   installer une configuration pour l’utiliser avec *sr3 add poll/aws-nexrad.conf*


v3 Exemples complexes
---------------------


flowcb/nodupe
~~~~~~~~~~~~~

suppression des doublons dans la v3, a:

* un after_accept qui achemine les doublons à partir de worklist.incoming.
   ( ajout de non-dupes à la cache de réception.)


flowcb/retry 
~~~~~~~~~~~~

  * dispose d’une fonction after_accept pour ajouter des messages de notification à la
    fil d’attente entrante, afin de déclencher une autre tentative de traitement.
  * a une routine after_work faisant quelque chose d’inconnu ... FIXME.
  * a une fonction de publication pour prendre les téléchargements échoués et les mettre
    sur la liste des nouvelles tentatives pour un examen ultérieur.



Table of v2 and sr3 Equivalents
-------------------------------


Voici un aperçu des plugins inclus dans Sarracenia,
On peut parcourir les deux arbres, et à l'aide du tableau ci-dessous,
peut examiner, comparer et contraster les implémentations.


* arbo v2: https://github.com/MetPX/sarracenia/tree/v2_stable/sarra/plugins
* arbo Sr3: https://github.com/MetPX/sarracenia/tree/v03_wip/sarracenia/flowcb

La dénomination donne également un exemple de mappage de convention de nom... par ex. plugins dont le nom v2 commence par :

* msg\_... -> filter/... où accept/...
* file\_... -> work/...
* poll\_... -> poll/... où gather/...
* hb\_... -> housekeeping/...

sont mappés aux répertoires conventionnels sr3 à droite.

Les chemins relatifs des dossiers ci-dessus sont indiqués dans le tableau (les liens sont dans le code source, donc en anglais):

+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| V2 plugins (all in one directory...)            | Sr3 flow callbacks (treeified)                                                                                                               |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| data\_...                                       | subclass sarracenia.transfer                                                                                                                 |
|                                                 |                                                                                                                                              |
| modifier le fichier en vol.                     | pas d´exemple disponible actuelement, veuillez consulter le code source.                                                                     |
|                                                 |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| destfn_sample.py                                | `destfn/sample.py <../../Reference/flowcb.html#module-sarracenia.flowcb.destfn.sample>`_                                                     |
|                                                 |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_age.py                                     | `work/age.py <../../Reference/flowcb.html#module-sarracenia.flowcb.work.age>`_                                                               |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_delete.py                                  | `work/delete.py <../../Reference/flowcb.html#module-sarracenia.flowcb.work.delete>`_                                                         |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_email.py                                   | `send/email.py <../../Reference/flowcb.html#module-sarracenia.flowcb.work.email>`_                                                           |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_rxpipe.py                                  | `work/rxpipe.py  <../../Reference/flowcb.html#module-sarracenia.flowcb.work.rxpipe>`_                                                        |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| hb_memory                                       | `housekeeping/resources.py  <../../Reference/flowcb.html#module-sarracenia.flowcb.housekeeping.resources>`_                                  |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| html_page.py                                    | subclass sarracenia.transfer                                                                                                                 |
|                                                 |                                                                                                                                              |
|                                                 | pas d´exemple disponible actuelement, veuillez consulter le code source.                                                                     |
|                                                 |                                                                                                                                              |
|                                                 | voir poll/nasa_mls_nrt.py comme exemple de tel cas.                                                                                          |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_2http.py                                    | `accept/tohttp.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.tohttp>`_                                                     |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_2localfile.py, msg_2local.py (not sure)     | `accept/tolocalfile.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.tolocalfile>`_                                           |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_delete.py                                   | `filter/deleteflowfiles.py <../../Reference/flowcb.html#module-sarracenia.flowcb.filter.deleteflowfiles>`_                                   |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_fdelay.py                                   | `filter/fdelay.py <../../Reference/flowcb.html#module-sarracenia.flowcb.filter.fdelay>`_                                                     |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_filter_wmo2msc.py                           | `filter/wmo2msc.py <../../Reference/flowcb.html#module-sarracenia.flowcb.filter.wmo2msc>`_                                                   |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_log.py,file_log.py, hb_log.py, post_log.py  | `log.py  <../../Reference/flowcb.html#module-sarracenia.flowcb.log>`_                                                                        |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_pclean.py, msg_pclean_f90.py                | `pclean.py <../../Reference/flowcb.html#module-sarracenia.flowcb.pclean>`_                                                                   |
|                                                 | `filter/pcleanf90.py <../../Reference/flowcb.html#module-sarracenia.flowcb.filter.pcleanf92>`_                                               |
|                                                 |                                                                                                                                              |
| msg_pclean_f92.py                               | filter/pcleanf92.py <../../Reference/flowcb.html#module-sarracenia.flowcb.filter.pcleanf92>`_                                                |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| post_rate_limit.py                              | incorporé dans l´application messageRateMax                                                                                                  |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_rename_dmf.py                               | `accept/renamedmf.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.renamedmf>`_                                               |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_rename_whatfn.py                            | `accept/renamewhatfn.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.renamewhatfn>`_                                         |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_rename4jicc.py                              | `accept/rename4jicc.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.rename4jicc>`_                                           |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_stopper.py                                  | incorporé dans l´application messageCountMax                                                                                                 |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_sundew_pxroute.py                           | `accept/sundewpxroute.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.sundewpxroute>`_                                       |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_speedo.py                                   | `accept/speedo.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.speedo>`_                                                     |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_to_clusters.py                              | `accept/toclusters.py <../../Reference/flowcb.html#module-sarracenia.flowcb.accept.toclusters>`_                                             |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_WMO_type_suffix.py                          | `accept/wmotypesuffix.py <../../Reference/flowcb.html#module-sarracenia.accept.wmotypesuffix>`_                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| anciennement inclu dans l´application           | `nodupe/__init__.py <../../Reference/flowcb.html#module-sarracenia.flowcb.nodupe>`_                                                          |
| suppresion de duplicata                         |                                                                                                                                              |
| hb_cache.py                                     |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| incoporé dan l´appli message subscriber         | `gather/message.py <../../Reference/flowcb.html#module-sarracenia.flowcb.gather.message>`_                                                   |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| incoporé dan l´appli message poster             | `post/message.py <../../Reference/flowcb.html#module-sarracenia.flowcb.post.message>`_                                                       |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| incoporé dan l´appli file scan or noticing.     | `gather/file.py <../../Reference/flowcb.html#module-sarracenia.flowcb.gather.file>`_                                                         |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| incoporé dan l´appli retry logic                | `retry.py <../../Reference/flowcb.html#module-sarracenia.flowcb.retry>`_                                                                     |
|                                                 |                                                                                                                                              |
| hb_retry.py                                     |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_email.py                                   | `poll/mail.py <../../Reference/flowcb.html#module-sarracenia.flowcb.poll.mail>`_                                                             |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_nexrad.py                                  | `poll/nexrad.py <../../Reference/flowcb.html#module-sarracenia.flowcb.poll.nexrad>`_                                                         |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_noaa.py                                    | `poll/noaa_hydrometric.py <../../Reference/flowcb.html#module-sarracenia.flowcb.poll.noaa_hydrometric>`_                                     |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_usgs.py                                    | `poll/usgs.py <../../Reference/flowcb.html#module-sarracenia.flowcb.poll.usgs>`_                                                             |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| spare                                           |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+


