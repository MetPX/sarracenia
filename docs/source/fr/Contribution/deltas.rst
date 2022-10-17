
Status: Pre-Draft


=============================================================
 Discussion sur la propagation de la modification de fichiers
=============================================================

C’était une réflexion précoce sur la façon de gérer les mises à jour de fichiers.
Les premières versions du protocole ne concernaient que des fichiers entiers.
Lorsque les ensembles de fichiers sont suffisamment volumineux, des mises
à jour partielles deviennent très souhaitables.
En outre, lorsque la taille des fichiers individuels est suffisamment grande et lors de la traversée
des liaisons WAN, on peut obtenir un avantage pratique substantiel en envoyant des
données utilisant plusieurs flux, plutôt qu’un seul.

Donc, dans v02, il y a un en-tête 'parts' qui indique la méthode de partitionnement
utilisé pour un transfert donné, et la conclusion sur le format/protocole
est maintenant documenté dans la page de manuel sr_post(7).
Ce dossier contient les premières discussions et notes.

Algorithme utilisé (quel que soit l’outil) :
	- Pour chaque 'bloc' (taille de bloc intéressante) il faut générer une signature.
	- Lorsqu’un abonné lit un message de notification, il inclut la signature.
	- Il compare les signatures sur le fichier qu’il a déjà, et le met à jour pour qu’il corresponde.

L’algorithme zsync est la bonne idée, peut peut-être l’utiliser directement.

Que se passe-t-il si chaque notification concerne un bloc, pas un fichier ?
---------------------------------------------------------------------------

Expérience de Gedanken... par messages de blocage, plutôt que par fichiers entiers ?
Que se passe-t-il si les messages que nous envoyons sont tous par bloc?

Pourquoi est-ce vraiment cool?

 - Il fait le truc gridftp, en divisant les transferts de fichiers uniques
   en flux parallèles.

 - Pour les fichiers volumineux, les ddsr peuvent avoir tout un tas de fichiers partiels,
   au lieu des complets, car le transfert est divisé sur
   plusieurs nœuds, pas de problème, tant que les étapes ultérieures sont souscrites
   à tous les DDSR.

 - les commutateurs intermédiaires n’ont pas besoin de stocker le fichier le plus volumineux
   qui peut être transférés, seulement un certain nombre des plus gros morceaux.
   Élimine le problème de taille maximale du fichier.

 - Cela concerne également les fichiers qui sont écrits au fil du temps, sans attendre
   jusqu’à ce qu’ils soient terminés avant d’appuyer sur envoyer.

 - pour que le client fasse un envoi multithread, il suffit de démarrer
   un nombre quelconque de sr_senders écoutant leur propre échange d’entrées.
   Partager l’abonnement, tout comme sr_subscribe (dd_subscribe) le fait.

 - Pour les fichiers volumineux, vous pouvez voir les rapports d’avancement reçus par les sources
   confirmation de chaque couche de commutation recevant chaque morceau.

disons que nous définissons une taille de bloc de 10 Mo, et que nous vérifions ce bloc, en notant le décalage, puis
on continue?

v01.post donc :
blocksz sz-inblocks rest blocknum flags chksum base-url relative-path flow ....

Voir Journalisation.txt pour une description de 'Flow', User Settable, avec une valeur par défaut.

flags indique si le chksum est pour le nom ou le corps. (si la somme de contrôle est pour le nom,
alors impossible d’utiliser des chksums bloquants.) ... indique que les sommes de contrôle
de nom ne doivent être utilisées que pour les petits fichiers.

Le blocksz établit le multiplicateur pour le sz et le blocknum.  le reste
est le dernier bit du fichier après la dernière limite de bloc.

Donc, vous calculez la somme de contrôle pour chaque bloc que vous envoyez un message avec le bloc,

De cette façon, pour les fichiers volumineux, le transfert peut être divisé sur un grand nombre de nœuds.
Mais alors le remontage est un peu un casse-tête.  Chaque nœud de DDSR aura-t-il seulement
Fichiers volumineux fractionnaires (c’est-à-dire clairsemés) ?   Tant que le sr_sub est aux deux DDSR, il devrait
tout obtenir.   Que se passe-t-il avec les fichiers fragmentés ?

https://administratosphere.wordpress.com/2008/05/23/sparse-files-what-why-and-how/

c’est bon...
Cela fonctionnerait, sous Linux, mais c’est un peu étrange, et causerait de la confusion dans la
pratique.  D’ailleurs, comment savons-nous quand nous avons terminé?

--- --- de remontage
Que diriez-vous de ce qui suit.  Lorsque sr_subscribe(dd_subscribe) écrit des fichiers, il écrit dans un fichier
suffixé .sr§1 lorsqu’il reçoit un fichier, et qu’il y a un .sr§ il vérifie la taille
du fichier, si la partie courante est contiguë, il suffit d’ajouter (via lseek & write)
les données du fichier .sr§.  Sinon, il crée un .sr§ <blocknum>séparé

suffixe .sr§
------------

Mais cela signifie qu’ils annoncent les pièces... Hmm... Les noms signifient maintenant quelque chose,
Nous utilisons le caractère de section au lieu de partie.  Pour éviter cela, choisissez un nom qui
est plus inhabituel que .part quelque chose comme .sr§partnum (en utilisant utf-8, intéressant
pour voir ce que l’encodage d’URL fera à cela.)  Il est bon d’utiliser des
caractères spéciaux UTF, parce que personne d’autre ne les utilise, donc peu susceptible de s’affronter.

Et si quelqu’un annonce un fichier .sr§? Qu’est-ce que cela signifie? Avons-nous besoin de
le détecter?

Ensuite, il regarde dans le répertoire pour voir si un .sr§<blocknum +1> existe, et l'ajoute
si c’est le cas, et boucle jusqu’à ce que toutes les parties contiguës soient ajoutées (les
fichiers correspondant supprimés.)

Remarque : N’utilisez pas l’écriture d’ajout .sr§, mais toujours lseek et write.  Cela empêche
race condition de causer des ravages.  S’il y a plusieurs sr_subscribe (dd_subscribes)  S’il y a plusieurs sr_subscribe
(dd_subscribes) écrivant le fichier, ils écriront simplement les mêmes données plusieurs fois (dans le pire des cas).

Quoi qu’il en soit, lorsque vous manquez de pièces contiguës, vous vous arrêtez.

Si le dernier bloc contigu reçu inclut la fin du fichier, effectuez la logique d’achèvement du fichier.

Comment sélectionner Chunksize
------------------------------

	- Choix de la source?
	- Nous imposons les nôtres à DDSR ?

Une valeur par défaut 10*1024*1024=10485760 octets, avec remplacement possible.

peut vouloir que la partie validation impose une taille de bloc minimale
sur les fichiers publiés, en plus du chemin d’accès au fichier.

nous fixons un minimum, disons 10 Mo, puis si c’est moins de 5% du fichier,
utilisez 5%, jusqu’à ce que nous arrivions à un morceau maximum... disons 500 Mo.
Remplacer par la taille 0 (pas de morcellement d’un long envoi.)

Quelle est la surcharge pour envoyer un bloc?
  - il n’y a pas de champs de largeur fixe dans les messages, ils sont tous de longueur variable ASCII.
  - estimer qu’une notification d’âge est de 100 octets,
  - Le message de journal est peut-être de 120 octets.

pour chaque bloc transféré.
	la notification va dans un sens,
	Au moins un message de journal par étendue passe dans l’autre sens.

    Si nous disons deux sauts + livraison client (un troisième saut)

    Donc un bloc aura de l’ordre de 100+4*120 = 580 octets.

Il a reconnu qu’il y avait une surcharge de protocole importante sur les petits fichiers.

Cependant, on pourrait espérer que les frais généraux deviendront plus raisonnables pour les fichiers plus volumineux,
Mais cela est limité par la taille du bloc.
Esthétiquement, il faut choisir une taille qui éclipse la surcharge.

Si nous faisons des cksums par blocs, chemin à partir de v00
------------------------------------------------------------
compatibilité... amélioration...
Les alertes v00.notify se résument à :

v01.post pourrait être:

filesz 1 0 0 ...
	- la taille du bloc est la longueur du fichier entier, 1 bloc est la taille
	- pas de reste.
	- 0ème bloc (le premier, zéro origine comptée)

Ou nous prenons la convention selon laquelle une taille de bloc de zéro signifie pas de blocage...
dans lequel la poursuite serait:

   0 1 fichiersz 0 ...
	- Stocker le SZ comme le reste.
	- désactiver le blocage pour ce fichier.

S’il y a une validation sur la taille de blocage, il doit il y avoir un moyen de le gérer.


Digression sur ZSync
--------------------

zsync est disponible dans les référentiels et zsync(1) est le client de téléchargement existant.
zsyncmake(1) construit les signatures, avec une taille de bloc programmable.

Il semble que zsync est utilisable tel quel?

Inconvénient : la portabilité.
    besoin de zsync sur Windows et Mac pour les téléchargements, la dépendance est pénible.
	il existe un binaire Windows, créé une fois en 2011... Hmm...
	Je ne l’ai pas vu sur Mac OS non plus... soupir...

Nous envoyons les signatures dans les messages de notification, plutôt que de les publier sur le site.
Si nous définissons la taille du bloc à une valeur élevé, alors pour les fichiers < 1 bloc, il n’y a pas de signature.

Est ce que sr_sarra doit publier la signature sur le site, pour la compatibilité avec ZSYNC ?

Je ne veux pas forker zsyncmake pour chaque produit...
Même si nous n’utilisons pas zsync lui-même, nous pourrions vouloir être compatibles... Alors utilisez
un format tiers et avoir un comparable.  1ère mise en œuvre ferait l’affaire
Avec un forking, la 2e version peut répliquer l’algorithme en interne.

Peut-être avons-nous un seuil, si le fichier est inférieur à un mégaoctet, nous envoyons simplement
le nouveau.  L’intention n’est pas de répliquer des arbres sources, mais de grands ensembles de données.

	- Pour la plupart des cas (lors de l’écriture d’un nouveau fichier), nous ne voulons pas de frais généraux supplémentaires.
	- La cible est les gros fichiers qui changent, pour les petits, transférer à nouveau, n’est pas un gros problème.
	- veulent minimiser la taille de la signature (tout comme les voyages avec des notifications.)
	- Définissez donc une taille de bloc à une valeur vraiment grande.

Peut-être construire le client zsync dans sr_subscribe (dd_subscribe), mais utiliser zsync make côté serveur ?
Ou lorsque le fichier est assez volumineux, le fork d’un zsync n’est pas un gros problème? Mais Mac & Win...


Considérations relatives au serveur/protocole
---------------------------------------------

HTTP :
	-- utilise la fonction de plage d’octets de HTTP.
	-- FIXME: trouver des échantillons à partir d’autres e-mails.

en SFTP/python/paramiko...
	-- il y a readv( ... ) qui permet de lire des sous-ensembles d’un fichier.
	-- la commande read dans la spécification SFTP PROTOCOL a offset comme argument standard de read

