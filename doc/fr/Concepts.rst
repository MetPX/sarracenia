
===============================
Concepts généraux de Sarracenia
===============================

Le présent document décrit idées fondamentales à Sarracénia.
Il n'est pas clair dans quelle mesure ces informations sont directement 
applicables à une utilisation normale, mais il semble que cette information 
devrait être disponible *en quelque part*.

.. contents::

Introduction
------------

Les pompes Sarracenia forment un réseau. Le réseau utilise des courtiers 
( *broker* ) amqp pour modéré les transferts de fichiers entre les pompes. On
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
également être mis en place. Les deux mécanismes actuelles sont le web et SFTP. 
Dans le cas le plus simple, tous les composants se trouvent sur le site 
Web du même serveur, mais cela n'est pas nécessaire. Le courtier pourrait 
être sur un serveur différent de l´origine et la destination d'un transfert.

La meilleure façon d'effectuer des transferts de données est d'éviter les 
sondages (examination récurrente de répertoires afin de détecter des 
changements de fichiers.) C'est plus efficace si les rédacteurs peuvent 
être amenés à émettre des messages sr_post (*avis*) appropriés. De même, 
lors de la livraison, il est idéal si les destinataires utilisent 
sr_subscribe, et un plugin on_file pour déclencher leur traitement ultérieur,
de sorte que le fichier est qui leur a été remis sans sondage. C'est la façon
la plus efficace de travailler, mais... il est entendu que pas tous les logiciels
ne seront coopératifs. Pour démarrer le flot en Sarracenia dans ces cas,
ca prend des outils de sondage:  sr_poll (à distance), et sr_watch (locale.)

D'une manière générale, Linux est la principale cible de déploiement et la 
seule plate-forme sur laquelle les configurations de serveur sont déployées.
D'autres plates-formes sont utilisées en configuration client.  Ceci 
n´est pas une limitation, c'est juste ce qui est utilisé et testé. 
Implémentations de la pompe sur Windows devrait fonctionner, ils ne 
sont tout simplement pas testés.


Corréspondance des concepts AMQP avec Sarracenia
------------------------------------------------

Une chose que l'on peut dire sans risque est qu'il faut comprendre un peu l'AMQP
pour travailler avec Sarracenia. L'AMQP est un sujet vaste et intéressant en 
soi. On ne tente pas de toute expliquer ici. Cette section fournit juste
un peu de contexte, et introduit seulement les concepts de base nécessaires à la 
compréhension et/ou à l'utilisation de la Sarracenia. Pour plus d'informations
sur l'AMQP lui-même, un ensemble de liens est maintenu à l'adresse suivante
le site web `Metpx <http://github.com/MetPX/blob/master/sarracenia/doc/fr/sarra.html#amqp>`_ 
mais un moteur de recherche révèlera aussi une richesse matérielle.

.. image:: AMQP4Sarra.svg
    :scale: 50%
    :align: center

Un serveur AMQP s'appelle un courtier. Le mot *Courtier* est parfois utilisé pour 
faire référence au logiciel, d'autres fois serveur exécutant le logiciel de 
courtage (même confusion que *serveur web*).  ci-dessus, le vocabulaire de 
l'AMQP est en orange, et les termes de sarracénie sont en bleu. Il y a
de nombreuses et différentes implémentations de logiciels de courtage. Nous 
utilisons rabbitmq. Nous n'essayons pas d´être spécifique au rabbitmq, mais 
les fonctions de gestion diffèrent d'une implémentation à l'autre.

Les *Queues* (files d´attentes) sont généralement prises en charge de manière transparente, mais vous avez besoin de connaître
   - Un consommateur/abonné crée une file d'attente pour recevoir des messages.
   - Les files d'attente des consommateurs sont *liées* aux échanges (langage AMQP).
   
Un *exchange* est un entremeteur entre *publisher* et les files d´attentes du
*consumer* 
   - Un message arrive d'une source de données.
   - l´avis passe à travers l'échange, est-ce que quelqu'un est intéressé par ce message ?
   - dans un échange basé sur un *topic*, le thème du message fournit la *clé d'échange*.
   - intéressé : comparer la clé de message aux liaison des *queues de consommateurs*.
   - le message est acheminé vers les *files d'attente des consommateurs* intéressés, ou supprimé s'il n'y en a pas.

Plusieurs processus peuvent partager une *files d'attente*, ils enlèvent les messages à tour de rôle.
   - Ceci est fortement utilisé pour sr_sarra et sr_subcribe multiples instances.
   
Queues* peut être *durable*, donc même si votre processus d'abonnement meurt,
  - si vous revenez dans un délai raisonnable et que vous utilisez la même file d'attente,
  - vous n'aurez manqué aucun message.
  
Comment décider si quelqu'un est intéressé.
   - Pour la sarracénie, nous utilisons (standard AMQP) *échanges thématiques*.
   - Les abonnés indiquent les thèmes qui les intéressent et le filtrage se fait côté serveur/courtier.
   - Les thèmes sont juste des mots-clés séparés par un point. wildcards : # correspond à n'importe quoi, * correspond à un mot.
   - Nous créons la hiérarchie des thèmes à partir du nom du chemin d'accès (mappage à la syntaxe AMQP).
   - La résolution et la syntaxe du filtrage des serveurs sont définies par l'AMQP. (. séparateur, # et * caractères génériques)
   - Le filtrage côté serveur est grossier, les messages peuvent être filtrés après le téléchargement en utilisant regexp 

topic_prefix ?  Nous commençons l'arborescence des sujets avec des champs fixes.
     - v02 la version/format des messages de sarracénie.
     - post .... le type de message, il s'agit d'une annonce
       d'un fichier (ou d'une partie d'un fichier) disponible.


Sarracenia est une application AMQP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MetPX-Sarracenia n'est qu'un léger enrobage autour de l'AMQP.

- Une pompe de données MetPX-Sarracenia est une application python AMQP qui utilise un (rabbitmq).
  pour coordonner les transferts de données des clients SFTP et HTTP, et accompagne un
  serveur web (apache) et serveur sftp (openssh), souvent sur la même adresse en face de l'utilisateur.

- Dans la mesure du possible, nous utilisons leur terminologie et leur syntaxe.
  Si quelqu'un connaît l'AMQP, il comprend. Si ce n'est pas le cas, ils peuvent faire des recherches.

  - Les utilisateurs configurent un *courtier*, au lieu d'une pompe.
  - par convention, le serveur virtuel par défaut'/' est toujours utilisé. (n'a pas encore ressenti le besoin d'utiliser d'autres serveurs virtuels)
  - les utilisateurs peuvent explicitement choisir leurs noms *files d'attente*.
  - les utilisateurs définissent *subtopic*,
  - les sujets avec séparateur de points sont transformés au minimum, plutôt qu'encodés.
  - file d'attente *durable*.
  - nous utilisons des *en-têtes de message* (langage AMQP pour les paires clé-valeur) plutôt que d'encoder en JSON ou dans un autre format de charge utile.

- réduire la complexité par le biais de conventions.
   - n'utiliser qu'un seul type d'échanges (Topic), prendre soin des fixations.
   - conventions de nommage pour les échanges et les files d'attente.
      - les échanges commencent par x.
        - xs_Weather - l'échange pour la source (utilisateur amqp) nommé Weather pour poster des messages.
        - xpublic -- central utilisé pour la plupart des abonnés.
      - les files d'attente commencent par q\


Le flot à travers des Pompes
----------------------------

.. image:: e-ddsr-components.jpg
    :scale: 100%
    :align: center

Une description du flux conventionnel de messages par le biais d'échanges sur une pompe :

- Les abonnés se lient généralement à l'échange public pour obtenir le flux de données principal.
  c'est la valeur par défaut dans sr_subscribe.

- Un utilisateur nommé Alice aura deux échanges :

  - xs_Alice l'échange où Alice poste ses notifications de fichiers et ses messages de rapports.(via de nombreux outils)
  - xr_Alice l'échange où Alice lit ses messages de rapport (via sr_report).

- généralement sr_sarra lira à partir de xs_alice, récupérer les données correspondant à Alice´s *post* et le rendre disponible sur la pompe, en l'annonçant à nouveau sur le réseau public.

- sr_winnow peut tirer de xs_alice à la place, mais suit le même modèle que sr_sarra.

- habituellement, sr_audit --users causera des configurations de 
  pelles rr_alice2xreport de rr_alice2xreport pour lire xs_alice et copier les 
  messages de rapport sur l'échange privé xreport.

- Les administrateurs peuvent pointer sr_report à l'échange xreport pour obtenir 
  une surveillance à l'échelle du système.  Alice n'aura pas la permission de 
  faire ça, elle ne peut que regarder xl_Alice, qui aurait dû avoir
  les messages du rapport qui la concernent.

-- rr_xreport2source shovel configurations auto-générées par sr_audit look 
   at messages for the utilisateur Alice local dans xreport, et les envoie à 
   xl_Alice.

L'objectif de ces conventions est d'encourager un mode de fonctionnement 
raisonnablement sûr. Si un message est tiré de xs_Alice, alors le processus de
lecture est responsable de ce qui suit en s'assurant qu'il est étiqueté comme
venant d'Alice sur ce cluster. Cela permet d'éviter certaines types de 
´spoofing´ comme les messages ne peuvent être affichés que par les
propriétaires appropriés.


