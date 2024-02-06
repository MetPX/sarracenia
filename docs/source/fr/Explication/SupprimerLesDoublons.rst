
Suppression de Doublons
=======================


Lors qu'on achemine les données à travers de réseaux, il faut se préoccuper des "orages" de données 
causé par des boucles de transfert (un serveur A envoit à B, qui renvoit à C, qui renvoit à A.  Si A
ne sait pas qu´il l´a déjà vu, on a un boucle infini, qui peut etre décrit comme un orage le volume
est dérangeant.)

Un attribut commun des flots de données critiques est d´avoir plusieurs serveurs qui produisent ces
données. Si la stratégie de disponibilité requiert que les deux serveurs soient actifs en même temps,
on a besoin de supprimer la production de la deuxième source. le potentiel pour des boucles, ou
des transmissions redondantes de données est haut.

Il s´avère supprimer les duplicat d´envoi a plein de cas d´usage et qu´un seule méthode ne suffit
pas, alors sr3 permet la modification de la méthode implanté dans le module *sarracenia.flowcb.nodupe*
pour augmenter la fléxibilité.

La supression de doublons::

  * crée un clé à partir d´un message d´annonce. 
  * crée un chemin (path) à partir d´un message d´annonce.

Quand un message est à propos d´un message jugé un doublons, on cesse de le traiter.

la clé d´un message d´annonce est préférablement simplement la somme de contrôle 
du champs *Identity*. Si la source de données ne fournit pas de champs *Identity*,
on se fie sur d´autres champes dans le message: *mtime*, *size*, *pubTime.*
Le champs *pubTime* étant mandatoire assure qu´un clé peut toujour être généré pour 
chaque message, mais des fois peut être inefficace.

On peut allumer la suppresion de doublons, ou bien le supprimer avec la
ligne suivante dans le fichier de configuraation::

   nodupe_ttl 300|off|on

(les | indique les choix... alors soit nodupe_ttl 300 où nodup_ttl on, où nodupe_ttl off )
quand on y fournit un chiffre c´est l´intervalle, en secondes, dont on se souvient
d´un messages.


Standard (basé sur le chemin et contenu)
----------------------------------------


**méthode**: Quand les produits on le même clé et chemin, ils sont des doublons.

Deux serveur peuvent envoyer le même produit, aven le même *relPath* à un serveur plus 
loin.


Data (basé uniquement sur le contenu)
-------------------------------------

**method**: Quand les produits on le même clé, ils sont des doublons.

dans le ficher de configuration on devrait voir::

    nodupe_basis data

ou bien::

    flowcb_prepend sarracenia.flowcb.nodupe.data.Data


remplace la génération de clé de suppression des doublons standard pour inclure uniquement 
la somme de contrôle du contenu du fichier. Ce module ajuste le champ *path* (chemin) utilisé par 
le champ standard de suppression des doublons. La directive *flowcb_prepend* assure qu'elle 
est appelée avant la traitement de doublons integrée.

Le produits identiques ont le même somme de contrôle.  à utiliser lorsque deux sources
génèrent le même produit. 


Name (basé uniquement sur le nom)
---------------------------------

**method**: Quand les fichiers ont le même nom, ils sont identiques.

dans le fichier de configuration, soit::

    nodupe_basis data

ou bien::

    flowcb_prepend sarracenia.flowcb.nodupe.name.Name

remplace la générations de clé de suppression de doublons en utilisant uniquement
le nom de fichier.

Quand plusieurs source génèrent un produit, mais les résultats ne sont pas identique
au niveau binaire, il faut une autre approche.

URP
~~~

Dans le cas des systèmes de traitement de données RADAR, il y 6 serveurs qui génèrent
les mêmes produits (bien qu´il ne soient pas exactement le même séquence d´octets.)
Les produit sont les même parce qu´ils sont dérivé de les même données en amont,
ont suivi une traitement semblable, mais les détails de traitement font en sorte
que les résultats ne sont pas identiques au niveau binaire.

Les serveur sont identifié commes sources distinctes, alors le chemin d´acces relatif 
(*relPath*) diffèrent. Mais les noms de fichier pour les produits sont les mêmes,
alors on peut utiliser le nom dans ce cas.


Le fichiers trop changeant (mdelaylatest)
------------------------------------------

**method**: retard les fichiers x secondes pour assurer qu´il n´y a pas de nouvelle version.

NB:
Il s'agit d'un filtre supplémentaire à la suppression des doublons, et ce qui précède
méthodes peuvent être utilisées conjointement avec mdelaylatest. ce filtre est idéalement
appliqué avant la suppression des doublons pour réduire la taille de la base de données.


Dans le fichier de configuration, soit::

    mdelay 30
    flowcb_prepend sarracenia.flowcb.mdelaylatest.MDelayLatest

va retarder la distribution des messages d´annonce par 30 secondes.
Si plusieurs versions sont produites avant que le fichier a 30 secondes d´age,
on envoie uniquement la dernière version lorsqu´il aura 30 secondes d´age.


cas d´usage
~~~~~~~~~~~

Dans certains cas, certaines sources de données re-écrivent très souvent les fichiers.
Si les fichiers sont volumineux (la copie prend beaucoup de temps) ou s'il y a une fil d'attente (l'abonné
a un certain temps de retard sur le producteur.), un algorithme pourrait écraser un fichier, ou
y ajouter trois ou quatre fois avant d'avoir une version "finale" qui durera un certain temps.

si le réseau a un délai de propagation supérieur à la période de remplacement, alors par
le moment où le consommateur demande le fichier, il sera différent (provoquant potentiellement 
des incompatibilités de somme de contrôle.) ou, si c'est assez rapide, copier un fichier qui 
ne durera pas plus de quelques secondes pourrait être un gaspillage de bande passante et de traitement.


les citypages du site météo.gc.ca
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


( https://hpfx.collab.science.gc.ca/YYYYMMDD/WXO-DD/citypage_weather/ )

là, les citypages sont un produit composé (dérivé de nombreux produits en amont distincts.)
le script qui crée les produits citypage semble écrire un en-tête, puis un enregistrement,
puis à la toute fin, une bande-annonce. il y a eu de nombreux cas de transmission de fichiers
comme *xml invalide* parce que la bande-annonce était manquante. Il faut attendre que le script ait
fini d'écrire le fichier 

Miroitage CHP
~~~~~~~~~~~~~

Dans la miroitage à grande vitesse des données entre des grappes de calcul haute performance, les programmes
passent souvent du temps à ajouter des enregistrements aux fichiers, peut-être des centaines de fois par seconde.
Une fois le script terminé, le fichier devient en lecture seule pour les consommateurs. Ce n'est pas utile
transmettre ces valeurs intermédiaires. Un fichier de 100 octets surveillé à l'aide de la bibliothèque shim
ou un sr_watch, pourrait être modifié des centaines de fois, provoquant une copie pour chaque modification potentiellement
déclenchant des centaines d'exemplaires. Il vaut mieux attendre la fin du processus de mise à jour,
pour que le fichier soit inactif, avant de poster un message d´annonce.


Fichiers trop vieux
-------------------

**method**: les messages à propos des fichiers trop vieux sont supprimés.

dans les fichiers de configuration::

    fileAgeMax 600

Les messages notificationsfichiers pour des fichiers qui sont agés de plus que 600 secondes (10 minutes) seront
supprimés.

Ceci est généralement utilisé avec des sondages (poll) qui ont des répertoires de très longue durée.
Exemple : un serveur distant dispose d'une base de données permanente de fichiers distants. ca ne sert à rien
de reexaminer de fichiers vieux de deux ans.



A votre gout!
-------------

Dans le fichier de configuration::

    vos_parametres 
    flowcb_prepend votre_class.VotreClass

Si aucune des méthodes intégrées de suppression des doublons ne fonctionne pour votre cas d'utilisation, vous pouvez
sous-classe sarracenia.flowcb.nodupe et dériver les clés d'une manière différente. Voir le
les classes sarracenia.flowcb.nodupe.name et sarracenia.flowcb.nodupe.data pour des exemples de
comment faire.

On peut également implémenter un filtre qui définit le champ *nodupe_override* dans le message ::

  msg['nodupe_override] = { 'key': votre_clé, 'path': votre_chemin }

et la méthode standard de suppression des doublons utilisera la clé et la valeur fournies.
Il existe également une fonction d'assistance disponible dans la classe nodupe ::

  def deriveKey(self, msg) --> str

qui examinera les champs du message et dérivera la clé *normale* qui sera
généré pour un message, que vous pouvez ensuite modifier si vous ne recherchez qu'un petit changement.


