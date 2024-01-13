
Status: Draft

===================
Conception Strawman
===================

.. section-numbering::

Ce document reflète la conception actuelle résultant de discussions et de réflexions
à un niveau plus détaillé que le document d’esquisse.  Voir `Aperçu <Outline.html>`_
pour une vue d’ensemble des exigences de conception.  Voir 'cas d’utilisation `<use-cases.html.html>`_ pour
une exploration de la fonctionnalité du fonctionnement de cette conception dans différentes situations.
La manière de progresser vers une mise en œuvre fonctionnelle est décrite dans le `plan <plan.html>`_.

.. contents::

Hypothèses/contraintes
----------------------

 - Existe-t-il des systèmes de fichiers en cluster disponibles partout ? Non.

 - Une équipe opérationnelle peut vouloir surveiller/alerter lorsque certains transferts rencontrent des difficultés.

 - La sécurité peut vouloir exécuter une analyse différente sur différents trafics (chaque bloc?)
   La sécurité peut nous demander de refuser certains types de fichiers, afin qu’ils subissent des analyses plus lourdes.
   ou effectuez une analyse plus lourde sur ces types de fichiers.

 - Les zones extranet ne peuvent pas initier de connexions aux zones internes.
   Les zones extranet reçoivent des connexions entrantes de n’importe où.

 - Les zones d’opérations gouvernementales peuvent initier des connexions n’importe où.
   cependant, la science est considérée comme une sorte d’extranet pour tous les partenaires.

 - Personne ne peut initier de connexions dans les réseaux partenaires, mais tous les départements partenaires
   peuvent initier des connexions dans science.gc.ca zone.  Dans les zones scientifiques, il y a le système de
   fichiers partagés, où les serveurs accèdent à un système de fichiers commun orienté cluster, ainsi
   qu’à quelques petites zones restreintes, où l’accès est très limité pour assurer la disponibilité.

 - Au sein du CNRC, il y a des laboratoires avec de l’équipement qui ne peut pas être entretenu, du point de vue des logiciels,
   pour corriger les vulnérabilités divulguées en raison de dépendances excessives aux tests (c.-à-d. certifier
   qu’un agitateur de train fonctionne toujours après l’application d’un patch.)  Ces systèmes n’ont pas accès
   à Internet, seulement à quelques autres systèmes sur le site.

 - Les collaborateurs sont des entités universitaires, d’autres gouvernements ou commerciaux dont les
   scientifiques du gouvernement échangent des données.

 - Les collaborateurs se connectent aux ressources extranet à partir de leurs propres réseaux.
   De la même façon que des partenaires, (sous réserve d’exceptions) aucune connexion ne peut être initiée
   à un réseau de collaborateurs.

 - Il n’y a pas de proxys, aucun système dans l’extranet n’a reçu d’autorisations exceptionnelles pour
   Initier des connexions entrantes.  Protocoles de stockage de fichiers, etc. sont complètement isolés entre
   eux. Aucun système de fichiers ne traverse les limites des zones réseau.

 - Une méthode pour améliorer la fiabilité du service consiste à utiliser les services internes à des fins internes
   et réserver des services destinés au public aux utilisateurs externes.  Des services isolés à l’intérieur
   sont complètement imperméables aux 'intempéries' d’Internet (DDOS de diverses formes, charge, etc...)
   Les charges internes et externes peuvent être mises à l’échelle indépendamment.


Nombre de commutateurs
----------------------

L’application est censée prendre en charge n’importe quel nombre de topologies, c’est-à-dire
n’importe quel nombre de pompes S = 0,1,2,3
peut exister entre l’origine et la livraison finale, et faire ce qu’il faut.

Pourquoi tout n’est-il pas point à point, ou quand insérez-vous une pompe?

 - les règles de topologie/firewall du réseau nécessitent parfois d’être au repos dans une zone de transfert entre deux
   organisations.  Les exceptions à ces règles créent des vulnérabilités, alors il vaux mieux éviter.
   Chaque fois que le trafic empêche d’initier une connexion, cela indique qu'une pompe Store & Forward
   peut être nécessaire.

 - topologie physique.  Bien que la connectivité puisse être présente, l’utilisation optimale de
   la bande passante peut impliquer de ne pas prendre le chemin par défaut de A à B, mais peut-être passer par C.

 - quand le transfert n’est pas 1:1, mais 1:<source ne sait pas comment> beaucoup. Le pompage prend
   soin de l’envoyer à plusieurs points.

 - lorsque les données sources doivent être disponibles de manière fiable.  Cela se traduit par la
   réalisation de nombreuses copies,
   plutôt qu’une seul, il est donc plus facile pour la source de publier une fois et d’avoir le réseau
   s’occuper de la réplication.

 - Pour des raisons de gestion, vous souhaitez observer de manière centralisée les transferts volumineux de données.

 - pour des raisons de gestion, d’acheminer les transferts d’une certaine manière.

 - pour des raisons de gestion, pour s’assurer que les échecs de transfert sont détectés et escaladés
   quand importants. Ils peuvent être corrigés plutôt que d’attendre une surveillance ad hoc pour détecter
   le problème.

 - Pour les transferts asynchrones.  Si la source a beaucoup d’autres activités, elle peut vouloir
   confier la responsabilité à un autre service pour effectuer des transferts de fichiers potentiellement longs.
   La pompe est insérée très près de la source et est full store & forward. sr_post
   se termine (presque instantanément), et à partir de ce moment-là, le réseau de pompage gère les transferts.


Sélection des fonctionnalités AMQP
----------------------------------

AMQP est un protocole universel de transmission de messages avec de nombreuses options différentes pour prendre en charge de nombreuses
différents modèles de messagerie.  MetPX-sarracenia spécifie et utilise un petit sous-ensemble de
modèles AMQP.  En effet, un élément important du développement de la sarracenia a été de choisir parmi les
de nombreuses possibilités un petit sous-ensemble de méthodes qui sont générales et faciles à comprendre,
pour maximiser le potentiel d’interopérabilité.

Spécifier l’utilisation d’un protocole seul peut être insuffisant pour fournir suffisamment d’informations pour
l’échange de données et l’interopérabilité.  Par exemple, lors de l’échange de données via FTP, un certain nombre de choix
doivent être faits au-delà du protocole de base.

 - utilisation authentifiée ou anonyme ?
 - comment signaler qu’un transfert de fichier est terminé (bits d’autorisation? suffixe? préfixe?)
 - convention de nommage.
 - transfert texte ou binaire.

Des conventions convenues au-delà du simple FTP (IETF RFC 959) sont nécessaires.

À l’instar de l’utilisation du FTP seul comme protocole de transfert est insuffisant pour spécifier
une procédure complète de transfert de données, l’utilisation de l’AMQP, sans plus d’informations, est incomplète.


AMQP 1.0 standardise le protocole sur le câble, mais laisse de côté de nombreuses fonctionnalités
de l’interaction du courtier. Comme le recours à des courtiers est la clé de l’utilisation par sarracenia,
était un élément fondamental des normes antérieures, et comme la norme 1.0 est relativement controversée,
ce protocole suppose un courtier standard antérieur à 1.0, comme le fournissent de nombreux courtiers
gratuits, tels que RabbitMQ, souvent appelé 0,8, mais 0,9 et post 0,9.
Les courtiers sont également susceptibles de bien interopérer.

Dans AMQP, de nombreux acteurs différents peuvent définir des paramètres de communication. Pour créer un
modèle de sécurité, Sarracenia contraint ce modèle : les clients sr_post ne sont pas censés déclarer
des échanges.  Tous les clients sont censés utiliser les échanges existants qui ont été déclarés par
les administrateurs de courtiers.  Les autorisations client sont limitées à la création de files
d’attente pour leur propre usage,
en utilisant des schémas de nommage convenus.  File d’attente pour le client : qc_<user>.????

Les échanges topic-based sont utilisés exclusivement. AMQP prend en charge de nombreux autres types d’échanges,
mais sr_post envoye la rubrique afin de prendre en charge le filtrage côté serveur à l’aide du topic
basé sur le filtrage.  Les rubriques reflètent le chemin d’accès des fichiers annoncés, ce qui permet un
filtrage direct côté serveur, complété par un filtrage côté client à la réception des messages.

La racine de l’arborescence des topics est la version de la charge utile du message. Cela permet aux courtiers uniques
de prendre facilement en charge plusieurs versions du protocole en même temps pendant les transitions. v02
est la troisième itération du protocole et les serveurs existants prennent régulièrement en charge les versions précédentes
simultanément de cette manière. Le deuxième topic de l’arborescence des topics définit le type de message.
Au moment de la rédaction de cet article : v02.post est le préfixe de topic pour les messages de notification actuels.

Les messages AMQP contiennent des messages de notification, pas de données de fichier réelles. AMQP est
optimisé pour et assume des petits messages. Garder les messages petits permet un débit maximal des messages
et permet aux clients qui d'utiliser des mécanismes de priorité basés sur le transfert de données,
plutôt que sur les messages de notification. Accommoder des messages volumineux créerait de nombreuses
complications pratiques et nécessiterait inévitablement la définition d’une taille de fichier maximale
à inclure dans le message lui-même, ce qui entraîne de la complexité pour couvrir plusieurs cas.

sr_post est destiné à être utilisé avec des fichiers arbitrairement volumineux, via la segmentation et le multi-streaming.
Les blocs de fichiers volumineux sont annoncés indépendamment, et les blocs peuvent suivre différents chemins
entre la pompe initiale et la livraison finale.

Les vhosts AMQP ne sont pas utilisés. Je n’en ai jamais vu le besoin. Les commandes prennent en charge leur option,
mais il n’y avait aucun but visible à les utiliser.

Les aspects de l’utilisation de l’AMQP peuvent être des contraintes ou des caractéristiques :

 - Les interactions avec un courtier sont toujours authentifiées.

 - Nous définissons le *anonymous* pour une utilisation dans de nombreuses configurations.

 - Les utilisateurs s’authentifient auprès du cluster local uniquement. Nous n’imposons aucune
   sorte d’informations d’identification ou de propagation d’identité ou de fédération, ou de confiance distribuée.

 - Les pompes représentent les utilisateurs en transférant des fichiers en leur nom, il n’est pas nécessaire
   d’inclure des informations sur les utilisateurs des sources ultérieurement dans le réseau.

 - Cela signifie que si l’utilisateur A de S0 est défini et qu’un utilisateur reçoit le même nom sur S1,
   ils peuvent entrer en collision. triste. Accepté comme limitation.

Application
-----------

Description de la logique d’application pertinente pour la discussion. Il existe un "plan de contrôle"
où les messages de notification concernant les nouvelles données disponibles sont mises en place et
les messages de journal signalant l’état des transferts des mêmes données sont acheminés entre
les utilisateurs du plan de contrôle et les pompes. Une pompe est un courtier AMQP et les utilisateurs
s’authentifient auprès du courtier. Les données peuvent (la plupart du temps) avoir une autre
méthode d’authentification différente.

Il existe des cas d’utilisation de sécurité très différents pour le transfert de fichiers :

 1. **Diffusion publique** des données sont produites, dont la confidentialité n’est pas un problème,
    le but est de diffuser à tous ceux qui sont intéressés aussi rapidement et de manière aussi fiable
    que possible, impliquant potentiellement de nombreuses copies. L’authentification des données est
    généralement null dans ce cas. Les utilisateurs émettent simplement des requêtes HTTP GET sans
    authentification. Pour l’authentification AMQP, cela peut être fait de manière anonyme, sans que
    les fournisseurs ne puissent surveiller.  S’il doit y avoir un support de la source de données,
    la source affectera un utilisateur non anonyme pour le trafic AMQP, et le client s’assurerait
    que la journalisation fonctionne, ce qui permettrait au fournisseur de surveiller et
    alerter lorsque des problèmes surviennent.

 2. **Transfert privé** Les données exclusives sont générées et doivent être déplacées vers un endroit
    où elles peuvent être archivé et/ou traité efficacement, ou partagé avec des collaborateurs spécifiques.
    Le trafic AMQP et HTTP doit être chiffré avec SSL/TLS.  L’authentification est généralement courante
    entre AMQP et HTTPS. Pour Apache httpd, la méthode htpasswd/htaccess devra être configurée en permanence
    par le système de livraison. Ces transferts peuvent avoir des exigences de haute disponibilité.

 3. **Transfert par des tiers** Le plan de contrôle est explicitement utilisé uniquement pour contrôler le
    transfert, l’authentification aux deux extrémités se fait séparément.  Les utilisateurs s’authentifient
    auprès de la pompe sans données ou une pompe SEP avec AMQP, mais l’authentification aux deux extrémités
    est hors du contrôle de Sarracenia.  Le transfert par des tiers est limité à S=0. Si les données ne
    traversent pas la pompe, elles ne peuvent pas être transmises. Aucun routage n’est donc pertinent dans ce cas.
    Cela dépend également de la disponibilité des deux points finaux, donc plus difficile à assurer dans la pratique.

Les transferts publics et privés sont destinés à soutenir des chaînes arbitraires de pompes entre
*source* et *consommateur*. Les cas dépendent du routage des messages de notification et des messages de journal.


.. NOTE::
   Routage vers l’avant...  Transferts privés et publics... Pas encore clair, toujours en considération.
   Ce qui est écrit ici à ce sujet est provisoire. On se demande si on divise, et on fait
   public d’abord, puis privé plus tard?

Pour simplifier les discussions, les noms seront sélectionnés avec un préfixe things selon le type
de l’entité:

 - Les échanges commencent par x.
 - Les files d’attente commencent par q.
 - Les utilisateurs commencent par u. Les utilisateurs sont également appelés *sources*
 - Les serveurs commencent avec svr
 - Les clusters commencent par c
 - 'pompes' est utilisé comme synonyme de cluster, et ils commencent par S (S majuscule) : S0, S1, S2...

Sur les pompes:
 - Les utilisateurs que les pompes utilisent pour s’authentifier les uns les autres sont des
   **interpump accounts**. Un autre mot: **feeder** , **concierge** ?
 - Les utilisateurs qui injectent des données dans le réseau sont appelés **sources**.
 - Les utilisateurs qui s’abonnent aux données sont appelés **consumers**.


Routage
-------

Il existe deux flux distincts à acheminer : les messages de notification et les journaux.
L’en-tête suivant dans les messages concerne le routage, qui est défini dans tous les messages.

 - *source* - l’utilisateur qui a injecté les messages de notification d’origine.
 - *source_cluster* - le cluster où la source a injecté les messages de notification.
 - *to_clust* - la liste séparée par des virgules des groupes de destination.
 - *private* - le drapeau pour indiquer si les données sont privées ou publiques.

Un objectif important du routage des messages de notification est que la *source* décide où vont
les messages de notification, donc le pompage des produits individuels doit être effectué uniquement
sur le contenu des messages de notification, et non sur une configuration d’administrateur.

Les administrateurs configurent les connexions interpompes (via SARRA et d’autres composants)
pour s’aligner sur les topologies de réseau, mais une fois configurées, toutes les données
doivent circuler correctement avec seules les commandes de routage initiées par la source.
Une configuration peut être nécessaire sur toutes les pompes chaque fois qu’une nouvelle
pompe est ajoutée au réseau.


Routage des publications
~~~~~~~~~~~~~~~~~~~~~~~~

Le routage des publications est le routage des messages de notification annoncés par les données *sources*.
Les données correspondant à la source qui suivent la même séquence de pompes que les messages de notification
elles-mêmes.  Lorsqu’un message de notification est traité sur une pompe, il est téléchargé, puis le
message de notification est modifié pour refléter la disponibilité de la pompe du saut suivant.

Les messages de publication sont définis dans la page de manuel sr_post(7).  Ils sont initialement émis par *sources*,
publié à xs_source.  Après la pré-validation, ils passent (avec les modifications décrites dans Sécurité) à
xPrivate ou xPublic.

.. note::
   FIXME: Provisoire!?
   Si ce n’est pas un échange séparé, alors n’importe qui peut voir n’importe quel message de notification
   (pas les données, mais oui le message de notification).
   Je pense que ce n’est pas bon.

Pour les données publiques, les *feeders* des pompes en aval se connectent à xPublic.
Ils regardent l’en-tête to_clust dans chaque message et consultent un fichier post2cluster.conf.
post2cluster.conf est juste une liste de noms de cluster configurés par l’administrateur ::

        ddi.cmc.ec.gc.ca
        dd.weather.gc.ca
        ddi.science.gc.ca 

Cette liste de clusters est censée être les clusters qui sont accessibles en traversant
cette pompe.  Si un cluster dans post2cluster.conf est répertorié dans la to_clust du
champ de message, puis les données doivent (?).
Des *feeders* distincts en aval se connectent à xPrivate pour les données privées.  Seuls les *feeders* sont
autorisé à se connecter à xprivate.

.. Note::
   FIXME: peut-être alimenter des échanges privés spécifiques pour chaque feeder?  x2ddiedm, x2ddidor, x2ddisci ?
   L’utilisation d’un xPrivate signifie que les pompes peuvent voir les messages qu’elles ne sont peut-être
   pas autorisées à télécharger (problème moindre qu’avec xPublic, mais dépend de la fiabilité de la pompe en aval.)

Journaux de routage
~~~~~~~~~~~~~~~~~~~

Les messages de journal sont définis dans la page de manuel sr_log(7).  Ils sont émis par les *consommateurs* à la fin,
ainsi que des *feeders* lorsque les messages traversent les pompes.  Les messages de journal sont publiés sur
l’échange xl_<user> et après validation du journal mis en fil d’attente pour l’échange XLOG.

Les messages en xlog destinés à d’autres clusters sont acheminés vers des destinations par
le composant Log2Cluster en utilisant le fichier de configuration log2cluster.conf.  log2cluster.conf
utilise des champs séparés par des espaces : le premier champ est le nom du cluster (défini selon soclust dans
messages de notification, le second est la destination pour envoyer les messages de journal pour publication
provenant de ce cluster) Exemple, log2cluster.conf::

      clustername amqp://user@broker/vhost exchange=xlog

Lorsque la destination du message est le cluster local, log2user (log2source ?) copie
les messages où source=<user> à sx_<user>.

Lorsqu’un utilisateur souhaite afficher ses messages, il se connecte à sx_<user> et s’abonne.
Cela peut être fait en utilisant *sr_subscribe -n --topic_prefix=v02.log* ou l’équivalent *sr_log*.


Modèle de sécurité
------------------



Utilisateurs, files d’attente et échanges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Chaque utilisateur Alice, sur un courtier auquel elle a accès :
 - a un xs_Alice d’échange, où elle écrit ses messages de notification et lit ses journaux.
 - a un xl_Alice d’échange, où elle écrit ses messages de journal.
 - peut créer des files d’attente qs_Alice\_.* pour se lier aux échanges.

Les commutateurs se connectent les uns aux autres à l’aide de comptes inter-échanges.
 - Alice peut créer et détruire ses propres files d’attente, mais personne d’autre.
 - Alice ne peut écrire qu’à son xs_exchange,
 - Les échanges sont gérés par l’administrateur, et non par n’importe quel utilisateur.
 - Alice ne peut publier que les données qu’elle publie (il s’agira d’elle)

.. NOTE::
   Testeur ^q_tester.*     ^q_tester.*|xs_tester    ^q_tester.*|^xl_tester$
   Laissant toutes les autorisations pour les files d’attente pour les utilisateurs AMQP donne
   également l’autorisation de créer/configurer/écrire des objets AMQP dont le nom commence par q_tester
   dans cet exemple.

Pré-validation
~~~~~~~~~~~~~~

La pré-validation fait référence aux contrôles de sécurité et d’exactitude effectués sur
les informations fournies par le message de notification avant le téléchargement des données elles-mêmes.
Certains outils peuvent appeler cela *validation des messages*

 - nettoyage des entrées (recherche d’erreurs/entrées malveillantes.)
 - un nombre indéfini de contrôles qui doivent être configurables (script ?)
 - varient selon la configuration et l’installation (tailles)

Lors de la lecture d’une source :
 - un message de notification arrive sur xs_Alice, d’un utilisateur connecté en tant qu’Alice.
 - écrase la source pour être Alice : source=Alice ... ou rejeter?
 - définit certains en-têtes pour lesquels nous ne faisons pas confiance aux utilisateurs : cluster=
 - Définissez l’en-tête du cluster sur local.

Lecture à partir d’un chargeur :
 - La source n’a pas d’importance. (les feeders peuvent représenter d’autres utilisateurs)
 - Ne pas écraser la source.
 - s’assurer que le cluster n’est pas un cluster local (car ce serait un mensonge.) ?

De toute façon:
 - vérifier la taille de partitionnement, si elle dépasse le maximum de la pompe, rejeter.
 - Vérifiez les limitations de bande passante en place. En cas de dépassement, attendez.
 - Vérifiez la limite d’utilisation du disque en place. En cas de dépassement, attendez.
 - Si l’indicateur privé est défini, alors acceptez en copiant sur xPrivate
 - Si l’indicateur privé n’est pas défini, alors acceptez par copie à xPublic

Résultats:
 - Accepter signifie : mettre en fil d’attente le message vers un autre échange (xinput) pour téléchargement.
 - Rejeter signifie : ne pas copier le message (toujours accepter & ack pour qu’il quitte la fil d’attente)
   message du journal du produit.
 - Hold signifie : ne pas consommer... mais dormez un moment.

Le hold est pour des raisons de type défaillance temporaire, telles que la bande passante de l’espace disque.
Étant donné que ces raisons sont indépendantes du message particulier, le hold s’applique à
l’ensemble de la fil d’attente, pas seulement le message.

Après le prétraitement, un composant tel que sr_sarra suppose que le message de notification est bon,
et le traite simplement. Cela signifie qu’il récupérera les données de la source de publication.
Une fois les données téléchargées, elles passent par la post-validation.


Post-Validation
~~~~~~~~~~~~~~~

Lorsqu’un fichier est téléchargé, avant de l’annoncer à nouveau pour des sauts ultérieurs,
il passe par une analyse.  Les outils peuvent appeler ceci *validation de fichier*:

 - lorsqu’un fichier est téléchargé, il passe par post-validation,
 - Invoquer un ou plusieurs antivirus choisis par la sécurité
 - les scanners ne seront pas les mêmes partout, même à différents endroits à l’intérieur de
   La même organisation peut avoir des normes d’analyse différentes (fonction sur la zone de sécurité).

 - Accepter signifie : il est acceptable d’envoyer ces données à d’autres sauts du réseau.
 - Rejeter signifie : ne pas transmettre ces données (éventuellement supprimer la copie locale.)
   Essentiellement une *quarantaine*

Validation du journal
~~~~~~~~~~~~~~~~~~~~~

Lorsqu’un client comme sarra ou subscribe termine une opération, il crée un message de journal
correspondant au résultat de l’opération.  (C’est une granularité beaucoup plus faible qu’un
fichier journal local.) Il est important qu’un client ne puisse pas usurper l’identité d’un autre
lors de la création de messages de journal.

 - Les messages dans les échanges n’ont aucun moyen fiable de déterminer qui les a insérés.
 - Ainsi, les utilisateurs publient leurs messages de journal sur l'échange sl_<user>.
 - Pour chaque utilisateur, le lecteur de journal lit le message et écrase l’utilisateur consommateur
   pour forcer la correspondance. (si vous lisez un message de sl_Alice, cela force le champ utilisateur consommateur
   à être Alice) voir sr_log(7) pour le champ d'utilisateur
 - sl_* sont en écriture seule pour tous les utilisateurs, ils ne peuvent pas lire leurs propres messages
   de notification pour cela.
 - Y a-t-il une vérification de la consommation d’host?
 - Accepter un message de journal signifie publier sur l’échange xlog.
 - Seules les fonctions d’administration peuvent lire à partir de xlog.
 - Le traitement en aval provient de l’échange XLOG qui est supposé être propre.
 - Rejeter un message de journal signifie de le copier nulle part.

 - Le contrôle des ressources n’a pas de sens lorsque des canaux sont utilisés pour le routage inter-pompes.
   Essentiellement, tout ce que les pompes en aval peuvent faire est de transmettre au cluster source.
   Les pompes recevant les messages de journal ne doivent pas convertir l’utilisateur consommateur sur ces liens.
   Preuve de la nécessité d’une sorte de réglage : réglage entre l’utilisateur et entre les pompes.


.. NOTE::
   FIXME : si vous rejetez un message de journal, génère-t-il un message de journal ?
   Potentiel de déni de service en générant simplement des messages de journal de tourbières infinis.
   Il est triste que si une connexion est mal configurée en tant qu’utilisateur, lorsqu’elle est inter-pompe,
   Cela entraînera l’abandon des messages.  Comment détecter une erreur de configuration?

Transfert de données privé vs public
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dans le passé, les transferts ont été publics, il s’agissait simplement de partager des informations publiques.
Une exigence cruciale du paquet est de prendre en charge les copies de données privées, lorsque les
fins du transfert ne sont pas partagées avec d’autres personnes arbitraires.

.. NOTE::
   FIXME: Cette section est une idée à moitié cuite! Je ne sais pas comment les choses vont tourner.
   problème de base: Alice se connectant à S1 veut partager avec Bob, qui a un
   compte sur S3.  Pour aller de S1 à S3, il faut traverser S2.  La façon normale
   de ce routage est effectué est via un abonnement sr_sarra à xpublic sur S1, et
   S2.  Ainsi, Eve, un utilisateur sur S1 ou S2, peut voir les données, et probablement les télécharger.
   sauf si les autorisations http sont définies sur refuser sur S1 et S2. Eve n’aurait pas accès.
   Implémenter via http/auth permettant des comptes inter-pompes sur S2
   pour accéder au compte S1/<private> et S3 à S2/<private>. puis autorisez Bob sur
   S3.

Il existe deux modes d’envoi de produits via un réseau, privé et public.
Avec l’envoi public, l’information transmise est supposée être publique et disponible
à tous les arrivants. Si quelqu’un voit les données sur une pompe intermédiaire, alors ils sont susceptibles
de pouvoir les télécharger à volonté sans autres arrangements.  Les données publiques sont publiées
pour les copies inter-pompes utilisant l’échange xPublic, auquel tous les utilisateurs peuvent également accéder.

Les données privées ne sont mises à la disposition que des personnes explicitement autorisées à y accéder.
Les données privées sont mises à disposition uniquement sur l’échange xPrivate.  Seul les utilisateurs
de canal Interpump ont accès à ces messages.

.. NOTE::
   - Deux échanges sont-ils nécessaires ou la définition d’autorisations est-elle suffisante ?
   - si personne sur B n’est autorisé, alors seul C est capable de télécharger à partir de B,
     ce qui fonctionne tout simplement.
   - Cela ne fonctionne qu’avec http car la définition des autorisations sftp va être un enfer.
   - Si vous utilisez seulement http, alors Even peut toujours voir toutes les publications,
     mais pas obtenir de données, sauf si xprivate se produit.

Pour les topologies SEP (voir Topologies), les choses sont beaucoup plus simples car les utilisateurs
finaux peuvent simplement utiliser des bits de mode.


Accès privé HTTPS
~~~~~~~~~~~~~~~~~

.. NOTE:: 
   FIXME: Pas encore conçu.
   Vraiment pas encore cuit.  Pour https, besoin de créer/gérer .htaccess (prédéfini mais généré tous les jours)
   et les fichiers .htpasswd (générés tous les jours).

Besoin d’une sorte de message adm que les sources peuvent envoyer N pompes plus tard pour modifier le contenu de .htpasswd
CRUD? Ou simplement écraser à chaque fois?  requête?

Sarra a probablement besoin de regarder cela et d’ajouter les fichiers ht* tous les jours.
Besoin de parler avec les gars de l’équipe de messagerie Web.

Comment changer les mots de passe


Topologies
----------

Questions... Il existe de nombreux choix pour la disposition des clusters. On peut faire H/A
simple sur une paire de nœuds, simple actif/passif ?  On peut aller à des conceptions évolutives
sur un tableau de nœuds, ce qui nécessite une charge d'équilibreur avant les nœuds de traitement.
Les disques d’un cluster peuvent être partagés ou individuels sur les nœuds de traitement, tout
comme l’état du courtage.  Explorer s’il faut prendre en charge toutes les configurations,
ou pour déterminer s’il existe un modèle de conception particulier qui peut être appliqué de
manière générale.

Pour prendre ces décisions, une exploration considérable est nécessaire.

Nous commençons par nommer les topologies afin qu’elles puissent être facilement référencées dans
les discussions ultérieures. Aucune des topologies ne suppose que les disques sont pompés entre
les serveurs dans le style HA traditionnel.

D’après l’expérience, le pompage de disque est considéré comme peu fiable dans la pratique, car il implique
des problèmes complexes. Interaction avec de nombreuses couches, y compris l’application.
Les disques sont soit dédiés aux nœuds, soit un système de fichiers en cluster doit être utilisé.
On s’attend à ce que la demande porte sur ces deux cas.

Quelques documents abrégés :

Bunny
       Une instance de broker partagée/en cluster, où plusieurs nœuds utilisent un broker commun pour se coordonner.

Effet Capybara
      *capybara à travers un serpent* où un gros rongeur déforme le corps d’un serpent
      au fur et à mesure qu’il est en cours de digestion.  Symbolique d’un mauvais équilibrage de charge, où un nœud
      subit un pic de charge et ralentit excessivement.

Vannage (winnowing) d’empreintes digitales
      Chaque produit a une somme de contrôle et une taille destinées à l’identifier de manière unique, appelées
      comme empreinte digitale.  Si deux produits ont la même empreinte digitale, ils sont considérés comme
      équivalent, et un seul peut être transmis.  Dans les cas où plusieurs sources de données équivalentes
      sont disponibles, mais les consommateurs en aval préféreraient recevoir des messages de notification uniques
      des produits, les processus peuvent choisir de publier des notifications du premier produit
      avec une empreinte digitale donnée, et ignorer les suivantes.

      C’est la base de la stratégie la plus robuste pour la haute disponibilité, mais la mise en place de
      plusieurs sources pour les mêmes données, acceptant les messages de notification pour tous, mais uniquement
      en acheminant un en aval.  En fonctionnement normal, une source peut être plus rapide que les
      autres, et donc les produits de la deuxième source sont généralement "winnowed". Lorsqu’une source
      disparaît, les données de l’autre source sont automatiquement sélectionnées, au fur et à mesure que
      les empreintes digitales sont maintenant *fraiches* et utilisés, jusqu’à ce qu’une source plus rapide
      devienne disponible.

      L’avantage de cette méthode est que maintenant une décision A / B est nécessaire, de sorte que
      le temps de *pompage* est nul.  D’autres stratégies font l’objet de retards considérables
      en prenant la décision de repomper, et les pathologies que l’on pourrait résumer comme battant,
      et/ou des impasses.

Autonome
~~~~~~~~

Dans une configuration autonome, il n’y a qu’un seul nœud dans la configuration.  J’exécute tous les composants
et n’en partage aucun avec d’autres nœuds.  Cela signifie que le courtier et les services de données tels que sftp et
Apache sont sur un nœud.

Une utilisation appropriée serait une petite installation d’acquisition de données non-24x7,
pour prendre la responsabilité de la fil d’attente des données et s'éloigner de l’instrument.


DDSR : Configuration de commutation/routage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il s’agit d’une configuration plus évolutive impliquant plusieurs nœuds de Data Mover et
potentiellement plusieurs brokers. Ces clusters ne sont pas des destinations de transferts
de données, mais des intermédiaires.  Les données circulent à travers eux, mais les interroger
est plus compliqué car aucun nœud ne dispose de toutes les données disponibles. Les clients en aval
des DDSR sont essentiellement d’autres cas de sarracenia.

Plusieurs options sont encore disponibles dans ce modèle de configuration.
DDSR Un courtier par nœud ?  (ou juste un courtier (clusterisé, logique) courtier?)

Sur un pompage/routeur, une fois que la livraison a eu lieu dans tous les contextes, pouvez-vous supprimer le fichier ?
Il suffit de regarder les fichiers journaux et de cocher chaque étendue qui confirme la réception.
Lorsque le dernier confirmé, supprimez. (rend re-xmit difficile ;-)

Basé sur un seuil de taille de fichier ? Si le fichier est trop volumineux, ne le conservez pas ?

L’objectif visé comporte un certain nombre d’options de mise en œuvre, qui doivent être subdivisées aux fins d’analyse.


DDSR indépendant
~~~~~~~~~~~~~~~~

Dans Independent DDSR, il existe un équilibreur de charge qui distribue chaque connexion entrante à
un courtier individuel exécuté sur un seul nœud.

DDSR - courtier

La validation préalable à la récupération se produirait sur le courtier.  Puis re-post pour les Sarra sur les movers.

 - Chaque courtier de nœud et moteur de transfert agit indépendamment. Robustesse maximale à l’échec.
 - L’équilibreur de charge supprime les nœuds de déplacement du fonctionnement lors de la détection d’une défaillance.
 - Les fichiers individuels atterrissent, la plupart du temps entièrement sur des nœuds uniques.
 - Aucun Data Mover ne voit tous les fichiers de tous les utilisateurs d’un cluster.

CONFIRMEZ : les processus exécutés sur les nœuds individuels sont abonnés au broker local.
Très sensible à l’effet Capybara où tous les blocs de
des fichiers volumineux sont canalisés via un seul nœud de traitement.  Les transferts de
fichiers volumineux le déclencheront.

CONFIRMEZ : Les performances maximales pour un seul transfert sont limitées à un seul nœud.

Courtier partagé DDSR
~~~~~~~~~~~~~~~~~~~~~

Bien que l’espace disque des nœuds de données reste indépendant, les courtiers sont regroupés pour
former une entité logique unique.

Sur tous les nœuds, les processus de déplacement utilisent des échanges et des files d’attente communs.

 - Chaque nœud est transféré indépendamment, mais dépend du cluster de courtiers.
 - L’équilibreur de charge supprime les nœuds (courtier ou déménageur) du fonctionnement.
 - Les utilisateurs externes se connectent à des files d’attente partagées, pas à des files
   d’attente spécifiques à un nœud.
 - Les moteurs de transfert se connectent aux files d’attente de cluster, obtenant des blocs.
 - Aucun Data Mover ne voit tous les fichiers de tous les utilisateurs d’un cluster.
 - Nécessite que le courtier soit regroupé, ce qui ajoute de la complexité ici.

Dans courtier partagé DDSR, *l'effet Capybara* est minimisé en tant que blocs individuels d’un transfert et
sont répartis sur tous les nœuds de déménagement.  Lorsqu’un fichier volumineux arrive, tous les déménageurs
sur tous les nœuds peuvent ramasser des blocs individuels, de sorte que le travail est automatiquement
répartis entre eux.

Cela suppose que les fichiers volumineux sont segmentés.  Comme différents nœuds de transfert auront
différents blocs d’un fichier, et la vue de données n’est pas partagée, pas de réassemblage des fichiers
est fait.

Le regroupement de courtiers est considéré comme une technologie mature et donc relativement fiable.

DD : Configuration de la diffusion des données (AKA : Data Mart)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La configuration de déploiement sr est davantage une configuration de point de terminaison.  Chaque nœud est censé :
Avoir une copie complète de toutes les données téléchargées par tous les nœuds.   Donner une vue unifiée rend
ca beaucoup plus compatible avec une variété de méthodes d’accès, telles qu’un navigateur de fichiers (sur HTTP,
ou sftp) plutôt que de se limiter aux messages de notification AMQP.  C’est le type de vue présenté par
dd.weather.gc.ca.

Avec ce point de vue, tous les fichiers doivent être entièrement réassemblés à la réception,
avant d’annoncer la disponibilité en aval.  Les fichiers peuvent avoir été fragmentés pour
être transférés entre les pompes intermédiaires.

Il existe plusieurs options pour obtenir cet effet visible de l’utilisateur final, chacune avec des compromis.
Dans tous les cas, il y a un équilibreur de charge devant les nœuds qui distribue les demandes entrantes
de connexion à un nœud pour le traitement.

 - plusieurs nœuds de serveur.  Chacun autonome.

- SR - Load Balancer, juste redirige vers un nœud SR?
   dd1,dd2,

Le courtier sur le nœud SR a une connexion par la suite.



DD indépendant
~~~~~~~~~~~~~~

 - L’équilibreur de charge transmet les demandes entrantes à plusieurs configurations independantes.

 - Chaque nœud télécharge toutes les données.  L'espace disque requis pour les nœuds dans cette configuration
   sont beaucoup plus grands que pour les nœuds DDSR, où chaque nœud ne contient que 1/n des données.

 - Chaque nœud annonce chaque produit qu’il a téléchargé, en utilisant son propre nom de nœud, car
   Il ne sait pas si d’autres nœuds ont ce produit.

 - Une fois la connexion établie, le client communiquera exclusivement avec ce nœud.
   Les performances ultimes sont limitées par les performances du nœud individuel.

 - Les Data Movers peuvent (pour une fiabilité maximale) être configurés indépendamment, mais si les entrées
   sont sur le WAN, on peut réduire l’utilisation de la bande passante N fois en ayant N nœuds
   Partagez les files d’attente pour les sources distantes, puis effectuez des transferts locaux entre les nœuds.

CONFIRMER: *Le vannage d’empreintes digitales* est-il nécessaire pour les copies intra-cluster?

   Lorsqu’un seul nœud échoue, il cesse de télécharger et les autres n-1 nœuds continuent le transfert.

.. NOTE::
  FIXME : courtier partagé et système de fichiers partagé... Hmm...  Pourrait utiliser un deuxième courtier
  Instance pour faire un téléchargement coopératif via le vannage Fingerprint.

Shared-Broker DD
~~~~~~~~~~~~~~~~

 - Un seul broker en cluster est partagé par tous les nœuds.

 - Chaque nœud télécharge toutes les données.  Espace disque requis pour les nœuds dans cette configuration
   sont beaucoup plus grands que pour les nœuds DDSR, où chaque nœud ne contient que 1/n des données.

 - Les clients se connectent à une instance d’agent à l’échelle du cluster, de sorte que les liens de
   téléchargement peuvent provenir de n’importe quel dans le cluster.

 - Si le broker en cluster échoue, le service est en panne. (devrait être fiable)

 - Un nœud ne peut pas annoncer chaque produit qu’il a téléchargé, en utilisant son propre nom de nœud, car
   Il ne sait pas si d’autres nœuds ont ce produit.   (Annonce en tant que DD1 vs. DD)

 -Ou:

    -- Ne peut annoncer un produit qu’une fois qu’il est clair que chaque nœud actif possède le produit.
    -- 1er arrivé, 1er servi : appliquer le vannage des empreintes digitales. Annoncez uniquement le nœud qui a obtenu les données en premier.

 - Comme dans la configuration indépendante, les nœuds partagent des files d’attente et téléchargent
   une fraction des données en amont.
   Ils ont donc besoin d’échanger des données entre eux, mais cela signifie utiliser un courtier. Il
   est donc probable qu’il y aura deux courtiers accessibles par les nœuds, un nœud local et un partagé.

 - C’est plus compliqué, mais cela évite d’avoir besoin d’un système de fichiers en cluster. Hmm... Choisissez votre poison.
   démo des deux?


DD de données partagées
~~~~~~~~~~~~~~~~~~~~~~~

 - L’équilibreur de charge transmet la requête entrante à plusieurs nœuds.

 - Chaque nœud dispose d’un accès en lecture/écriture à un système de fichiers partagé/cluster.

 - Configuration du broker en cluster, tous les nœuds voient le même broker.

 - téléchargé une fois signifie disponible partout (écrit sur un disque partagé)

 - peut donc faire de la publicité immédiatement avec la spécification d’hôte partagé (DD vs DD1)

 - Si le broker en cluster échoue, le service est en panne. (devrait être fiable)

 - Si le système de fichiers en cluster échoue, le service est en panne. (??)

SEP: Shared End-Point Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La configuration SEP, tous les nœuds de déplacement sont directement accessibles aux utilisateurs.
Le courtier ne fournit pas de service de données, juste un pur courtier de messages. Peut être appelé
*sans données*, ou un *bunny*.

Le broker est exécuté en cluster et rien ne peut être dit sur les nœuds de déplacement.
Les consommateurs et les observateurs peuvent être démarrés par n’importe qui sur n’importe quelle collection de nœuds,
et toutes les données visibles à partir de n’importe quel nœud où les systèmes de fichiers de cluster offrent cet avantage.

L’administration de l’espace disque est entièrement un paramètre de configuration d'utilisateur, pas dans le
contrôle de l’application (les utilisateurs définissent directement des quotas ordinaires pour leurs systèmes de fichiers)


