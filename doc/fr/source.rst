
===================================
 Guide pour les sources de données
===================================

---------------------------------------------------------------
Injection de données dans un réseau de pompage MetPX-Sarracenia 
---------------------------------------------------------------

.. warning::
  **FIXME** : Les sections manquantes sont mises en évidence par **FIXME**. Ce qui est ici devrait être exact !

.. contents::

... note::
  CORRECTIF** : éléments manquants connus : bonne discussion sur le choix de
  la somme de contrôle. Mises en garde concernant les stratégies de mise à
  jour des fichiers. Cas d'utilisation d'un fichier qui est constamment mis 
  à jour, plutôt que d'émettre de nouveaux fichiers.

Fiche de révision
-----------------

:version: @Version@
:date: @Date@


Une pompe de données Sarracenia est un serveur web (ou sftp) avec en plus des 
avis pour les abonnés, pour qu'ils puissent savoir rapidement quand de nouvelles
données sont arrivées. Pour savoir quelles données sont déjà disponibles sur 
une pompe, visualiser l'arbre avec un navigateur Web. Pour des besoins immédiats
simples, on peut télécharger les données en utilisant le navigateur lui-même, ou 
un outil standard tel que wget. L'intention habituelle est que sr_subscribe
télécharge automatiquement les données, les placant dans un répertoire sur une
machine d'abonné ou d'autres logiciels peut le traiter. Notez que ce manuel
utilise les abonnements pour tester l'injection de données, de sorte que le
guide de l'abonné devrait probablement être lu avant celle-ci.

Quelle que soit la façon de procéder, injecter des données signifie dire à 
la pompe où se trouvent les données à propager.  Pour ce faire, il faut soit
en utilisant la commande sr_post active et explicite, ou simplement en 
utilisant sr_watch sur un répertoire. Lorsqu'il y a un grand nombre de 
dossiers, et/ou des contraintes d'actualité serrées, l'invocation de 
sr_post directement par le producteur du fichier est optimal, car
sr_watch peut fournir une performance décevante. Une autre approche
explicite, mais à basse fréquence, est l'approche sr_poll, qui permet 
d'interroger des systèmes distants pour extraire des données.

Alors que sr_watch est écrit comme un système de surveillance de répertoires 
optimal, il n'y a tout simplement pas de moyen suffisament rapide de 
surveiller les grands (disons, plus de 100 000 fichiers) arborescences de
répertoires.  Dans dd.weather.gc.ca, par exemple, il y a 60 millions de 
fichiers dans environ un million de répertoires. Il faut plusieurs heures
pour parcourir l'arborescence des répertoires. Pour trouver de nouveaux
fichiers, la meilleure résolution temporelle est toutes les quelques
heures (disons 3 heures). Donc, en moyenne, la notification se produira
1,5 heures après l'arrivée du fichier. En utilisant I_NOTIFY (sous Linux),
il s'agit toujours de prend plusieurs heures pour démarrer, parce qu'il a 
besoin de faire une première passe à travers l'arborescence des fichiers.
Après ça, ce sera instantané, mais s'il y en a trop. (et 60 millions, c'est 
très probablement trop), il s'écrasera et refusera de fonctionner.  Ce 
sont des limites inhérentes au visionnement des annuaires, peu importe
la façon dont on le fait. S'il est vraiment nécessaire de le faire, il 
y a de l'espoir.  S'il vous plaît
consulter `Annonce rapide de très grands arbres sur Linux`_.

Avec sr_post, le programme qui place le fichier n'importe où dans 
l'arborescence arbitrairement profonde[1]_ publie à la pompe (qui 
indiquera aux abonnés) exactement où regarder. Il n'y a pas de limites au 
système de s'inquiéter. C'est ainsi que fonctionne dd.weather.gc.ca, et les
notifications sont inférieures à la seconde.  60 millions de fichiers sur
le disque. Il est beaucoup plus efficace, en général, que d'effectuer des
sondages directs. Par contre, dans de petits arborescences de fichiers 
et des cas simples, cela fait peu de différence sur le plan pratique.

Dans le cas le plus simple, la pompe prend les données de votre compte, où
ils sont placés, à condition que vous lui donniez la permission. Nous 
décrivons d'abord cette affaire.

.. [1] Alors que l'arbre de fichiers lui-même n'a pas de limites en 
   profondeur ou en nombre, la capacité à basé sur *sujets* est limité 
   par AMQP à 255 caractères. Donc, le *subtopic* est un sous-thème et 
   est limité à un peu moins que cela. Il n'y a pas d'un seul limit parce 
   que les sujets sont encodés en utf8, ce qui est de longueur variable. 
   Notez que le *subtopic* directive a pour but de fournir une classification 
   grossière, et l'utilisation de *accept/reject* est destinée à un travail 
   plus détaillé. Clauses accept/reject ne se fient pas aux en-têtes AMQP, 
   en utilisant les noms de chemins stockés dans le corps de l´avis
   et ne sont donc pas affectés par cette limite.



Injection avec SFTP
-------------------

L'utilisation directe de la commande sr_post(1) est la façon la plus simple 
d'injecter des données dans le réseau de pompes. Pour utiliser sr_post, vous
devez savoir :

- le nom du courtier local : ( disons : ddsr.cmc.ec.ec.gc.ca. ).
- vos informations d'authentification pour ce courtier ( disons : user=rnd : password=rndpw)
- votre propre nom de serveur. (disons : grumpy.cmc.ec.ec.gc.ca).
- votre propre nom d'utilisateur sur votre serveur (disons : peter)

Supposons que l'objectif est que la pompe accède au compte de Peter via SFTP. 
Alors vous avez besoin pour prendre la clé publique de l´usager de la pompe, et 
la placer dans les .ssh/authorized_keys de peter sur le serveur que vous 
utilisez (*grumpy*), il faut faire quelque chose comme ceci::

  cat pump.pub >>~peter/.ssh/authorized_keys

Cela permettra à la pompe d'accéder au compte de Peter sur grumpy à l'aide 
de sa clé privée. Donc en supposant qu'on est connecté au compte de Peter sur
grumpy, on peut stocker les information pour se connecter au courtier comme
ceci::

  echo'amqps://rnd:rndpw@ddsr.cmc.ec.gc.ca' >> ~/.config/sarra/credentials.conf :


.. Note::
  Les mots de passe sont toujours stockés dans le fichier credentials.conf.

Il ne nous reste plus qu'à trouver où envoyer le fichier.  Sr_post fait la 
supposition par défaut que la seule destination est le courtier vers lequel le
message est envoyé. On peut remplacer cela pour que les données soient 
transmises à plusieurs pompes de données. On peut outrepasser cela pour que les
données soient transmises à plusieurs pompes de données avec l'option *to*.

Donc maintenant la ligne de commande pour sr_post est juste l'url à pour que 
ddsr récupère le fichier fichier sur le serveur grumpy::

  sr_post -broker amqp://guest:guest@localhost/ -post_base_dir /var/www/posts/ \
  -post_url  http://grumpy:81/frog.dna

  2016-01-20 14:53:49,014 [INFO] Output AMQP  broker(localhost) user(guest) vhost(/)
  2016-01-20 14:53:49,019 [INFO] message published :
  2016-01-20 14:53:49,019 [INFO] exchange xs_guest topic v02.post.frog.dna
  2016-01-20 14:53:49,019 [INFO] notice   20160120145349.19 http://localhost:81/ frog.dna
  2016-01-20 14:53:49,020 [INFO] headers  parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c to_clusters=test_cluster

Il y a un sr_subscribe pour s'abonner à tous les messages ``*.dna``. Voici le 
fichier de configuration::

  broker amqp://guest:guest@localhost
  directory /var/www/subscribed
  subtopic #
  accept .*dna*

et voici la sortie correspondante du fichier journal d'abonnement::

  2016-01-20 14:53:49,376 [INFO] Received v02.post.frog.dna '20160120145349.19 http://grumpy:81/ frog.dna' parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c to_clusters=test_cluster
  2016-01-20 14:53:49,377 [INFO] downloading/copying into /var/www/test/20160120/guest/frog.dna
  2016-01-20 14:53:49,377 [INFO] Downloads: http://grumpy:81/frog.dna  into /var/www/test/20160120/guest/frog.dna 0-16
  2016-01-20 14:53:49,380 [INFO] 201 Downloaded : v02.report.frog.dna 20160120145349.19 http://grumpy:81/ frog.dna 201 sarra-server-trusty guest 0.360282 parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c from_cluster=test_cluster source=guest to_clusters=test_cluster message=Downloaded
  2016-01-20 14:53:49,381 [INFO] message published :
  2016-01-20 14:53:49,381 [INFO] exchange xpublic topic v02.post.20160120.guest.frog.dna
  2016-01-20 14:53:49,381 [INFO] notice   20160120145349.19 http://grumpy:80/ 20160120/guest/frog.dna

Ou bien, voici le log d'une instance sr_sarra::

  2016-01-20 14:53:49,376 [INFO] Received v02.post.frog.dna '20160120145349.19 http://grumpy:81/ frog.dna' parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c to_clusters=test_cluster
  2016-01-20 14:53:49,377 [INFO] downloading/copying into /var/www/test/20160120/guest/frog.dna
  2016-01-20 14:53:49,377 [INFO] Downloads: http://grumpy:81/frog.dna  into /var/www/test/20160120/guest/frog.dna 0-16
  2016-01-20 14:53:49,380 [INFO] 201 Downloaded : v02.report.frog.dna 20160120145349.19 http://grumpy:81/ frog.dna 201 sarra-server-trusty guest 0.360282 parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c from_cluster=test_cluster source=guest to_clusters=test_cluster message=Downloaded
  2016-01-20 14:53:49,381 [INFO] message published :
  2016-01-20 14:53:49,381 [INFO] exchange xpublic topic v02.post.20160120.guest.frog.dna
  2016-01-20 14:53:49,381 [INFO] notice   20160120145349.19 http://grumpy:80/ 20160120/guest/frog.dna

la commande demande à ddsr de récupérer le fichier treefrog/frog.dna en enregistrant les données.
dans grumpy comme peter (en utilisant la clé privée de la pompe.) pour le récupérer et l'afficher.
sur la pompe, pour le transfert vers les autres destinations de la pompe.

Comme sr_subscribe, on peut aussi placer les fichiers de configuration dans un répertoire sr_post spécifique::

  blacklab% sr_post edit dissem.conf

  broker amqps://rnd@ddsr.cmc.ec.gc.ca/
  to DDIEDM,DDIDOR,ARCHPC
  url sftp://peter@grumpy

et puis::

  sr_post -c dissem -url treefrog/frog.dna















