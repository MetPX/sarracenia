==================
 MetPX-Sarracenia
==================

[ Français_ ]

Overview
--------

MetPX-Sarracenia is a data duplication or distribution pump that leverages 
existing standard technologies (web servers and the `AMQP <http://www.amqp.org>`_ 
brokers) to achieve 
real-time message delivery and end to end transparency in file transfers.  
Data sources establish a directory structure which is carried through any 
number of intervening pumps until they arrive at a client.  The client can 
provide explicit acknowledgement that propagates back through the network 
to the source.  Whereas traditional file switching is a point-to-point affair 
where knowledge is only between each segment, in Sarracenia, information 
flows from end to end in both directions.

At it's heart, sarracenia exposes a tree of web accessible folders (WAF), using 
any standard HTTP server (tested with apache).  Weather applications are soft 
real-time, where data should be delivered as quickly as possible to the next
hop, and minutes, perhaps seconds, count.  The standard web push technologies, 
ATOM, RSS, etc... are actually polling technologies that when used in low latency 
applications consume a great deal of bandwidth an overhead.  For exactly these 
reasons, those standards stipulate a minimum polling interval of five minutes.
Advanced Message Queueing Protocol (AMQP) messaging brings true push to 
notifications, and makes real-time sending far more efficient.

homepage: http://metpx.sf.net

Man Pages online: http://metpx.sourceforge.net/#sarracenia-documentation


Sarracenia is an initiative of Shared Services Canada ( http://ssc-spc.gc.ca )
in response to internal needs of the Government of Canada.


.. _Français:

Survol
------

MetPX-Sarracenia est un engin de copie et de distribution de données qui utilise 
des technologies standards (tel que les services web et le courtier de messages 
AMQP) afin d'effectuer des transferts de données en temps réel tout en permettant 
une transparence de bout en bout. Alors que chaque commutateur Sundew est unique 
en soit, offrant des configurations sur mesure et permutations de données multiples, 
Sarracenia cherche à maintenir l'intégrité de la structure des données, tel que 
proposée et organisée par la source, à travers tous les noeuds de la chaîne, 
jusqu'à destination. Le client peut fournir des accusés de réception qui se 
propagent en sens inverse jusqu'à la source. Tandis qu'un commutateur traditionnel 
échange les données de point à point, Sarracenia permet le passage des données 
d'un bout à l'autre du réseau, tant dans une direction que dans l'autre.

Sarracenia, à sa plus simple expression, expose une arborescence de dossiers disponibles 
sur la toile ("Web Accessible Folders"). Le temps de latence est une composante 
névralgique des applications météo: les minutes, et parfois les secondes, sont comptées. 
Les technologies standards, telles que ATOM et RSS, sont des technologies qui consomment 
beaucoup de bande passante et de ressouces lorsqu'elles doivent répondre à ces contraintes. 
Les standards limitent la fréquence maximale de vérification de serveur à cinq minutes. 
Le protocol de séquencement de messages avancés (Advanced Message Queuing Protocol, 
AMQP) est une approche beaucoup plus efficace pour la livraison d'annonces de 
nouveaux produits.

Sarracenia est une initiative de Services Partagés Canada ( http://ssc-spc.gc.ca )
