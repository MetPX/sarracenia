===================
Notes de Traduction
===================

La traduction n´est pas tellement poli en ce moment. Il y a des termes dont 
le mot juste en français n´est pas tellement claire.  On a commencé avec
www.deepl.com, et ajuster après avec un peu de révision, mais ce n´est pas
super réussi.  Il faut un peu plus de travail.

Placement
---------

Il y a un répertoire fr/ sous doc dans le répository git.  Il y a seulement
sr_subscribe.1.rst là pour l´instant. Il n´est pas linké par d´autres pages
en ce moment.  On rajoutera d´autres page dans la même place, et comme cela
les lien relatifs vont marcher pareil que l´anglais.  On songera a comment
arriver au francais quand ca sera plus complète.

Méthode
-------

On prend www.deepl.com/translate comme point de départ.  Il fait bien la job,
mais il ne peut pas savoir que *then sends a post* ne veut pas 
dire *envoie ensuite un poteau.* En particulier il faut s'attarder aux 
exemples d'execution:

 -  *sr_subscribe foreground first.conf # your first configuration* n'équivaut pas à
 -  *sr_subscribe premier plan premier.conf # votre premier configuration.*

Il faut laisser les exemples, incluant les messages d´erreurs en anglais,
et seulement traduire les commentaires et le text. Alors on prend un
ou deux paragraphes à la fois, et on revise.  Il y a un glossaire plus bas,
la plupart des mots sont évident, mais j´aimerais que des francophones révise
les choix, parce que mon oreille carrée n´est pas toute à faite apte pour 
cette tâche.

 


Glossaire
---------

+---------------+---------------------+-----------------+-------------------+
| Term          | literal translations| Pick            | reasoning         |
+===============+=====================+=================+===================+
|binding        |liaison              |                 |good.              |
+---------------+---------------------+-----------------+-------------------+
|checksum       |somme de contrôle    |                 |um, ok will french |
|               |                     |                 |people get that?   |
+---------------+---------------------+-----------------+-------------------+
|Exchange       | échange, bourse?    | échange?        |probable plain     |
|               |                     |                 |English *exchange* |
|               |                     |                 |is better?         |
+---------------+---------------------+-----------------+-------------------+
|publish        |publier, annoncer    | annoncer/publier|It is supposed to  |
|post           |poteau, afficher     | (verbe)         |be fast.           |
|announce       |publication          | avis (nom)      |should noun be     |
|notifications  |notifications        |                 |a dépêche?         |
+---------------+---------------------+-----------------+-------------------+
|subscribe      |abonner              |                 |good.              |
+---------------+---------------------+-----------------+-------------------+
| topic         |sujet, thème, objet  | thème           |Daniel used it     |
+---------------+---------------------+-----------------+-------------------+
| shim          |cale?                | cale            |deepl, does not    |
| as in library |                     |                 |seem right to me.  |
|               |                     |                 |                   |
+---------------+---------------------+-----------------+-------------------+
| library       |bibliothèue - deepl  |                 |                   |
|               |librarie?            |                 |                   |
|               |                     |                 |                   |
+---------------+---------------------+-----------------+-------------------+




Publish/Post/Announced
======================

Un des problèmes, même en anglais, est qu´on n´a pas choisi un seul mot 
pour l´activité d´envoyer un message à un courtier.  Il y a au moins trois 
familles de mots:

Des fois, *post* qui devrait être compris dans le sense *dépêche*, mais qui 
est des fois traduit comme *poteau.* 

On utilise *advertised* qui devient *annoncer*, ce qui n´est pas pire.

On utilse *publish* qui devient *publier*. 

des fois on vois *affiché*.

Il me semble qu´on devrait choisir un mot pour facilité la compréhension,
et il me semble que *dépêche* est le plus juste. 

conseils bienvenus.
