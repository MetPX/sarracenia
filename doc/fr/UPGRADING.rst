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

jusqqu´a 2.18.05b4
------------------

*NOTIFICATION* Début de traduction de documentation.
