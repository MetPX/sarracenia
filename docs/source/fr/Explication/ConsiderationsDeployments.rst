Considérations relatives au déploiement
=======================================

Les pompes de données Sarracenia sont souvent placées dans des réseaux de conceptions près des points de démarcation, pour fournir
un point de démarcation au niveau de l’application pour permettre l’analyse de sécurité et limiter la visibilité
dans différentes zones.  Les pompes peuvent avoir tous les services incorporés sur un seul serveur,
ou généralement le broker principal est sur un nœud dédié, et les nœuds qui effectuent le transfert de données
sont appelés *Moteurs de transport* (Transport Engines). Dans les déploiements hautes performances, chaque moteur de transport
peut avoir un courtier local pour s’occuper des transferts et des transformations locales.


Engins de transport
-------------------

Les engins de transport sont les serveurs de données interrogés par les abonnés,
par les utilisateurs finaux ou d'autres pompes. Les abonnés lisent les avis
et récupèrent les données correspondantes, en utilisant le protocole indiqué.
Le logiciel pour servir les données peut être SFTP ou HTTP (ou HTTPS).  En
configurant les serveurs pour l'utilisation, veuillez consulter la documentation
des serveurs eux-mêmes. Notez également que les protocoles additionnels peuvent
être activés par l'utilisation des plugins do\_ plugins, tels que décrit dans
le Guide de programmation.


IPv6
~~~~

Une pompe d'échantillonnage a été implémentée sur un petit VPS avec IPv6 activé.
Un client lointain connecté au courtier rabbitmq en utilisant IPv6, et
l'abonnement au httpd apache httpd a travaillé sans problèmes. *It just works*.
Il n'y a pas de différence entre IPv4 et IPv6. Sarracenia est agnostiques
aux adresses IP.

On s'attend à utiliser des noms d'hôtes, puisque l'utilisation d'adresses IP
brisera le certificat. Utilisation pour la sécurisation de la couche de
transport (TLS, aka SSL) Pas de test des adresses IP dans les URLs (dans
l'une ou l'autre IP)) a été réalisée.

Plans de Pompes
---------------

Il existe de nombreux arrangements différents dans lesquels la Sarracenia peut
être utilisée.

Dataless
  où l'on ne fait que de la Sarracenia en plus d'un courtier sans moteur de
  transfert local. Ceci est utilisé, par exemple pour exécuter sr_winnow sur
  un site pour fournir des sources de données redondantes.

Autonome
  la plus évidente, exécuter toute la pile sur un seul serveur, openssh et
  un serveur web ainsi que le courtier et Sarra lui-même. Réalise une pompe de
  données complète, mais sans redondance.

Commutateurs/Routage
  Où, afin d'atteindre des performances élevées, un cluster de nœuds autonomes
  sont placés derrière les nœuds suivants un équilibreur de charge.
  L'algorithme de l'équilibreur de charge n'est que round-robin, sans tentative
  d'association d´une source donnée avec un noeud donné. Ceci a pour effet de
  pomper différentes parties de fichiers volumineux à travers différents nœuds.
  Ainsi on verra des parties de fichiers annoncés par une telle pompe, à être
  réassemblés par les abonnés.

Diffusion des données
  Lorsque, afin de servir un grand nombre de clients, plusieurs serveurs
  identiques, chacun d'entre eux ayant un système d'exploitation complet,
  miroitent des données

FIXME :
  Ok, j'ai ouvert la grande gueule, il faut maintenant travailler sur les exemples.

Dataless ou S=0
~~~~~~~~~~~~~~~

Une configuration qui n'inclut que le courtier AMQP. Cette configuration peut
être utilisée lorsque les utilisateurs ont accès à de l'espace disque aux
deux extrémités et n'ont besoin que d'un médiateur. Voici la configuration
de hpfx.science.gc.ca, où l'espace disque HPC fournit l'espace de stockage
de sorte que la pompe ne pas besoin de pompes ou de pompes déployées pour
fournir une HA redondante aux centres de données distants.

... note::

  FIXME : exemple de configuration des pelles, et sr_winnow (avec sortie
  vers xpublic) pour permettre dans le CPS pour obtenir des données de edm
  ou dor.

Notez que si une configuration peut être sans données, elle peut toujours
utiliser rabbitmq clustering pour les besoins de haute disponibilité
(voir ci-dessous).


Dataless vannée
~~~~~~~~~~~~~~~

Un autre exemple de pompe sans données serait de fournir une sélection de
produits à partir de deux pompes en amont en utilisant sr_winnow. Le sr_winnow
est alimenté par des pelles provenant de sources en amont.  les clients locaux
se connectent simplement à cette pompe locale. sr_winnow prend le soin de ne
présenter que les produits du premier serveur à les rendres disponibles. On
configurerait sr_winnow pour la sortie vers l'échange xpublic sur la pompe.

Les abonnés locaux ne font que pointer vers la sortie de sr_winnow sur la
pompe locale. Ce est la manière dont les aliments sont mis en œuvre dans
les centres de prévision des intempéries de ECCC, où ils peut télécharger
des données à partir de n'importe quel centre national qui produit les
données en premier.


Dataless Avec Sr_poll
~~~~~~~~~~~~~~~~~~~~~

Le programme sr_poll peut sonder (vérifier si les produits sur un serveur
distant sont prêts ou modifiés.)  Pour chaque produit, il émet une avis sur la
pompe locale. On pourrait utiliser sr_subscribe n'importe où, écoutez les
annonces et obtenez les produits (à condition que l'option avoir les
informations d'identification pour y accéder)


Autonome
~~~~~~~~

Dans une configuration autonome, il n'y a qu'un seul nœud dans la configuration.
Il exécute tous les composants et n'en partage aucun avec d'autres nœuds.
Cela signifie le courtier et les services de données tels que sftp et sftp.
apache sont sur le seul nœud.

Une utilisation appropriée serait une petite installation d'acquisition de
données non 24x7, pour prendre la responsabilité des données. La mise en file
d'attente et la transmission en dehors de l'instrument. Il est redémarré
lorsque l'occasion se présente. Il s'agit simplement d'installer et de
configurer tout un moteur de flux de données, un courtier et le package.
sur un seul serveur. Les systèmes *ddi* sont généralement configurés de cette
façon.



Commutateurs/Routage
~~~~~~~~~~~~~~~~~~~~

Dans la configuration de commutation/routage, il y a une paire de machines
qui font tourner un seul courtier pour un pool de moteurs de transfert. Ainsi,
chaque transfert engine´s vue de l'espace fichier est local, mais les files
d'attente sont les suivantes globale à la pompe.

Note : Sur de tels clusters, tous les nœuds qui exécutent un composant avec
l'option le même fichier de configuration crée par défaut un ***queue**
identique. Cibler les même courtier, il force la fil d'attente à être
partagée. S'il faut l'éviter, l'utilisateur peut écraser la valeur par
défaut **queue_name** en y rajoutant **${HOSTNAME}**.  Chaque nœud aura
sa propre fil d'attente, qui ne sera partagée que par les instances du nœud.
ex : nom_de_files d'attente q_${BROKER_USER}.${PROGRAM}.${CONFIG}.${HOSTNAME}. )

Souvent, il y a un trafic interne de données acquises avant qu'elles ne
soient finalement publiées.  En tant que moyen de mise à l'échelle, souvent
les moteurs de transfert auront également des courtiers pour gérer le
trafic local, et ne publient les produits finaux qu´au coutier princiapal.
C'est ainsi que les systèmes *ddsr* sont généralement
configurés.



Considérations de sécurité
---------------------------

Cette section a pour but de donner un aperçu à ceux qui ont besoin d'effectuer un examen de sécurité.
de l'application avant la mise en œuvre.

Client
~~~~~~

Toutes les informations d'identification utilisées par l'application sont stockées.
dans le fichier ~/.config/sr3/credentials.conf, et ce fichier est forcé à 600 permissions.


Serveur/courtier
~~~~~~~~~~~~~~~~

L'authentification utilisée par les moteurs de transport est indépendante de celle utilisée pour les courtiers. Une sécurité
l'évaluation des courtiers rabbitmq et des différents moteurs de transfert en service est nécessaire pour évaluer
la sécurité globale d'un déploiement donné.


La méthode de transport la plus sûre est l'utilisation de SFTP avec des clés plutôt que des mots de passe. Sécurisé
le stockage des clés sftp est couvert dans la documentation de divers clients SSH ou SFTP. Les lettres de créance
ne fait que pointer vers ces fichiers clés.

Pour la Sarracenia elle-même, l'authentification par mot de passe est utilisée pour communiquer avec le courtier de l'AMQP,
donc l'implémentation du transport de socket crypté (SSL/TLS) sur tout le trafic des courtiers est très forte.
recommandé.

Les utilisateurs de Sarracenia sont en fait des utilisateurs définis sur des courtiers rabbitmq.
Chaque utilisateur Alice, sur un courtier auquel elle a accès :

 - a un échange xs_Alice_Alice, où elle écrit ses messages et lit ses journaux.
 - a un échange xr_Alice xr_Alice, où elle lit ses messages de rapport.
 - peut configurer (lire et reconnaître) les files d'attente nommées qs_Alice\_.* pour lier les échanges.
 - Alice peut créer et détruire ses propres files d'attente, mais pas celles des autres.
 - Alice ne peut écrire qu'à son échange (xs_Alice),
 - Les échanges sont gérés par l'administrateur, et non par n'importe quel utilisateur.
 - Alice ne peut poster que les données qu'elle publie (elle se référera à elle).

Alice ne peut pas créer d'échanges ou d'autres files d'attente qui ne figurent pas ci-dessus.

Rabbitmq fournit la granularité de la sécurité pour restreindre les noms de
mais pas leurs types. Ainsi, étant donné la possibilité de créer une fil d'attente nommée q_Alice,
une Alice malveillante pourrait créer un échange nommé q_Alice_xspecial, et ensuite configurer
Les files d'attente pour s'y lier, et établir un usage séparé du courtier non lié à la Sarracenia.

Pour éviter de telles utilisations abusives, sr_audit est un composant qui est
invoqué régulièrement à la recherche de mauvaise utilisation et de le nettoyer.

Validation des entrées
~~~~~~~~~~~~~~~~~~~~~~

Les utilisateurs tels qu'Alice publient leurs messages sur leur propre échange
(xs_Alice). Les processus qui lisent à partir de les échanges d'utilisateurs
ont une responsabilité en matière de validation. Le processus qui lit xs_Alice
(probablement un sr_sarra) écrasera tout en-tête *source* ou *cluster* écrit
dans le message avec les valeurs correctes de le cluster courant, et
l'utilisateur qui a posté le message.

L'algorithme de la somme de contrôle utilisé doit également être validé.
L'algorithme doit être connu. De même, si il y a un en-tête malformé d'une
certaine sorte, il doit être rejeté immédiatement. Seuls les messages bien
formés doit être transmise pour traitement ultérieur.

Dans le cas de sr_sarra, la somme de contrôle est recalculée lors du
téléchargement des données s'assure qu'il correspond au message. S'ils ne
correspondent pas, un message d'erreur est publié.  Si l'option
*recompute_checksum* est True, la somme de contrôle nouvellement calculée est
placée dans le message. Selon le niveau de confiance entre une paire de
pompes, le niveau de validation peut être détendue pour améliorer
les performances.

Une autre différence avec les connexions inter-pompes, c'est qu'une pompe
agit nécessairement comme un agent pour l'ensemble de la pompe sur les
pompes à distance et toutes les autres pompes pour lesquelles la pompe
est transférée. Dans ce cas, la validation est un peu différent:

 - La source va varier. (les chargeurs peuvent représenter d'autres
   utilisateurs, donc n'écrasez pas)
 - Il faut s'assurer que le cluster n'est pas un cluster local (car cela
   indique soit une boucle, une mauvaise utilisation).

Si le message échoue le test de cluster non-local, il doit
être rejeté et enregistré (FIXME: publié? hmm? à clarifier)

.. NOTE::
 FIXME:
   - if the source is not good, and the cluster is not good... cannot report back. so just log locally?

Accès au système privilégié
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les utilisateurs ordinaires (sources et abonnés) exploitent sarra dans le cadre
de leurs propres permissions sur le système, comme une commande scp. Le compte
administrateur de la pompe fonctionne également sous un compte utilisateur linux
normal et, exige des privilèges uniquement sur le courtier AMQP, mais rien sur
le système d'exploitation sous-jacent. Il est pratique d'accorder à
l'administrateur de la pompe les privilèges sudo pour la commande rabbitmqctl.

Il peut s'agir d'une seule tâche qui doit fonctionner avec des privilèges :
nettoyer la base de données, ce qui est une tâche facilement script vérifiable
qui doit être exécuté sur une base régulière. Si toute l'acquisition se fait
via sarra, alors tout ce qui suit les fichiers appartiendront à l'administrateur
de la pompe (la compte sarra), et un accès privilégié (root) n'est pas
nécessaire pour cela non plus.

Glossaire
---------

La documentation sur la Sarracenia utilise un certain nombre de mots d'une
manière particulière. Ce glossaire devrait faciliter la compréhension du
reste de la documentation.

Source
  Quelqu'un qui veut envoyer des données à quelqu'un d'autre. Pour ce faire,
  ils font des avis pour annoncés des arbres de fichiers a copier du point
  de départ vers une ou plusieurs pompes dans le réseau. Les sources
  produisent des avis qui indiquent aux autres exactement où se
  trouvent les fichier et comment les télécharger, et les
  Sources disent où ils veulent que le fichier pour se rend.

  Les sources utilisent des programmes comme `sr_post.1 <../Reference/sr3.1.html#post>`_,
  `sr_watch.1 <../Reference/sr3.1.html#watch>`_, et `sr_poll(1) <../Reference/sr3.1.html#poll>`_ créer
  leurs avis.

Abonnés
  sont ceux qui examinent les annonces au sujet des fichiers disponibles ; et
  téléchargent les fichiers qui les intéressent.

  Les abonnés utilisent `sr_subscribe(1) <../Reference/sr3.1.html#subscribe>`_


Afficher, Avis, Notification, publication,
  Ce sont des messages AMQP construits par sr_post, sr_poll, sr_poll, ou
  sr_watch pour laisser les utilisateurs savoir qu'un fichier particulier est
  prêt. Le format de ces messages AMQP est le suivant décrit par la page manuel
  `sr_post(7) <../Reference/sr3.1.html#post>`_ . Tous ces les mots sont utilisés de façon
  interchangeable. Les avis à chaque étape préservent l´origine d'origine
  du fichier, de sorte que les rapports de disposition puissent y être
  réacheminés.


Rapports
  Ce sont des messages AMQP (au format `sr_post(7) <../Reference/sr3.1.html#post>`_  format)
  construits par les consommateurs de messages, pour indiquer ce qu'une pompe
  ou un abonné donné a fait avec un fichier. Ils s'écoulent conceptuellement
  dans la direction opposée de dans un réseau, pour revenir à la source.

Pompe ou courtier
  Une pompe est un hôte exécutant Sarracenia, un serveur rabbitmq AMQP (appelé *broker*
  en langage AMQP) La pompe a des utilisateurs administratifs et gère le courtier AMQP.
  en tant que ressource dédiée. Une sorte de moteur de transport, comme un apache.
  ou un serveur openssh, est utilisé pour supporter les transferts de fichiers. SFTP, et
  HTTP/HTTPS sont les protocoles qui sont entièrement pris en charge par la Sarracenia. Pompes
  copier des fichiers à partir de quelque part, et les écrire localement. Ils ont ensuite ré-annoncé l'initiative du
  de la copie locale à ses pompes voisines, et aux abonnés utilisateurs finaux, ils peuvent
  obtenir les données de cette pompe.

.. Note::

 Pour les utilisateurs finaux, une pompe et un courtier, c'est la même chose
 à tout fins pratique.  Mais, lorsque les administrateurs de pompes configurent
 des clusters multi-hôtes, cependant, une pompe peut être exécuté sur deux
 hôtes, et le même courtier pourrait être utilisé par de nombreux moteurs de
 transport. La grappe entière serait considérée comme une pompe. Ainsi, le
 deux mots n´ont pas toujours les même sens.

Pompes Dataless
  Il y a des pompes qui n'ont pas de moteur de transport, elles servent de
  médiateur des transferts pour d'autres serveurs, en mettant les messages
  à la disposition des clients et des clients dans leur zone réseau.


Transferts Dataless
  Parfois, les transferts à travers les pompes se font sans utiliser l'espace
  local sur la pompe.


Réseau de pompage
  Un certain nombre de serveurs d'interconnexion exécutant la pile sarracenia.
  Chaque pile détermine la façon dont il achemine les articles vers le saut
  suivant, de sorte que la taille ou l'étendue entière du réseau peut ne pas
  être connu de ceux qui y mettent des données.


Cartes réseau
  Chaque pompe devrait fournir une carte du réseau pour informer les
  utilisateurs de la destination connue qu'ils devraient faire de la publicité
  pour envoyer à. *FIXME* non défini jusqu'à présent.


