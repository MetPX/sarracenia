=======
Aperçu
=======

**MetPX-Sarracenia est une boîte à outils de gestion des publications/abonnements pour la publication de données en temps réel.**

Sarracenia ajoute une couche de protocole de mise en fil d’attente de messages d'annonce de disponibilité de fichiers
aux serveurs de fichiers et Web pour piloter des flux de travail qui transfèrent et transforment les données en continu
dans un contexte en temps réel et critique.

L’un des principaux objectifs de la boîte à outils est de relier les processus afin qu’ils évitent d’avoir
à interroger (interroger en continu, répertorier, puis filtrer) des serveurs ou des répertoires. Sarracenia
peut également être utilisé pour mettre en œuvre un sondage initial en amont, qui est toujours gagnant car
les tâches au-delà de l’identification initiale du fichier à traiter peuvent être pilotées par des notifications,
qui sont nettement moins chers (en i/o et en traitement) que l’interrogation même des répertoires locaux.


Cette couche de gestion fournit des méthodes simples pour obtenir le parallélisme dans les transferts de fichiers,
la robustesse face aux défaillances, l’équilibrage de charge entre les étapes d’un flux de travail, et
prend en charge de nombreux modes de défaillance, de sorte que les développeurs d’applications n’ont pas besoin de le faire.
Des centaines de ces flux peuvent être composés ensemble en grandes pompes de données et
exploité à l’aide de méthodes courantes familières aux administrateurs système Linux.

Vidéo de conception de 2015: `Sarracenia in 10 Minutes Video <https://www.youtube.com/watch?v=G47DRwzwckk>`_

Aperçu Détaillé
---------------

**MetPX-Sarracenia** est un fichier de configuration et un service piloté par ligne de commande pour
télécharger les fichiers au fur et à mesure qu’ils sont mis à disposition. On peut s’abonner à un
serveur Web Sarracenia activé (appelé pompe de données) et sélectionner les données à diffuser à partir de celui-ci,
en utilisant Linux, Mac ou Windows. Plus que cela:

* Cela évite aux gens d’avoir à interroger le serveur Web pour savoir si leurs données sont
  là (peut être 100x moins de travail pour le client et le serveur).

* c'est plus facile de télécharger en utilisant true pub / sub. Il reçoit des notifications
  exactement quand le fichier est prêt.

* C’est naturellement parallèle: quand un processus ne suffit pas, il suffit d’en ajouter d’autres. Ils
  partagera les mêmes sélections de manière transparente.

* On peut enchaîner plusieurs pompes de données ensemble, afin que les gens puissent maintenir des
  arborescences copiées indépendantes en temps réel pour la redondance des services et également pour le réseau pour des
  raisons de topologie (pour desservir des réseaux privés, par exemple).

* Plusieurs copies signifient une disponibilité découplée. Un serveur en panne n'affecte pas
  l’ensemble du réseau d’APIS imbriquées. Les pompes de données forment des mailles, là où les données sont
  transféré afin que chacun puisse en avoir une copie s’il le souhaite. C’est un moyen très simple
  d'y parvenir.

* Il peut également pousser des arbres (en utilisant un expéditeur au lieu d’un abonné), ce qui est bien
  pour les transferts entre les démarcations réseau (firewall).

* En utilisant uniquement la configuration, les fichiers peuvent être renommés sur place et la structure
  du répertoire peut être complètement modifiée.

* Avec l’API de plugin, on peut transformer l’arbre ou les fichiers dans l’arbre.
  L’arbre de sortie ne peut avoir aucune ressemblance avec l’arbre d’entrée.

* L’API du plugin peut être utilisée pour mettre en œuvre des flux de travail efficaces pilotés par les données,
  réduire ou éliminer l’interrogation des répertoires et des tâches planifiées qui imposent des
  charges lourdes et augmentatent la latence de transfert.


* Les flux de travail en plusieurs étapes sont naturellement mis en œuvre en plus de
  mettre en relation les producteurs et les consommateurs. La transformation est un consommateur au sein de la
  pompe de données, tandis que les consommateurs externes accèdent aux produits finaux. Les files d’attente entre les composants
  assure la coordination de flux.

* Vous pouvez configurer un *poll* pour que n’importe quel site Web agisse comme une pompe de données Sarracenia.
  Ainsi, le flux peut fonctionner même sans pompe Sarracenia pour commencer.

* Sarracenia est robuste. Ca fonctionne 24h/24 et 7j/7 et prend des dispositions étendues pour être un
  participant civilisé dans les flux de données de mission critiques :

   * Lorsqu’un serveur est en panne, il utilise un backoff exponentiel pour éviter ses conséquences.
   * Lorsqu’un transfert échoue, il est placé dans une fil d’attente de nouvelles tentatives. Les autres transferts se
     poursuivent et le transfert échoué est réessayé ultérieurement lorsque les flux en temps réel le permette.
   * La fiabilité est réglable pour de nombreux cas d’utilisation.

* Puisque Sarracenia s’occupe des pannes transitoires et des files d’attente, votre application
  ne traite que des cas normaux.

* Il utilise des protocoles de fil d’attente de messages (actuellement AMQP et / ou MQTT) pour envoyer des avis fichiers
  et les transferts de fichiers peuvent être effectués via SFTP, HTTP ou tout autre site Web
  service.

* Il ne dépend d’aucune technologie propriétaire. L'utilisation est entièrement gratuite et peut être  utilisé
  à n'importe quel fins.

* Un exemple de mise en œuvre suivant les  `World Meteorological Organizations <WMO>`_
  essaye de remplacer le Système mondial de télécommunications (GTS) par des solutions modernes.

À la base, Sarracenia expose une arborescence de dossiers accessibles sur le Web (WAF), en utilisant n'importe quel
serveur HTTP standard (testé avec apache) ou serveur SFTP, avec d'autres types de serveurs possible via des modules.
Les applications météorologiques sont en temps réel souple (anglais: soft real-time), où les données
doivent être transmises le plus rapidement possible jusqu'au prochain saut, et les minutes, peut-être
les secondes, comptent. Les technologies web push standard, ATOM, RSS, etc.... sont en fait des
technologies de sondage qui, lorsqu'elles sont utilisées dans des applications à faible latence,
consomment beaucoup de bande passante et surcharge les serveurs et réseaux inutilement.  Pour ces raisons
précises, ces normes stipulent un intervalle minimal de sondage de cinq minutes. La messagerie AMQP
(Advanced Message Queueing Protocol) pousse réellement les notifications et rend l'envoi en temps réel
beaucoup plus efficace.

.. image:: ../../Explanation/Concepts/sr3_flow_example.svg
    :scale: 100%
    :align: center

Les sources de données publient leurs produits, les pompes extraient les données en utilisant HTTP ou SFTP via arborescence de dossiers (WAF), puis annoncent cette arborescence aux clients en aval.
Lorsque les clients téléchargent des données, ils peuvent écrire un rapport au serveur. Les serveurs sont configurés pour renvoyer ces messages de rapport du
client par l'intermédiaire de la fonction à la source. : La source peut voir le chemin au complet pris par les données pour arriver jusqu'à chaque client. Dans le
cas des applications de commutation traditionnelles, les sources ne voient que ce qu'elles ont livré au premier maillon d'une chaîne. Au-delà de ce premier maillon,  le
routage est opaque, et le traçage du cheminement des données nécessitent l'aide des administrateurs de chacun des systèmes. Avec la transmission de rapport de Sarracenia, le réseau de commutaiton est relativement transparent pour les sources.
Le diagnostic est alors grandement simplifié.


Pour les gros fichiers / haute performance, les fichiers sont segmentés à l'ingestion s'ils sont suffisamment gros pour que cela en vaille la peine.
Chaque fichier peut traverser le réseau de pompage de données indépendamment, et le réassemblage du fichier initial ne se fait qu'à la fin du processus de transfert. Un fichier de taille suffisante annoncera
la disponibilité de plusieurs segments pour le transfert, des fils multiples ou des nœuds de transfert prendront ces segments et les transféreront. Plus il y a de segments disponibles, plus le niveau de parallèlisme du transfert est élevé. Dans de nombreux cas, Sarracenia gère le parallélisme et l'utilisation du
réseau sans intervention explicite de l'utilisateur.Les pompes de données ne doivent ni stocker ni transférer des fichiers entiers, la taille maximale de fichier qui peut voyager à travers le réseau est maximisée.

* **REMARQUE:** Pour la v03, la fonctionnalité de segmentation a été supprimée temporairement. Prévu pour retour dans la version 3.1.

Implémentations
---------------

Une partie de Sarracénia définit un message d'annonce avec AMQP comme transport.
Il y a des implémentations multiples qui acceptent ses messages d'annonce:


- Sarracenia elle-même (http://github.com/MetPX/sarracenia)
  une implémentation de référence complète en Python >= 3.4.
  Il fonctionne sous Linux, Mac et Windows.

- sarrac ( https://github.com/MetPX/sarrac) est une implémentation en
  C de l'insertion de données (post & watch.) C'est Linux uniquement. Il
  y a aussi une libcshim pour pouvoir implémenter de manière transparente
  l'insertion de données avec cet outil, et libsarra permet aux programmes
  C de poster directement. Il y a aussi du code consommateur (sr_cpump,
  pour lire les files d'attente) mais pas de téléchargement jusqu'à présent.
  Ce sous-ensemble est destiné à être utilisé là où les environnements
  python3 ne sont pas pratiques (certains environnements HPC).

- node-sarra ( https://github.com/darkskyapp/node-sarra) Une implémentation embryonnaire pour node.js.

- ecpush ( https://github.com/TheTannerRyan/ecpush ) un simple client in Go ( http://golang.org )

- PySarra ( https://github.com/JohnTheNerd/PySarra ) un client archi-simple en python3.

- dd_subscribe ( https://github.com/MetPX/sarracenia) client en python2 (Le prédécesseur de Sarracénia.) Toujours compatible.

D'autres clients sont les bienvenues.


Pourquoi ne pas simplement utiliser Rsync ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Il existe un certain nombre d'outils de réplication d'arbres qui sont largement
utilisés, pourquoi en inventer un autre ? `RSync <https://rsync.samba.org/>`_,
par exemple, est un outil fabuleux, et nous avons Il est fortement recommandé
pour de nombreux cas d'utilisation. mais il y a des moments où la Sarracenia peut aller
72 fois plus rapide que rsync : Étude de cas : `HPC Mirroring Use Case <History/HPC_Mirroring_Use_Case.html>`_

Rsync et d'autres outils sont basés sur la comparaison (traitant d'une source et d'une destination
unique) Sarracénie, bien qu´elle n'utilisent pas la multidiffusion, est orienté vers une livraison
à plusieurs récepteurs, en particulier lorsque la source ne sait pas qui sont tous les
récepteurs (pub/sub.) La synchronisation rsync est typiquement faite en marchant un à un.
L'intervalle de synchronisation est intrinsèquement limité à la fréquence
à laquelle on peut traverser (sonder?) l'arbre de fichiers (dans les grands arbres, cela peut être long).
La Sarracenia évite les promenades dans les arbres de fichiers en demandant
aux sources de données de signaler directement aux lecteurs par des messages, réduisant ainsi
les frais généraux de plusieurs ordres de grandeur.`Lsyncd <https://github.com/axkibe/lsyncd>`_
est un outil qui exploite les fonctionnalités INOTIFY de Linux. pour atteindre le même genre
de rapidité de détection the changement, et il pourrait être plus approprié, mais il n'est
évidemment pas portable, et reste très lente en comparaison avec les avis émis directement
par les sources. De plus, faire faire cela par le système de fichiers est considéré comme
lourd et moins général qu'explicite passage de messages via middleware, qui gère également
les logs de manière simple.

Un des objectifs de Sarracenia est d'être de bout en bout. Rsync est point-à-point,
ce qui signifie qu'il ne prend pas en charge la *transitivité* des transferts
de données entre plusieurs pompes de données qui est désiré. D'autre part, le
premier cas d'utilisation de la Sarracenia est la distribution du nouveaux
fichiers. Au départ, les mises à jour des dossiers n'étaient pas courantes.
`ZSync <http://zsync.moria.org.uk>`_ est beaucoup plus proche dans l'esprit
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
Les pilotes de transfert intégrés incluent des accellerateurs binaires
et des critères accordables pour les utiliser.

**Caveat La segmentation des fichiers a été supprimée. FIXME**

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



Références et liens
~~~~~~~~~~~~~~~~~~~
D'autres logiciels, quelque peu similaires, aucun endossement ou jugement ne devrait être tiré de ces liens :


- `Local Data Manager <https://www.unidata.ucar.edu/software/ldm>`_ LDM comprend un réseau,
   et il souhaite fondamentalement échanger avec d’autres systèmes LDM.  Ce paquet était
   instructif, au début des années 2000, il y a eu un effort appelé NLDM qui mettait la
   messagerie météorologique en couches sur un protocole TCP/IP standard.  Cet effort est mort, cependant,
   mais l’inspiration de garder le domaine (météo) séparé de la couche de transport (TCP/IP)
   était une motivation importante pour MetPX.
- `Automatic File Distributor  <https://www.dwd.de/AFD>`_ - du service météorologique allemand.
   Achemine les fichiers à l’aide du protocole de transport choisi par l’utilisateur.  Philosophiquement proche de MetPX Sundew.
- `Corobor <https://www.corobor.com>`_ - commutateur WMO commercial
- `Netsys  <https://www.netsys.co.za>`_ -commutateur WMO commercial
- `IBLSoft <https://www.iblsoft.com>`_ -commutateur WMO commercial
- Variété de moteurs de transferts: Standard Networks Move IT DMZ, Softlink B-HUB & FEST,
  Globalscape EFT Server, Axway XFB, Primeur Spazio, Tumbleweed Secure File Transfer, Messageway.
- `Quantum <https://www.websocket.org/quantum.rst>`_ à propos des sockets web HTML5. Une bonne discussion
  des raisons pour lesquelles le push web traditionnel est horrible, montrant comment les sockets web
  peuvent aider. AMQP est une solution de socket pure qui a les mêmes avantages que les
  webockets pour l'efficacité. Note : la compagnie derrière KAAZING a écrit la pièce... pas désintéressé.

- `Rsync  <https://rsync.samba.org/>`_  moteur de transfert.
- `Lsyncd <https://github.com/axkibe/lsyncd>`_   moteur de transfert.
- `ZSync <https://zsync.moria.org.uk>`_ ( optimised rsync over HTTP. ) moteur de transfer.
