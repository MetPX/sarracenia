==========================
 Sarracenia v3 (MetPX-Sr3)
==========================

[ homepage (En): https://metpx.github.io/sarracenia ] [ `(Fr) fr/ <https://metpx.github.io/sarracenia/fr>`_ ]

.. image:: https://img.shields.io/pypi/v/metpx-sr3?style=flat
  :alt: PyPI version
  :target: https://pypi.org/project/metpx-sr3/

.. image:: https://img.shields.io/pypi/pyversions/metpx-sr3.svg
    :alt: Supported Python versions
    :target: https://pypi.python.org/pypi/metpx-sr3.svg

.. image:: https://img.shields.io/pypi/l/metpx-sr3?color=brightgreen
    :alt: License (GPLv2)
    :target: https://pypi.org/project/metpx-sr3/

.. image:: https://img.shields.io/github/issues/MetPX/sarracenia
    :alt: Issue Tracker
    :target: https://github.com/MetPX/sarracenia/issues

.. image:: https://github.com/MetPX/sarracenia/actions/workflows/ghcr.yml/badge.svg
    :alt: Docker Image Build Status
    :target: https://github.com/MetPX/sarracenia/actions/workflows/ghcr.yml

.. image:: https://github.com/MetPX/sarracenia/actions/workflows/flow.yml/badge.svg?branch=v03_wip
    :alt: Run Static Flow
    :target: https://github.com/MetPX/sarracenia/actions/workflows/flow.yml

+----------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------+
|                                                                                        |                                                                                           |
| [ `Getting Started <https://metpx.github.io/sarracenia/How2Guides/subscriber.html>`_ ] | [ `Un bon départ <https://metpx.github.io/sarracenia/fr/CommentFaire/subscriber.html>`_ ] |
| [ `Source Guide <https://metpx.github.io/sarracenia/How2Guides/source.html>`_ ]        | [ `Guide de Source <https://metpx.github.io/sarracenia/fr/CommentFaire/source.html>`_ ]   |
|                                                                                        |                                                                                           |
+----------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------+
|                                                                                        |                                                                                           |
| MetPX-sr3 (Sarracenia v3) is a data duplication                                        | MetPX-sr3 (Sarracenia v3) est un engin de copie et de                                     |
| or distribution pump that leverages                                                    | distribution de données qui utilise des                                                   |
| existing standard technologies (web                                                    | technologies standards (tel que les services                                              |
| servers and Message queueing protocol                                                  | web et le courtier de messages AMQP) afin                                                 |
| brokers) to achieve real-time message delivery                                         | d'effectuer des transferts de données en                                                  |
| and end-to-end transparency in file transfers.                                         | temps réel tout en permettant une transparence                                            |
| Data sources establish a directory structure                                           | de bout en bout. Alors que chaque commutateur                                             |
| which is carried through any number of                                                 | Sundew est unique en soit, offrant des                                                    |
| intervening pumps until they arrive at a                                               | configurations sur mesure et permutations de                                              |
| client.                                                                                | données multiples, Sarracenia cherche à                                                   |
|                                                                                        | maintenir l'intégrité de la structure des                                                 |
|                                                                                        | données, tel que proposée et organisée par la                                             |
|                                                                                        | source jusqu'à destination.                                                               |
|                                                                                        |                                                                                           |
+----------------------------------------------------------------------------------------+-------------------------------------------------------------------------------------------+
