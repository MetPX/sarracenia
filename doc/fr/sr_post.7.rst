
=========
 SR_post 
=========

-------------------------------------
Format/Protocol d´avis Sarracenia v02 
-------------------------------------

:Manual section: 7
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::


SYNOPSIS
--------

Le format des avis de changement de fichier pour sr_post.

Un message sr_post se compose de quatre parties : AMQP TOPIC, première ligne, restant du message, Entêtes AMQP**.

**AMQP Topic:** *<version>.post.{<dir>.}*

::
           <version> = "v02" la version du protocole ou du format.
           "post" = le type de message dans le protocole.
           <dir> = un sous-répertoire menant au fichier (peut-être plusieurs répertoires profonds)


**En-têtes AMQP:** *<série de paires clé-valeur>.*

::

           "parts" = taille et informations de partitionnement.
           "sum" = indicateur de l´algorithme de la somme de contrôle, et sa valeur.

**Corps du message:** *<première ligne> = <horodate> <base_url> <relpath> <nouvelle ligne>*.

: :

          <horodate> - YYYYYMMDDHHHMMSS.ss - Horodatage UTC.
          <base_url> - racine de l'url à télécharger.
          <relpath> - chemin relatif peut-être catenéné à <base_url>.
                         peut à la place être un renommage.

<*Le reste du corps du message est réservé pour une utilisation future.*>


DESCRIPTION
-----------

Les sources créent des messages au format *sr_post* pour annoncer les changements 
de fichiers. Les Abonnés lisent le message pour décider si le téléchargement du 
contenu annoncé est justifié.  Les messages sont des charges utiles pour un bus 
de messages AMQP (Advanced Message Queuing Protocol), mais le transfert des 
fichiers est séparé, en utilisant des protocoles plus courants tels que SFTP, 
HTTP, HTTPS, ou FTP (ou autre.) Les fichiers sont transportés comme de purs 
flux d'octets, aucune métadonnée au-delà du contenu du fichier n'est transportés 
(bits de permission, attributs étendus, etc....) Permissions des fichiers
sur le système de destination sont à la discrétion du récepteur.

Avec cette méthode, les messages AMQP fournissent un "couche de contrôle " pour 
les transferts de données. Pendant que chaque message est essentiellement point 
à point, les pompes de données peuvent être reliées entre elles de façon transitive 
pour créé des réseaux de complexité illimité.  
Chaque publication est consommée par le saut suivant dans la chaîne. Chaque 
houblon ré-publie de houblon (crée un nouveau message pour) les données pour 
les sauts ultérieurs. Les avis se déplacent dans le même sens que les données.
Si les consommateurs l'autorisent, les messages de rapport (voir sr_report(7)) 
passent également par la couce de contrôle, mais dans la direction opposée, 
permettant aux sources de connaître l'ensemble de leur disposition.

La couche minimale sur AMQP brute offre une fonctionnalité de transfert de 
fichiers plus complète::


Filtrage des sources (utilisation des échanges `AMQP TOPIC`_)
   Les messages utilisent les *topic exchanges* de l'AMQP, où les thèmes sont hiérarchisés.
   destinés à représenter des thèmes d'intérêt pour un consommateur.  Un consommateur peut 
   télécharger le fichier critères de sélection au courtier afin que seul un petit sous-ensemble d'avis
   sont transmises au client. Lorsqu'il y a beaucoup d'utilisateurs intéressés par de 
   petits sous-ensembles seulement de données, les économies de trafic sont importantes.

Fingerprint Winnowing (utilisation de l'en-tête sum_)
   Chaque produit a une somme de contrôle et une taille destinée à l'identifier 
   de manière unique, désignée sous le nom de une *empreinte digitale*.  Si deux fichiers 
   ont la même empreinte digitale, ils sont considéré équivalents.  Dans les cas où 
   plusieurs sources de données équivalentes sont disponibles, mais 
   les consommateurs en aval préféreraient recevoir des annonces uniques
   de fichiers, les processus intermédiaires peuvent choisir de publier les 
   notifications du premier fichier avec une empreinte digitale donnée, et ignorer 
   les suivantes.  Ceci à l´effet de propager uniquement la première occurrence d'une 
   donnée reçue en aval, en se basant sur les éléments suivants son empreinte 
   digitale, est appelée : *Fingerprint Winnowing*.

   Le vannage *Fingerprint Winnowing* est la base d'une stratégie robuste de haute 
   disponibilité:  Plusieurs sources pour les mêmes données sont misent en place, les 
   consommateurs acceptent les annonces de chacun d'entre eux, mais seulement
   l'acheminement du premier reçu en aval.  En fonctionnement normal, une source peut 
   être plus rapide que les autres, de sorte que les fichiers des autres sources sont 
   généralement'vannés'. Lorsqu'une source disparaît, les données des autres sources sont 
   automatiquement sélectionnées. Comme les empreintes digitales sont maintenant *fraîches* 
   et utilisées, jusqu'à ce qu'une source plus rapide devienne disponible.

   L'avantage de cette méthode pour la haute disponibilité est qu'aucune décision A/B n'est requise.
   Le temps de *switchover* est zéro.  D'autres stratégies sont sujettes à des retards considérables.
   dans la décision de passer au numérique, et les pathologies que l'on pourrait résumer 
   comme des oscillations, et/ou des *deadlock.*

   *Fingerprint winnowing* permet également des toplogies d´interconnexion de serveurs arbitraires. 
   On peut tout interconnecté un nœud avec d'autres, et les messages se propagent.  
   Leur cheminement spécifique dans le cadre de la n'est pas défini, mais chaque 
   participant téléchargera chaque nouveau référentiel à partir du premier qui le 
   met à leur disposition. Garder les messages petits et séparés des données
   est optimal pour cet usage.

Partitionnement (utilisation de l´entête parts_ )
   Dans tout réseau de pompage de données de stockage et de transmission de 
   données qui transporte des fichiers entiers limite le maximum à la taille minimale 
   disponible sur n'importe quel nœud intermédiaire.  Pour éviter de définir un maximum
   la taille du fichier, une norme de segmentation est spécifiée, ce qui permet 
   aux nœuds intermédiaires de tenir en attente seulement des segments du fichier, 
   et les transmettre au fur et à mesure qu'ils sont reçus, plutôt que d'être
   forcé de conserver l'intégralité du dossier.

   Le partitionnement permet également à plusieurs flux de transférer des parties du 
   fichier en parallèle. Les flux multiples peuvent fournir une optimisation efficace 
   sur des liens de long portée.


AMQP TOPIC
----------

Dans les échanges thématiques AMQP ( *topic based exchanges* ), chaque message a un 
en-tête *topic*.  AMQP définit un point comme séparateur hiérarchique (comme '\' dans 
un nom de chemin d'accès à Windows, ou'/' sur linux) il y a également un paire de 
caractères génériques définis par la norme: '*' correspond à un seul sujet,'#' correspond 
au reste de la norme la chaîne de sujet. Pour permettre des changements dans le corps
du message à l'avenir, l'arborescence des sujets commence par le numéro de version du protocole.

AMQP permet de filtrer les sujets côté serveur à l'aide de caractères génériques. 
Les abonnés spécifient les sujets suivants (qui correspondent à des répertoires sur 
le serveur), ce qui leur permet de réduire l'espace de travail de l'utilisateur.
nombre de notifications envoyées du serveur au client.

La racine de l'arbre des sujets est le spécificateur de version : "v02". Vient ensuite 
le spécificateur de type de message. Ces deux champs définissent le protocole 
utilisé pour le reste du message.  Le type de message pour les avis publiés est "post".  
Après le préfixe du thème corrigé, les sous-thèmes restants sont les éléments de 
chemin du fichier sur le serveur web.

Par exemple, si un fichier est placé sur www.example.com/a/b/c/d/foo.txt
alors le sujet complet du message sera :  *v02.post.a.b.b.c.d*
Les champs AMQP sont limités à 255 caractères, et les caractères dans les champ 
sont encode en utf8, de sorte que la limite de longueur réelle peut être inférieure 
à cette limite. 


La première ligne
-----------------

la première ligne d'un message contient tous les éléments obligatoires d'une annonce.
Il y a une série de champs séparés par des espaces blancs : 

*<horodate>*: quand l´avis est créé. Format: YYYMMJJHHMMSS.*<fractions de seconde>*

Note : L'horodatage est toujours dans le fuseau horaire UTC.

*<base_url>* -- l'URL de base utilisée pour récupérer les données.

L'URL que les consommateurs utiliseront pour télécharger les données.  Exemple d'une URL complète::

 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_HiRes_000.gif


*<relativepath>* la partie variable de l'URL, habituellement ajoutée à *base_url*.


LE RESTE DU MESSAGE
-------------------

Seule la première ligne de la charge utile AMQP est actuellement définie.
Le reste de la charge utile est réservé pour une utilisation future.



Entêtes AMQP
------------

En plus de la première ligne du message contenant tous les champs obligatoires, 
des éléments optionnelles sont stockés dans les en-têtes AMQP (paires clé-valeur 
codées en utf8 limitées à 255 octets de longueur).  

**from_cluster=<<nom_cluster_name>**
   Le from_cluster définit le nom du cluster source où les données ont été introduites dans le réseau.
   Il est utilisé pour renvoyer les logs vers le cluster à chaque fois que ses produits sont utilisés.

**link=<valeur du lien symbolique>**
  lorsque le fichier à transférer est un lien symbolique, l'en-tête 'link' est créé pour contenir sa valeur.

.. _parts :

**parts=<méthode>,<bsz>,<blktot>,<blktot>,<brem>,bno**

 Un en-tête indiquant la méthode et les paramètres de partitionnement appliqués au fichier.
 Le partitionnement est utilisé pour envoyer un fichier unique comme une collection de 
 parties. Le partitionnement est utilisé pour accélérer les transferts de grands ensembles 
 de données en utilisant la fonction des flux multiples, et/ou pour réduire l'utilisation du 
 stockage pour les fichiers extrêmement volumineux.

 lors du transfert de fichiers partitionnés, chaque partition est annoncée et potentiellement transportée.
 indépendamment à travers un réseau de pompage de données.


 *<methode>*
 

 Indique quelle méthode de partitionnement, le cas échéant, a été utilisée dans la transmission.
 
 +-----------+---------------------------------------------------------------------+
 |   Methode | Description                                                         |
 +-----------+---------------------------------------------------------------------+
 |    p      | Le fichier est partitionné, des fichiers de pièces individuelles    |
 |           | sont créés.                                                         |
 +-----------+---------------------------------------------------------------------+
 |    i      | Le fichier est partitionné, mais les blocs sont lus à partir d´une  |
 |           | seul fichier d´origine, plutôt que des parties.                     |
 +-----------+---------------------------------------------------------------------+
 |    1      | Le fichier est dans une seule partie (pas de partitionnement)       |
 +-----------+---------------------------------------------------------------------+
 

 - similaire aux options rsync: --inplace, --partial,
 

 *<Taille du parties en octets> : bsz*
 
 Le nombre d'octets dans un partie.  Lorsque vous utilisez la méthode 1, la taille du bloc 
 est la taille du fichier. Les champs restants ne sont utiles que pour les fichiers 
 partitionnés.    

 *<blocs au total> : blktot*

 Le nombre total de parties dans le fichier (la dernière partie peut être partielle)

 *<Reste> : Brem*.
 normalement 0, sur le dernier bloc, les octets restants dans le fichier.
 pour le transfert.

        if (fzb=1 et brem=0)
               puis bsz=fsz en octets en octets en octets.
               des fichiers entiers remplacés.
               c'est la même chose que le mode --whole-file de rsync.

 *<block#>> : bno*.
 0 origine, le numéro de parties concerné par cet avis.



**rename=<relpath>**

 Ne pas utiliser. Le chemin d'accès relatif du répertoire courant dans lequel 
 vous devez placer le fichier.

**oldname=<path>**
**newname=<path>**

 lorsqu'un fichier est renommé à la source, pour l'envoyer aux abonnés, deux messages
 sont publiés: Un message avec le nouveau nom comme base_url, et l'en-tête *oldname*
 avec le nom précédent du fichier.  Un autre message est envoyé avec l'ancien nom 
 comme chemin, et l´entête *newname* contenant le nouveau nom.  Ceci permet de s'assurer 
 que les clauses *accept/rejet* sont correctement interprété, comme un *rename* peut 
 donner lieu à un téléchargement si l'ancien nom correspond à une clause *reject*, 
 ou à une suppression de fichier si le nouveau nom correspond à une clause de *reject*.
 
 les liens durs sont également traités comme un message ordinaire du fichier avec 
 un entête *oldname*.

.. _sum:

**sum=<methode>,<valeur>**

La somme est une signature calculée pour permettre aux destinataires de 
déterminer s'ils ont déjà téléchargé la partition d'ailleurs.
 
 *<méthode>* - champ de caractères indiquant l'algorithme de la somme de contrôle utilisé.
 
 +-----------+---------------------------------------------------------------------+
 |  Methode  | Description                                                         |
 +-----------+---------------------------------------------------------------------+
 |     0     | Pas de somme de contrôle. Copie inconditionnelle.                   |
 +-----------+---------------------------------------------------------------------+
 |     d     | Somme de contrôle MD5 (IETF RFC 1321) sur le fichier au complet.    |
 +-----------+---------------------------------------------------------------------+
 |     L     | lien symbolique, SHA512 de la valeur du lien.                       |
 +-----------+---------------------------------------------------------------------+
 |     n     | Somme de contrôle MD5 (IETF RFC 1321) sur le nom du fichier         |
 +-----------+---------------------------------------------------------------------+
 |     R     | fichier enlevé (SHA512 du nom du fichier enlevé)                    |
 +-----------+---------------------------------------------------------------------+
 |     s     | Somme de contrôle SHA512 (IETF RFC 6234) sur le fichier au complet  |
 +-----------+---------------------------------------------------------------------+
 |     z     | Calcul de somme de contrôle lors de téléchargement, utilisant       |
 |           | la méthode fourni comme argument.  Exmple: z,d spécifie que         |
 |           | la somme de contrôle MD5 devrait être calculé durant le télécharge  |
 |           | ment. Cette valeur calculée servira quand l´avis pour ce fichier est|
 |           | propagé en aval.                                                    |
 +-----------+---------------------------------------------------------------------+
 |  *<name>* | Un autre somme de contrôle qui doit être reconnu par tous les       |
 |           | récipients de données pour qu´ils puissent les confirmer.           |
 +-----------+---------------------------------------------------------------------+


*<valeur>* La valeur est calculée en appliquant la méthode donnée à la partition transférée.
  pour les algorithmes pour lesquels aucune valeur n'a de sens, un entier aléatoire est généré pour prendre en charge
  l'équilibrage de charge basé sur la somme de contrôle.


**to_clusters=<<cluster_name1,cluster_name2,.....>**
 Le to_clusters définit une liste de clusters de destination où les données doivent aller dans le réseau.
 Chaque nom devrait être unique au sein de tous les groupes de lapin échangeants. Il est utilisé pour faire le transit des produits et de leurs avis à travers les grappes d'échange.

Tous les autres en-têtes sont réservés pour une utilisation future.
Les en-têtes qui sont inconnus d'un client donné doivent être transmis sans modification.

EXEMPLE
-------

:: 

 Topic: v02.post.NRDPS.GIF.NRDPS_HiRes_000.gif
 first line: 201506011357.345 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif NRDPS/GIF/  
 Headers: parts=p,457,1,0,0 sum=d,<md5sum> flow=exp13 source=ec_cmc


       - v02 - version du protocole
       - post - indique le type de message.
       - La version et le type déterminent ensemble le format des sujets suivants et le corps du message.

       - la taille du bloc est de 457 (== taille du fichier)
       - le nombre de blocs est de 1
       - le reste est égal à 0.
       - le numéro de bloc est 0.
       - d - d - la somme de contrôle a été calculée sur le corps du fichier.
       - le débit est exp13
       - URL source complète spécifiée (ne se termine pas par'/')
       - chemin d'accès relatif spécifié pour

        de... :
                sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_HiRes_000.gif

        chemin de téléchargement relatif complet :
                NRDPS/GIF/NRDPS_HiRes_HiRes_000.gif

                -- prend le nom de fichier de base_url.
                -- peut être modifié par le processus de validation.


Un autre exemple
----------------

Le post résultant de la commande sr_watch suivante, remarquant la création du fichier 'foo'::

  sr_watch -s s_sftp://stanley@mysftpserver.com//data/shared/products/foo -pb amqp://broker.com

Ici, *sr_watch* vérifie si le fichier /data/shared/products/foo est modifié.
Quand cela se produit, *sr_watch* lit le fichier /data/shared/products/foo et calcule sa somme de contrôle.
Il construit ensuite un message, se connecte à broker.com en tant qu'utilisateur'guest' 
(informations d'identification par défaut) et envoie le message aux valeurs par défaut vhost'/' 
et échange'sx_guest' (échange par défaut)

Un abonné peut télécharger le fichier /data/shared/products/foo en se connectant en tant 
qu'utilisateur stanley.  Sur mysftpserver.com en utilisant le protocole sftp à broker.com en 
supposant qu'il a les informations d'identification appropriées.

La sortie de la commande est la suivante ::

  Topic: v02.post.20150813.data.shared.products.foo
  Première ligne du corps: 20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo
  en-têtes: parts=1,256,1,0,0 sum=d,25d231ec0ae3c569ba27ab7a74dd72ce source=guest

Les messages sont publiés sur les échanges de thème de l'AMQP, ce qui signifie que 
chaque message a un en-tête *topic*. Le corps se compose d'un temps *20150813161959.854*, suivi des 
deux parties de l'URL de téléchargement.  Les en-têtes suivent avec les premières les *parts*, 
une taille en octets *256*, le nombre de blocs de cette taille *1*, les octets restants *0*, le 
nombre de blocs de cette taille *1*, les octets restants *0*, le nombre d'octets
bloc courant *0*, un drapeau *d* signifiant que la somme de contrôle md5 est 
effectué sur les données, la somme de contrôle *25d231ec0ae3c569ba27ab7a74dd72ce*,

MetPX-Sarracénie
----------------

Le projet Metpx ( https://github.com/MetPX) comporte un sous-projet appelé Sarracénie, qui est destiné à
comme banc d'essai et mise en œuvre de référence pour ce protocole.  Cette implémentation est sous licence
en utilisant la Licence Publique Générale (Gnu GPL v2), et est donc libre d'utilisation, et peut être utilisé pour
confirmer l'interopérabilité avec toute autre mise en œuvre qui pourrait survenir.   Alors que la sarracénie
lui-même devrait être très utilisable dans une variété de contextes, il n'y a pas d'intention pour cela.
pour implémenter toute fonctionnalité non décrite dans cette documentation.  

Cette page du manuel a pour but de spécifier complètement le format des messages et leur format.
de manière à ce que d'autres producteurs et consommateurs de messages puissent être mis en œuvre.




Sélection des caractéristiques de l'AMQP
----------------------------------------

AMQP est un protocole universel de transmission de messages avec beaucoup d´options afin d´accommoder
de nombreux modèles de messagerie différents.  MetPX-sarracénie spécifie et utilise un
un petit sous-ensemble de modèles AMQP.  Un élément important du développement de la 
sarracénie consistait à choisir parmi les nombreuses possibilités, un petit sous-ensemble 
de méthodes est général et facile à comprendre, afin de maximiser le potentiel d'interopérabilité.

Préciser l'utilisation d'un protocole à lui seul peut être insuffisant pour fournir 
suffisamment d'informations pour l'échange de données et l'interopérabilité.  Par exemple, 
lors de l'échange de données via FTP, plusieurs choix s'offrent à vous. doivent se faire 
au-delà du protocole.

        utilisation authentifiée ou anonyme ?
        comment signaler qu'un transfert de fichiers est terminé (bits de permission ? suffixe ? préfixe ? préfixe ?)
        convention d'appellation.
        transfert de texte ou binaire.

Des conventions convenues au-delà du simple FTP (IETF RFC 959) sont nécessaires.  Similaire à l'utilisation
de FTP seul comme protocole de transfert est insuffisant pour spécifier un transfert de données complet.
l'utilisation de l'AMQP, sans plus d'information, est incomplète.   L'intention des conventions
superposé à l'AMQP doit être un montant minimum pour obtenir un échange de données significatif.

AMQP 1.0 standardise le protocole sur fil, mais ne tient pas compte de nombreuses caractéristiques de l'interaction avec les courtiers.
Comme l'utilisation de courtiers est la clé de sarracenia´s, l'utilisation de, était un élément fondamental des normes antérieures,
et comme la norme 1.0 est relativement controversée, ce protocole suppose qu'il s'agit d'un courtier avant la norme 1.0,
comme c'est fourni par de nombreux courtiers gratuits, comme rabbitmq, souvent appelé 0.8, mais 0.9 et post
0,9 Les courtiers sont également susceptibles de bien fonctionner entre eux.

Dans AMQP, de nombreux acteurs différents peuvent définir des paramètres de communication. dans RabbitMQ
(le courtier initial utilisé), les permissions sont attribuées à l'aide d'expressions régulières. Donc
un modèle de permission où les utilisateurs de l'AMQP peuvent définir et utiliser *leurs* échanges et files d'attente.
est appliqué par une convention d'appellation facilement mappée aux expressions régulières (toutes ces expressions régulières).
les ressources incluent le nom d'utilisateur près du début. Les échanges commencent par : xs_<user>_.
Les noms de file d'attente commencent par : q_<user>_.

.. NOTE: :
   FIXME : autres paramètres de connexion : persistance, etc...

Les échanges thématiques sont utilisés exclusivement.  L'AMQP prend en charge de nombreux autres types d'échanges,
mais sr_post a envoyé le sujet afin de supporter le filtrage côté serveur en utilisant le sujet.
à base de filtrage.  Les sujets reflètent le chemin des fichiers annoncés, ce qui permet à l'utilisateur d'accéder aux fichiers.
le filtrage simple côté serveur, qui doit être complété par un filtrage côté client sur
réception du message.

La racine de l'arbre des sujets est la version de la charge utile du message.  Cela permet aux courtiers individuels
de supporter facilement plusieurs versions du protocole en même temps pendant les transitions.  *v02*,
créé en 2015, est la troisième itération du protocole et les serveurs existants supportent couramment les serveurs précédents.
simultanément de cette façon.  Le deuxième sous-thème définit le type de message.
au moment de la rédaction : v02.post est le préfixe du sujet pour les messages courants.

Les messages AMQP contiennent des annonces, pas de données réelles.  L'AMQP est optimisé pour et suppose que
petits messages.  Le fait de garder les messages petits permet d'obtenir un débit maximum de messages et des permis.
d'utiliser des mécanismes de priorité fondés sur le transfert de données plutôt que sur les annonces.
Accommoder les messages volumineux créerait de nombreuses complications pratiques et nécessiterait inévitablement

JEU DE CARACTÈRES & ENCODAGE
----------------------------

Tous les messages doivent utiliser le jeu de caractères UNICODE (ISO 10646),
représenté par le codage UTF-8 (IETF RFC 3629.)
L'encodage d'URL, selon IETF RFC 1738, est utilisé pour échapper aux caractères dangereux, le cas échéant.



LECTURE COMPLÉMENTAIRE
----------------------

https://github.com/MetPX - page d'accueil de metpx-sarracenia

http://rabbitmq.net - page d'accueil du courtier de l'AMQP utilisé pour développer la sarracénie.


AUSSI VOIR
==========


`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés. (page principale de référence.)

`sr_shovel(1) <sr_shovel.1.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(1) <sr_winnow.1.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - traiter les rapport de télémétrie.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sarra(1) <sr_sarra.1.rst>`_ - Outil pour s´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_post(1) <sr_post.1.rst>`_ - Publier la disponibilité d'un fichier aux abonnés.

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.




