=================
Bienvenue à MetPX
=================

MetPX - L'échangeur de produits météorologiques
===============================================

.. |Date| date::

Date: |Date|

[ English_ ]

.. _English: indexe.html


MetPX est une collection dŽoutils créée afin de faciliter lŽacquisition, lŽaiguillage, et la dissémination 
de données dans un contexte météorologique. Il y a deux applications principales: Sundew et Sarracenia. 
MetPX-Sundew_ est axé sur le support et la compatibilité des systèmes matures de Système de télécommunication
mondiale (STM) de lŽOrganisation mondiale de la météo (OMM). Il acquiert, transforme, et livre des produits 
individuels, tandis que MetPX-Sarracenia_ adopte une nouvelle approche, et offre la copie 
complète (filtrée) de l'arborescence source. Sarracenia abandonne la compatibilité afin de répondre aux 
besoins actuels. Par contre, sundew demeure tout de même un lien essentiel aux 
anciens systèmes.

[ liste de couriel (Anglais-Français): `metpx-devel <http://lists.sourceforge.net/lists/listinfo/metpx-devel>`_ , `metpx-commit <http://lists.sourceforge.net/lists/listinfo/metpx-commit>`_ ] 
[ projet: `Sourceforge <http://www.sourceforge.net/projects/metpx>`_ ]
[ Documentation_ ]
[ `Téléchargement <http://sourceforge.net/project/showfiles.php?group_id=165061>`_ ]
[ `Accès au code source`_ ]
[ `Liens et Références`_ ]

[ liste de couriel (Anglais-Français): `metpx-devel <http://lists.sourceforge.net/lists/listinfo/metpx-devel>`_ , `metpx-commit <http://lists.sourceforge.net/lists/listinfo/metpx-commit>`_ ] 
[ Page principale de dévéloppement: `Sourceforge <http://www.sourceforge.net/projects/metpx>`_ ]


MetPX-Sarracenia
================

MetPX-Sarracenia est un engin de copie et de distribution de données qui utilise des technologies 
standards (tel que les services web et le courtier de messages AMQP) afin d'effectuer des transferts de 
données en temps réel tout en permettant une transparence de bout en bout. Alors que chaque commutateur 
Sundew est unique en soit, offrant des configurations sur mesure et permutations de données multiples, 
Sarracenia cherche à maintenir l'intégrité de la structure des données, tel que proposée et organisée 
par la source, à travers tous les noeuds de la chaîne, jusqu'à destination. Le client peut 
fournir des accusés de réception qui se propagent en sens inverse jusqu'à la source. Tandis qu'un 
commutateur traditionnel échange les données de point à point, Sarracenia permet le passage des 
données d'un bout à l'autre du réseau, tant dans une direction que dans l'autre.

Sarracenia, à sa plus simple expression, expose une arborescence de dossiers disponibles sur la toile 
("Web Accessible Folders"). Le temps de latence est une composante névralgique des applications météo: les minutes, et parfois les secondes, sont comptées. Les technologies standards, telles que ATOM et
RSS, sont des technologies qui consomment beaucoup de bande passante et de ressouces lorsqu'elles doivent répondre à ces contraintes. Les standards limitent la fréquence maximale de vérification de serveur à cinq minutes. 
Le protocol de séquencement de messages avancés (Advanced Message Queuing Protocol, AMQP) est une 
approche beaucoup plus efficace pour la livraison d'annonces de nouveaux produits.

.. image:: f-ddsr-components.gif

Les sources annoncent la disponibilité des données, les commutateurs en font une copie 
et la diffusent à leurs clients. Quand les clients téléchargent des données, ils ont l'option 
d'enregistrer cette transaction. Les enregistrements de transaction sont réacheminés aux sources, 
en passant par chaque système du chemin inverse. Ceci permet aux sources de voir exactement le 
chemin qu'ont pris les données pour se rendre aux clients.  Avec les systèmes traditionnels 
d'échange de données, chaque source peut seulement confirmer que le transfert vers le prochain 
noeud de la chaîne a été complété. Tout transfert subséquent est « opaque » et tracer le 
cheminement d'un produit exige l'aide des administrateurs des systèmes intermédiaires. Grâce au 
concept de Sarracenia, prévoyant l'acheminement des enregistrements de transactions à travers 
le réseau, la diffusion des données devient transparente aux sources. Les diagnostiques en 
sont aussi grandement simplifiés.

Tandis que Sundew supporte plusieurs protocoles et formats de la météorologie,
Sarracenia se retire de cette spécificité et généralise son approche, ce qui lui permet d'être utile pour dŽautres domaines scientifiques. Le client prototype, dd_subscribe, est en service depuis
2013 et implante une grande partie des fonctions de consommateurs de données. Elle est la seule composante
dans les paquets Debian actuels. Le reste des composantes devraient être disponibles durant le printemps de 2016.

Sarracenia est plus simple que Sundew, peu importe l'utilisateur: opérateur, dévéloppeur, analyste, 
source et consommateurs de données. Bien quŽil impose une interface pour lŽaccès au 
données, Sarracenia est complètement générique et portable.  Il sera disponible sur nŽimporte 
quelle plateforme moderne (GNU/Linux, Windows, Apple)

Pourquoi ne pas utiliser RSync?
===============================

Il existe multiples solutions pour la copie de données, pourquoi en inventer une autre? Rsync et la
plupart des autres outils sont 1:1, ils comparent source et destination.  Sarracenia, bien quŽil ne sert
pas de multi-cast, est orienté vers la livraison à de multiples clients en temps réél. La synchronization 
RSync se fait via la communication de lŽarborescences, en calculant des signatures pour chaque fichier, pour
chaque client. Pour les arborescences importantes, comprennant plusieurs clients, ces calculs et transactions deviennent onéreuses, limitant la fréquence de mise à jour et le nombre de clients peuvant être supportés. Sarracenia évite le parcours des arborescences, et les processus qui écrivent les fichiers calculent les checksum une fois seulement, afin d'être utilisé directement par tous les intervenants. Ces deux améliorations rendent Sarracenia beaucoup plus efficace que RSync dans le cas d'arborescences imposantes comprenant l'ajout fréquent de fichiers. LSync est un outil qui utilise INOTIFY sur GNU/Linux pour avoir une notification en temps réel, mais la gestion 
des checksum et la communication des enregistrements à travers le réseau n'existent pas. De plus,
LSync nŽest pas interopérable avec d'autres systèmes d'exploitation.

 
RSync est également une solution point à point. Sarracenia mise sur la "transitivité", c'est-à-dire sur la capacité d'enchaîner plusieurs commutateurs de produits et de sŽassurer que les accusées de réception se propagent jusquŽà
la source. Par contre, lŽimplantation initiale de sarracenia ne traite pas des deltas (changement de 
contenu de fichiers existants) et va télécharger le contenu complet a chaque annonce. On étudie présentement
le cas des deltas, et lŽutilisation de lŽalgorithm RSync via lŽoutil zsync est en considération.


MetPX-Sundew
============


MetPX-Sundew est un système de commutation de messages sur les circuits TCP/IP du 
Système de télécommunications mondiales (STM) de l'Organisation mondial de 
la météorologie (l'`OMM <http://www.wmo.int>`_ ) Pour certaines fonctionnalités, le système est déjà d'une qualité opérationelle et est utilisé au Centre météorologique canadien en tant que noyau national de commutation de bulletins
et fichiers (satelites, radars, produits numériques). le logiciel permet
la participation canadienne à des projets internationaux tel que 

`Unidata <http://www.unidata.ucar.edu/>`_ et `TIGGE <http://tigge.ecmwf.int/>`_ via une passerelle 
à LDM, ainsi que `NAEFS <http://www.emc.ncep.noaa.gov/gmb/ens/NAEFS.html>`_ via le transfert de fichiers.
MetPX se démarque par sa capacité de routage détaillé a très faible latence et à haute vitesse.
Le projet se veut une sorte de plateforme partagé et universelle pour les télécommunications via STM, sur 
le modèle dŽApache pour les serveurs web.

Types de connections TCP/IP:

 - AM (socket proriétaire aux systèmes canadiens)
 - sockets OMM (voir le manuel 386) 
 - FTP pour le transport, pas de nomenclature de l'OMM pour lŽinstant (facile à ajouter)
 - SFTP (but similaire au FTP, mais avec plus de sécurité)
 - AFTN/IP passerelle (Version NavCanada du "Aviation Fixed Telecommunications Network", normalement basée sur du X.25)
 - AMQP (protocol ouvert de messagerie provenant du monde des affaires)

Fonctionnalités:

 - Routage détaillé (.... avec 30&nbsp;000 entrées distinctes dans la table de routage)
 - modalités de commutation commun entre les fichiers et les bulletins.
 - Temps de commutation inférieur à une seconde (avec 28&nbsp;000 entrées)
 - Commutation et livraison à haute vitesse (était plus de 300 messages par seconde l'an dernier) 
   mais il est à noter que plusieurs fonctionnalités ont été ajoutés qui pourraient 
   affecter la vitesse. Il serait nécessaire de re-vérifier cet aspect.
 - Aucune limite de taille des messages.
 - Segmentation de messages (pour protocols tels que AM &amp; OMM qui ont de telles limites)
 - Supression des duplicata (à l'envoi)
 - AFTN/IP canadien.
 - collecte de bulletins
 - mécanisme de filtrage général (les collections seront adaptées à ce mécanisme) 

Il y a actuellement trois modules dans ce projet et un quatrième est à l'étude. 
Les modules de MetPX sont nommés selon des noms d'espèces de plantes 
en voie de disparition au Canada. (voir `Espèces en péril <http://www.especesenperil.gc.ca>`_ )

 - sundew: module de commutation de l'OMM
 - columbo: module de surveillance, pour sundew et PDS
 - stats: module de collecte et affichages de statistiques.
 

Plateforme: GNU/Linux dérivé de Debian (Sarge, Etch, Lenny, Ubuntu...) NŽimporte quel système GNU/Linux moderne (2.6 vanille ou bien 2.4 avec plusieurs rustines). Python version 2.3 où plus récent)

license: GPLv2

le code source en dévéloppement est disponible en utilisant subversion via: git clone git://git.code.sf.net/p/metpx/git metpx
( accès anonyme pour fins de lecture. )

Documentation
=============

La documentation en français nŽest pas disponible pour le moment.
Ca va être traduite une fois quŽon aura stabilisé une première édition en anglais.

Veuillez consulter la `Documentation anglaise <indexe.html#Documentation>`_ pour lŽinstant

Téléchargement
==============

`Téléchargement <http://sourceforge.net/project/showfiles.php?group_id=165061>`_

Le module Sundew est relativement stable et peut être téléchargé du site 
de Sourceforge.  Les autres modules ne sont pas assez matures pour être distribués.

Accès au code source
====================

Présentement, les installations sont faites une à la fois, à partir du code source.
Le développement se fait dans le branche ŽmainŽ (terminologie de git.) Quand
on installe, on crée une branche de maintenance pour lŽinstallation. Il y a des 
fichiers README et INSTALL qui peuvent donner des indices pour arriver a une 
installation initiale.

Il est à noter qu'il est assez critique dŽinstaller des Žjobs cronŽ (mr-clean 
en particulier) parce que le cas écheant, le serveur va tranquillement rouler 
de plus en plus lentement jusquŽau moment où il arrête carrément. Ça serait 
optimal de vous inscrire à la liste de couriel (français, bienvenu, peut-être 
même préféré...) ce qui nous donnera des indices pour des tâches futures et de
potentielles collaborations.

Sentez-vous libre de prendre une copie de la version à jour du code source via::

 git clone git://git.code.sf.net/p/metpx/git metpx

(disponible anonymement en lecture seulement.) DŽautre versions sont disponibles 
en téléchargeant une branche spécifique.

AMQP
====

AMQP est un protocol standard pour l'échange de messages qui origine du domaine de la finance.  
AMQP est apparu en 2007 et a graduellement gagné en maturité. Il y a aujourd'hui plusieurs 
implémentations de ce protocole en logiciel libre.  AMQP offre une méthode pour le transport des 
messages JAVA, mais il n'est pas dédié uniquement à ce langage. Sa neutralité envers les différents 
langages de programmation facilite l'interopérabilité avec les fournisseurs JMS, sans se limiter 
à JAVA. Le langage AMQP et ses messages sont neutres. Certaines implémentations utilisent 
python, C++ et ruby, tandis que les fournisseurs de JMS sont fortement orientés JAVA.

 - `www.amqp.org <http://www.amqp.org>`_ Définition dŽAMQP.
 - `www.openamq.org <http://www.openamq.org>`_ prémière Implantation de JPMorganChase
 - `www.rabbitmq.com <http://www.rabbitmq.com>`_ Une autre implantatation. Celle utilisé par le présent projet.
 - `Apache Qpid <http://cwiki.apache.org/qpid>`_ Encore une autre implantation.
 - `Apache ActiveMQ <http://activemq.apache.org>`_ Un "fournisseur JMS" avec la capacité dŽutiliser AMQP comme transport. 

Sarracenia utilise les concepts de « courtier de messages » et « échanges basés sur le sujet » qui, 
antérieurement à la version 1.0, étaient standards dans AMQP. A partir de la version 1.0, le comité 
des standards AMQP a décidé de retirer ces aspects avec l'idée de les réintroduire dans le futur. 
Dû à cette décision, Sarracenia dépend des versions pré 1.0 de AMQP, tel que « rabbitmq ».

Liens et Références
===================

DŽautres projets et produits qui sont vaguement dans une domaine similaire. Les mentions ici ne doivent pas être interpretées comme des recommandations.

 - le manuel WMO 386, référence pour le domaine.(version sans doute périmée est `WMO-386 <WMO-386.pdf>`_ ici. Voir http://www.wmo.int pour une version plus récente.
 - `http://www.unidata.ucar.edu/software/ldm <http://www.unidata.ucar.edu/software/ldm>`_ - Local Data 
   Manager. LDM inclut un protocol résautique, et veut fondamentalement échanger des données avec dŽautres serveurs LDM. 
   Ce logiciel a servi comme inspiration de plusieurs façons. Au début des années 2000, nous avions étudié le protocol 
   pour les besoins du CMC et identifié des charactéristiques qui le rendaient inapte à notre application.  Par 
   contre, il y avait un effort ŽNLDMŽ qui avait remplacé le protocol résautique de 
   LDM par un protocol standard (NNTP.) LŽéffort a sombré, par contre, ça a servi comme inspiration pour la séparation de le domaine météorologique de protocol de télécommunication, ce qui a été reprit philosophiquement par MetPX. 
 - `http://www.dwd.de/AFD <http://www.dwd.de/AFD>`_ - Automatic File Distributor - du Service météorologique allemand. Aiguilleur de fichiers dans le protocol au choix de lŽusager. Similaire à MetPX en philosophie
 - `Corrobor <http://www.corobor.com>`_ - commutateur OMM commerciale.
 - `Netsys <http://www.netsys.co.za>`_ - commutateur OMM commerciale.
 - `IBLSoft <http://www.iblsoft.com>`_ - commutateur OMM commerciale.
 - Quelques autres logiciels de transfert de fichiers: Standard Networks Move IT DMZ, Softlink B-HUB & 
   FEST, Globalscape EFT Server, Axway XFB, Primeur Spazio, Tumbleweed Secure File Transfer, Messageway
 - `Rsync <https://rsync.samba.org/>`_ engin de transfert incrementale rapide.
 - `Lsync <https://code.google.com/p/lsyncd>`_ engin de synchronization en temps reel.
 - `Zsync <http://zsync.moria.org.uk>`_ RSync sur HTTP.


