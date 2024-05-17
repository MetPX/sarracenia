===============================
Concepts généraux de Sarracenia
===============================

Les pompes Sarracenia forment un réseau. Le réseau utilise
des courtiers amqp ( *broker* )  `Message Queueing Protocol (MQP) <https://en.wikipedia.org/wiki/Message_queue>`_
pour modéré les transferts de fichiers entre les pompes. On
envoie les avis de nouveau fichiers dans un sens et les rapports de succès ou
trouble dans la direction opposée. Les administrateurs configurent les chemins
d'accès à travers lesquels les données circulent. Chaque pompe agit de façon
indépendante, en gérant les activités des moteurs de transfert
qu'il peut atteindre, sans connaissance de l'ensemble du réseau. Les
emplacements de pompes et les directions du flux de circulation sont
choisis pour travailler avec les débits autorisés. Idéalement, aucune
exception de règle de pare-feu et nécessaire.

Sarracenia ne transporte pas de données. Il s'agit d'une couche de gestion pour
coordonner les activités de l'utilisation d´engins de transport. Donc, pour
obtenir une pompe fonctionnelle, les mécanismes de transport réels doivent
également être mis en place, le cas d'utilisation
le plus commun est `RabbitMQ <https://www.rabbitmq.com/>`_.
Les deux mécanismes actuelles sont le web et SFTP.
Dans le cas le plus simple, tous les composants se trouvent sur le site
Web du même serveur, mais cela n'est pas nécessaire. Le courtier pourrait
être sur un serveur différent de l´origine et la destination d'un transfert.

La meilleure façon d'effectuer des transferts de données est d'éviter les
sondages (examination récurrente de répertoires afin de détecter des
changements de fichiers.) C'est plus efficace si les rédacteurs peuvent
être amenés à émettre des messages d'annonce en format sr3_post appropriés. De même,
lors de la livraison, il est idéal si les destinataires utilisent
sr_subscribe, et un plugin on_file pour déclencher leur traitement ultérieur,
de sorte que le fichier est qui leur a été remis sans sondage. C'est la façon
la plus efficace de travailler, mais... il est entendu que pas tous les logiciels
ne seront coopératifs. Pour démarrer le flot en Sarracenia dans ces cas,
ca prend des outils de sondage:  sr_poll (à distance), et sr3_watch (locale.)

D'une manière générale, Linux est la principale cible de déploiement et la
seule plate-forme sur laquelle les configurations de serveur sont déployées.
D'autres plates-formes sont utilisées en configuration client.  Ceci
n´est pas une limitation, c'est juste ce qui est utilisé et testé.
Implémentations de la pompe sur Windows devrait fonctionner, ils ne
sont tout simplement pas testés.

Une pompe de données Sarracénia peut être implanté avec un seul serveur, ou bien une grappe, avec des rôles identiques ou spécialisés.
Voir `Options de déploiement <ConsiderationDeployments.rst>` pour plus de détails. À l´intérieur d´une pompe, les conceptes décrites
dans les sections suivantes s'appliquent.

L'algorithme de Flux
--------------------

Tous les composants qui s'abonnent (subscribe, sarra, sarra, sender, shovel, winnow)
partagent un code substantiel et ne diffèrent que par leur reglages de défaut.
Chaque composant suit le même algorithme général, l'algorithme de Flux.
Les étapes de l’algorithme Flux sont les suivantes :


* Rassembler une liste de messages d'annonce
* Filtrez-les avec des clauses d’accept/reject
* Travailler sur les messages d'annonce acceptés
* Afficher le travail accompli pour le prochain flux

En plus de detail:

.. table:: **Tableau 1 : Algorithme pour tous les composants**
 :align: center

 +----------+-------------------------------------------------------------+
 |          |                                                             |
 |  PHASE   |                 DESCRIPTION                                 |
 |          |                                                             |
 +----------+-------------------------------------------------------------+
 | *gather* | Obtenez de l'information sur une liste initiale de fichiers |
 |          |                                                             |
 |          | A partir: d'une fil d’attente, un répertoire,               |
 |          | un script de polling.                                       |
 |          |                                                             |
 |          | Sortie: worklist.incoming rempli de messages d'annonce.     |
 |          |                                                             |
 |          | Chaque message d'annonce est un dictionnaire python         |
 +----------+-------------------------------------------------------------+
 | *Filter* | Réduire la liste de fichiers sur lesquels agir.             |
 |          |                                                             |
 |          | Appliquer les clauses accept/reject.                        |
 |          |                                                             |
 |          | callbacks after_accept                                      |
 |          | déplacer les messages d´annonce de worklist.incoming à      |
 |          | worklist.rejected                                           |
 |          |                                                             |
 |          | Ceux a éxécuter: flowcb/nodupe.py (suppresion des doublons.)|
 |          |                                                             |
 +----------+-------------------------------------------------------------+
 | *work*   | Traitez le message en le téléchargeant ou en l’envoyant.    |
 |          |                                                             |
 |          | exécuter le transfert (télécharger ou envoyer.)             |
 |          |                                                             |
 |          | Exécuter after_work                                         |
 +----------+-------------------------------------------------------------+
 | *post*   | Publier l’annonce des téléchargements/envois de fichiers à  |
 |          | post_broker ou se débarrasser de la tache (à file/retry... )|
 +----------+-------------------------------------------------------------+

Les principaux composants de l’implémentation python de Sarracenia implémentent
tous le même algorithme décrit ci-dessus. L’algorithme comporte différents endroits
où un traitement personnalisé peut être inséré (à l’aide de flowCallbacks) ou
dériver des classes de flux, d’intégrité ou de transfert.

Les composants ont juste des paramètres par défaut différents:

.. table:: **Tableau 2 : Utilisation de l’algorithme de flux par chaque composant**
 :align: center

 +------------------------+------------------------------+------------------------+
 | Composant              | Utilisation de l’algorithme  | options clé            |
 +------------------------+------------------------------+------------------------+
 +------------------------+------------------------------+------------------------+
 | *subscribe*            | Gather = gather.message      | flowMain subscribe     |
 |                        |                              |                        |
 |   Télécharger un       | Filter                       | mirror off             |
 |   fichier d'une pompe  |                              | (dans les autres       |
 |                        | Work = Télécharger           |  composants, c'est     |
 |                        |                              |  mirror on )           |
 |   défaut mirror=False  | Post = facultatif            |                        |
 |   (True pour tous les  |                              | download on            |
 |   autres)              |                              |                        |
 |                        |                              |                        |
 +------------------------+------------------------------+------------------------+
 | *sarra*                | Gather = gather.message      |                        |
 |                        |                              | flowMain sarra         |
 | Utilisé sur des        |                              |                        |
 | pompes.                |                              | mirror on              |
 |                        |                              | download on            |
 | Télécharge un fichier  |                              |                        |
 |                        |                              |                        |
 | Publié un message par  |                              |                        |
 | la suite aux consom-   |                              |                        |
 | mateurs.               |                              |                        |
 |                        |                              |                        |
 | Abonnés de la pompe    | Work = Télécharger           |                        |
 | locale puissent        |                              |                        |
 | télécharer à leur      | Post = publier               |                        |
 | tour                   |                              |                        |
 |                        |                              |                        |
 +------------------------+------------------------------+------------------------+
 | *poll*                 | Gather                       |                        |
 |                        | if has_vip: poll             | flowMain poll          |
 | Trouver des fichiers   |                              |                        |
 | sur d'autre serveurs   | Filter                       | pollUrl                |
 | pour publier.          |                              |                        |
 |                        | if has_vip:                  |                        |
 |                        |     Work = nil               |                        |
 | Utilise has_vip*       |                              |                        |
 | (voir ci-dessous)      |     Post = oui               |                        |
 +------------------------+------------------------------+------------------------+
 | *shovel*               | Gather = gather.message      | acceptUnmatched True   |
 |                        |                              |                        |
 |                        |                              | nodupe_ttl 0           |
 | Déplacer les messages  | Filter (shovel cache=off)    | download off           |
 | de place.              |                              |                        |
 |                        |                              | callback gather.message|
 |                        | Work = nil                   |                        |
 |                        |                              | callback post.message  |
 |                        | Post = oui                   |                        |
 +------------------------+------------------------------+------------------------+
 | *winnow*               | Gather = gather.message      |                        |
 |                        |                              | acceptUnmatched true   |
 |                        |                              |                        |
 | Déplacer les messages  | Filter (shovel cache=on)     | nodupe_ttl 300         |
 | de place.              |                              |                        |
 |                        | Work = nil                   | callback gather.message|
 |                        |                              |                        |
 | Suppression de         |                              | callback post.message  |
 | doublons à l'aide      | Post = oui                   |                        |
 | du cache et d'un VIP   |                              |                        |
 | partagé                |                              |                        |
 +------------------------+------------------------------+------------------------+
 | *post/watch*           | Gather = gather.file         | path /file/a/afficher  |
 |                        |                              |                        |
 | Trouve un fichier sur  | Filter                       | sleep -1 # pour post   |
 | un serveur **local**   |                              |                        |
 | pour le publier        | Work = nil                   | sleep 5  # pour watch  |
 |                        |                              |                        |
 |                        | Post = oui                   | callback gather.file   |
 |                        |                              |                        |
 |                        |   Message?, File?            | callback post.message  |
 +------------------------+------------------------------+------------------------+
 | *sender*               | Gather = gather.message      |                        |
 |                        |                              | flowMain sender        |
 | Enovoyer des fichiers  | Filter                       |                        |
 |                        |                              | sendTo                 |
 | Optionnel              | Do = sendfile                |                        |
 | Publie un message après|                              |                        |
 | l'envoie               |                              |                        |
 |                        |                              |                        |
 |                        | Outlet = facultatif          |                        |
 +------------------------+------------------------------+------------------------+


Dans la colonne de gauche, on peut voir le nom et la description générale de chaque composant.
dans la colonne du milieu, on voit à quoi s'appliquent les différentes phases de l'algorithme Flow.
A droite, on voit comment exprimer, dans un fichier de configuration de flux générique, le composant.
La plupart des composants peuvent utiliser la classe de flux parent, mais ceux qui ont besoin 
de plus utilise des sous-classes de flux. Ces cas sont configurés à l'aide de l'option flowMain.

Les composants sont facilement composés à l'aide de courtiers AMQP, qui créent
des réseaux élégants de communiquer des processus séquentiels. (CSP dans
le sens `Hoare <http://dl.acm.org/citation.cfm?doid=359576.359585>`_ )


Multiple processes: Instances, Singletons and VIP
-------------------------------------------------

L’algorithme de flux ne se limite pas à un seul processus. De nombreux processus
peuvent exécuter la même configuration de flux. Pour les composants sarra, sender, shovel
et subscribe, on définit le paramètre *instance* au nombre de processus à exécuter
et à consommer à partir de la *queue* configurée qu’ils partagent.

Les composantes de poll, de post, et de watch, en revanche, sont limitées à un
processus unique sur un serveur donné. Dans le tableau ci-dessus, il y a une note
à propos de *has_vip*. Lorsque plusieurs serveurs participent à une
configuration, la directive vip peut être utilisée pour que les serveurs
coopérent pour fournir un service unique (où un seul serveur est
actif à la fois.) Pour la plupart des composants, la directive VIP dans un
fichier de configuration définit une adresse IP virtuelle qu’un serveur doit
activement avoir pour que ce composant soit actif. Si Sarracenia
détecte que l’interface n’est pas présente sur le serveur, le composant
s’exécutera en mode passif.

Pour presque tous les composants, le mode passif signifie qu’aucun traitement n’est effectué.
Le nœud vérifiera passivement s’il a obtenu le
Vip. Si le nœud n’a pas le vip, il restera en stand-by indéfiniment.

L’exception à cela est le sondage (poll), qui fonctionne différemment. Dans le sondage,
lorsque vous n’avez pas le vip, la boucle algorithmique suivante
continue:

* gather
* filter
* after_accept

Le gather (et/ou le sondage) du sondage s’abonne à l’échange ou d’autres
participants qui ont le vip publient et met à jour sa cache à partir des messages d´annonce, pour
éviter que les autres sondages interrogent le même point de terminaison pour la
même liste de fichiers.

Corréspondance des concepts AMQP avec Sarracenia
------------------------------------------------

Une chose que l'on peut dire sans risque est qu'il faut comprendre un peu l'AMQP
pour travailler avec Sarracenia. L'AMQP est un sujet vaste et intéressant en
soi. On ne tente pas de toute expliquer ici. Cette section fournit juste
un peu de contexte, et introduit seulement les concepts de base nécessaires à la
compréhension et/ou à l'utilisation de la Sarracenia. Pour plus d'informations
sur l'AMQP lui-même, un ensemble de liens est maintenu à l'adresse suivante
le site web `Metpx web site <sarra.rst#amqp>`_
mais un moteur de recherche révèlera aussi une richesse matérielle.

.. image:: Concepts/amqp_notion_de_flux.svg
    :scale: 50%
    :align: center

Un serveur AMQP s'appelle un courtier. Le mot *Courtier* est parfois utilisé pour
faire référence au logiciel, d'autres fois serveur exécutant le logiciel de
courtage (même confusion que *serveur web*).  ci-dessus, le vocabulaire de
l'AMQP est en orange, et les termes de Sarracenia sont en bleu. Il y a
de nombreuses et différentes implémentations de logiciels de courtage. Nous
utilisons rabbitmq. Nous n'essayons pas d´être spécifique au rabbitmq, mais
les fonctions de gestion diffèrent d'une implémentation à l'autre.


Les *Queues* (files d´attentes) sont généralement prises en charge de manière transparente, mais vous avez besoin de connaître
   - Un consommateur/abonné crée une fil d'attente pour recevoir des messages d'annonce.
   - Les files d'attente des consommateurs sont *liées* aux échanges (langage AMQP).

Un *exchange* est un entremeteur entre *publisher* et les files d´attentes du
*consumer*

   - Un message  d'annonce arrive d'une source de données.
   - l´avis passe à travers l'échange, est-ce que quelqu'un est intéressé par ce message d'annonce?
   - dans un échange basé sur un *topic*, le thème du message d'annonce fournit la *clé d'échange*.
   - intéressé : comparer la clé de message d'annonce aux liaison des *queues de consommateurs*.
   - le message d'annonce est acheminé vers les *files d'attente des consommateurs* intéressés, ou supprimé s'il n'y en a pas.
   - n’existe pas dans MQTT, utilisé comme racine de la hiérarchie des thèmes.

Plusieurs processus peuvent partager une *queue*, d´ou ils prélève les messages d'annonce à tour de rôle.
   - Ceci est fortement utilisé pour sr_sarra et sr_subscribe multiples instances.
   - Le même concept est disponible en tant qu'*abonnements partagés* dans MQTT.


Comment décider si quelqu'un est intéressé.
   - Pour la Sarracenia, nous utilisons (standard AMQP) *échanges thématiques*.
   - Les abonnés indiquent les thèmes qui les intéressent et le filtrage se fait côté serveur/courtier.
   - Les thèmes sont juste des mots-clés séparés par un point. wildcards : # correspond à n'importe quoi, * correspond à un mot.
   - Nous créons la hiérarchie des thèmes à partir du nom du chemin d'accès (mappage à la syntaxe AMQP).
   - La résolution et la syntaxe du filtrage des serveurs sont définies par l'AMQP. (. séparateur, # et * caractères génériques)
   - Le filtrage côté serveur est grossier, les messages d'annonce peuvent être filtrés après le téléchargement en utilisant regexp


AMQP v09 (Rabbitmq) Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MetPX-Sarracenia n’est qu’un léger revêtement autour des protocoles de
fil d’attente des messages. Pour ceux qui sont familiers avec
les protocoles sous-jacents, voici les mappages:

- Une pompe de données MetPX-Sarracenia est une application python AMQP qui utilise un (rabbitmq).
  pour coordonner les transferts de données des clients SFTP et HTTP, et accompagne un
  serveur web (apache) et serveur sftp (openssh), souvent sur la même adresse en face de l'utilisateur.

- Une pompe de données MetPX-Sarracenia peut également fonctionner avec rabbitmq remplacé par
  un courtier MQTT tel que mosquitto.org (mais certaines administrations doivent être gérées manuellement).

- Dans la mesure du possible, nous utilisons leur terminologie et leur syntaxe.
  Si quelqu'un connaît l'AMQP, il comprend. Si ce n'est pas le cas, ils peuvent faire des recherches.

    - Les utilisateurs configurent un *courtier*, au lieu d'une pompe.
    - par convention, le serveur virtuel par défaut'/' est toujours utilisé. (n'a pas encore ressenti le besoin d'utiliser d'autres serveurs virtuels)
    - les utilisateurs peuvent explicitement choisir leurs noms *files d'attente*.
    - les utilisateurs définissent *subtopic*,
    - les sujets avec séparateur de points sont transformés au minimum, plutôt qu'encodés.
    - La fil d’attente est définie sur *durable* afin que les messages ne soient pas perdus lors des redémarrages du broker.
    - nous utilisons des *en-têtes de message* (langage AMQP pour les paires clé-valeur) plutôt que d'encoder en JSON ou dans un autre format de charge utile.
    - *expire* combien de temps pour conserver une fil d’attente inactive ou un échange.

- réduire la complexité par le biais de conventions.
   - n'utiliser qu'un seul type d'échanges (Topic), prendre soin des fixations.
   - conventions de nommage pour les échanges et les files d'attente.
      - les échanges commencent par x.
        - xs_Weather - l'échange pour la source (utilisateur amqp) nommé Weather pour poster des messages.
        - xpublic -- central utilisé pour la plupart des abonnés.
      - les files d'attente commencent par q\

MQTT (version =5) Paramètres
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MQTT est en fait un meilleur match à Sarracenia que AMQP, car il est
entièrement basé sur des thèmes hiérarchiques. Alors que les sujets
ne sont qu’un parmi une variété de choix pour les méthodes de routage dans AMQP.

  - Dans MQTT, le séparateur de thème est / au lieu de .
  - Le caractère générique de la rubrique MQTT *#* est le même que dans AMQP (correspond au reste du sujet)
  - Le caractère générique de la rubrique MQTT *+* est le même que l’AMQP *\** (correspond à un thème).
  - Un « Échange » AMQP est mappé à la racine de l’arborescence des thèmes MQTT,
  - Une « fil d’attente » AMQP est représentée dans MQTT par *client-id* et un *abonnement partagé*. Remarque : Les abonnements partagés ne sont présents que dans MQTTv5.

    * AMQP: Une fil d’attente nommée *queuename* est liée à un échange xpublic avec clé: v03.observations ...
    * Abonnement MQTT: thème $shared/*queuename*/xpublic/v03/observations ...

  - Les connexions sont normalement clean_sesssion = 0, pour récupérer les messages lorsqu’une connexion est rompue.
  - MQTT QoS==1 est utilisé pour s’assurer que les messages sont envoyés au moins une fois et éviter les frais généraux
    de ne s’assurer qu’une seule fois.
  - AMQP *prefetch* mappé à MQTT *receiveMaximum*
  - *expire* a la même signification en MQTT que dans AMQP.

MQTT v3 manque d’abonnements partagés et la logique de récupération est très différente. Sarracenia ne prend en charge que la v5.

Le flux à travers des Pompes
----------------------------

.. image:: Concepts/sr3_exemple_de_flux.svg
    :scale: 100%
    :align: center



Une description du flux conventionnel de messages par le biais d'échanges sur une pompe :

- Les abonnés se lient généralement à l'échange public pour obtenir le flux de données principal.

- Un utilisateur user aura deux échanges :

  - xs_user l'échange où Alice poste ses notifications de fichiers et ses messages de rapports
  - xr_user l'échange où user lit ses messages de rapport
  - Remarque: les échanges « user » seront le nom d’utilisateur spécifié par l’utilisateur. Pas explicitement « xs_user » ou « xr_user ».

- Habituellement, le composant sarra lira à partir de xs_user, récupérera les données correspondant au
  message *post* des utilisateurs, puis les rendra disponibles sur la pompe, en les ré-annonçant sur l’échange xpublic.

- Les administrateurs auront accès à un échange xreport pour obtenir une surveillance à l’échelle du système.
  L’utilisateur n’aura pas l’autorisation de le faire, il ne peut regarder que xr_user, qui aura les messages
  de rapport spécifiques pour l’utilisateur uniquement.

Le but de ces conventions est d’encourager un moyen d’exploitation raisonnablement sûr. Si un message
provient d’xs_user, le processus de lecture est chargé de s’assurer qu’il est marqué comme provenant
de l’utilisateur sur ce cluster. Cela empêche certains types de spoofing d’identité, car les messages
ne peuvent être publiés que par les propriétaires appropriés.


Utilisateurs et rôles
---------------------

Les noms d'utilisateur pour l'authentification des pompes sont significatifs
dans la mesure où ils sont visibles par tous. Ils sont utilisés dans le chemin
du répertoire sur les arbres publics, ainsi que pour authentifier le courtier.
Ils doivent être compréhensibles. Ils ont souvent une portée plus large qu'une
personne, peut-être les appeler "Comptes". Il peut être élégant de configurer
les mêmes noms d'utilisateur pour une utilisation dans les moteurs de transport.

Tous les noms de compte doivent être uniques, mais rien n'évitera les conflits
lorsque les sources proviennent de différents réseaux de pompes, et des clients
à différentes destinations. Dans la pratique, les conflits de noms sont les
suivants adressée par routage pour éviter que deux sources différentes' avec
le même nom aient leur nom. les offres de données combinées sur un seul arbre.
D'autre part, les conflits de noms ne sont pas toujours une erreur.
L'utilisation d'un nom de compte source commun sur différents clusters peut
être utilisée pour implémenter des dossiers qui sont partagés entre les deux
comptes portant le même nom.

Les utilisateurs de pompe sont définis avec l'option *declare*. Chaque option
commence avec l'option *declare* suivi du rôle spécifié, et enfin le nom
de l'utilisateur qui a ce rôle.  rôle peut en être un de :

subscriber
  Un *subscriber* ( abonné ) est un utilisateur qui ne peut s'abonner qu'aux messages de données et de rapport. Interdiction d'injecter des données.
  Chaque abonné reçoit un xs_<user> named exchange sur la pompe, où si un utilisateur est nommé *Acme*,
  l'échange correspondant sera *xs_Acme*. Cet échange est l'endroit où un sr_subscribe sr_subscribe
  enverra ses messages de rapport.

  Par convention/défaut, l'utilisateur *anonyme* est créé sur toutes les pompes pour permettre l'abonnement sans
  un compte spécifique.

source
  Un utilisateur autorisé à s'abonner ou à générer des données. Une source ne
  représente pas nécessairement une personne ou un type de données, mais plutôt
  une organisation responsable des données produites. Ainsi, si une organisation
  recueille et met à disposition dix types de données avec un seul interlocuteur
  email ou numéro de téléphone pour des questions sur les données et leur
  disponibilité, alors tous les ces activités de recouvrement pourraient
  utiliser un seul compte "source".

  Chaque source a un échange xs_<user> pour l'injection de messages de données,
  et, similaire à un abonné, pour envoyer des messages de rapport sur le
  traitement et la réception des données.

  Chaque source est en mesure de visualiser tous les messages pour les données
  qu'elle a injectées, mais l'endroit où tous ces messages sont disponibles
  varie en fonction de la configuration de l'administrateur du routage des
  rapports. Ainsi, une source peut injecter des données sur la pompe A, mais
  peut s'abonner à des rapports sur une pompe différente. Les rapports
  correspondant aux données que la source injectée est écrite en échange xr_<user>.

  Lors de l´injection initiale des données, le chemin est modifié par Sarracenia
  pour préparer une partie supérieure fixe de l'arborescence des répertoires.
  Le premier niveau d'annuaire est le jour de l'ingestion dans le réseau en
  format AAAAMMJJ. Le répertoire de deuxième niveau est le nom de la source.
  Donc pour une utilisatrice Alice, s'injecter le 4 mai 2016, la racine de
  l'arborescence du répertoire est : 20160504/Alice. Notez que tous les on
  s'attend à ce que les pompes fonctionnent dans le fuseau horaire UTC.

  Il y a des annuaires quotidiens parce qu'il y a une durée de vie à l'échelle
  du système pour les données, elle est supprimée.

  Puisque tous les clients verront les répertoires, et donc les configurations
  des clients les incluront.  il serait sage de considérer le nom du compte
  public, et relativement statique.

  Les sources déterminent qui peut accéder à leurs données, en spécifiant à
  quelle grappe envoyer les données.

feeder
  un utilisateur autorisé à s'abonner ou à générer des données, mais considéré
  comme représentant une pompe. Cet utilisateur local de pompe serait utilisé
  pour exécuter des processus tels que sarra, le routage des rapports report
  avec des shovels, etc....

Admin
  Un utilisateur autorisé à gérer la pompe locale. C’est le vrai rabbitmq-server
  administrateur. L’administrateur exécute sr_audit pour créer/supprimer des échanges,
  utilisateurs, ou nettoyer les files d’attente inutilisées, etc.


Exemple d'un fichier admin.conf valide complet, pour un hôte nommé *blacklab* ::

  cluster blacklab
  admin amqps://hbic@blacklab/
  feeder  amqps://feeder@blacklab/
  declare source goldenlab
  declare subscriber anonymous

Un credentials.conf correspondant ressemblerait à::

  amqps://hbic:hbicpw@blacklab/
  amqps://feeder:feederpw@blacklab/
  amqps://goldenlab:puppypw@blacklab/
  amqps://anonymous:anonymous@blacklab/
