
=========================
File Detection Strategies
=========================


Le travail fondamental de sr3_watch est de remarquer quand les fichiers sont
disponibles pour être transférés. La stratégie appropriée varie en fonction de:

 - le **nombre de fichiers de l'arbre** à surveiller,
 - le délai **minimum pour signaler les changements** aux fichiers qui est acceptable, et
 - la **taille de chaque fichier** dans l'arbre.


**L'arbre le plus facile à surveiller est le plus petit** Avec un seul répertoire à surveiller où l'on
affiche un message pour un composant *sr_sarra*, alors l'utilisation de l'option *delete* gardera en tout temps
le nombre minimale de fichiers dans le répertoire et minimisera le temps de remarquer les nouveaux. Dans ces
conditions optimales, l'observation des fichiers dans un centième de seconde, c'est raisonnable
de s'y attendre. N'importe quelle méthode fonctionnera bien pour de tels arbres, mais...  les charge imposé
sur l´ordinateur par la méthode par défaut de sr3_watch (inotify) sont généralement les plus basses.

Lorsque l’arborescence devient grande, la décision peut changer en fonction d’un certain nombre de facteurs,
décrit dans le tableau suivant. Il décrit les approches qui seront les plus basses en
latence et en débit le plus élevé d’abord, et éventuellement l'option la moins efficace
qui cause le plus de retard par détection.


Tableau de stratégie de détection de fichiers
----------------------------------------------


+--------------------------------------------------------------------------------------------+
|                                                                                            |
| Stratégies de détection de fichiers (ordre : de la plus rapide à la plus lente)            |
| Le Méthodes plus rapides marchent sur les plus grands arborescences.                       |
|                                                                                            |
+-------------+---------------------------------------+--------------------------------------+
| Méthode     | Description                           | Application                          |
+=============+=======================================+======================================+
|             |Livraison de fichiers annoncée par     |Beaucoups de travaux d´utilisateur qui|
|             |libsrshim                              |ne peuvent pas être modifié afin de   |
|             |                                       |publier explicitement.                |
|Implicite    | - nécessite le paquet C.              |                                      |
|publier      | - export LD_PRELOAD=libsrshim.so.1    |                                      |
|avec biblio  | - usage accru de *reject*             | - arbres de millions de fichiers.    |
|thque de cale| - fonctionne sur n´importe quelle     | - efficacité maximale.               |
|             |   taille d´arbre de fichiers.         | - complexité maximale.               |
|(LD_PRELOAD) | - très multi-tâches.                  | - ou python3 n´est pas disponible.   |
|             | - E/S par origine (plus efficace)     | - pas de sr_watch.                   |
|(en C)       |                                       | - pas de plugins.                    |
|             |                                       |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Publications d´avis via                |l´usager publie quand il a fini d´    |
|Publication  |`sr_post(1) <sr_post.1.rst>`_          |écrire le fichier.                    |
|explicite par|où d´autres composants sr\_            |                                      |
|clients      |une fois écriture complété.            |                                      |
|             |                                       | - contrôle plus fine.                |
|             | - publieur fait la somme de contrôle  | - d´habitude meilleur.               |
|C: sr_cpost  | - Moins de aller-retouers             | - meilleur approche que sr_watch.    |
|où           | - un peu plu len que le bibliothèque  | - L´usager doit publier explicitement|
|Python:      | - pas de balayage de répertoire.      |   dans ces scripts/jobs.             |
|sr_post      | - très multi-tâches.                  |                                      |
+-------------+---------------------------------------+--------------------------------------+
|sr_cpost     |fonctionne comme watch si sleep > 0    | - ou python3 est dure a avoir.       |
|             |                                       | - ou la vitesse est important.       |
|(en C)       | - plus vite que sr_watch.             | - ou on n´a pas besoin de plugins.   |
|             | - utilise moins de mémoire vive que   | - limité sues with tree size         |
|             |   sr3_watch                            |   as sr_watch, just a little later.  |
|             | - peut marcher avec des arbres        |   (see following methods)            |
|             |   plus grand que sr3_watch             |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Fichier transférés avec *.tmp* suffixe.|Réception de livraisons d´autres      |
|sr_watch avec|lorsque complete, renommé pour enlevé  |systèmes ( .tmp étant standard)       |
|reject       |suffix. Suffix est programmable.       |Pour recevoir de Sundew.              |
|.*\.tmp$     |                                       |                                      |
|(suffix)     | - require aller-retour pour renommage |Meilleur choix pour des arbres de     |
|             |   (un peu plus lent)                  |taille modéré sur un seul serveur.    |
|             |                                       |les plugins sont fonctionnent         |
|             | - on peu présumer 1500 fichier/second |                                      |
|  (defaut)   | - gros arborescences auras de delais  |Va bien avec quelques milliers de     |
|             |   au démarrage                        |fichiers avec seulement quelques      |
|(en Python)  | - chaque noeud dans un grappe a besoin|secondes de delai au démarrage.       |
|             |   de tourner un instance.             |                                      |
|             | - chaque sr3_watch est une seul tâche. |trop lent pour des arbres de millions |
|             |                                       |fichiers.                             |
+-------------+---------------------------------------+--------------------------------------+
|sr_watch avec|utilisez conventsion linux pour cacher |                                      |
|reject       |des fichiers avec un prefix '.'        |envoi à des systèmes qui ne tolérent  |
|^\\..*       |                                       |pas des suffix.                       |
|(Prefix)     |compatabilité                          |                                      |
|             |performance identique à la méthode     |                                      |
|             |précédente.                            |                                      |
+-------------+---------------------------------------+--------------------------------------+
|sr_watch avec|Age minimal (de modification)du fichier|Dernier choix, impose un delai fix.   |
|inflight     |avant qu´il est considéré complet.     |Seulement si aucune autre méthode     |
|numéro       |                                       |marche.                               |
|(mtime)      | - rajout ce délai sur chaque transfert|                                      |
|             | - Vulnérable à des pannes réseau.     |Réception de sources non-coopératives |
| où          | - Vulnérable à des horloges désynchr  |                                      |
|             |   onizés                              |(choix valable avec PDS)              |
|nodupe__\    |                                       |                                      |
|fileAgeMin   |                                       |Si un processus re-écrit un fichier   |
|             |                                       |souvent, mtime peut servire à réduire |
|             |                                       |le rhythme de publication d´avis.     |
+-------------+---------------------------------------+--------------------------------------+
|force_polling|Tel que les 3 méthodes précedentes     |Seulement quand INOTIFY ne marche pas |
|avec  reject |mais en se servant de listings de      |Comme dans une grappe multi-noeud.    |
|où mtime     |répertoires                            |                                      |
|             |                                       |                                      |
|             | - Gros arbres plus lents              |                                      |
|             | - le plus compatbile (marchera        |Nécessaire sur des systèmes avec      |
|             |   n´importe où)                       |NFS sure plusieurs noeuds qui écrivent|
|             |                                       |en parallèle.                         |
+-------------+---------------------------------------+--------------------------------------+

sr_watch est sr3_post avec l'option *sleep* qui lui permettra de boucler les répertoires donnés en arguments.
sr_cpost est une version C qui fonctionne de manière identique, sauf qu'elle est plus rapide et
utilise beaucoup moins de mémoire, à l'adresse le coût de la perte du support des plugins.  Avec
sr_watch (et sr_cpost) La méthode par défaut de la remarque les changements dans les répertoires
utilisent des mécanismes spécifiques au système d'exploitation (sous Linux : INOTIFY)
pour reconnaître les modifications sans avoir à analyser manuellement l'arborescence complète des répertoires.
Une fois amorcés, les changements de fichiers sont remarqués instantanément, mais nécessitent
une première marche à travers l'arbre, *une passe d'amorçage*.

Par exemple, **supposons qu'un serveur peut examiner 1500 fichiers/seconde**. Si un arbre de taille
moyenne est de 30 000 fichiers, alors il faudra 20 secondes pour une passe d'amorçage**. En utilisant
la méthode la plus rapide disponible, on doit supposer qu'au démarrage d'une telle arborescence de répertoires,
il faudra environ 20 secondes avant qu'elle ne démarre de façon fiable. L'affichage de tous les fichiers
dans l'arborescence. Après cette analyse initiale, les fichiers sont remarqués avec une latence inférieure à la seconde.
Donc un **sommeil de 0.1 (vérifiez les changements de fichiers toutes les dixièmes de seconde)
est raisonnable, à condition que nous acceptions l'amorçage initial.** Si l'on choisit
l'option **force_polling**, alors ce délai de 20 secondes est encouru pour chaque passe de balayage,
plus le temps nécessaire pour effectuer l'affichage lui-même. Pour le même arbre, un réglage *sleep* de
30 secondes serait le minimum à recommander. Attendez-vous à ce que les fichiers seront remarqués
environ 1,5*, les paramètres *sleep* en moyenne. Dans cet exemple, environ 45 secondes. Certains seront
ramassés plus tôt, d'autres plus tard.  A part les cas spéciaux où la méthode par défaut manque de
fichiers, *force_polling* est beaucoup plus lente sur des arbres de taille moyenne que la méthode par
défaut et ne devrait pas être utilisé si la rapidité d'exécution est une préoccupation.

Dans les clusters de supercalculateurs, des systèmes de fichiers distribués sont utilisés, et les
méthodes optimisées pour le système d'exploitation les modifications de fichiers (INOTIFY sous Linux)
ne franchissent pas les limites des nœuds. Pour utiliser sr3_watch avec la stratégie par défaut
sur un répertoire dans un cluster de calcul, on doit généralement avoir un processus sr_watch
sr_watch s'exécutant sur chaque noeud. Si cela n'est pas souhaitable, alors on peut le déployer sur
un seul nœud avec *force_polling* mais le timing sera le suivant être limité par la taille du répertoire.


Au fur et à mesure que l'arbre surveillé prend de l'ampleur, la latence au démarrage de sr_watch´s
augmente, et si le sondage ( *force_polling* ) est utilisé, la latence à la modification des fichiers d'avis augmentera
également. Par exemple, avec un arbre avec 1 million de fichiers, il faut s'attendre, au mieux, à
une latence de démarrage de 11 minutes. S'il s'agit d'un sondage, alors une attente raisonnable
du temps qu'il faut pour remarquer les nouveaux fichiers serait de l'ordre de 16 minutes.


Si la performance ci-dessus n'est pas suffisante, alors il faut considérer l'utilisation de la
librairie de cales ( *shim* library ) à la place de sr_watch. Tout d'abord, il faut installer la version C de Sarracenia,
et en suite rajouter à l'environnement pour tous les processus qui vont écrire des fichiers à publier
pour l'appeler::

  export SR_POST_CONFIG=shimpost.conf
  export LD_PRELOAD="libsrshim.so.1"

où *shimpost.conf* est un fichier de configuration sr_cpost dans le répertoire ~/.config/sarra/post/.
Un sr_cpost est le même que celui de sr_post, sauf que les plugins ne sont pas supportés.  Avec la
librairie en place, chaque fois qu'un fichier est écrit, les clauses *accept/reject* du fichier
shimpost.conf sont les suivantes consulté, et s'il est accepté, le fichier est publié tel qu'il le serait par sr_watch.

Jusqu'à présent, la discussion a porté sur le temps nécessaire pour remarquer qu'un fichier
a changé. Un autre facteur à prendre en considération est le temps d'afficher les fichiers une
fois qu'ils ont été remarqués. Il y a des compromis basés sur l'algorithme de checksum choisi.
Le choix le plus robuste est le choix par défaut : *s* ou SHA-512. Lorsque vous utilisez la
méthode de la somme *s*, l'ensemble du fichier sera lue afin de calculer sa somme de contrôle,
ce qui est susceptible de déterminer le temps jusqu'à l'affichage. la somme de contrôle sera
utilisé par les consommateurs en aval pour déterminer si le fichier annoncé est nouveau ou s'il
s'agit d'un fichier qui a déjà été vu, et c'est vraiment pratique.

Pour les fichiers plus petits, le temps de calcul de la somme de contrôle est négligeable, mais
il est généralement vrai que les fichiers plus volumineux Lorsque **en utilisant la méthode shim library**,
le processus qui a écrit le fichier est le même que celui qui a écrit le fichier. **En calculant la somme de contrôle**,
la probabilité que les données du fichier se trouvent dans un cache
accessible localement est assez élevée, de sorte qu'il est aussi peu coûteux que possible**.
Il convient également de noter que la commande sr_watch/sr_cpost Les processus de surveillance
des répertoires sont à thread unique, alors que lorsque les jobs utilisateur appellent sr_post,
ou utilisent le shim.  il peut y avoir autant de processus d'affichage de fichiers qu'il y a
de rédacteurs de fichiers.

Pour raccourcir les temps d'enregistrement, on peut sélectionner des algorithmes *sum* qui ne
lisent pas la totalité de l'enregistrement comme *N* (SHA-512 du nom du fichier seulement), mais
on perd alors la capacité de différenciation entre les versions du fichier.

note ::
  devrait penser à utiliser N sur sr_watch, et à faire recalculer les sommes de contrôle par des pelles multi-instance.
  pour que cette pièce devienne facilement parallélisable. Devrait être simple, mais pas encore exploré.
  à la suite de l'utilisation de la bibliothèque de cales. FIXME.

Une dernière considération est que dans de nombreux cas, d'autres processus sont en train
d'écrire des fichiers dans des répertoires surveillés par sr_watch. Le fait de ne pas établir
correctement les protocoles de complétion de fichiers est une source commune de
problèmes intermittents et difficiles à diagnostiquer en matière de transfert de fichiers.
Pour des transferts de fichiers fiables, Il est essentiel que les processus qui écrivent
des fichiers et sr3_watch s'entendent sur la façon de représenter un fichier qui n'est pas complet.





SHIM LIBRARY USAGE
------------------

Rather than invoking a sr3_post to post each file to publish, one can have processes automatically
post the files they right by having them use a shim library intercepting certain file i/o calls to libc
and the kernel. To activate the shim library, in the shell environment add::

  export SR_POST_CONFIG=shimpost.conf
  export LD_PRELOAD="libsrshim.so.1"

where *shimpost.conf* is an sr_cpost configuration file in
the ~/.config/sarra/post/ directory. An sr_cpost configuration file is the same
as an sr3_post one, except that plugins are not supported.  With the shim
library in place, whenever a file is written, the *accept/reject* clauses of
the shimpost.conf file are consulted, and if accepted, the file is posted just
as it would be by sr3_post. If using with ssh, where one wants files which are
scp'd to be posted, one needs to include the activation in the .bashrc and pass
it the configuration to use::

  expoert LC_SRSHIM=shimpost.conf

Then in the ~/.bashrc on the server running the remote command::

  if [ "$LC_SRSHIM" ]; then
      export SR_POST_CONFIG=$LC_SRSHIM
      export LD_PRELOAD="libsrshim.so.1"
  fi

SSH will only pass environment variables that start with LC\_ (locale) so to get it
passed with minimal effort, we use that prefix.


Shim Usage Notes
~~~~~~~~~~~~~~~~

Cette méthode de notification nécessite une certaine configuration de l’environnement de l'utilisateur.
L’environnement de l'utilisateur doit être défini sur les variables d’environnement LD_PRELOAD
avant le lancement du processus. Il restent encore des complications qui restent qui ont été
testé pendant les deux dernières années depuis que la library shim a été implémenté :

* si nous voulons remarquer les fichiers créés par des processus scp distants (qui créent des shells sans connexion),
  alors le hook d’environnement doit être dans .bashrc. et il faut utiliser une variable d'environnement
  qui commence par *LC_* pour que ssh transmette la valeur de la configuration sans
  avoir à modifier la configuration sshd dans les distributions Linux typiques.
  ( discussion complète: https://github.com/MetPX/sarrac/issues/66 )

* un code qui présente certaines faiblesses, comme dans FORTRAN un manque de NONE IMPLICITE
  https://github.com/MetPX/sarracenia/issues/69 peut se bloquer lorsque la bibliothèque shim
  est introduite. La correction nécessaire dans ces cas, jusqu’à présent, consiste à corriger
  l’application, et non la librarie.
  ( aussi: https://github.com/MetPX/sarrac/issues/12 )

* les codes qui utilisent l’appel *exec* à `tcl/tk <www.tcl.tk>`_, considère par défaut que toute
  sortie vers le descripteur de fichier 2 (type d'erreur) est une condition d’erreur.
  Ces messages peuvent être étiquetés comme INFO, ou priorité d'AVERTISSEMENT, mais ca va causer
  l'appelant tcl à indiquer qu’une erreur irrécupérable s’est produite.  Additionnant
  *-ignorestderr* aux invocations de *exec* évite de tels avortements injustifiés.

* Les scripts shell complexes peuvent avoir un impact démesuré sur les performances.
  Puisque les *scripts shell de haute performance* est un oxymore, la meilleure solution
  en termes de performance, est de réécrire les scripts avec un langage de scripting plus efficace
  tel que python ( https://github.com/MetPX/sarrac/issues/15 )

* Des bases de code qui déplacent des hiérarchies de fichiers volumineux (par exemple, *mv tree_with_thousands_of_files new_tree* )
  aura un coût beaucoup plus élevé pour cette opération, car elle est mise en œuvre en tant qu'un
  changement de nom de chaque fichier de l’arborescence, plutôt qu’une seule opération sur la racine.
  Ceci est actuellement considéré comme nécessaire car la correspondance de modèle d’acceptation/rejet
  peut entraîner un arbre très différent sur la destination, plutôt que simplement le
  même arbre en miroir. Voir ci-dessous pour plus de détails.

* *export SR_SHIMDEBUG=1* obtiendra plus de sortie que vous ne le souhaitez. utiliser avec précaution.

Processus de Renommage
~~~~~~~~~~~~~~~~~~~~~~

C'est à noter que le changement de nom de fichier n’est pas aussi simple dans le cas de mise en miroir que dans le cas sous-jacent
du système d’exploitation. Alors que l’opération est une seule opération atomique dans un système d’exploitation,
avec l’aide de notifications, il existe des cas d’acceptation/rejet qui créent quatre effets possibles.

+---------------+---------------------------+
|               |    L'ancien nom est:      |
+---------------+--------------+------------+
|Nouveau nom est|  *Accepted*  | *Rejected* |
+---------------+--------------+------------+
|  *Accepted*   |   renomme    |   copie    |
+---------------+--------------+------------+
|  *Rejected*   |   supprime   |   rien     |
+---------------+--------------+------------+

Lorsqu’un fichier est déplacé, deux notifications sont créées :

*  Une notification a le nouveau nom dans le *relpath*, tout en gardant un champ *oldname*
   qui pointe vers l’ancien nom.  Cela déclenchera des activités dans la première moitié de
   la table, soit un renommage, à l’aide du champ oldname, soit une copie si elle n’est pas présente à
   la destination.

*  Une deuxième notification avec l’ancien nom dans *relpath* qui sera acceptée
   encore une fois, mais cette fois, il y a le champ *newname* et traite l’action de suppression.

Alors que le renommage d’un répertoire à la racine d’un grand arbre est une opération atomique et peu cher
dans Linux/Unix, la mise en miroir de cette opération nécessite la création d’une publication de renommage pour chaque fichier
dans l’arbre, et est donc beaucoup plus cher.



