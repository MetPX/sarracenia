==================
 MetPX-Sarracenia
==================

.. image:: https://img.shields.io/pypi/v/metpx-sarracenia?style=flat
  :alt: PyPI version
  :target: https://pypi.org/project/metpx-sarracenia/

.. image:: https://img.shields.io/pypi/pyversions/metpx-sarracenia.svg
    :alt: Supported Python versions
    :target: https://pypi.python.org/pypi/metpx-sarracenia.svg

.. image:: https://img.shields.io/pypi/l/metpx-sarracenia?color=brightgreen
    :alt: License (GPLv2)
    :target: https://pypi.org/project/metpx-sarracenia/

.. image:: https://img.shields.io/github/issues/MetPX/sarracenia
    :alt: Issue Tracker
    :target: https://github.com/MetPX/sarracenia/issues

.. image:: https://travis-ci.com/MetPX/sarracenia.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.com/MetPX/sarracenia


+-------------------------------------------------------+-----------------------------------------------------------------+
| [ `Guides <doc/sr_subscribe.1.rst#documentation>`_ ]  |  [ `Orientation <doc/fr/sr_subscribe.1.rst#documentation>`_ ]   |
| [ `Manual Pages <doc/sr_subscribe.1.rst#see-also>`_ ] |  [ `Référence <doc/fr/sr_subscribe.1.rst#aussi-voir>`_ ]        |
+-------------------------------------------------------+-----------------------------------------------------------------+
|                                                       |                                                                 |
|MetPX-Sarracenia is a data duplication                 |MetPX-Sarracenia est un engin de copie et de                     |
|or distribution pump that leverages                    |distribution de données qui utilise des                          |
|existing standard technologies (web                    |technologies standards (tel que les services                     |
|servers and the `AMQP <http://www.amqp.org>`_          |web et le courtier de messages AMQP) afin                        |
|brokers) to achieve real-time message delivery         |d'effectuer des transferts de données en                         |
|and end-to-end transparency in file transfers.         |temps réel tout en permettant une transparence                   |
|Data sources establish a directory structure           |de bout en bout. Alors que chaque commutateur                    |
|which is carried through any number of                 |Sundew est unique en soit, offrant des                           |
|intervening pumps until they arrive at a               |configurations sur mesure et permutations de                     |
|client. The client can provide explicit                |données multiples, Sarracenia cherche à                          |
|acknowledgement that propagates back through           |maintenir l'intégrité de la structure des                        |
|the network to the source. Whereas traditional         |données, tel que proposée et organisée par la                    |
|file switching is a point-to-point affair              |source jusqu'à destination. Le client peut fournir               |
|where knowledge is only between each segment,          |des accusés de réception qui se propagent                        |
|in Sarracenia, information flows from end-to-          |à travers tous les noeuds de la chaîne,                          |
|end in both directions.                                |en sens inverse jusqu'à la source. Tandis qu'un                  |
|                                                       |commutateur traditionnel échange les données                     |
|At its heart, Sarracenia exposes a tree of             |de point à point, Sarracenia permet le passage                   |
|web accessible folders (WAF), using any standard       |des données d'un bout à l'autre du réseau,                       |
|HTTP server (tested with apache).  Weather             |tant dans une direction que dans l'autre.                        |
|applications are soft real-time, where data            |                                                                 |
|should be delivered as quickly as possible to          |Sarracenia, à sa plus simple expression,                         |
|the next hop, and minutes, perhaps seconds,            |expose une arborescence de dossiers disponibles                  |
|count. The standard web push technologies, ATOM,       |sur la toile ("Web Accessible Folders"). Le                      |
|RSS, etc... are actually polling technologies          |temps de latence est une composante névralgique                  |
|that when used in low latency applications             |des applications météo: les minutes, et parfois                  |
|consume a great deal of bandwidth and overhead.        |les secondes, sont comptées. Les technologies                    |
|For exactly these reasons, those standards             |standards, telles que ATOM et RSS, sont des                      |
|stipulate a minimum polling interval of five           |technologies qui consomment beaucoup de bande                    |
|minutes. Advanced Message Queueing Protocol            |passante et de ressouces lorsqu'elles doivent                    |
|(AMQP) messaging brings true push to                   |répondre à ces contraintes. Ces standards                        |
|notifications, and makes real-time sending             |limitent la fréquence maximale de vérification                   |
|far more efficient.                                    |du serveur à cinq minutes. Le protocole de                       |
|                                                       |séquencement de messages avancés (Advanced                       |
|                                                       |Message Queuing Protocol, AMQP) est une                          |
|                                                       |approche beaucoup plus efficace pour la                          |
|                                                       |livraison d'annonces de nouveaux produits.                       |
|                                                       |                                                                 |
+-------------------------------------------------------+-----------------------------------------------------------------+
|An initiative of Shared Services Canada                |Une initiative de Services partagés Canada                       |
|http://ssc-spc.gc.ca in support of internal            |https://ssc-spc.gc.ca pour appuyer les opérations                |
|needs of the Government of Canada                      |du gouvernement du Canada                                        |
|                                                       |                                                                 |
+-------------------------------------------------------+-----------------------------------------------------------------+

page web / homepage: http://github.com/MetPX/sarracenia

**Videos:**

- Concept Overview: `Sarracenia in 10 Minutes Video (anglais seulement) <https://www.youtube.com/watch?v=G47DRwzwckk>`_
- v2 Installation Tutorial: `Sarracenia v2 Intro Guide <https://www.youtube.com/watch?v=XV5M4P0zKgg>`_

Documentation *master* location: https://github.com/MetPX/sarracenia/blob/master/doc/sr_subscribe.1.rst#documentation

Documentation *principale* située à: https://github.com/MetPX/sarracenia/blob/master/doc/fr/sr_subscribe.1.rst#documentation

