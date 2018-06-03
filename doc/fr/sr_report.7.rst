

=========
sr_report
=========

-------------------------------------------
Format/Protocole Rapports de Sarracenia v02 
-------------------------------------------

:Date: @Date@
:Version: @Version@
:Manual section: 7
:Manual group: MetPX-Sarracenia


.. contents::


SYNOPSIS
========

**AMQP Topic: <version>.report.{<dir>.}*<filename>**

**En-têtes AMQP:** *<serie of paires clé-valeur>*

**Body:** *<prémière ligne>*

*<prémière ligne> == <horodate> <base_url> <relpath> <statuscode> <consuminghost> <consuminguser> <duration> <newline>*

<*Le reste du corps du message est réservé pour une utilisation future.*>



DESCRIPTION
===========

Les sources créent des avis (messages au format *sr_post*) pour annoncer les changements de fichiers. 
Les abonnés lisent le message pour décider si le téléchargement du contenu annoncé est justifié.
Les abonnés peuvent fournir des informations aux sources en envoyant un message de 
rapport indiquant le résultat du traitement d'un courrier.  Le format de message de rapport, 
décrit par cette spécification, est un écho de l´avis reçu à la source avec quelques petits 
changements. Veuillez consulter la page de manuel sr_post(7) pour une explication complète 
des champs qui sont partagés avec le format d'avis.

Pareil qu´un avis en sr_post, un message sr_report se compose de quatre parties: :

    AMQP TOPIC, First Line, Rest of Message, AMQP HEADERS.

AMQP TOPIC
==========

Le thème d'un message de rapport est similaire à sr_post, sauf que le deuxième sous-thème 
est "report" plutôt que "post".


La première ligne
-----------------

la première ligne d'un message contient tous les éléments obligatoires d'une annonce sr_post(7).
Il y a une série de champs séparés par des espaces blancs:

*<horodate>*: quand l´avis est créé. Format: YYYMMJJHHMMSS.*<fractions de seconde>*

Note : L'horodatage est toujours dans le fuseau horaire UTC.

*<base_url>* -- l'URL de base utilisée pour récupérer les données.

L'URL que les consommateurs utiliseront pour télécharger les données.  Exemple d'une URL complète::

 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_HiRes_000.gif


*<relativepath>* la partie variable de l'URL, habituellement ajoutée à *base_url*.

Les champs ci-dessus sont tirés du format sr_post(7).  Il y a des champs supplémentaires 
dans le rapport sr_report :

un code d'état à trois chiffres, adopté à partir du protocole HTTP (w3.org/IETF RFC 2616).

Conformément au RFC, tout code retourné doit être interprété comme suit :

    2xx indique qu'il a été complété avec succès,
    3xx indique qu'une action supplémentaire est nécessaire pour terminer l'opération.
    4xx indique une erreur permanente sur le client empêché une opération réussie.
    5xx indique un problème sur le serveur a empêché le bon fonctionnement.

.. NOTE: :
   FIXME: il faut valider si l'utilisation de codes d'erreur coïncide avec l'intention générale.
   exprimé ci-dessus.... un 3xx signifie-t-il qu'on s'attend à ce que le client fasse quelque chose ?
   que l'échec était du côté du courtier/serveur ?

Les codes d'erreur spécifiques retournés et leur signification dépendent de l'implémentation.
Pour la mise en œuvre de la Sarracenia, les codes suivants sont définis :

+----------+--------------------------------------------------------------------------------------------+
|   Code   | Corresponding text and meaning for sarracenia implementation                               |
+==========+============================================================================================+
|   201    | Téléchargement ŕeussi.                                                                     |
+----------+--------------------------------------------------------------------------------------------+
|   205    | Téléchargement complété, mais le fichier et plus court que le messages indiquait.          |
|          |                                                                                            |
+----------+--------------------------------------------------------------------------------------------+
|   205    | Données Reçu, on a recalculé la somme de contrôle lors de réception.                       |
+----------+--------------------------------------------------------------------------------------------+
|   304    | Non modifié ( somme de contrôle inchangé, alors pas téléchargé. )                          |
+----------+--------------------------------------------------------------------------------------------+
|   307    | insertion dífféré (données placé dans un fichier temporarire)                              |
+----------+--------------------------------------------------------------------------------------------+
|   417    | Valeur inattendu, entête corrompue                                                         |
+----------+--------------------------------------------------------------------------------------------+
|   499    | Panne: Téléchargement non réussi problème de transfert.                                    |
+----------+--------------------------------------------------------------------------------------------+
|   503    | Service non-disponible (téléchargement avorté)                                             |
+----------+--------------------------------------------------------------------------------------------+
|   503    | pas capable d´envoyer un fichier, erreurs de transfert.                                    |
+----------+--------------------------------------------------------------------------------------------+
|   503    | protocol de transport inconnue, aucune mécanisme de téléchargement disponible.             |
+----------+--------------------------------------------------------------------------------------------+
|   xxx    | les plugins peuvent généré d´autres statuts et messages.                                   |
+----------+--------------------------------------------------------------------------------------------+



*<Consuminghost>* nom d'hôte à partir duquel la récupération a été initiée.

*<Consuminguser>* Nom d'utilisateur du courtier à partir duquel la récupération a été initiée.

*<durée>* combien de temps a duré le traitement, en secondes (décimales)

*<newline>* La fin de la première ligne du message est signalée par un caractère d'alimentation d'une seule ligne.


LE RESTE DU MESSAGE
-------------------

Seule la première ligne de la charge utile AMQP est actuellement définie.
Le reste de la charge utile est réservé pour une utilisation future.



Entêtes AMQP
------------

En plus de la première ligne du message contenant tous les champs obligatoires, l'optionnelle
sont stockés dans les en-têtes AMQP (paires clé-valeur), inclus dans les messages lorsque
approprié.   En plus des en-têtes spécifiés dans la page de manuel sr_post(7), la balise
les en-têtes spécifiques à l'état suivants sont définis :

message=<msgstring>

Une représentation textuelle en anglais du code d'état. selon w3.org/IETF RFC 2616 Status Code Definitions.

EXAMPLE
=======

::

 topic: v02.report.NRDPS.GIF.NRDPS_HiRes_000.gif
 first line: 201506011357.345 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif NRDPS/GIF/ 201 castor anonymous 0.0006767
 headers: parts=p,457,1,0,0 sum=d,<md5sum> message=Downloaded source=ec_cmc from_cluster=ddi.cmc.ec.gc.ca to_clusters=ddi.science.gc.ca,bunny.nrcan.gc.ca


   v02 - version de protocol
   report - type de message

        version et type ensemble specifient le format du message.

   ec_cmc - le nom d´usager AMQP de la source qui a publié le message originalement.

   ddi.cmc.ec.gc.ca - la grappe d´origine de ces données.

   ddi.science.gc.ca,bunny.nrcan.gc.ca - ou on veut envoyer ces données.

          -- taille de partie is 457  (== taille du fichier)
          -- quantités de parties est 1
          -- le restant est 0.
          -- numéro de cette partie est 0.
          -- d - l´algorithm utilisé pour calculé la somme de contrôle.
          -- base_url - l´URL de base pour le ...
          -- chemin relatif 

   on attend que les consommateurs tirent à partir de:
                sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif

   le chemin relatif là dedans étant:
                NRDPS/GIF/NRDPS_HiRes_000.gif

                -- takes file name from base_url.
                -- may be modified by validation process.

   Message 201, téléchargement réussi, de castor, comme usager anonymous, a pris 0.006767 secondes.



LECTURE COMPLÉMENTAIRE
----------------------

https://github.com/MetPX - page d'accueil de metpx-sarracenia

http://rabbitmq.net - page d'accueil du courtier de l'AMQP utilisé pour développer la Sarracenia.


AUSSI VOIR
==========


`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés. (page principale de référence.)

`sr_shovel(8) <sr_shovel.8.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(8) <sr_winnow.8.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - traiter les rapport de télémétrie.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Outil pour s´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_audit(8) <sr_audit.8.rst>`_ - Daémon de surveillance de configuration.

`sr_post(1) <sr_post.1.rst>`_ - Publier la disponibilité d'un fichier aux abonnés.

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.


