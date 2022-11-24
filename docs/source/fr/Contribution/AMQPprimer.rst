
=================================
 AMQP - Introduction à sarracénia
=================================

Il s’agit d’un briefing court mais plutôt dense pour expliquer
la motivation de l’utilisation de l’AMQP par la pompe de données MetPX-Sarracenia.
Sarracenia est essentiellement une application AMQP,
il est donc très utile de comprendre l’AMQP.
L’AMQP est un sujet vaste et intéressant en soi.  Aucune tentative n’est faite pour expliquer
tout cela ici. Ce mémoire fournit juste un peu de contexte et ne présente que des
concepts de base nécessaires pour comprendre et/ou utiliser Sarracenia.  Pour plus d’informations
sur l’AMQP lui-même, un ensemble de liens est maintenu à
sur le `site web Metpx <http://metpx.sourceforge.net/#amqp>`_ mais un moteur de recherche
révélera également une richesse de matériel.

.. contents::

Sélection des fonctionnalités AMQP
----------------------------------
AMQP est un protocole universel de transmission de messages avec de nombreuses
options pour prendre en charge de nombreux modèles de messagerie différents.  MetPX-sarracenia spécifie et utilise un
petit sous-ensemble de modèles AMQP. Un élément important du développement de Sarracenia a été de
choisir parmi les nombreuses possibilités un petit sous-ensemble de méthodes qui sont générales et
facile à comprendre, afin de maximiser le potentiel d’interopérabilité.

Analogie FTP
~~~~~~~~~~~~

Spécifier l’utilisation d’un protocole seul peut être insuffisant pour fournir suffisamment d’informations pour
l’échange de données et l’interopérabilité.  Par exemple, lors de l’échange de données via FTP, un certain nombre de choix
doivent être fait au-delà du protocole.
        - utilisation authentifiée ou anonyme ?
        - comment signaler qu’un transfert de fichier est terminé (bits d’autorisation? suffixe? préfixe?)
        - convention de nommage
        - transfert binaire ou texte

Des conventions convenues au-delà du simple FTP (IETF RFC 959) sont nécessaires.
Semblable à l’utilisation de FTP seul comme protocole de transfert est insuffisant
pour spécifier une procédure complète de transfert de données, l’utilisation d’AMQP,
sans plus d’informations, est incomplète. L’intention des conventions superposées à
l’AMQP est d’être un montant minimum pour obtenir un échange de données significatif.

AMQP: pas 1.0, mais 0.8 or 0.9
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AMQP 1.0 standardise le protocole sur le fil, mais supprime toute normalisation des courtiers.
Étant donné que l’utilisation de courtiers est essentielle à l’utilisation de Sarracenia,
était un élément fondamental des normes antérieures,
et comme la norme 1.0 est relativement controversée, ce protocole suppose un courtier standard pré 1.0,
comme il est fourni par de nombreux courtiers gratuits, tels que rabbitmq et Apache QPid, souvent appelés 0.8,
mais les courtiers de 0,9 et de post-0,9 pourraient bien interagir.


Échanges et files d’attente nommés
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dans AMQP avant la version 1.0, de nombreux acteurs différents peuvent définir des paramètres de communication, tels que les échanges
auquels publier, les files d’attente où les messages de notification s’accumulent et les liaisons entre les deux. Les applications
et les utilisateurs déclarent et utilisent leurs échanges, files d’attente et liaisons. Tout cela a été abandonné
dans le passage à la version 1.0 faisant des échanges thématiques, un fondement important des modèles pub/sub
beaucoup plus difficile.


dans AMQP 0.9, un abonné peut déclarer une fil d’attente, puis plusieurs processus (avec les bonnes
autorisations et le nom de la fil d’attente) peuvent consommer à partir de la même fil d’attente. Cela nécessite d’être capable
de nommer la fil d’attente. Dans un autre protocole, tel que MQTT, on ne peut pas nommer la fil d’attente, et donc
ce modèle de traitement n’est pas pris en charge.

La convention de mappage décrite dans `Topic < ../../Reference/sr3_post.7.html#topic>`_, permet à
MQTT d'établir des hiérarchies distinctes qui fournissent une distribution fixe entre
les travailleurs, mais pas exactement la fil d’attente partagée auto-équilibrée fournie par AMQP.


.. NOTE::

  Dans RabbitMQ (le broker initial utilisé), les autorisations sont attribuées à l’aide d’expressions régulières. Alors
  un modèle d’autorisation où les utilisateurs AMQP peuvent définir et utiliser *leurs* échanges et files d’attente
  est appliqué par une convention d’affectation de noms facilement mappée aux expressions régulières (toutes ces
  ressources incluent le nom d’utilisateur vers le début). Les échanges commencent par : xs_<user>_.
  Les noms des files d’attente commencent par : q_<user>_.


Échanges thématiques
~~~~~~~~~~~~~~~~~~~~

Les échanges thématiques sont utilisés exclusivement. AMQP prend en charge de nombreux autres
types d’échanges, mais la rubrique de sr_post est envoyée afin de prendre en charge le filtrage
côté serveur à l’aide du filtrage par rubrique. À l’AMQP 1.0, les échanges thématiques
(en fait, tous les échanges ne sont plus définis). Le filtrage côté serveur permet d’utiliser
beaucoup moins de hiérarchies de rubriques et d’utiliser des sous-divisions beaucoup plus efficaces.

Dans Sarracenia, les topics sont choisis pour refléter le chemin des fichiers annoncés, ce qui permet le
filtrage direct côté serveur, à compléter par un filtrage côté client sur la
réception des messages.

La racine de l’arborescence des rubriques est la version de la charge utile du message.  Cela permet aux courtiers individuels
de facilement prendre en charge plusieurs versions du protocole en même temps pendant les transitions.  *v02*,
créé en 2015, est la troisième itération du protocole et les serveurs existants prennent régulièrement en charge les
versions précédentes simultanément de cette manière.  La deuxième sous-rubrique définit le type de message.
Au moment de la rédaction de cet article : v02.post est le préfixe de rubrique pour les messages de notification actuels.

Peu de données
~~~~~~~~~~~~~~

Les messages AMQP contiennent des messages de notification, pas de données de fichier réelles. AMQP est optimisé pour et suppose
de petits messages. Garder les messages petits permet un maximum de transmission de messages et permet
aux clients d'utiliser des mécanismes de priorité basés sur le transfert de données, plutôt que sur les messages de notification.
Accommoder de grands messages créerait de nombreuses complications pratiques et nécessiterait inévitablement
la définition d’une taille de fichier maximale à inclure dans le message lui-même, ce qui entraîne une
complexité pour couvrir plusieurs cas.

Sr3_post est destiné à être utilisé avec des fichiers arbitrairement volumineux, via la segmentation et le multi-streaming.
Les blocs de fichiers volumineux sont annoncés indépendamment et les blocs peuvent suivre différents chemins
entre la pompe initiale et la livraison finale. Le protocole est unidirectionnel,parce qu’il
n'y a pas de dialogue entre l’éditeur et l’abonné. Chaque publication est un élément autonome qui
est un message dans un flux qui, à la réception, peut être réparti sur un certain nombre de nœuds.

Cependant, il est probable que, pour les petits fichiers sur des liens à latence élevée, il est
plus efficace d’inclure le corps des fichiers dans les messages de notification eux-mêmes,
plutôt que de forcer une phase de récupération séparée.  L’avantage relatif dépend de :

* la grossièreté relative du filtrage côté serveur signifie qu’un certain filtrage est effectué sur
  côté client.  Toutes les données incorporées pour les messages de notification ignorées côté client
  sont des déchets.

* Sarracenia établit des connexions à longue durée de vie pour certains protocoles, tels que SFTP,
  la surcharge relative pour une récupération peut donc ne pas être longue.

* On atteindra un taux de messagerie plus élevé sans que les données soient intégrées, et si
  les messages de notification sont distribués à un certain nombre de travailleurs, il est possible que le résultat
  de taux de messages est plus élevé sans données intégrées (en raison d’une distribution plus rapide pour
  téléchargement parallèle) que les économies réalisées grâce à l’intégration.

* plus la latence de la connexion est faible, moins l’avantage de performance est faible
  d’intégration, et plus cela devient un facteur limitant sur la haute performance de transferts.

D’autres travaux sont nécessaires pour mieux clarifier quand il est judicieux d’intégrer du contenu
dans les messages de notification. Pour l’instant, l’en-tête *content* est inclus pour permettre de telles expériences
à se produire.


Autres paramètres
~~~~~~~~~~~~~~~~~
AMQP a de nombreux autres paramètres et une fiabilité pour un cas d’utilisation particulier
est assuré en faisant les bons choix.

* persistance (les files d’attente survivent aux redémarrages du courtier, par défaut true),

* expiration (combien de temps une fil d’attente doit exister lorsque personne n’en consomme.  Valeur par défaut : quelques
  minutes pour le développement, mais peut être réglé beaucoup plus longtemps pour la production)

* message_ttl (durée de vie des messages de notification en fil d’attente. Les messages trop vieux ne le pourront pas
  être livré : la valeur par défaut est éternelle.)

* La pré-récupération est un AMQP réglable pour déterminer le nombre de messages de notification qu’un client va
  récupérer à partir d’un courtier à la fois, en optimisant le streaming. (valeur par défaut : 25)

Ceux-ci sont utilisés dans les déclarations de files d’attente et d’échanges pour fournir des
traitement des messages.  Cette liste n’est pas exhaustive.

Mappage des concepts AMQP à Sarracenia
--------------------------------------

.. image:: ../../Explanation/Concepts/AMQP4Sarra.svg
    :scale: 50%
    :align: center

Un serveur AMQP est appelé Broker. *Broker* est parfois utilisé pour désigner le logiciel,
d’autres fois le serveur exécutant le logiciel broker (même confusion que *serveur web*.) Dans le diagramme ci-dessus,
Le vocabulaire AMQP est en orange et les termes Sarracenia sont en bleu.

Il existe de nombreuses implémentations de logiciels de courtage différentes. Nous utilisons rabbitmq.
Ne pas essayer d’être spécifique à rabbitmq, mais les fonctions de gestion diffèrent d’une implémentation à l’autre.
Ainsi, les tâches d’administration nécessitent un 'portage' alors que les principaux éléments de l’application ne le font pas.

*Queues* sont généralement prises en charge de manière transparente, mais vous devez savoir
   - Un consommateur/abonné crée une fil d’attente pour recevoir des messages de notification.
   - Les files d’attente des consommateurs sont *liées* aux échanges (AMQP-speak)

Un *exchange* est un entremetteur entre les files d’attente *publisher* et *consumer*.
   - Un message arrive d’un éditeur.
   - le message va à l’échange, est-ce que quelqu’un s’intéresse à ce message?
   - dans un *échange basé sur une rubrique*, la rubrique du message fournit le *exchange key*.
   - intéressé : comparer la clé de message aux liaisons des *files d’attente des consommateurs*.
   - le message est acheminé vers les *files d’attente des consommateurs* intéressés, ou supprimé s’il n’y en a pas.

- Plusieurs processus peuvent partager une *queue*, ils en suppriment simplement à tour de rôle les messages de notification.
   - Ceci est fortement utilisé pour sr_sarra et sr_subcribe plusieurs instances.

- Les *Queues* peuvent être *durables*, donc même si votre processus d’abonnement meurt,
  si vous revenez dans un délai raisonnable et que vous utilisez la même fil d’attente,
  vous n’aurez manqué aucun message de notification.

- Comment décider si quelqu’un est intéressé.
   - Pour Sarracenia, nous utilisons (norme AMQP) *topic based exchangess*.
   - Les abonnés indiquent les sujets qui les intéressent, et le filtrage se produit côté serveur/courtier.
   - Les sujets ne sont que des mots-clés séparés par un point. caractères génériques : # correspond à n’importe quoi,
     * correspond à un mot.
   - Nous créons la hiérarchie des rubriques à partir du nom du chemin (mappage à la syntaxe AMQP)
   - La résolution et la syntaxe du filtrage des serveurs sont définies par AMQP. (. séparateur, caractères génériques # et *)
   - Le filtrage côté serveur est grossier, les messages de notification peuvent être filtrés
     après le téléchargement à l’aide de regexp sur les chemins réels (les directives reject/accept).

- préfixe de sujet ?  Nous commençons l’arborescence des sujets avec des champs fixes
     - v02 la version/format des messages de notification sarracenia.
     - Publier... le type de message, il s’agit d’un message de notification
       d’un fichier (ou d’une partie d’un fichier) disponible.


Sarracenia est une application MQP
----------------------------------

Dans la version 2, MetPX-Sarracenia n’est qu’un léger wrapper/revêtement autour de l’AMQP.
Dans la version 3, cela a été retravaillé et un pilote MQTT a été ajouté pour le rendre
moins spécifique à l’AMQP.

- Une pompe MetPX-Sarracenia est une application PYTHON AMQP qui utilise un courtier (rabbitmq)
  pour coordonner les transferts de données client SFTP et HTTP, et accompagne un
  serveur Web (apache) et serveur sftp (openssh) sur la même adresse d'utilisateur.

- Chaque fois que cela est raisonnable, nous utilisons leur terminologie et leur syntaxe.
  Si quelqu’un connaît l’AMQP, il comprend. Sinon, ils peuvent faire des recherches.

- Les utilisateurs configurent un *broker*, au lieu d’une pompe.
  - les utilisateurs peuvent explicitement choisir leurs noms de *queue*.
  - les utilisateurs définissent *subtopic*,
  - les sujets avec séparateur de points sont peu transformés, plutôt que codés.
  - fil d’attente *durable*.
  - nous utilisons des *message headers* (AMQP-speak pour les paires clé-valeur) plutôt
    que l’encodage en JSON ou dans un autre format de charge utile.

- réduire la complexité par le biais de conventions.
   - n’utiliser qu’un seul type d’échanges (Topic), s’occuper des liaisons.
   - les conventions de nommage pour les échanges et les files d’attente.
      - les échanges commencent par x.
        - xs_Weather - l’échange pour la source (utilisateur amqp) nommée Météo pour poster des messages de notification
        - xpublic -- échange utilisé pour la plupart des abonnés.
      - les files d’attente commencent par q

- Les ressources Internet sont plus utiles et réduisent notre charge de documentation.
- Nous écrivons moins de code (exposer l’AMQP brut signifie moins de colle.)
- Moins de potentiel de bugs / plus de fiabilité.
- nous faisons un nombre minimum de choix/restrictions
- définir des valeurs par défaut raisonnables.


Révision
--------

Si vous avez compris le reste du document, cela devrait avoir du sens pour vous :

Un courtier AMQP est un processus de serveur qui héberge les échanges et les files d’attente
utilisés pour acheminer les messages de notification
avec une latence très faible. Un éditeur envoie des messages de notification à un échange, tandis qu’un consommateur lit les
messages de notification de leur fil d’attente. Les files d’attente sont *liées* aux échanges. Sarracenia lie un courtier
à un serveur Web pour fournir des notifications rapides et utilise des échanges de sujets pour activer le
filtrage côté serveur des consommateurs. L’arborescence des rubriques est basée sur l’arborescence de fichiers que vous pouvez
naviguez si vous visitez le serveur Web correspondant.

Annexe A : Contexte
-------------------

Pourquoi utiliser AMQP?
~~~~~~~~~~~~~~~~~~~~~~~

- standard ouvert, multiples implémentations libres.
- transmission de messages à faible latence.
- encourage les modèles/méthodes asynchrones.
- langue, protocole et fournisseur neutres.
- très fiable.
- adoption robuste (deux sections suivantes à titre d’exemples)

D’où vient l’AMQP?
~~~~~~~~~~~~~~~~~~

- Norme ouvertes international du monde financier.
- De nombreux systèmes propriétaires similaires existent, AMQP construit pour échapper au verrouillage.
  Le standard est construit avec une longue expérience des systèmes de messagerie des fournisseurs, et donc assez mature.
- invariablement utilisé dans les coulisses en tant que composant dans le traitement côté serveur, et non visible par l’utilisateur.
- de nombreuses entreprises web (soundcloud)
- voir une bonne adoption dans la surveillance et l’intégration pour le HPC

Pile Intel/Cray HPC
~~~~~~~~~~~~~~~~~~~

`Intel/Cray HPC stack <http://www.intel.com/content/www/us/en/high-performance-computing/aurora-fact-sheet.html>`_ 

.. image:: ../../Contribution/AMQPprimer/IntelHPCStack.png
    :scale: 50%
    :align: center


OpenStack
~~~~~~~~~

`AMQP is the messaging technology chosen by the OpenStack cloud. <http://docs.openstack.org/developer/nova/rpc.html>`_


.. image:: ../../Contribution/AMQPprimer/OpenStackArch.png
    :scale: 70%
    :align: center


Comment adopter l’AMQP
~~~~~~~~~~~~~~~~~~~~~~

Adopter AMQP ressemble plus à l’adoption de XML qu’à l’adoption de FTP.  l'Interopérabilité FTP
est facile car les choix sont limités. Avec XML, cependant, vous obtenez **plus de palette que de peinture.** Beaucoup
de dialectes différents, méthodes de schéma, etc...  XML sera valide et analysé, mais sans
normalisation supplémentaire, l’échange de données reste incertain.  Pour une réelle interopérabilité,
il faut normaliser des dialectes spécifiques.  Exemples:

     - RSS/Atom, 
     - Common Alerting Protocol (CAP)

Les courtiers AMQP et le logiciel client peuvent se connecter et envoyer des messages de notification, mais sans
normalisation supplémentaire, les applications ne communiqueront pas.  AMQP appellent
ces couches supplémentaires *applications*.  AMQP permet tous les messages imaginables,
de sorte qu’une application **bien formée** est construite en éliminant les fonctionnalités de
considération, **choix des couleurs à utiliser.**
Sarracenia est une application de message AMQP passant au transfert de fichiers.

Au fur et à mesure que CAP réduit le XML, Sarracenia réduit la portée de l’AMQP. Ce rétrécissement est
nécessaire pour obtenir un résultat utile :
l'interopérabilité.  Les conventions et formats de Sarracenia sont définis dans :

   - `sr_post format man page <../Reference/sr_post.7.html>`_



