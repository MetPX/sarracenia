
=========
 SR_Post
=========

--------------------------------------------------
Publier la disponibilité d'un fichier aux abonnés.
--------------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite

.. contents::


SYNOPSIS
========

**sr_post|sr_cpost** [ *OPTIONS* ][ *-pb|--post_broker broker* ][ *-pbu|--post_base_url url[,url]...* ][ *-pbu|--post_base_url url* ]
[ *-p|--path ] path1 path1 path2...pathN* ]

DESCRIPTION
===========

**sr_post** affiche la disponibilité d'un fichier en créant un avis.
Contrairement à la plupart des autres composants de la Sarracenia qui agissent comme des démons,
sr_post est une invocation intéractive qui publie et termine.
Les abonnés utilisent `sr_subscribe <sr_subscribe.1.rst>`_ pour obtenir les avis,
et télécharger les fichiers corréspondants.

Pour mettre les fichiers à disposition des abonnés, **sr_post** publie les avis.
à un serveur AMQP (aussi appelé courtier, ou *broker* .)

Cette page de manuel est principalement consacrée à l'implémentation de python,
mais il y a aussi une implémentation en C ( *sr_cpost* ) , qui fonctionne presque à l'identique,
Différences :

 - Les plugins ne sont pas supportés dans l'implémentation C.
 - L'implémentation en C utilise les expressions régulières POSIX, la grammaire de python3 est légèrement différente.
 - lorsque l'option *sleep* (utilisée uniquement dans l'implémentation C) est réglée sur > 0,
   il transforme sr_cpost en un démon qui fonctionne comme `sr_watch(1) <sr_watch.1.rst>`_.


L'option [*-pbu|--post_base_url url,url,...*] spécifie l'emplacement des fichiers sur le serveur
à publier pour les abonnés.  Il y a généralement un avis par fichier. le Format de l'argument 
de l'option *post_base_url* est naturellement un *url* ::

       ftp|http|http|sftp]://[user[:password]@]host[:port]/ /[:port
       ou
       fichier :

Quand plusieurs url sont offerts, et il y a plusieurs fichiers à annoncer, on va choisir un 
url parmi la liste pour chaque fichier annoncer afin de faire un genre d´équilibrage de charge.

L'option[*-p|--path path1 path2. pathN*] spécifie le chemin des fichiers local au serveur.
Il y a généralement un message par fichier.  Format de l'argument de l'option *path*::

       chemin_absolu_vers_le/nom_du_fichier
       ou
       chemin_relatif_au_nom_du/nom_du_fichier

l'option *-pipe* peut être spécifiée pour que sr_post lise les noms de chemin d'accès à partir 
de l´entrée standard. 

Un exemple d'invocation de *sr_post*: :

 sr_post -pb amqp://broker.com -pbu s_ftp://stanley -p /data/shared/products/foo 

Par défaut, sr_post lit le fichier /data/shared/products/foo et calcule sa somme de contrôle.
Il construit ensuite un message, se connecte à broker.com en tant qu'utilisateur 'guest' 
(informations d'identification par défaut) et envoie le message aux valeurs par défaut 
vhost'/' et l'échange par défaut. L'échange par défaut est le préfixe *xs_* suivi du nom 
d'utilisateur du courtier, donc par défaut à'xs_guest'. Un abonné peut télécharger le 
fichier /data/shared/products/foo en s'authentifiant comme utilisateur stanley sur 
mysftpserver.com en utilisant le protocole sftp à broker.com en supposant qu'il a 
les informations d'identification appropriées.  La sortie de la commande est la suivante ::

 [INFO] Published xs_guest v02.post.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo' sum=d,82edc8eb735fd99598a1fe04541f558d parts=1,4574,1,0,0

Dans MetPX-Sarracenia, chaque avis est publié sous un certain thème ( *topic* ).
La ligne de log commence par '[INFO]', suivi du **topic** du fichier
poste. Les thèmes dans *AMQP* sont des champs séparés par des points. Le thème complet commence par
un *topic_prefix* (voir option) version *V02*, une action *post*,
suivi d'un *subtopic* (voir option) ici par défaut, le chemin du fichier séparé par des points.
*data.shared.products.foo* *data.shared.products.foo*

Le deuxième champs de la sortie ci-haut est le corps de l´avis.  Il s'agit d'un temps
tampon *20150813161959.854*, et l'url source du fichier dans les 2 derniers champs.

Le reste de l'information est stocké dans des en-têtes de message AMQP, composés de paires clé=valeur.
L'en-tête *sum=d,82edc8eb735fd99598a1fe04541f558d* donne l'empreinte digitale du fichier (ou somme de contrôle).
).  Ici, *d* signifie la somme de contrôle md5 effectuée sur les données, et *82edc8eb735fd99598a1fe04541f558d*.
est la valeur de la somme de contrôle. Les *parts=1,4574,1,0,0,0* indiquent que le fichier est 
disponible en 1 partie de 4574 octets.  Le reste *1,0,0,0* n'est pas utilisé pour les 
transferts de fichiers avec une seule partie.

Un autre exemple::

 sr_post -pb amqp://broker.com -pbd /data/web/public_data -pbu http://dd.weather.gc.ca/ -p bulletins/alphanumeric/SACN32_CWAO_123456

Par défaut, sr_post lit le fichier /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concaténer le post_base_dir et le chemin relatif de l'url source pour obtenir le chemin du fichier local)
et calcule sa somme de contrôle. Il construit ensuite un message, se connecte à broker.com en tant qu'utilisateur'guest'.
(informations d'identification par défaut) et envoie le message à vhost'/' et échangez'xs_guest'.

Un abonné peut télécharger le fichier http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_CWAO_123456 
en utilisant http sans authentification sur dd.weather.gc.ca.

ARGUMENTS ET OPTIONS
=====================

Veuillez vous référer à la page `sr_subscribe(1) <sr_subscribe.1.rst>`_ manuel pour une 
description détaillée des éléments suivants les paramètres communs et les méthodes 
de spécification.

[-c|--config <configfile>]
--------------------------

  Une liste des paramètres d'un fichier de configuration.

[--cache|--suppress_duplicates on|off|999]
------------------------------------------

  Lorsque l'on planifie le repostage de répertoires, cette option met en cache
  ce qui a été affiché et n'affichera que des fichiers (ou des parties de fichiers) qui étaient nouveaux.
  quand on l'invoque à nouveau. 

  Si la mise en cache est utilisée, **blocksize** doit être réglé à 1 (soit 1 (annoncer le fichier entier).
  ou une taille de bloc fixe), sinon la taille du bloc variera en fonction de la taille du fichier.

[-p|--path chemin1 chemin1 chemin2 chemin2 .... cheminN]
--------------------------------------------------------

  **sr_post** évalue les chemins du système de fichiers à partir de l'option **path**.
  et éventuellement le **base_dir** si l'option est utilisée.

  Si un chemin définit un fichier, ce fichier est annoncé.

  Si un chemin d'accès définit un répertoire, alors tous les fichiers de ce répertoire sont les suivants
  annoncé.

[-pb|--post_broker <broker>]
----------------------------

  le courtier auquel la poste est envoyée (publié.)

[-pbd|--post_base_base_dir <path>]
----------------------------------

  L'option *base_dir* fournit le chemin du répertoire qui,
  lorsqu'ils sont combinés avec les chemins d'accès données, 
  donne le chemin absolu local vers le fichier de données à enregistrer.
  La partie racine du chemin d'accès local sera supprimée de l'annonce affichée.
  pour sftp : url's il peut être approprié de spécifier un chemin relatif à un compte utilisateur.
  Un exemple de cette utilisation serait :  -dr ~user -post_base_url sftp:user@host  
  pour file : url's, base_dir n'est généralement pas approprié.  Pour afficher un chemin absolu,
  omettez le paramètre -dr, et spécifiez simplement le chemin complet en argument.
  
[-ex|--échange <échange <échange>]
----------------------------------

  Sr_post publie à une échange nommée *xs_*"broker_username" par défaut.
  Utilisez l'option *exchange* pour remplacer cette valeur par défaut.
  
[-h|-help|--help]
-----------------

  Afficher les options du programme.


[--blocksize <valeur>>]
-----------------------

  Cette option contrôle la stratégie de partitionnement utilisée pour poster des fichiers.
  la valeur doit être l'une des valeurs suivantes: :

     0 - calcul automatique d'une stratégie de partitionnement appropriée (par défaut)
     1 - toujours envoyer des fichiers entiers en une seule partie.
     <taille du bloc> - utilisation d'une taille de partition fixe (exemple : 1M)

  Les fichiers peuvent être annoncés comme plusieurs parties. Chaque partie a une somme de contrôle.
  Les parties et leurs sommes de contrôle sont stockées dans le cache. Les parties peuvent traverser
  le réseau séparément, et en parallèle.  Lorsque les fichiers changent, les transferts sont 
  optimisé en n'envoyant que des parties qui ont changé.

  La valeur du *blocksize* est un entier qui peut être suivi de l'indicatif *[B|K|M|G|T]* :
  pour les Bytes, Kilobytes, Megabytes, Gigabytes, Terabytes respectivement.  Toutes ces références 
  sont des pouvoirs de 2. Les fichiers plus grands que cette valeur seront annoncés avec des pièces 
  de taille *blocksize*.

  L'algorithme d'autocalcul choisi une taille de bloc qui encourage un nombre raisonnable de pièces.
  pour des fichiers de différentes tailles. Pour les fichiers qui changent de taille, le calcul 
  automatique donnera des valeurs différentes a différents moments. Ceci aura pour résultat de 
  renvoyer des informations qui n'ont pas été modifiées en tant que partitions d'une partition 
  différente.  Le parties aura des sommes différentes, et sera donc étiquetée comme différente.

  Par défaut, **sr_post** calcule une taille de bloc raisonnable qui dépend de la taille du fichier.
  L'utilisateur peut définir une taille de bloc fixe si elle est meilleure pour ses produits ou 
  s'il le souhaite profiter du mécanisme **suppress_duplicates**.  Dans les cas où des fichiers 
  volumineux qui grandissent par la fin (mode *append*), par exemple, il est judicieux de spécifier 
  une taille de partition fixe pour que les blocs dans le cache soient les suivants les mêmes 
  blocs que ceux générés lorsque le fichier est plus volumineux, évitant ainsi la retransmission.
  Alors, utilisez de " 10M " serait logique dans ce cas.

  Dans les cas où on utilise un téléchargeur personnalisé qui ne comprend pas le partitionnement, 
  il est nécessaire d´éviter que le fichier soit divisé en plusieurs parties, donc on 
  spécifierait '1' pour forcer l'envoi de tous les fichiers en entier (sans partitions.)


[-pbu|--post_base_url <url>]
----------------------------

  L'option **url** définit le protocole, les informations d'identification, l'hôte et le port sous
  que le produit peut être récupéré.  L'avis en AMQP est faite des trois champs, l'heure de l'annonce,
  cette valeur **url** et le chemin **donné** vers lequel a été retiré du *base_dir*.

  La concaténation des deux derniers champs de l'annonce définit ce que les abonnés utiliseront 
  pour télécharger le produit.

[-pipe <boolean>>]
------------------

  L'option pipe est pour sr_post pour lire les noms des fichiers à poster à partir de l'entrée 
  standard pour lire à partir de fichiers redirigés, ou sortie en pipeline d'autres commandes. 
  La valeur par défaut est *off*, n'acceptant les noms de fichiers que sur la ligne de commande.

[--pulse_message <message>]
---------------------------

  Option administrateur pour envoyer un message à tous les abonnés.  Similaire à la 
  fonctionnalité "wall" (sur Linux/UNIX). Lorsque cette option est activée, un message 
  d'impulsion est envoyé, ignorant les paramètres du thème ou les fichiers donnés en argument.

[--reset]
---------

  Quand on a utilisé **--suppress_duplicates|--cache**, cette option vide le cache.


[-rn|--rename <path>]
---------------------

  Avec l'option *rename*, l'utilisateur peut suggérer un chemin d'accès à ses fichiers. Si le
  se termine par'/', il suggère un chemin d'accès au répertoire......  Si ce n'est pas le cas, 
  l'option spécifie un renommage de fichier.

[--sleep <time> <time> ]
------------------------

   Cette option n'est disponible que dans l'implémentation c (sr_cpost)**.

   Quand l'option est activée, elle transforme cpost en sr_watch, avec *sleep* étant le temps 
   d'attente entre la génération d'événements.  Lorsque les fichiers sont écrits fréquemment, 
   il est contre-productif de produire un post pour chaque changement, car il peut produire un 
   flux continu de changements lorsque les transferts ne peuvent être effectués assez rapidement
   pour suivre le rythme. Dans de telles circonstances, on peut regrouper tous les 
   changements apportés à un dossier durant une intervalle de *sleep* , et de produire un seul poste.

   NOTE: :
       dans sr_cpost, lorsqu'il est combiné avec force_polling (voir `sr_watch(1) <sr_watch.1.rst>`_) 
       le *sleep* ne devrait pas être inférieur à environ cinq secondes, car il se peut que 
       certains fichiers ne soient pas affichés. *FIXME: Vrai? à confirmer.*


[-sub|--subtopic <key>]
-----------------------

  La valeur par défaut du sous-thème peut être écrasée par l'option *subtopic*.


[--suppress_duplicates|-sd|-sd|-nd|--no_duplicates|--cache on|off|999]
----------------------------------------------------------------------

  Évitez de publier des doublons. Lors de la publication de répertoires, cette option met en cache
  ce qui a été affiché et n'affichera que des fichiers (ou des parties de fichiers) nouveaux.

  Au fil du temps, le nombre de fichiers dans le cache peut devenir trop important, et les
  anciennes entrées sont donc vidés de la mémoire cache.  La durée de vie par défaut d'une 
  entrée de cache est de cinq minutes (300 secondes). Cette durée de vie peut être changé
  avec un intervalle de temps comme argument ("999" ci-dessus).

  Si l'élimination des doublons est utilisée, il faut s'assurer qu'un taille fixe de **blocksize** soit
  utilisé (valeur différente de 0), sinon la taille des blocs variera au fur et à mesure que la 
  taille des fichiers augmente, et il en résultera beaucoup de transfert de données en double.


[-to|--to <destination>,<destination>,... ]
-------------------------------------------

  Une liste séparée par des virgules des grappes de destination auxquelles les données publiés 
  doivent être envoyées. Demandez aux administrateurs de pompes la liste des destinations valides.
  
  default : le nom d'hôte du courtier.

  FIXME: une bonne liste de destination devrait être découvrable.

[-sum|--sum <string>]
---------------------


  Tous les avis incluent une somme de contrôle.  Il est placé dans un en-tête du
  message amqp qui aura la forme d'un entrée *sum* avec la valeur par défaut
  'd,md5_checksum_on_data'. L'option *sum* indique au programme comment calculer
  la somme de contrôle. C'est une chaîne de caractères séparés par des virgules.
  Les valeurs de *sum* valides sont ::

    [0|n|d|d|s|N|N|z]
    où    0 : no checksum.... la valeur dans post est un entier aléatoire (uniquement pour tester/déboguer.)
          d : do md5sum on file content (par défaut pour l'instant, compatibilité)
          n : fait la somme de contrôle md5sum sur le nom de fichier
          N : fait la somme de contrôle SHA512 sur le nom de fichier.
          s : do SHA512 sur le contenu du fichier (par défaut à l'avenir)
          z,a : calculer la valeur de la somme de contrôle à l'aide de l'algorithme a et assigner après le téléchargement.

  D'autres algorithmes peuvent être contribués. Voir la Programmer´s Guide.

[-tp|--topic_prefix <key>]
--------------------------

  *Non utilisé d'habitude*
  Par défaut, le sujet est fait du topic_prefix : version *V02*, une action *post*,
  suivi du sous-thème par défaut : le chemin du fichier séparé par des points 
  (le point étant le séparateur de thème pour amqp).
  Vous pouvez écraser le préfixe du thème en définissant cette option.



[-header <nom>=<valeur>]
------------------------

  Ajout d'un en-tête <nom> avec la valeur donnée aux annonces. Utilisé pour passer des chaînes de caractères comme métadonnées.


SPÉCIFIQUE À L'ADMINISTRATEUR
=============================

[--queue|--queue_name|-qn] <queue>
----------------------------------

  Si un client veut qu'un produit soit publié de nouveau,
  l'administrateur du courtier peut utiliser *sr_post* et publier
  directement dans la file d'attente du client. Le client pourrait fournir
  le nom de ce file d'attente... ou l'administrateur le trouverait sur
  le courtier... À partir du journal où le produit a été transformé le
  le courtier, l'administrateur trouverait tous les messages.
  propriétés. L'administrateur doit être attentif aux petits détails.
  différences entre les champs dans des fichier journal et les 
  arguments à *sr_post*.  Les journaux mentionneraient *from_cluster* 
  *to_clusters*.  Pour **sr_post** les arguments seraient *-cluster* et *-to*.
  respectivement. L'administrateur exécuterait **sr_post**, à condition que
  toutes les options et le paramétrage de tout ce qui se trouve 
  dans le journal plus l'option *-queue q_...*


OPTIONS SPÉCIFIQUES AUX DÉVELOPPEURS
====================================

[-debug|--debug]
----------------

  afficher plus de messages diagnostique dans les journeaux.

[-r|--randomize]
----------------

  Si un fichier est comptabilisé dans plusieurs blocs, l'ordre de publication
  est randomisé de façon à ce que l'abonné ne les reçoive pas en ordre.
  L'option rend aussi le choix d'algorithm de calcul de somme de contrôle 
  aléatoire, prennant priorité sur l´option *sum*
  
[-rc|--reconnect]
-----------------

  Si un fichier est affiché dans plusieurs blocs, reconnecter au courtier
  pour chaque publication de block.


[--parts]
---------

  L'utilisation habituelle de l'option *blocksize* est décrite ci-dessus.
  l'en-tête *parts* dans les messages produits, mais il existe plusieurs 
  façons d'utiliser l´entête des *parts* qui ne sont généralement pas utiles 
  en dehors du développement.

  En plus des spécifications de taille de bloc* orientées utilisateur énumérées 
  ci-dessus, tout en-tête de " pièces " valide, tel qu'il est indiqué dans le fichier
  en-tête de pièce (par ex.'i,1,150,0,0,0') .  Il est également possible de 
  spécifier une autre taille de bloc de base pour le bloc automatique en lui 
  donnant après le '0', (ex.'0,5') utilisera 5 octets (au lieu de 50M) comme 
  taille de bloc de base, de sorte que l'un des éléments suivants peut voir 
  comment l'algorithme fonctionne. 

  
VARIABLES D'ENVIRONNEMENT
=========================

Dans l'implémentation C (sr_cpost), si la variable SR_CONFIG_EXAMPLES est 
définie, alors la directive *add* peut être utilisée pour copier des exemples 
dans le répertoire de l'utilisateur à des fins d'utilisation et/ou de personnalisation.

Une entrée dans le fichier ~/.config/sarra/default.conf (créé via sr_subscribe 
edit default.conf) pourrait être utilisé pour définir la variable::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/exemples

la valeur est disponible à partir de la sortie d'une commande *sr_post list*
( de la version en python. )


AUSSI VOIR
==========


`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés. (page principale de référence.)

`sr_shovel(8) <sr_shovel.8.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(8) <sr_winnow.8.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - traiter les rapport de télémétrie.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Outil pour s´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.




