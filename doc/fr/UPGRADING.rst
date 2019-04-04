------------------
 GUIDE MISE A JOUR
------------------

Ce fichier documente les changements de comportement afin de fournir des conseils aux personnes chargées de la mise à niveau.
d'une version précédente.  Pour effectuer une mise à niveau sur plusieurs versions, il faut commencer par
à la version après celle installée, et tenez compte de toutes les notifications pour les notifications intérimaires.
versions.  Bien que la stabilité du langage de configuration soit un élément important de l
à l'occasion, des changements ne peuvent être évités. Ce fichier ne documente pas les nouveaux documents.
mais uniquement les changements qui suscitent des inquiétudes lors des mises à niveau.  Les avis
prendre la forme :

**CHANGE**
   indique où les fichiers de configuration doivent être modifiés pour obtenir le même comportement qu'avant la publication.

**ACTION**
   Indique une activité de maintenance requise dans le cadre d'un processus de mise à niveau.

**BUG**
  indique un bogue grave pour indiquer que le déploiement de cette version n'est pas recommandé.

*NOTIFICATION*
  un changement de comportement qui sera perceptible pendant la mise à niveau, mais qui n'est pas préoccupant.

*INTERVENTION*
  indiquer les interventions recommandées qui sont recommandées, mais non obligatoires. Si l'activité prescrite n'est pas effectuée,
  la conséquence est soit une ligne de configuration qui n'a pas d'effet (gaspillage), soit l'application.
  peut générer des messages.

Instructions d´Installations
----------------------------

`Guide d´Installation <Install.rst>`_

git origin/master 
-----------------

2.19.04.b1
----------

*NOTICE*: le problèm avec v03 corrigé.

2.19.03.b6
----------

**BUG**:  sr_post avec *post_topic_prefix v03.post* ne marche plus dans cette version.


2.19.03.b1
----------

*NOTICE*: le problèm sur Ubuntu 14.04 et 16.04 de la version antérieur est reglée.


2.19.02.b2
----------

*CHANGE*: Le paramètre *logrotate* était une durée (une quantité de jours à garder les logs). 
          Il indique maintenant la nombre de fichiers à garder.



2.19.02.b1
----------

*ACTION*: nom de paquet ubuntu à changé de *python3-metpx-sarracenia* à *metpx-sarracenia*
          pour mieux conformé au normes debian. les mises-à-jour automatisé ne vont
          pas marcher. Il faut enlever l´ancien pacquet et installer le nouveau.



*ACTION*: remplacement de librarie AMQP utilisé par Sarracenia: de python3-amqplib à
          python3-amqp.  Il faut s´assurer que la nouvelle librarie soit installer
          avant la nouvelle version.

**BUG**:  En Ubuntu 14.04 et 16.04, le changement de librarie à causé une panne,
          parce qu´un appel nécessaire dans les versions plus neuf (*connect*) n´éxiste
          pas dans les anciennes versions.

*NOTICE*: un option d´installation binaire Windows et maintenant disponible,
          rendant l´installation plus commode. On peut encore emprunter les
          anciens méthodes (pip dans un environnement python3)


*NOTICE*: défaillance de *remove* en 2.19.01b1 corrigé. 



2.19.01b1
---------

 **BUG**: l´action *remove* ne marche pas dans certains cas.

*NOTICE*: Le format des fichiers créés par *-save* et *-restore* a changé pour permettre
          le nouveau format `v03 <sr_postv3.7.rst>`_. Des fichiers de sauvegarde créés avec
          la nouvelle version ne seront pas lisible par les anciennes versions.  
          La nouvelle version peut pourtan lire les fichiers créés par les versions antérieurs.

*CHANGE*: Dans chaque message (utilisé dans des *plugin*) le nom de l´attribut de l´heure
          d´insertion à changé de nom de *msg.time* à *msg.pubtime*
          Si un *plugin* modifie *msg.time* un message d´avertissement sera émit.



2.18.09b2
---------

*ACTION*: L´encodage des noms de fichiers stockés dans le fichier qui indique
          le fichiers récemment reçus passe par la routine python urrlib.parse.quote().
          Ceci corrige une problème que les anciennes version avait avec les fichiers
          qui comprennent des espaces.  Vaut mieux effectuer un --reset lors d´une
          mise-à-jour.

2.18.08b1
---------

*CHANGE*: les options de sr_subscribe *strip, mirror, flatten,* avait une étendu globale.
          Dès cette version, ces options sont interpretés conjointement avec les
          options *directory* qui les suivent. Il faut reviser les configurations
          éxistantes pour assurer que ces options soient placées avant les occurrences
          de *directory* , ce qui semble être naturel de toute façon.



jusqqu´a 2.18.05b4
------------------

*NOTIFICATION* Début de traduction de documentation.
