===============================
Histoire/Contexte de Sarracenia
===============================

**MetPX-Sarracenia** est un produit du projet d’échange de produits météorologiques,
provient d’Environnement Canada, mais est maintenant géré par Services partagés Canada sur son
nom. Le projet a débuté en 2004, dans le but de fournir une pile gratuite qui
met en œuvre l’échange de données en temps réel standard de l’Organisation météorologique mondiale,
et aussi les besoins adjacents. `Sundew <https://github.com/MetPX/Sundew>`_ était le
commutateur WMO 386 (GTS) de première génération.

En 2007, lorsque MetPX était à l’origine open source, le personnel responsable faisait partie
d'environnement Canada. En l’honneur de la Loi sur les espèces en péril (LEP), pour souligner le sort
d’espèces en voie de disparition qui ne sont pas poilues (les espèces à fourrure attirent toute l’attention) et
parce que les moteurs de recherche trouveront plus facilement des références à des noms plus inhabituels,
le commutateur WMO MetPX original a été nommé d’après une plante carnivore sur l’espèce à
registre des risques : Le *Thread-leaved Sundew*.

Sundew, le commutateur de WMO, devait également être compatible avec les mécanismes de transfert interne existant
fortement basés sur FTP. Cela a fonctionné, mais le GTS lui-même est obsolète dans de nombreux cas.
Les travaux ont commencé en 2009 pour étendre Sundew afin de tirer parti des nouvelles technologies,
tels que les protocoles de mise en file d’attente des messages, à partir de 2008. Les versions de Sundew sont
généralement étiqueté < 1,0.

Les prototypes initiaux de Sarracenia tiraient parti de MetPX Sundew, l’ancêtre de Sarracenia.
Les plugins Sundew ont été développés pour créer des messages de notification pour les fichiers livrés par Sundew,
et Dd_subscribe a été initialement développé en tant que client de téléchargement pour **dd.weather.gc.ca**, un
site Web d’Environnement Canada où une grande variété de produits météorologiques sont fabriqués
à la disposition du public. C’est du nom de ce site que Sarracenia prend le préfixe dd\_ pour ses outils.
La version initiale a été déployée en 2013 à titre expérimental en tant que dd_subscribe.


Renommage dd_subscribe
----------------------

Le nouveau projet (MetPX-Sarracenia) a de nombreux composants, est utilisé pour plus de distribution,
et plus d’un site Web, et cause de la confusion pour les administrateurs de système pensant qu’il est associé
à la commande dd(1) (pour convertir et copier des fichiers).  Ainsi, les composants ont été commutés pour utiliser
le préfixe sr\_. L’année suivante, le soutien des sommes de contrôle ont été ajoutées et, à l’automne 2015,
les flux ont été mis à jour vers la version v02.

Nous nous sommes finalement heurtés aux limites de cette approche d’extension et, en 2015, nous avons
commencé `Sarracenia <https://metpx.github.io/sarracenia>`_ en tant que remplacement de deuxième génération,
libéré de la stricte compatibilité GTS héritée. Sarracenia (version 2) était initialement un prototype,
et de nombreux changements de toutes sortes ont eu lieu au cours de sa vie.
C’est encore (en 2022) la seule version déployée opérationnellement. Ca a subi trois changements opérationnels
de format du message (exp, v00 et v02.) Il prend en charge des centaines de milliers de transferts de
fichiers par heure 24h / 24 et 7j / 7 au Canada.

Où Sundew prend en charge une grande variété de formats de fichiers, de protocoles et de conventions
spécifique à la météorologie en temps réel, Sarracenia s’éloigne un peu plus des
applications spécifiques et est un moteur de réplication d’arborescence impitoyablement générique, qui
devrait permettre son utilisation dans d’autres domaines. Le prototype du client initial, dd_subscribe,
en usage depuis 2013, était une sorte d’impasse logique. Une voie à suivre a été décrite
avec `Sarracenia in 10 Minutes <https://www.youtube.com/watch?v=G47DRwzwckk>`_
en novembre 2015, ce qui a conduit au remplacement de dd_subscribe en 2016 par le
package Sarracenia, avec tous les composants nécessaires à la production ainsi que
la consommation des arborescences de fichiers.

L’organisation derrière MetPX est passée à Services partagés Canada en 2011, mais lorsque
il est venu le temps de nommer un nouveau module, nous avons gardé le thème des plantes carnivores, et
en a choisi une autre indigène dans certaines régions du Canada : *Sarracenia*, une variété
de pichets insectivores. Nous aimons les plantes qui mangent de la viande!

Sarracenia s’appelait initialement v2, comme dans la deuxième architecture de pompage de données
dans le projet MetPX, (v1 étant Sundew.) un bon calendrier de déploiements / réalisations
est `ici <mesh_gts.html#Maturity>`_. Bien qu’il se soit avéré très prometteur,
et a très bien fonctionné, au fil des années, un certain nombre de limitations avec
la mise en œuvre est devenue claire :

* Le faible support pour les développeurs python. Le code v2 n’est pas du tout du Python idiomatique.
* La logique étrange de plugin, avec un mauvais rapport d’erreur.
* L’incapacité de traiter des groupes de messages.
* L’impossibilité d’ajouter d’autres protocoles de file d’attente (limités à rabbitmq/AMQP.)
* Difficulté d’ajouter des protocoles de transfert.

En 2020, le développement a commencé sur `Version 3 <../Contribution/v03.html>`_, maintenant
surnommé Sr3. Sr3 est environ 30% moins de code que v2, offre une API bien améliorée,
et prend en charge des protocoles de message supplémentaires, plutôt que simplement rabbitmq.

Moins de Klocs, de meilleurs Klocs
----------------------------------

+-------+----------------------------+------------+---------------------------------------------------+
|                Historique des applications de pompage de données pour Environnement Canada          |
+-------+----------------------------+------------+---------------------------------------------------+
| Era   | Application                | Code size  | Fonctionnalités                                   |
+-------+----------------------------+------------+---------------------------------------------------+
| 1980s | Tandem, PDS (domestic GTS) |  500kloc   | X.25, WMO Socket, AM Socket, FTP (push only)      |
+-------+----------------------------+------------+---------------------------------------------------+
| 2000s | Sundew                     |   30kloc   | WMO Socket/TCP, FTP, SFTP (push only)             |
+-------+----------------------------+------------+---------------------------------------------------+
| 2010s | Sarracenia v2              |   25kloc   | AMQP, HTTP, SFTP, FTP (pub/sub and push)          |
+-------+----------------------------+------------+---------------------------------------------------+
| 2020s | Sarracenia v3 (sr3)        |   15kloc   | AMQP, MQTT, HTTP, SFTP, API (pub/sub and push)    |
+-------+----------------------------+------------+---------------------------------------------------+


Déploiements/cas d’utilisation
------------------------------

État du déploiement en 2015: `Sarracenia in 10 Minutes Video (5:26 in) <https://www.youtube.com/watch?v=G47DRwzwckk&t=326s>`_

État du déploiement en 2018: `Deployments as of January 2018 <deployment_2018.html>`_


Site web du projet
------------------

Avant mars 2018, le site Web principal du projet était metpx.sf.net.
Ce site Web MetPX a été construit à partir de la documentation dans les différents modules
dans le projet. Il se construit en utilisant tous les fichiers **.rst** trouvés dans
**sarracenia/doc** ainsi que *certains* des fichiers **.rst** trouvés dans
**Sundew/doc**. Au printemps 2018, le développement s’est déplacé à github.com.
github.com rend .rst lors de l’affichage des pages, donc le traitement séparé pour le rendu
des pages Web ne sont plus nécessaires.

Entre 2018 et 2022, la mise à jour a été effectuée en validant les modifications apportées aux fichiers .rst
Directement sur GitHub, donc la page d’accueil est : https://github.com/MetPX/sarracenia)
Aucun post-traitement n’était requis. Comme les liens sont tous relatifs et
d’autres services tels que GitLab prennent également en charge un tel rendu, le
*site Web* est portable à n’importe quelle instance GitLab, etc ... Et le point d’entrée est à partir du
fichier README.rst dans le répertoire racine de chaque référentiel.

Cela avait des problèmes de lisibilité, avec des gens qui disaient "N’a-t-il pas un site Web?"
une mauvaise navigation, et pas d’indexation. En 2022/03, le sphinx a été adopté dans le cadre
de #380 (Document Restructure) et le processus de construction local est maintenant essentiellement
exécutez sur Sphinx. Le nouveau site web ( https://metpx.github.io/sarracenia ) est mis à jour
par un workflow GitHub à chaque commit.

Mise à jour du site Web sf.net
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Seules les pages index-e.html et index-f.html sont utilisées sur le site Web de sf.net
Aujourd’hui. À moins que vous ne souhaitiez modifier ces pages, cette opération est inutile.
Pour toutes les autres pages, les liens vont directement dans les différents fichiers .rst sur
github.com.