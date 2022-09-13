
=========
 SR_post
=========

--------------------------------------
Format/Protocole d´avis Sarracenia v03
--------------------------------------

:Manual section: 7
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia


STATUS: Stable/Default
----------------------

Les messages de Sarracenia version 2 sont la norme précédente, utilisée pour des téraoctets
et des transferts de millions de fichiers par jour. La version 3 propose une prochaine
itération des messages Sarracenia.

La plupart des champs et leur signification sont les mêmes dans la version 3 que dans la version 2.
Certains champs changent parce que le protocole est exposé a une revision plus approfondi qu’auparavant.

Le changement de protocole de charge utile vise à simplifier les implémentations futures
et à activer l’utilisation par des protocoles de messagerie autres que l’AMQP antérieur à la version 1.0.
Voir `v03 Modifications <.. /Explanations/History/messages_v03.html>`_ pour plus de détails.

Pour générer des messages en format v03, utilisez le paramètre suivant ::

  post_topicPrefix v03

Pour sélectionner les messages à consommer dans ce format::

  topicPrefix v03



SYNOPSIS
--------

Version 03 du format des annonces de modification d'un fichier pour sr_post.

Un message sr_post se compose d’un sujet et du *BODY*

**AMQP Topic:** *<version>.{<dir>.}*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::
           <version> = « v03 » la version du protocole ou du format.
           « post » = le type de message dans le protocole.
           <dir> = un sous-répertoire menant au fichier (peut être de nombreux répertoires profonds)

**BODY:** *{ <en-tête> }* (JSON encoding.)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les en-têtes sont un tableau de paires nom:valeur::

  OBLIGATOIRE:

          "pubTime"       - YYYYMMDDTHHMMSS.ss - UTC date/horodatage.
          "baseUrl"       - racine de l’URL à télécharger.
          "relPath"       - Le chemin relatif peut être concaténé à <base_url>
          "integrity"     - Version WMO du champ de sum v02, en cours de développement.
          {
             "method" : "md5" | "sha512" | "md5name" | "link" | "remove" | "cod" | "random" ,
             "value"  : "base64 valeur de somme de contrôle encodée"
          }

  FACULTATIF:

          pour compatibilité GeoJSON:
          "type": "Feature"
          "geometry": RFC 7946 (geoJSON) spécification géographique compatible.


          "size"          - le nombre d’octets annoncés.
          "blocks"        - si le fichier publié est partitionné, alors :
          {
              "method"    : "inplace" | "partitioned" , - Le fichier est-il déjà en parties ?
              "size"      : "9999", -  taille des blocs.
              "count"     : "9999", - nombres de blocs dans un fichier.
              "remainder" : "9999", - taille du dernier bloc.
              "number"    : "9999", - quel est ce bloc.
          }
          "rename"        - nom pour écrire au fichier localement.
          "retPath"       - le chemin de récupération relatif peut être concaténé avec <base_url> pour remplacer relPath -
                            utilisé pour les cas d’API.
          "topic"         - copie du sujet de l’en-tête AMQP (généralement omis)
          "source"        - l’entité d’origine du message.
          "from_cluster"  - le cluster d’origine d’un message.
          "to_clusters"   - une spécification de destination.
          "link"          - valeur d’un lien symbolique. (si 'sum' commence par L)
          "atime"         - heure du dernier accès à un fichier (facultatif)
          "mtime"         - heure de la dernière modification d’un fichier (facultatif)
          "mode"          - bits d’autorisation (facultatif)

          "content"       - pour les fichiers plus petits, le contenu peut être incorporé.
          {
              "encoding" : "utf-8" | "base64"  ,
              "value"    " "contenu de fichier encodé"
          }

          Pour le messages de thème "v03.report", les en-têtes additionnelles qui suivent seront présents:

          "report" { "code": 999  - Code de réponse de style HTTP.
                     "message" :  - message de rapport d’état documenté dans `Report Messages`_
                   }

          "type": "Feature"   - utilisé pour la compatibilité geoJSON.
          "geometry" : ... selon la compatibilité GoJSON RFC7946.

          des paires supplémentaires nom:valeur définies par l’utilisateur sont autorisées.

REMARQUE:
     L’en-tête **parts** n’a pas encore été revu par d’autres. Nous avons commencé la discussion sur *size*,
     mais il n’y a pas eu de conclusion.

DESCRIPTION
-----------

Les sources créent des messages en format *sr_post* pour annoncer les modifications apportées aux fichiers.
Les abonnés lisent le message pour décider si un téléchargement du contenu annoncé est justifié.  Cette page
de manuel décrit entièrement le format de ces messages.  Les messages sont des charges utiles
pour un bus de messages AMQP (Advanced Message Queuing Protocol), mais le transport de données de fichiers
est séparé, utilisant des protocoles plus courants tels que SFTP, HTTP, HTTPS ou FTP (ou autre?).
Les fichiers sont transportés sou forme de flux d'octets purs, aucune métadonnée au-delà du contenu du fichier
n'est transporté (bits de permission, attributs étendus, etc....)

Avec cette méthode, les messages AMQP fournissent un « plan de contrôle » pour les transferts de données.
Alors que chaque message de publication est essentiellement point à point, les pompes de données peuvent
être reliées transitivement entre elles pour créer des réseaux arbitraires.  Chaque publication est consommée
par le saut suivant de la chaîne. Chaque saut re-publie (crée un nouveau poste pour) les données des sauts ultérieurs.
Les avis se déplacent dans le même sens que les données. Si les consommateurs le permettent, les messages de
rapport circulent également dans le chemin de contrôle, mais dans la direction opposée, permettant aux sources
de connaître l'ensemble de leur disposition.

La couche minimale sur AMQP brut offre une fonctionnalité de transfert de fichiers plus complète :

Filtrage des sources (utilisation des échanges `AMQP TOPIC`_)
   Les messages utilisent les *topic exchanges* de l’AMQP, où les thèmes sont des hiérarchies
   destiné à représenter des thèmes d’intérêt pour un consommateur. Un consommateur peut télécharger le
   critères de sélection pour le courtier de sorte que seulement un petit sous-ensemble d’avis
   sont transmis au client.  Lorsqu’il y a beaucoup d’utilisateurs intéressés par seulement un
   petit sous-ensembles de données, les économies de trafic sont importantes.

Fingerprint Winnowing (utilisation de l'en-tête integrity_)
   Chaque produit a une empreinte digitale d’intégrité et une taille destinée à l’identifier de manière unique,
   appelée *fingerprint*. Si deux fichiers ont la même empreinte digitale, ils sont considérés comme équivalents.
   Dans les cas où plusieurs sources de données équivalentes sont disponibles, mais les consommateurs en aval
   préféreraient recevoir des annonces uniques des fichiers, les processus intermédiaires peuvent choisir de
   publier des notifications du premier avec une empreinte digitale donnée, et ignorez les suivantes.
   Propager uniquement la première occurrence d’une référence reçue en aval, sur la base de
   son empreinte digitale, est appelée: *Fingerprint Winnowing*.

   *Fingerprint Winnowing* est la base d’une stratégie robuste de haute disponibilité : mettre en place plusieurs
   sources pour les mêmes données, les consommateurs acceptent les annonces de chacune des sources, mais seulement
   en transférant le premier qui est reçu en aval. En fonctionnement normal, une source peut être plus rapide
   que les autres, et donc les fichiers des autres sources sont généralement « winnowed ». Quand une source
   disparaît, les données des autres sources sont automatiquement sélectionnées, parce ce que les empreintes
   digitales sont maintenant *fresh* et utilisés, jusqu’à ce qu’une source plus rapide soit disponible.

   L’avantage de cette méthode pour une haute disponibilité est qu’aucune décision A/B n’est requise.
   Le temps d'un *switchover* est nul. D’autres stratégies sont sujet à des retards considérables
   en prenant la décision de passer au numérique, et les pathologies que l’on pourrait considérer comme des oscillations,
   et/ou des deadlocks.

   *Fingerprint Winnowing* permet également le *mesh-like*, ou un réseau *any to any*, où l’on interconnecte simplement
   un nœud avec d’autres et les messages se propagent. Leur chemin spécifique à travers le
   le réseau n’est pas défini, mais chaque participant téléchargera chaque nouvelle référence à partir du premier
   nœud qui le met à sa disposition. Garder les messages petits et séparés des données
   est optimal pour cet usage.

Partitionnement (utilisation de l´entête parts_ )
   Dans n’importe quel réseau de pompage de données de stockage et de transmission de données qui transporte des fichiers
   entiers, limite la taille maximale d'un fichier au minimum disponible sur n’importe quel nœud intermédiaire.
   Pour éviter de définir la taille maximale d'un fichier, une norme de segmentation est spécifiée, permettant aux
   nœuds intermédiaires de tenir uniquement des segments du fichier, et de les transmettre au fur et à mesure qu’ils
   soient reçus, plutôt que d’être forcé à conserver le fichier entier.

   Le partitionnement permet également à plusieurs flux de transférer des parties du fichier en parallèle.
   Plusieurs flux peuvent fournir une optimisation efficace sur les liens longs.

THÈME (TOPIC)
-------------

Dans les échanges basé par thèmes dans AMQP, chaque message a un en-tête de thème. AMQP définit le caractère '.'
en tant que séparateur hiérarchique (comme '\' dans un nom de chemin Windows, ou '/' dans Linux), il existe également une
paire de caractères génériques définis par la norme : '*' correspond à un seul thème, '#' correspond au reste de
la chaîne de caractère du thème. Pour permettre des modifications dans le corps du message à l’avenir, les
arborescences de thèmes commencent par le numéro de la version du protocole.

AMQP permet le filtrage des thèmes côté serveur à l’aide de wildcards. Les abonnés spécifient les sujets d'intérêt
(qui correspondent à des répertoires sur le serveur), leur permettant de réduire le
nombre de notifications envoyées du serveur au client.

La racine de l’arborescence des thèmes est le spécificateur de version : « v03 ».  Ensuite il y a le spécificateur
de type de message. Ces deux champs définissent le protocole utilisé pour le reste du message.
Le type de message pour les messages de publication est « post ».  Après avoir fixé le préfixe du thème,
les sous-thèmes restants sont les éléments de chemin d’accès du fichier sur le serveur Web.
Par exemple, si un fichier est placé sur http://www.example.com/a/b/c/d/foo.txt,
alors le thème complet du message sera : *v03.a.b.c.d*
Les champs AMQP sont limités à 255 caractères et les caractères du champ sont
encodé en utf8, de sorte que la limite de longueur réelle peut être inférieure à cela.

REMARQUE::

  Sarracenia s’appuie sur des courtiers pour interpréter l’en-tête du thème. Les courtiers interprètent
  des en-têtes spécifiques au protocole *AMQP, et ne décode pas efficacement la charge utile pour extraire les en-têtes.
  Par conséquent, l’en-tête du thème est stocké dans un en-tête AMQP, plutôt que dans la charge utile qui autorise le
  filtrage côté serveur. Pour éviter d’envoyer deux fois les mêmes informations, cet en-tête est
  omis de la charge utile JSON.

  De nombreuses implémentations côté client, une fois le message chargé, définiront l’en-tête *topic*
  dans la structure en mémoire, il serait donc très imprudent de définir l’en-tête *topic*
  dans une application même si elle n’est pas visible dans la charge utile sur fil.


Mappage vers MQTT
~~~~~~~~~~~~~~~~~

L’un des objectifs du format v03 est d’avoir un format de charge utile qui fonctionne avec plus que l’AMQP.
Message Queing Telemetry Transport (MQTT v3.11) est une norme iso ( https://www.iso.org/standard/69466.html
un protocole qui peut facilement prendre en charge le même modèle de messagerie publication/abonnement, avec quelques détails
different, donc un mappage est nécessaire.

Tout d’abord, le séparateur de thème dans MQTT est une barre oblique (/), au lieu du point (.) qui est utilisé dans AMQP.

Deuxièmement, avec AMQP, on peut établir des hiérarchies de thèmes différents en utilisant des *topic-based exchanges*.
MQTT n’a pas de concept similaire, il n’y a qu’une seule hiérarchie, donc lors du mappage, il faut placer le nom
de l’échange à la racine de l'hiérarchie des thèmes pour obtenir le même effet ::

  AMQP:   Exchange: <exchange name>
             topic: v03.<directory>...

  MQTT:   topic: <exchange name>/v03/<directory>...



LES EN-TÊTES FIXES
------------------

Le message est un tableau encodé en JSON unique, avec un ensemble obligatoire de champs, tout en permettant
l’utilisation d'autres champs arbitraires.  Les champs obligatoires doivent être présents dans chaque message:

 * "pubTime" : "*<horodatage>*" : la date de publication de l’affichage qui a été émis.  Format: YYYYMMDDTHHMMSS. *<decimalseconds>*

 Remarque : L’horodatage est toujours dans le fuseau horaire UTC.

 * "baseUrl" : "<*base_url*>" -- l’URL de base utilisée pour récupérer les données.

 * "relPath" : "<*relativepath*>" --   la partie variable de l’URL, généralement ajoutée à *baseUrl*.

L’URL que les consommateurs utiliseront pour télécharger les données. Exemple d’URL complet ::

 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_000.gif


Champs supplémentaires :

**from_cluster=<nom_du_cluster>**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   L’en-tête from_cluster définit le nom du cluster source où
   les données ont été introduites dans le réseau. Cela est utilisé pour renvoyer les journaux
   au cluster chaque fois que ses produits sont utilisés.

**link=<valeur du lien symbolique>**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   Lorsque le fichier à transférer est un lien symbolique, l’en-tête 'link' est créé pour
   contenir sa valeur.

**size and blocks**
~~~~~~~~~~~~~~~~~~~

.. _parts:

::
     "size":<sz> ,

     "blocks" :
     {
            "method": "inplace" or "partitioned",
            "size": <bsz>,
            "count": <blktot>,
            "remainder": <brem>,
            "number": <bno>
     }

 Un en-tête indiquant la méthode et les paramètres de partitionnement appliqués au fichier.
 Le partitionnement est utilisé pour envoyer un seul fichier en tant que collection de segments, plutôt qu'en une
 seule entité.  Le partitionnement est utilisé pour accélérer les transferts de grands ensembles de données en utilisant
 plusieurs flux et/ou pour réduire l’utilisation du stockage pour les fichiers extrêmement volumineux.

 Lors du transfert de fichiers partitionnés, chaque partition est annoncée et potentiellement transportée
 indépendamment sur un réseau de pompage de données.

 *<méthode>*

 Indique quelle méthode de partitionnement, si il y en a une, a été utilisée dans la transmission.

 +-----------------+---------------------------------------------------------------------+
 |   Méthode       | Déscription                                                         |
 +-----------------+---------------------------------------------------------------------+
 | p - partitioned | Le fichier est partitionné, des fichiers en pièce individuels       |
 |                 | sont créés.                                                         |
 +-----------------+---------------------------------------------------------------------+
 | i - inplace     | Le fichier est partitionné, mais les blocs sont lus à partir d’un   |
 |                 | seul fichier, plutôt que des parties.                               |
 +-----------------+---------------------------------------------------------------------+
 | 1 - <sizeonly>  | Le fichier est dans une seule partie (pas de partitionnement).      |
 |                 | dans v03, seul l’en-tête *size* sera présent. *blocs* est omis.     |
 +-----------------+---------------------------------------------------------------------+

 - analogue aux options rsync : --inplace, --partial,

 *<blocksize in bytes>: bsz*

 Nombre d’octets dans un bloc.  Lorsque vous utilisez la méthode 1, la taille du bloc est la taille du fichier.
 Les restants des champs sont seulement utiles pour les fichiers partitionnés.

 *<blocks in total>: blktot*
 le nombre total (en entier) de blocs dans le fichier (le dernier bloc peut être partiel)

 *<remainder>: brem*
 normalement 0, pour le dernier bloc, octets restants dans le fichier
 à transférer.

        -- if (fzb=1 and brem=0)
               then bsz=fsz in bytes in bytes.
               -- fichiers entièrement remplacé.
               -- c’est la même chose que le mode --whole-file de rsync.

 *<block#>: bno*
 0 origine, le numéro de bloc couvert par cette publication.


**rename=<relpath>**
~~~~~~~~~~~~~~~~~~~~

 Chemin d’accès relatif du répertoire actif dans lequel placer le fichier.

**oldname=<chemin>** / **newname=<chemin>**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 lorsqu’un fichier est renommé à la source, pour l’envoyer aux abonnés, il va y avoir deux posts: un message
 est annoncé avec le nouveau nom comme base_url, et l’en-tête *oldname* va prendre la valeur de l'ancien nom du fichier.
 Un autre message est envoyé avec l’ancien nom comme chemin src et le *newname*
 comme en-tête.  Cela garantit que les clauses *accept/reject* sont correctement
 interprété, parce qu'un *rename* peut entraîner un téléchargement si l’ancien nom
 correspond à une clause *reject* ou à une suppression de fichier si le nouveau nom
 correspond à une clause *reject*.

 Les hard links sont également traités comme un post ordinaire du fichier avec un ensemble d'en-tête *oldname*.

**integrity**
~~~~~~~~~~~~~

Le champ d’intégrité donne une somme de contrôle qui est utile pour identifier le contenu
d’un fichier::

 "integrity" : { "method" : <méthode>, "value": <valeur> }

Le champ d’intégrité est une signature calculée pour permettre aux récepteurs de déterminer
s’ils ont déjà téléchargé le produit ailleurs.

   *<method>* - champ de chaîne de caractère (string field) indiquant la méthode de somme de contrôle utilisée.

 +------------+---------------------------------------------------------------------+
 |  Méthode   | Déscription                                                         |
 +------------+---------------------------------------------------------------------+
 |  random    | Pas de sommes de contrôle (copie inconditionnelle). Ignore la       |
 |            | lecture du fichier (plus rapide)                                    |
 +------------+---------------------------------------------------------------------+
 |  arbitrary | valeur arbitraire définie par l’application qui ne peut pas être    |
 |            | calculée                                                            |
 +------------+---------------------------------------------------------------------+
 |  md5       | Somme de contrôle de l’ensemble des données                         |
 |            | (MD-5 selon IETF RFC 1321)                                          |
 +------------+---------------------------------------------------------------------+
 |  link      | Lié : SHA512 somme de la valeur du lien                             |
 +------------+---------------------------------------------------------------------+
 |  md5name   | Somme de contrôle du nom du fichier (MD-5 selon IETF RFC 1321)      |
 +------------+---------------------------------------------------------------------+
 |  remove    | Supprimé : SHA512 du nom du fichier.                                |
 +------------+---------------------------------------------------------------------+
 |  sha512    | Somme de contrôle de l’ensemble des données                         |
 |            | (SHA512 selon IETF RFC 6234)                                        |
 +------------+---------------------------------------------------------------------+
 |  cod       | Somme de contrôle du téléchargement, avec algorithme comme argument |
 |            | Exemple : cod,sha512 signifie télécharger, appliquer la somme de    |
 |            | contrôle SHA512 et annoncer avec cette somme de contrôle calculée   |
 |            | lors de la propagation ultérieure.                                  |
 +------------+---------------------------------------------------------------------+
 | *<name>*   | Somme de contrôle avec un autre algorithme, nommé *<name>*          |
 |            | *<name>* doit être *registered* dans le réseau de pompage de données|
 |            | Enregistré signifie que tous les abonnés en aval peuvent obtenir    |
 |            | l’algorithme pour valider la somme de contrôle.                     |
 +------------+---------------------------------------------------------------------+

*<value>* La valeur est calculée en appliquant la méthode donnée à la partition transférée.
  pour un algorithme ou aucune valeur n’a de sens, un entier aléatoire est généré pour prendre en charge
  l'équilibrage de charge basé sur la somme de contrôle.


Report Messages
---------------

Certains clients peuvent renvoyer la télémétrie à l’origine des données téléchargées à des fins de dépannage
et à des fins de statistiques. Ces messages ont le thème *v03.report* et ont un en-tête *report*
qui est un *object* JSON avec quatre champs :

 { "elapsedTime": <report_time>, "resultCode": <report_code>, "host": <report_host>, "user": <report_user>* }

 * *<report_code>*  les codes de résultat décrits dans la section suivante

 * *<report_time>*  l’heure à laquelle le rapport a été généré.

 * *<report_host>*  nom d’hôte à partir duquel la récupération a été lancée.

 * *<report_user>*  nom d’utilisateur du courtier à partir duquel la récupération a été lancée.


Les messages de rapport ne doivent jamais inclure l’en-tête *content* (aucun fichier incorporé dans les rapports).


Report_Code
~~~~~~~~~~~

Le code de rapport est un code d’état à trois chiffres, adopté à partir du protocole HTTP (w3.org/IETF RFC 2616)
encodé sous forme de texte.  Conformément à la RFC, tout code renvoyé doit être interprété comme suit :

	* 2xx indique une réussite.
	* 3xx indique qu’une action supplémentaire est nécessaire pour terminer l’opération.
	* 4xx indique qu’une erreur permanente sur le client a empêché une opération réussie.
	* 5xx indique qu’un problème sur le serveur a empêché une opération réussie.

.. REMARQUE::
   FIXME: besoin de valider si notre utilisation des codes d’erreur coïncide avec l’intention générale
   exprimé ci-dessus... Un 3xx signifie-t-il que nous nous attendons à ce que le client fasse quelque chose? 5xx signifie-t-il
   que la défaillance était du côté du courtier/serveur ?

Les codes d’erreur spécifiques renvoyés et leurs significations dépendent de l’implémentation.
Pour l’implémentation sarracenia, les codes suivants sont définis :

+----------+--------------------------------------------------------------------------------------------+
|   Code   | Texte correspondant et signification pour la mise en œuvre de sarracenia                   |
+==========+============================================================================================+
|   201    | Téléchargement réussi. (variantes: Downloaded, Inserted, Published, Copied, or Linked)     |
+----------+--------------------------------------------------------------------------------------------+
|   203    | Informations non-autoritaire : transformées pendant le téléchargement.                     |
+----------+--------------------------------------------------------------------------------------------+
|   205    | Réinitialiser le contenu : tronqué. Le fichier est plus court que prévu (longueur modifiée |
|          | pendant le transfert). Cela ne se produit que lors des transferts en plusieurs parties.    |
+----------+--------------------------------------------------------------------------------------------+
|   205    | Réinitialiser le contenu : somme de contrôle recalculée à la réception.                    |
+----------+--------------------------------------------------------------------------------------------+
|   304    | Non modifié (Somme de contrôle validée, inchangée, donc aucun téléchargement en suit.)     |
+----------+--------------------------------------------------------------------------------------------+
|   307    | Insertion différée (écriture dans une partie du fichier temporaire pour le moment.)        |
+----------+--------------------------------------------------------------------------------------------+
|   417    | Échec de l’attente : message non valide (en-têtes corrompus)                               |
+----------+--------------------------------------------------------------------------------------------+
|   496    | failure: During send, other protocol failure.                                              |
+----------+--------------------------------------------------------------------------------------------+
|   497    | failure: During send, other protocol failure.                                              |
+----------+--------------------------------------------------------------------------------------------+
|   499    | Échec : Non copié. Problème de téléchargement SFTP/FTP/HTTP                                |
+----------+--------------------------------------------------------------------------------------------+
|   503    | Service indisponible. supprimer (la suppression de fichiers n’est pas prise en charge.)    |
+----------+--------------------------------------------------------------------------------------------+
|   503    | Impossible de traiter : Service indisponible                                               |
+----------+--------------------------------------------------------------------------------------------+
|   503    | Protocole de transport spécifié dans la publication n'est pas pris en charge               |
+----------+--------------------------------------------------------------------------------------------+
|   xxx    | Les codes d’état de validation des messages et des fichiers dépendent du script            |
+----------+--------------------------------------------------------------------------------------------+
 FIXME: will 3 error codes that are the same cause confusion? ^

Autres champs de rapport
~~~~~~~~~~~~~~~~~~~~~~~~


*<report_message>* une chaine de caractères.


En-têtes facultatives
---------------------

pour le cas d’utilisation de la mise en miroir de fichiers, des en-têtes supplémentaires seront présents :

**atime,mtime,mode**
~~~~~~~~~~~~~~~~~~~~

  man 2 stat - les métadonnées du fichier standard linux/unix :
  temps d’accès, temps de modification et autorisation (bits de mode)
  les heures sont dans le même format que le champ pubTime.
  la chaîne d’autorisation est composée de quatre caractères destinés à être interprétés comme suit :
  autorisations octal linux/unix traditionnelles.

**Les en-têtes qui sont inconnus à un courtier DOIVENT être transmis sans modification.**

Sarracenia fournit un mécanisme permettant aux utilisateurs d’inclure d’autres en-têtes arbitraires dans les messages,
pour amplifier les métadonnées pour une prise de décision plus détaillée sur le téléchargement de données.
Par exemple::

  "PRINTER" : "name_of_corporate_printer",

  "GeograpicBoundingBox" :
   {
           "top_left" : { "lat": 40.73, "lon": -74.1 } ,
           "bottom_right": { "lat": -40.01, "lon": -71.12 }
   }

permettrait au client d’appliquer un filtrage/traitement côté client plus élaboré et plus précis.
L’implémentation intermédiaire peut ne rien savoir de l’en-tête,
mais ils ne devraient pas être dépouillés, car certains consommateurs peuvent les comprendre et les traiter.

EXEMPLE
-------

::

 AMQP TOPIC: v03.NRDPS.GIF
 MQTT TOPIC: exchange/v03/NRDPS/GIF/
 Body: { "pubTime": "201506011357.345", "baseUrl": "sftp://afsiext@cmcdataserver", "relPath": "/data/NRPDS/outputs/NRDPS_HiRes_000.gif",
    "rename": "NRDPS/GIF/", "parts":"p,457,1,0,0", "integrity" : { "method":"md5", "value":"<md5sum-base64>" }, "source": "ec_cmc" }

        - v03 - version du protocole
        - post - indique le type du message
        - la version et le type ensemble determine le format des thèmes qui suivent et du corps du message.

        - blocksize est 457  (== taile du fichier)
        - block count est 1
        - restant est 0.
        - block number est 0.
        - d - somme de contrôle a été calculé à partir du corps du fichier.
        - la source complète de l'URL spécifiée (ne se termine pas par '/')
        - chemin relatif spécifié pour

        tirer de:
                sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif

        chemin de téléchargement relatif complet :
                NRDPS/GIF/NRDPS_HiRes_000.gif

                -- prends le nom du fichier de base_url.
                -- peut être modifié par un processus de validation.


Un Autre Exemple
----------------

Le post résultant de la commande de sr_watch suivante, a noter la création du fichier 'foo'::

 sr_watch -pbu sftp://stanley@mysftpserver.com/ -path /data/shared/products/foo -pb amqp://broker.com
Ici, *sr_watch* vérifie si le fichier /data/shared/products/foo est modifié.
Lorsque cela se produit, *sr_watch* lit le fichier /data/shared/products/foo et calcule sa somme de contrôle.
Il crée ensuite un message de publication, se connecte à broker.com en tant qu’utilisateur « invité »
(informations d’identification par défaut) et envoie la publication aux vhosts '/' par défaut et
à l'échange 'sx_guest' (l'échange par défaut).

Un abonné peut télécharger le fichier /data/shared/products/foo en se connectant en tant qu’utilisateur stanley
sur mysftpserver.com en utilisant le protocole sftp pour broker.com en supposant qu’il dispose des
informations d’identification appropriées.

La sortie de la commande est la suivante ::

  AMQP Topic: v03.20150813.data.shared.products
  MQTT Topic: <exchange>/v03/20150813/data/shared/products
  Body: { "pubTime":"20150813T161959.854", "baseUrl":"sftp://stanley@mysftpserver.com/",
          "relPath": "/data/shared/products/foo", "parts":"1,256,1,0,0",
          "sum": "d,25d231ec0ae3c569ba27ab7a74dd72ce", "source":"guest" }

Les posts sont publiés sur les échanges de thèmes AMQP, ce qui signifie que chaque message a un en-tête de thème.
Le corps se compose d’un temps *20150813T161959.854*, suivi des deux parties de
l'URL de récupération. Les en-têtes ont d’abord les *parts*, une taille en octets *256*,
le nombre de blocs de cette taille *1*, les octets restants *0*, le
bloc actuel *0*, un indicateur *d* signifiant que la somme de contrôle md5 est
effectuée sur les données, et la somme de contrôle *25d231ec0ae3c569ba27ab7a74dd72ce*.

Possibilités d’optimisation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

L’objectif d’optimisation est la lisibilité et la facilité de mise en œuvre, beaucoup plus
que l’efficacité ou la performance. Il existe de nombreuses optimisations pour réduire les
frais généraux de plusieur aspects, ce qui augmente la complexité de l'implémentation.
exemples: gzip la charge utile permettrait d’économiser peut-être 50% de taille,
regroupant également des en-têtes fixes (l’en-tête 'body' peut contenir
tous les champs fixes: « pubtime, baseurl, relpath, sum, parts », et un autre
champ 'meta' pourrait contenir: atime, mtime, mode donc il y aurait moins de
champs nommés et ca économiserais peut-être 40 octets de surcharge par avis. Mais
tous les changements augmentent la complexité, et ca rends les messages plus difficile à analyser.

Standards
---------

 * Sarracenia s’appuie sur `AMQP pre 1.0 <https://www.rabbitmq.com/resources/specs/amqp0-9-1.pdf>`_
   vu que la norme 1.0 a éliminé les concepts : courtier, échange, file d’attente et
   reliure.  L’ensemble de fonctionnalités 1.0 est inférieur au minimum nécessaire pour prendre en charge
   L’architecte publication-abonnement de Sarracenia

 * MQTT fait référence à `MQTT v5.0 <https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.pdf>`_
   et `MQTT v3.1.1 <http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html>`_,
   MQTT v5 a une extension importante: les abonnements partagés (fortement utilisés dans Sarracenia.)
   donc v5 est fortement recommandé. La prise en charge de la version 3.1 est uniquement pour des raisons de support héritées.

 * JSON est défini par `IETF RFC 7159 <https://www.rfc-editor.org/info/rfc7159>`_.
   La norme JSON inclut l’utilisation obligatoire de l'ensemble de caractères UNICODE (ISO 10646)
   L'ensemble de caractères par défaut JSON est UTF-8, mais autorise plusieurs caractères
   (UTF-8, UTF-16, UTF-32), mais interdit également la présence de marques d’ordre d’octets (byte order markings, BOM.)

 * comme Sarracenia v02, UTF-8 est obligatoire. Sarracenia restreint le format JSON
   en exigeant un codage UTF-8 (IETF RFC 3629) qui n’a pas besoin/n’utilise pas de BOM.
   Aucun autre codage n’est autorisé.

 * Le codage d’URL, conformément à la RFC 1738 de l’IETF, est utilisé pour échapper aux caractères dangereux
   quand approprié.



VOIR AUSSI
----------

`sr3(1) <sr3.1.html>`_ - rracenia ligne de commande principale.

`sr3_post(1) <sr3_post.1.html>`_ - poste des annoncements de fichiers (implémentation en Python.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - poste des annoncements de fichiers (implémentation en C.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - C implementation of the shovel component. (copy messages)

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - Convertissez les lignes du fichier journal au format .save pour le rechargement/le renvoi.

`sr3_options(7) <sr_options.7.html>`_ - les options de configurations


**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia : une boîte à outils de gestion du partage de données pub/sub en temps réel


