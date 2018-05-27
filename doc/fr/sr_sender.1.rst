
==========
 SR_Sender 
==========

----------------------------------------------------
Envoyer des fichiers publiés à des serveurs distants
----------------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::


DESCRIPTION
===========

**sr_sender** est un composant dérivé de `sr_subscribe(1) <sr_subscribe.1.rst>`_ utilisé 
pour envoyer des fichiers locaux à un serveur distant, principalement avec SFTP.
**sr_sender** est un consommateur standard, utilisant tous les paramètres AMQP normaux 
pour les courtiers, les bourses, les files d'attente, et tout le filtrage standard 
côté client avec *accept*, *reject*, et *on_message.*

Souvent, un courtier annoncera les fichiers à l'aide d'un protocole réseau tel que HTTP,
mais pour l'expéditeur, il s'agit en fait d'un fichier local. Dans de tels cas, on pourra
voir un message : **ERROR : The file to send is not local.**
Un plugin on message convertira l'url web en fichier local: :

  base_dir /var/httpd/www
  on_message msg_2localfile msg_2localfile

Ce plugin on_message fait partie des paramètres par défaut pour les expéditeurs, mais un plugin
doit encore spécifier base_dir pour qu'il fonctionne.

Si un **post_broker** est défini, **sr_sender** vérifie si le nom de grappe indiqué
par l'option **to** se trouve dans l'un des groupes de destination du message.
Si ce n'est pas le cas, le message est ignoré (le fichier n´est pas envoyé.)


DESTINATION INDISPONIBLE
------------------------

Si le serveur auquel les fichiers sont envoyés va être indisponible pour
une période prolongée, et il ya un grand nombre de messages à leur envoyer, puis
la file d'attente s'accumulera sur le courtier. Comme la performance de l'ensemble du courtier
est affecté par de grandes files d'attente, il faut minimiser ces files d'attente.

Les options *-save* et *-restore* sont utilisées pour éloigner les messages du courtier.
alors qu'une file d'attente trop longue s'accumulera certainement.
L'option *-save* copie les messages dans un fichier disque (par instance) (dans le même répertoire).
qui stocke les fichiers state et pid), sous forme de chaînes codées json, une par ligne.
Quand une file d'attente s'accumule::

   sr_sender stop <config>
   sr_sender -save start <config>

Et exécutez l'expéditeur en mode *save* (qui écrit continuellement les messages entrants sur le disque).
dans le journal, une ligne pour chaque message écrit sur le disque::

  2017-03-03 12:14:51,386 [INFO] sr_sender saving 2 message topic: v02.post.home.peter.sarra_devdocroot.sub.SASP34_LEMM_031630__LEDA_60215

Continuez dans ce mode jusqu'à ce que le serveur absent soit à nouveau disponible.  A ce moment-là::

   sr_sender stop <config> 
   sr_sender -restore start <config> 

Lors de la restauration à partir du fichier disque, des messages tels que les suivants apparaîtront dans le journal::

  2017-03-03 12:15:02,969 [INFO] sr_sender restoring message 29 of 34: topic: v02.post.home.peter.sarra_devdocroot.sub.ON_02GD022_daily_hydrometric.csv

après le dernier, on verra::

  2017-03-03 12:15:03,112 [INFO] sr_sender restore complete deleting save file: /home/peter/.cache/sarra/sender/tsource2send/sr_sender_tsource2send_0000.save 

et le sr_sender fonctionnera normalement par la suite.



EXEMPLE 1 : REPLICATION POMPE À POMPE
-------------------------------------

 - **mirror             <boolean>   (default: True)**
 - **base_dir      <directory> (None)**

 - **destination        <url>       (MANDATORY)**
 - **do_send            <script>    (None)**
 - **kbytes_ps          <int>       (default: 0)**
 - **post_base_dir <directory> (default: '')**

 - **to               <clustername> (default: <post_broker host>)**
 - **on_post           <script>     (default: None)**
 - **post_broker        amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
 - **url                <url>       (default: destination)**

Pour la duplication de données d´une pompe a une autres, **mirror** est réglé sur True (par défaut).

**base_dir** fournit le chemin d'accès au répertoire qui, lorsqu'il est combiné avec le chemin d'accès relatif.
un dans la notification sélectionnée donne le chemin absolu du fichier à envoyer.
La valeur par défaut est None, ce qui signifie que le chemin d'accès dans la notification est le chemin absolu.

La **destination** définit le protocole et le serveur à utiliser pour livrer les produits.
Sa forme est une url partielle, par exemple :  **ftp://myuser@myhost****
Le programme utilise le fichier ~/.conf/sarra/credentials.conf pour obtenir les détails restants.
(mot de passe et options de connexion).  Les protocoles supportés sont ftp, ftps et sftp. Si le
l'utilisateur a besoin d'implémenter un autre mécanisme d'envoi, il fournirait le script du plugin.
par l'option **do_send**.

Sur le site distant, le **post_base_dir** sert aux mêmes fins que le **base_dir** sur ce serveur.
La valeur par défaut est None, ce qui signifie que le chemin d'accès délivré est absolu.
Maintenant, nous sommes prêts à envoyer le produit..... Par exemple, si la notification sélectionnée ressemble à ceci :

**2015081316161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_produit****.

**sr_sender** effectue la pseudo-livraison suivante :

envoie le fichier local[**base_dir**]/relative/path/to/IMPORTANT_product
à **destination**/[**post_base_dir**]/relative/path/to/IMPORTANT_product
(**kbytes_ps** est supérieur à 0, le processus tente de respecter cette vitesse 
de livraison... ftp,ftps,ftps,ou sftp)

A ce stade, un besoin de configuration de pompe à pompe doit envoyer la notification 
à distance.....  (Si le post_broker n'est pas défini, il n'y aura pas de publication.... 
juste la réplication de produits)

L´avis contient toutes les mêmes informations (attributs de thème et autres en-têtes), à 
l'exception du champ url, dans notre exemple.. :  **http://this.pump.com/****

Par défaut, **sr_sender** met la **destination** dans ce champ.
L'utilisateur peut écraser ceci en spécifiant l'option **post_base_url**. Par exemple :

**post_base_url http://remote.apache.com**

L'utilisateur peut fournir un script **on_post**. Juste avant que le message n'arrive
publier au **post_broker** et **post_exchange**, le routine **on_post** est appelé.... 
avec l'instance de classe **sr_sender** comme argument.
Le script peut effectuer tout ce que vous voulez.... s'il renvoie False, le message ne sera pas
être publié. Si Vrai, le programme continuera le traitement.


EXEMPLE 2: DISSEMINATION ( STYLE SUNDEW )
-----------------------------------------

Dans ce type d'utilisation, nous ne repost généralement pas.... mais si la fonction
**post_broker** et **post_exchange** (**url**,**on_post**) sont définis,
le produit sera annoncé (avec éventuellement un nouvel emplacement et un nouveau nom)
Réintroduire les options dans un ordre différent.
avec de nouvelles pour faciliter l'explication.

 - **mirror             <boolean>   (défaut: True)**
 - **base_dir      <directory>      (défaut: None)**

 - **destination        <url>       (OBLIGATOIRE)**
 - **post_base_dir <directory>      (défaut: '')**

 - **directory          <path>      (OBLIGATOIRE)**
 - **on_message            <script> (défaut: None)**
 - **accept        <regexp pattern> (défaut: None)**
 - **reject        <regexp pattern> (défaut: None)**


Il y a 2 différences avec le cas précédent : le répertoire****, et les 
options **nom de fichier**.  Le **base_dir** est le même, et il en va de même pour le
**destination** et les options **post_base_dir**.

L'option **répertoire** définit un autre "chemin relatif" pour le produit.
à sa destination.  Il est marqué aux options **accept** définies après lui.
Si une autre séquence de **répertoire****/**accept** suit dans le fichier de configuration,
le deuxième répertoire est étiqueté aux acceptations suivantes et ainsi de suite.

Les modèles **accept/reject** s'appliquent à l'url d'avis de message comme ci-dessus.
Voici un exemple, voici quelques options de configuration ordonnées.. ::

  directory /my/new/important_location

  accept .*IMPORTANT.*

  directory /my/new/location/for_others

  accept .*

l'avis en cause:

**20150813161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_product**

Le fichier a été sélectionné par la première option **accept**. Le chemin relatif distant devient
**/my/new/important_location** .... et **sr_sender** effectue la pseudo-livraison suivante :

envoie le fichier local[**base_dir**]/relative/path/to/IMPORTANT_product
à **destination**/[**post_base_dir**]/my/new/important_location/IMPORTANT_product

Habituellement, cette façon d'utiliser **sr_sender** ne nécessite pas de publication du produit.
Mais si **post_broker** et **post_exchange** sont fournis, et **post_base_url**, comme ci-dessus, 
est réglé sur **http://remote.apache.com**, que **sr_sender** reconstruirait :


Topic (thème):
**v02.post.my.new.important_location.IMPORTANT_product**

Avis:
**20150813161959.854 http://remote.apache.com/ my/new/important_location/IMPORTANT_product**


AUSSI VOIR
==========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés.

`sr_shovel(1) <sr_shovel.1.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(1) <sr_winnow.1.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - messages de rapport de processus.

`sr_post(1) <sr_post.1.rst>`_ - publier les avis de fichiers.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sarra(1) <sr_sarra.1.rst>`_ - Outil pour S´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.


