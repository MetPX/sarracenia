========
Sr3_Post
========

--------------------------------------------------
Publie la Disponibilitée d'un fichier aux abonnés.
--------------------------------------------------

:Manual section: 1 
:Date: |today|
:Version: |release|
:Manual group: MetPx Sarracenia Suite

SYNOPSIS
========

**sr3_post|sr3_cpost** [ *OPTIONS* ][ *-pb|--post_broker broker* ][ *-pbu|--post_baseUrl url[,url]...** ] 
[ *-p|--path ] path1 path2...pathN* ]

( aussi **libsrshim.so** )

DESCRIPTION
===========

**sr3_post** affiche la disponibilité d'un fichier en créant une annonce.
Contrairement à la plupart des autres composants de Sarracenia qui agissent comme des démons,
sr3_post est une invocation unique qui publie et quitte.
Pour faire des fichiers
disponible pour les abonnés, **sr3_post** envoie les annonces
à un serveur AMQP, également appelé courtier (broker). 

Cette page de manuel principalement sur l'implémentation en python,
il existe également une implémentation en C qui fonctionne presque identiquement.
Les différences sont:

 - les plugins ne sont pas supportés dans l'implémentation en C.
 - L'implémentation en C utilise des expressions régulières POSIX, la grammaire python3 est légèrement différente.
 - lorsque l'option *sleep* (utilisée uniquement dans l'implémentation C) est définie comme > 0,
    il transforme sr_cpost en démon qui fonctionne comme le composant *watch*
    de `sr3(1) <sr3.1.html>`_.  

Options obligatoires
--------------------

L'option *post_base_url url,url,...* spécifie l'emplacement
où les abonnés téléchargeront le fichier. Il y a généralement un article (post) par fichier.
le format de l'argument des options de *post_base_url* ::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       ou
       file:

Lorsque plusieurs URL sont données sous forme de liste séparée par des virgules à *post_base_url*,
les URL fournies sont utilisées dans le style round-robin pour fournir une forme grossière d'équilibrage de charge.

L'option [*-p|--path path1 path2 .. pathN*] spécifie le chemin des fichiers
Être annoncé. Il y a généralement un article par fichier.
Format de l'argument pour les option *path* ::

       /absolute_path_to_the/filename
       ou
       relative_path_to_the/filename

L'option *-pipe* peut être spécifiée pour que sr_post lise les noms de chemin des fichiers également à partir 
de l'entrée standard.

Un exemple d'invocation de *sr3_post* ::

 sr3_post --post_broker amqp://broker.com --post_baseUrl sftp://stanley@mysftpserver.com/ --path /data/shared/products/foo 


Par défaut, sr_post lit le fichier /data/shared/products/foo et calcule sa somme de contrôle (checksum).
Il crée ensuite un message de publication, se connecte à broker.com en tant qu'utilisateur "invité" (informations d'identification par défaut)
et envoie l'article au vhost par défaut '/' et à l'échange par défaut. L'échange par défaut
est le préfixe *xs_* suivi du nom d'utilisateur du courtier, donc par défaut 'xs_guest'.
Un abonné peut télécharger le fichier /data/shared/products/foo en s'authentifiant en tant qu'utilisateur stanley
sur mysftpserver.com en utilisant le protocole sftp vers broker.com en supposant qu'il possède des informations d'identification appropriées.
La sortie de la commande est ::

 [INFO] Published xs_guest v02.post.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo' sum=d,82edc8eb735fd99598a1fe04541f558d parts=1,4574,1,0,0


Dans MetPX-Sarracenia, chaque article est publié sous un certain sujet.
La ligne de la sortie d'exécution (log) commence par '[INFO]', suivi du **sujet** de
l'article. Les rubriques dans *AMQP* sont des champs séparés par un point. Le sujet complet commence par
un topicPrefix (voir option), version *V02*, une action *post*,
suivi d'un sous-thème (voir option) ici la valeur par défaut, le chemin du fichier séparé par des points
*data.shared.products.foo*.

Le deuxième champ de la ligne de la sortie d'exécution est l'avis de message. Il se compose d'un horodatage (timestamp) 
*20150813161959.854*, et l'URL source du fichier dans les 2 derniers champs.

Le reste des informations est stocké dans des en-têtes de message AMQP, constitués de paires clé=valeur.
L'en-tête *sum=d,82edc8eb735fd99598a1fe04541f558d* donne l'informations surl'empreinte du fichier (ou somme de contrôle).
Ici, *d* signifie somme de contrôle md5 effectuée sur les données, et *82edc8eb735fd99598a1fe04541f558d*
est la valeur de la somme de contrôle. Le *parts=1,4574,1,0,0* indiquent que le fichier est disponible en 1 partie de 4574 octets
(la taille du fichier.) Le *1,0,0* restant n'est pas utilisé pour les transferts de fichiers avec une seule partie.

Un autre exemple::

 sr3_post --post_broker mqtt://broker.com --post_baseDir /data/web/public_data --postBaseUrl http://dd.weather.gc.ca/ --path bulletins/alphanumeric/SACN32_CWAO_123456

Par défaut, sr_post lit le fichier /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(en concaténant le post_base_dir et le chemin relatif de l'url source pour obtenir le chemin du fichier local)
et calcule sa somme de contrôle. Il crée ensuite un message d'article, se connecte à broker.com en tant qu'utilisateur "invité"
(informations d'identification par défaut) et envoie l'article au vhost par défaut '/' et échange 'xs_guest', résultant
à la publication au broker MQTT sous le topic : *xs_guest/v03/bulletins/alphanumeric/SACN32_CWAO_123456*

Un abonné peut télécharger le fichier http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 en utilisant http
sans authentification sur dd.meteo.gc.ca.


ARGUMENTS ET OPTIONS
=====================

Veuillez vous référer à la page de manuel `sr3_options(7) <sr3_options(7)>`_ pour une description détaillée de
tous les paramètres et les méthodes pour les spécifier.

path path1 path2 ... pathN
--------------------------

  **sr3_post** évalue les chemins du système de fichiers à partir de l'option **path**
  et éventuellement le **baseDir** si l'option est utilisée.

  Si un chemin définit un fichier, ce fichier est annoncé.

  Si un chemin définit un répertoire, alors tous les fichiers de ce répertoire sont
  annoncés...

post_broker <broker>
--------------------

  le courtier auquel l'article est envoyé.

post_baseDir <path>
-------------------

  L'option *base_dir* fournit le chemin du répertoire qui,
  lorsqu'ils sont combinés (ou trouvés) dans le *chemin* donné,
  donne le chemin local absolu du fichier de données à afficher.
  La partie racine du document du chemin local sera supprimée de l'annonce publiée.
  Pour les URL sftp : il peut être approprié de spécifier un chemin relatif à un compte utilisateur.
  Un exemple de cette utilisation serait : -dr ~user -post_base_url sftp:user@host
  Pour les URL de fichiers: base_dir n'est généralement pas approprié. Pour afficher un chemin absolu,
  omettez le paramètre -dr et spécifiez simplement le chemin complet comme argument.

post_exchange <exchange>
------------------------

  Sr_post publie sur un échange nommé *xs_*"broker_username" par défaut.
  Utilisez l'option *post_exchange* pour remplacer cette valeur par défaut.

-h|--help
---------

  Afficher les options du programme.

blocksize <value>
-----------------

**Inutile pour le moment, sera rétabli après la version v3**

Cette option contrôle la stratégie de partitionnement utilisée pour publier les fichiers.
La valeur doit être l'une des suivantes::

     0 - calcule automatiquement une stratégie de partitionnement appropriée (par défaut)
     1 - toujours envoyer des fichiers entiers en une seule partie.
     <blocksize> - utilise une taille de partition fixe (taille d'exemple : 1M )

Les fichiers peuvent être annoncés en plusieurs parties. Chaque partie a une somme de contrôle distincte.
Les pièces et leurs sommes de contrôle sont stockées dans le cache. Les partitions peuvent traverser
le réseau séparément et en parallèle. Lorsque les fichiers changent, les transferts sont
optimisé en n'envoyant que les pièces qui ont changé. 

La valeur de *blocksize* est un nombre entier pouvant être suivi de la lettre *[B|K|M|G|T]* signifiant:
pour Octets, Kilooctets, Mégaoctets, Gigaoctets, Teraoctets respectivement. Toutes ces références sont des puissances de 2.
Les fichiers plus gros que cette valeur seront annoncés avec des parties de taille *blocksize*.

L'algorithme d'autocomputation détermine une taille de bloc qui encourage un nombre raisonnable de pièces
pour des fichiers de différentes tailles. Comme la taille du fichier varie, le calcul automatique donnera différents
résultats. Cela entraînera le renvoi d'informations qui n'ont pas changé en tant que partitions d'un autre
size aura des sommes différentes et sera donc étiqueté comme différent.

Par défaut, **sr_post** calcule une taille de bloc raisonnable qui dépend de la taille du fichier.
L'utilisateur peut définir une *blocksize* fixe si c'est mieux pour ses produits ou s'il veut
tirer avantage du mécanisme de **cache**. Dans les cas où des fichiers volumineux sont ajoutés, par exemple,
il est logique de spécifier une taille de partition fixe afin que les blocs du cache soient les
mêmes blocs que ceux générés lorsque le fichier est plus volumineux, et ainsi éviter la retransmission. Alors utiliser
'10M' aurait du sens dans ce cas.
  
Dans les cas où un téléchargeur personnalisé est utilisé qui ne comprend pas le partitionnement, il est nécessaire
d'éviter que le fichier ne soit divisé en plusieurs parties. Il faudrait donc spécifier '1' pour forcer l'envoi de tous les fichiers
comme une seule pièce.

post_baseUrl <url>
------------------

L'option **url** définit le protocole, les informations d'identification, l'hôte et le port
où le produit peut être récupéré.

L'annonce AMQP est composée des trois champs, l'heure de l'annonce,
cette valeur **url** et le **chemin** donné vers lequel a été retiré du *base_dir*
si nécessaire.

La concaténation des deux derniers champs de l'annonce définit
ce que les abonnés utiliseront pour télécharger le produit.

reset
-----

Quand on a utilisé **--suppress_duplicates|--cache**, cette option vide le cache.


rename <path>
-------------

Avec l'option *renommer*, l'utilisateur peut suggérer un chemin de destination vers ses fichiers. Si le chemin donné
se termine par '/', il suggère un chemin de répertoire... Si ce n'est pas le cas, l'option spécifie un changement de nom de fichier.

*sr3_post*, et *sr3 watch* utilisent un modèle basé sur un fichier basé sur un processus et un cache disque,
dont la conception est à filetage unique. La bibliothèque shim est généralement utilisée par de nombreux processus
à la fois, et aurait des problèmes de conflit de ressources et/ou de corruption avec le cache.
La bibliothèque shim a donc un cache purement basé sur la mémoire, réglable avec
les options de shim\_ suivantes. 

shim_defer_posting_to_exit EXPERIMENTAL
--------------------------------------- 

  Repousse la publication du fichier jusqu'à la fin du processus.
  Dans les cas où un même fichier est ouvert et ajouté à plusieurs reprises, ce
  paramètre peut éviter les publications redondantes. (par défaut: Faux)

shim_post_minterval *interval* EXPERIMENTAL
-------------------------------------------

  Si un fichier est ouvert en écriture et fermé plusieurs fois dans l'intervalle,
  il ne sera affiché qu'une seule fois. Lorsqu'un fichier est écrit plusieurs fois, en particulier
  dans un script shell, cela fait de nombreux messages et le script shell affecte les performances.
  les abonnés ne pourront en aucun cas faire des copies assez rapidement, donc
  il y a peu d'avantages, par exemple, à 100 messages du même fichier dans la même seconde.
  Il est sage de fixer une limite supérieure à la fréquence de publication d'un fichier donné. (par défaut : 5s)
  Remarque: si un fichier est toujours ouvert ou a été fermé après sa publication précédente, alors
  lors du traitement de la sortie du processus, il sera réenregistré, même si l'intervalle
  n'est pas respecté, afin de fournir le message final le plus précis.

shim_skip_parent_open_files EXPERIMENTAL
----------------------------------------
 
  L'option shim_skip_ppid_open_files signifie qu'un processus vérifie
  si le processus parent a le même fichier ouvert, et n'affiche
  pas si c'est le cas. (par défaut: Vrai)

sleep *time*
------------

  **Cette option n'est disponible que dans l'implémentation c (sr_cpost)**

  Lorsque l'option est définie, elle transforme cpost en sr3 watch, *sleep* étant le temps d'attente entre
  la génération des événements. Lorsque les fichiers sont écrits fréquemment, il est contre-productif de produire un message pour
  chaque changement, car cela peut produire un flux continu de changements où les transferts ne peuvent pas être effectués assez rapidement
  pour suivre. Dans de telles circonstances, on peut regrouper toutes les modifications apportées à un fichier
  en *sleep*, et produisez un seul message.

  REMARQUE::
      dans sr_cpost, lorsqu'il est combiné avec force_polling (voir `sr3 watch(1) <sr3.1.html>`_ ) l'intervalle de 
      sommeil ne doit pas être inférieur à environ cinq secondes, car il peut manquer la publication de certains fichiers. 

subtopic <key>
--------------

  Le sous-thème par défaut peut être remplacé par l'option *subtopic*.


nodupe_ttl on|off|999
---------------------

  Évitez de publier des doublons en comparant chaque fichier à ceux vus lors de l'inverval
  *suppress_duplicates*. Lors de la publication de répertoires, ceci entraînera
  *sr_post* a publier uniquement les fichiers (ou parties de fichiers) qui étaient nouveaux lorsqu'ils sont invoqués à nouveau.

  Au fil du temps, le nombre de fichiers dans le cache peut devenir trop grand, et il est donc nettoyé des
  anciennes entrées. La durée de vie par défaut d'une entrée de cache est de cinq minutes (300 secondes). Cette
  durée de vie peut être remplacé par un intervalle de temps comme argument (le 999 ci-dessus).

  Si la suppression des doublons est utilisée, il faut s'assurer qu'un **blocksize** fixe est
  utilisé (défini sur une valeur autre que 0) car sinon la taille de bloc variera à mesure que les fichiers grandissent,
  et beaucoup de transfert de données en double en résultera.

identity <method>[,<value>]
---------------------------

Toutes les publications de fichiers incluent une somme de contrôle. L'option *sum* spécifie comment la calculer.
C'est une chaîne séparée par des virgules. Les méthodes d'intégrité valides sont ::

        cod,x - Calculer au téléchargement en appliquant x
        sha512 - faire SHA512 sur le contenu du fichier (par défaut)
        md5 - faire md5sum sur le contenu du fichier
        random - inventez une valeur aléatoire pour chaque publication.
        arbitrary - appliquer la valeur fixe littérale.

.. Note::

  Les sommes de contrôle sont stockées dans les attributs de fichier étendus (ou Alternate Data Streams sous Windows).
  Ceci est nécessaire pour que la méthode *arbitrary* fonctionne, puisque nous n'avons aucun moyen de la calculer.

topicPrefix <key>
-----------------

  *Pas habituellement utilisé*
  Par défaut, le topic est composé du topicPrefix par défaut : version *V03*
  suivi du sous-sujet par défaut: le chemin du fichier séparé par des points (le point étant le séparateur de sujet pour amqp).
  Vous pouvez écraser le topicPrefix en définissant cette option.

  *Not usually used*
  By default, the topic is made of the default topicPrefix : version *V03*
  followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
  You can overwrite the topicPrefix by setting this option.

header <name>=<value>
---------------------

  Ajoutez une en-tête <name> avec la valeur donnée aux annonces. Utilisé pour transmettre des chaînes en tant que métadonnées.

UTILISATION DE LA LIBRAIRIE SHIM
================================

Plutôt qu'invoquer un sr_post pour poster chaque fichier à publier, on peut avoir des processus automatiquement
publiez les fichiers qu'ils écrivent en leur faisant utiliser une bibliothèque de shim interceptant certains appels d'i/o de fichiers vers la libc
et le noyau. Pour activer la bibliothèque shim, dans l'environnement shell, ajoutez ::

  export SR_POST_CONFIG=shimpost.conf
  export LD_PRELOAD="libsrshim.so.1"

où *shimpost.conf* est un fichier de configuration sr_cpost dans
le répertoire ~/.config/sarra/post/. Un fichier de configuration sr_cpost est le même
qu'un sr_post, sauf que les plugins ne sont pas pris en charge. Avec la
bibliothèque shim en place, chaque fois qu'un fichier est écrit, les clauses *accept/reject* du
fichier shimpost.conf sont consultés, et s'il est accepté, le fichier est affiché
comme ce serait par sr_post. Si vous utilisez ssh, où l'on veut des fichiers
scp à publier, il faut inclure l'activation dans le .bashrc et y passer
la configuration à utiliser ::

  expoert LC_SRSHIM=shimpost.conf

Puis dans le ~/.bashrc sur le serveur exécutant la commande à distance ::

  if [ "$LC_SRSHIM" ]; then
      export SR_POST_CONFIG=$LC_SRSHIM
      export LD_PRELOAD="libsrshim.so.1"
  fi
SSH ne transmettra que les variables d'environnement qui commencent par LC\_ (locale) afin d'obtenir
les variables passées avec un minimum d'effort, nous utilisons ce préfixe.

Trucs d'utilisation de shim
----------------------------

Cette méthode de notification nécessite une certaine configuration de l'environnement utilisateur.
L'environnement utilisateur a besoin du jeu de variables d'environnement LD_PRELOAD
avant le lancement du processus. Des complications qui restent telles que nous les avons
testées depuis deux ans depuis la première mise en œuvre de la bibliothèque de shim:

* si nous voulons remarquer les fichiers créés par des processus scp distants (qui créent des shells sans connexion)
  alors le crochet d'environnement doit être dans .bashrc. et en utilisant un environnement
  variable qui commence par *LC_* pour que ssh transmette la valeur de configuration sans
  avoir à modifier la configuration sshd dans les distributions Linux typiques.
  ( discussion complète : https://github.com/MetPX/sarrac/issues/66 )

* code qui a certaines faiblesses, comme dans FORTRAN un manque d'IMPLICIT NONE
  https://github.com/MetPX/sarracenia/issues/69 peut planter lorsque la bibliothèque shim
  est introduit. La correction nécessaire dans ces cas a jusqu'à présent consisté à corriger
  l'application, et non la bibliothèque.
  ( aussi : https://github.com/MetPX/sarrac/issues/12 )

* code utilisant l'appel *exec* vers `tcl/tk <www.tcl.tk>`_, considère par défaut tout
  sortie vers le descripteur de fichier 2 (erreur standard) comme condition d'erreur.
  ces messages peuvent être étiquetés comme priorité INFO ou WARNING, mais ils vont
  faire en sorte que l'appelant tcl indique qu'une erreur fatale s'est produite. Ajouter
  *-ignorestderr* aux invocations de *exec* évite de tels abandons injustifiés.

* Les scripts shell complexes peuvent avoir un impact démesuré sur les performances.
  Puisque *scripts shell hautes performances* est un oxymore, la meilleure solution,
  du point de vue des performances consiste à réécrire les scripts dans un langage de script plus efficace
  tel que python ( https://github.com/MetPX/sarrac/issues/15 )

* Les bases de code qui déplacent les hiérarchies de fichiers volumineux (par exemple, *mv tree_with_thousands_of_files new_tree* )
  verra un coût beaucoup plus élevé pour cette opération, car elle est mise en œuvre comme
  un renommage de chaque fichier dans l'arborescence, plutôt qu'une seule opération sur la racine.
  Ceci est actuellement considéré comme nécessaire car la correspondance du modèle accept/reject
  peut entraîner une arborescence très différente sur la destination, plutôt que simplement
  même arbre en miroir. Voir `Traitement de renommage`_ ci-dessous pour plus de détails.

* *export SR_SHIMDEBUG=1* obtiendra plus de sortie que vous ne le souhaitez. utiliser avec précaution.

Traitement de renommage
-----------------------

Il est à noter que renommer le fichier n'est pas aussi simple dans le cas de la mise en miroir que dans le système opérateur  
sous-jacent. Alors que l'opération est une opération atomique unique dans un système d'exploitation, lorsque
en utilisant les notifications, il existe des cas d'acceptation/rejet qui créent quatre effets possibles.

+---------------+---------------------------+
|               |      old name est:        |
+---------------+--------------+------------+
|               |  *Accepté*   |  *Rejeté*  |
| new name est: |              |            |
+---------------+--------------+------------+
|  *Accepté*    |   renommer   |   copier   |
+---------------+--------------+------------+
|  *Rejeté*     |   retirer    |   rien     |
+---------------+--------------+------------+

Lorsqu'un fichier est déplacé, deux notifications sont créées:

* Une notification a le nouveau nom dans le *relpath*, tout en contenant un champ *oldname*
  pointant vers l'ancien nom. Cela déclenchera des activités dans la moitié supérieure de
  la table, soit un renommage, en utilisant le champ *oldname*, soit une copie s'il n'est pas présent
  à destination.

* Une deuxième notification avec l'ancien nom dans *relpath* sera acceptée
  encore une fois, mais cette fois, il contiendra le champ *newname* et traite l'action de suppression.

Renommer un répertoire à la racine d'un grand arbre est une opération atomique efficace
sous Linux/Unix, la mise en miroir de cette opération nécessite la création d'une publication de renommage pour chaque fichier
dans l'arbre, et est donc beaucoup plus cher.


VARIABLES ENVIRONNEMENTALES
===========================

Dans l'implémentation C (sr_cpost), si la variable SR_CONFIG_EXAMPLES est définie, alors la directive *add* peut être utilisée
pour copier des exemples dans le répertoire de l'utilisateur à des fins d'utilisation et/ou de personnalisation.

Une entrée dans le ~/.config/sarra/default.conf (créé via sr_subscribe edit default.conf )
pourrait être utilisé pour définir la variable ::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/examples

la valeur doit être disponible à partir de la sortie d'une commande de liste à partir de
l'implémentation python.


Voir aussi
==========

`sr3(1) <sr3.1.html>`_ - Interface de ligne de commande principale de Sarracenia.

`sr3_post(1) <sr3_post.1.html>`_ - publication des annonces de fichiers (implémentation python.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - publication des annonces de fichiers (implémentation c.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - implémentation en c du composant shovel. (copier les messages)

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - Convertir les lignes du fichier journal au format .save pour recharger/renvoyer.

`sr3_options(7) <sr_options.7.html>`_ - les options de configuration

`sr3_post(7) <sr_post.7.html>`_ - le format des annonces

**Page d'acceuil:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: une boîte à outils de gestion du partage de données pub/sub en temps réel




