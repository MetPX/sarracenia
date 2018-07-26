
==========
Sarracenia
==========

[ `English version <../sarra.rst>`_ ]

.. contents::


**MetPX-Sarracenia** est un moteur de duplication ou de distribution de données qui exploite les technologies standards
(serveurs de fichiers, serveurs Web et courtiers AMQP_) pour obtenir des messages en temps réel, et la transparence 
de transferts de fichiers à travers une chaines de serveurs. Alors que dans Sundew, chaque pompe
est une configuration autonome qui transforme les données de manière complexe, dans Sarracenia, l'application
à la sources de données établissent une hiérarchie dans l'arborescence des fichiers qui 
se propage à travers n'importe quel nombre de maillons dans la chaîne jusqu'à ce qu'ils arrivent chez un client.
Le client peut fournir une reconnaissance explicite du fait que se propage à travers le réseau jusqu'à la 
source. Alors que le transfert de fichier traditionnel est une affaire de point à point où la connaissance 
est seulement entre chaque segment, dans Sarracenia, l'information circule d'un bout à l'autre dans les deux sens.

Aperçu
------


Sarracenia expose une arborescence de dossiers accessibles sur le Web (WAF), en utilisant n'importe quel
serveur HTTP standard (testé avec apache) ou serveur SFTP, avec d'autres types de serveurs tels que
une option enfichable. Les applications météorologiques sont douces et en temps réel, où les données 
doivent être transmises le plus rapidement possible jusqu'au prochain saut, et les minutes, peut-être 
les secondes, comptent. Les technologies web push standard, ATOM, RSS, etc.... sont en fait des 
technologies de sondage qui, lorsqu'elles sont utilisées dans des applications à faible latence, 
consomment beaucoup de bande passante et surcharge les serveurs et réseaux inutilement.  Pour ces raisons 
précises, ces normes stipulent un intervalle minimal de sondage de cinq minutes. La messagerie AMQP (Advanced 
Message Queueing Protocol) apporte une véritable *push*  aux notifications et rend l'envoi en 
temps réel beaucoup plus efficace.


.. image:: f-ddsr-components.gif

Les sources de données publient leurs produits, les pompes tirent les données en utilisant HTTP
ou SFTP sur leurs arbres WAF, puis annoncent à leur tour, leurs arbres pour les clients en aval.
Lorsque les clients téléchargent des données, ils peuvent écrire un message de rapport sur le 
serveur. Les serveurs sont configurés pour renvoyer ces messages de rapport du
client par l'intermédiaire de la fonction à la source. La Source peut voir le 
chemin entier que les données ont pris pour atteindre chaque client. Dans le
cas des applications de commutation traditionnelles, les sources ne voient que
qu'ils ont livré au premier maillon d'une chaîne. Au-delà de ce premier maillon, le 
routage est opaque, et le traçage du cheminement des données nécessitaient l'aide des 
administrateurs de chacque système entre eux. Avec le report forwarding de Sarracenia, 
le réseau de commutation est le suivant relativement transparent pour les sources. 
Le diagnostic est grandement simplifié.

Pour les gros fichiers / haute performance, les fichiers sont segmentés à l'
ingestion s'ils sont suffisamment performants pour que cela en vaille la peine.
Chaque fichier peut traverser le réseau de pompage de données indépendamment,
et le remise en entier n'est nécessaire qu'a la fin du voyage. Un fichier de taille suffisante annoncera
la disponibilité de plusieurs segments pour le transfert, des fils multiples ou des nœuds de transfert
prendra des segments et les transférera. Plus il y a de segments disponibles, le plus de parallélisme du 
transfert est possible. Dans de nombreux cas, Sarracenia gère le parallélisme et l'utilisation du 
réseau sans intervention explicite de l'utilisateur. En tant que pompes d'intervention ne pas 
stocker et transférer des fichiers entiers, la taille maximale de fichier qui peut traverser
le réseau est maximisé.

Sundew prend en charge une grande variété de formats de fichiers, de 
protocoles et de conventions.  spécifique à la météorologie en temps réel. 
Sarracenia s´enligne plus loin d´applications spécifiques et est plus un 
moteur de réplication d'arbre impitoyablement générique, qui
devrait permettre son utilisation dans d'autres domaines. Le client prototype 
initial, dd_subscribe, en service depuis 2013, a été remplacé en 2016 par 
l'ensemble Sarracenia entièrement soufflé, avec tous les composants nécessaires
à la production ainsi qu'à la consommation d'arbres de fichiers.

On s'attend à ce que la Sarracenia soit une application beaucoup plus simple 
de n´importe lequel point de vue : Opérateur, Développeur, Analyste,
Sources de données, Consommateurs de données. Sarracenia impose un mécanisme
d'interface unique, mais ce mécanisme est complètement portable et générique.
Il devrait fonctionner sans problème sur tout ce qui est moderne plate-forme (Linux, Windows, Mac)

Pour plus d'informations sur Sarra, consultez le site vidéo (en anglais seulement)
`Sarracenia in 10 Minutes <https://www.youtube.com/watch ?v=G47DRwzwckk>`_`
ou passer à la documentation détaillée `documentation <sr_subscribe.1.rst#documentation>`_


Implémentations
---------------

Une partie de Sarracénie définit un message de couche d'application sur AMQP comme un transport.
La Sarracenia a des implémentations multiples :

- Sarracenia elle-même (http://github.com/MetPX/sarracenia) une implémentation de référence complète en Python >= 3.4. Il fonctionne sous Linux, Mac et Windows.

- sarrac ( https://github.com/MetPX/sarrac) est une implémentation en C de l'insertion de données (post & watch.) C'est Linux uniquement. Il y a aussi une libcshim pour pouvoir implémenter de manière transparente l'insertion de données avec cet outil, et libsarra permet aux programmes C de poster directement. Il y a aussi du code consommateur (sr_cpump, pour lire les files d'attente) mais pas de téléchargement jusqu'à présent. Ce sous-ensemble est destiné à être utilisé là où les environnements python3 ne sont pas pratiques (certains environnements HPC).

- node-sarra ( https://github.com/darkskyapp/node-sarra) Une implémentation embryonnaire pour node.js.

- ecpush ( https://github.com/TheTannerRyan/ecpush ) an simple client in Go ( http://golang.org )

- PySarra ( https://github.com/JohnTheNerd/PySarra ) un client archi-simple en python3.

- dd_subscribe ( https://github.com/MetPX/sarracenia) client en python2 (Le prédécesseur de Sarracénia.) Toujours compatible.

D'autres clients sont les bienvenues.

Télécharger Sarracenia
----------------------

Les étapes pour télécharger la dernière version de Sarracenia sont disponibles sur notre page `téléchargement/Installation <Install.rst>`_.

Obtenir le code source
----------------------

Le code source est disponible dans notre `git repository <https://github.com/MetPX/sarracenia>`_`_ ....

Documentation
-------------

La documentation pour Sarracenia est ici: `documentation <sr_subscribe.1.rst#documentation>`_...

Usage/Déploiments
-----------------

Statut en 2015 (en anglais): `Sarracenia in 10 Minutes Video (5:26 in) <https://www.youtube.com/watch?v=G47DRwzwckk&t=326s>`_

en 2018 historique de déploiements: `Deployments as of January 2018 <deployment_2018.rst>`_

Mailing Lists
-------------

* `metpx-devel <http://lists.sourceforge.net/lists/listinfo/metpx-devel>`_  
* `metpx-commit <http://lists.sourceforge.net/lists/listinfo/metpx-commit>`_ 

Pourquoi?
---------

Pourquoi ne pas simplement utiliser Rsync ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il existe un certain nombre d'outils de réplication d'arbres qui sont largement
utilisés, pourquoi en inventer un autre ? `RSync <https://rsync.samba.org/>`_, 
par exemple, est un outil fabuleux, et nous avons Il est fortement recommandé 
pour de nombreux cas d'utilisation. mais il y a des moments où la Sarracenia peut
72 fois plus rapide que rsync : Étude de cas : `HPC Mirroring Use Case (anglais) <../mirroring_use_use_case.rst>`_

Rsync et d'autres outils sont basés sur la comparaison (traitant d'une source et d'une destination 
unique) Sarracénie, bien qu´elle n'utilisent pas la multidiffusion, est orienté vers une livraison 
à plusieurs récepteurs, en particulier lorsque la source ne sait pas qui sont tous les 
récepteurs (pub/sub.) La synchronisation rsync est typiquement faite en marchant un à un.
C'est-à-dire que l'intervalle de synchronisation est intrinsèquement limité à la fréquence 
à laquelle on peut traverser (sonder?) l'arbre de fichiers (dans les grands arbres, cela peut être long).
La Sarracenia évite les promenades dans les arbres de fichiers en demandant
aux sources de données de calculer les sommes de contrôle une fois pour toutes,
et de les signaler directement aux lecteurs par des messages, réduisant ainsi 
les frais généraux de plusieurs ordres de grandeur.  Lsyncd <https://github.com/axkibe/lsyncd>`_ 
est un outil qui exploite les fonctionnalités INOTIFY de Linux. pour atteindre le même genre
de rapidité de détection the changement, et il pourrait être plus approprié, mais il n'est 
évidemment pas portable.  Faire faire cela par le système de fichiers est considéré comme 
lourd et moins général qu'explicite passage de messages via middleware, qui gère également
les logs de manière simple.

Un des objectifs de Sarracenia est d'être de bout en bout. Rsync est point-à-point,
ce qui signifie qu'il ne prend pas en charge la *transitivité* des transferts
de données entre plusieurs pompes de données qui est désiré. D'autre part, le
premier cas d'utilisation de la Sarracenia est la distribution du nouveaux 
fichiers. Au départ, les mises à jour des dossiers n'étaient pas courantes. 
`ZSync <http://zsync.moria.org.uk/>`_ est beaucoup plus proche dans l'esprit 
de ce cas d'utilisation. Sarracenia divise les fichiers en block de facon similaire,
bien que généralement beaucoup plus grand (50M est un bon choix), que les blocs 
Zsync (typiquement 4k), plus propice à l'accélération. Utilisation d'une 
annonce par bloc de somme de contrôle permet d'accélérer les transferts plus
facilement.

L'utilisation du bus de messages AMQP permet l'utilisation de transferts de
tiers partis, flexibles, une surveillance simple à l'échelle du système et 
l'intégration d'autres caractéristiques telles que la sécurité à l'intérieur
du flux.

Une autre considération est que Sarracenia n´implante aucun transport. Il est
agnostique au protocole utilisé pour le transfert des données. Il peut 
annoncer des URLs de protocole arbitraire, et on peut rajouter des plugins
pour fonctionner avec des nouveaux protocoles, ou substituer des téléchargeurs 
accélérés pour traiter les transferts avec des protocoles déjà connus.
Le `download_scp <download_scp.py>`_ plugin, inclus avec le paquet, affiche
l'utilisation des mécanismes de transfert de python intégrés, mais l'
utilisation simple d'un binaire pour accélérer les téléchargements lorsque
le fichier dépasse une taille de seuil, en rendant cette méthode plus 
efficace. Utilisation d'un autre binaire compatible, tel que 
`dd <download_dd.py>`_ ou`_. `cp <accel_cp.py>`_, (pour les fichiers 
locaux), `scp <download_scp.py>`_, ou `wget <accel_wget.py>`_ via est
également simple.

 
Pas de FTP ?
~~~~~~~~~~~~

Les protocoles de transport entièrement pris en charge par Sarracenia sont 
http(s) et SFTP (SSH File Transfer Protocol).  Dans de nombreux cas, lorsque 
des données publiques sont échangées, `FTP <https://tools.ietf.org/html/rfc959>`_ 
est une lingua franca qui est utilisée. L'avantage principal étant la simplicité relative,
l'accès aux programmes, ce qui est très simple avec Sarracenia.
De nos jours, avec l'augmentation des préoccupations en matière de sécurité, et
l´arrivée d´instructions de cryptage danse les processeurs centrales
et les noyaux multiples quelque on a, en quelque sort,  une surabondance de processeurs,
et il n'est plus très logique de ne pas crypter le trafic. De plus, pour
Sarracenia utilise des plages d'octets, qui sont les suivantes
fournis par les serveurs SFTP et HTTP, mais pas FTP. Nous ne pouvons donc pas 
soutenir le fichier partitionnement sur FTP. Ainsi, bien que le FTP fonctionne
en quelque sorte, ce n'est pas maintenant, ni ne le fera jamais.
être, pleinement soutenu.



AMQP
~~~~

AMQP est le protocole avancé de mise en file d'attente des messages (Advanced Message
Queueing Protocol), qui a émergé de l'industrie du commerce financier et qui a peu à peu
a mûri. Les premières implémentations sont apparues en 2007, et il y a maintenant
plusieurs versions open source. Mise en œuvre du programme AMQP ne sont pas de
la plomberie JMS. JMS standardise l'utilisation de l'API par les programmeurs,
mais pas le protocole d´echanges bruts. Donc typiquement, on ne peut pas échanger
des messages entre les personnes utilisant différents fournisseurs de JMS. L'AMQP
normalise pour l'interopérabilité, et fonctionne efficacement comme une cale 
d'interopérabilité pour JMS, sans pour autant être limité à Java. L'AMQP est 
neutre sur le plan linguistique et neutre sur le plan des messages. Python, C+++, 
et ruby. On pourrait très facilement adapter les protocoles OMM-GTS pour 
fonctionner sur AMQP. En contraste, les JMS sont très orientés Java.

* `www.amqp.org <http://www.amqp.org>`_ -  Définition d´AMQP
* `www.openamq.org <http://www.openamq.org>`_ - l´implantation originale courtier de JP Morgan.
* `www.rabbitmq.com <http://www.rabbitmq.com>`_ - une autre courtire logiciel libre.
* `Apache Qpid <http://cwiki.apache.org/qpid>`_ - et une troisième.
* `Apache ActiveMQ <http://activemq.apache.org/>`_ - Ceci est plus un pont JMS, mais prétend être un courtier AMQP aussi.

Sarracenia s'appuie fortement sur l'utilisation de courtiers et d'échanges thématiques, 
qui occupaient une place prépondérante dans les efforts de normalisation de l'AMQP avant
la version 1.0, date à laquelle ils ont été supprimés. On espère que ces concepts seront
réintroduits à un moment donné. Jusqu'à à ce moment-là, l'application s'appuiera sur des
courtiers de messages standard pré-1.0, comme rabbitmq.


Références et liens
~~~~~~~~~~~~~~~~~~~

D'autres logiciels, quelque peu similaires, aucun endossement ou jugement ne devrait être tiré de ces liens :

- Manual sur le système global de Telecommunications, de l´OMM : *WMO Manual 386*. le standard pour ce domaine. (Voilà une copie probablement désuète `here <WMO-386.pdf>`_.) Essayez: http://www.wmo.int  pour une version plus à jour.
- `Local Data Manager <http://www.unidata.ucar.edu/software/ldm>`_ LDM  protocol américaine populaire dans la dissémination météorologique.
- `Automatic File Distributor  <http://www.dwd.de/AFD>`_ -  Distribution de fichiers automatiquement... Venant de la service Allemend, 
- `Corobor <http://www.corobor.com>`_ - commutateur WMO commercial
- `Netsys  <http://www.netsys.co.za>`_ - commutateur WMO commercial
- `IBLSoft <http://www.iblsoft.com>`_ - commutateur WMO commercial
- Variété de moteurs de transferts: Standard Networks Move IT DMZ, Softlink B-HUB & FEST, Globalscape EFT Server, Axway XFB, Primeur Spazio, Tumbleweed Secure File Transfer, Messageway.
- `Quantum <https://www.websocket.org/quantum.rst>`_ à propos des sockets web HTML5. Une bonne discussion 
des raisons pour lesquelles le push web traditionnel est horrible, montrant comment les sockets web 
peuvent aider. AMQP est une solution de socket pure qui a les mêmes avantages que les 
webockets pour l'efficacité. Note : KAAZING a écrit la pièce, pas désintéressé.
- `Rsync  <https://rsync.samba.org/>`_ - moteur de transfert.
- `Lsyncd <https://github.com/axkibe/lsyncd>`_ ( Live syncing (Mirror) Daemon. ) moteur de transfert.
- `Zsync <http://zsync.moria.org.uk>`_ ( optimised rsync over HTTP. ) moteur de transfer.
                                                                      

