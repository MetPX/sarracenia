
Annonce de Sr3
--------------

Après deux ans de développement, le 11/04/2022, nous sommes heureux d’annoncer la disponibilité
de la première version bêta de Sarracenia version 3: Sr3. Pour célébrer la sortie, il y a un
nouveau site Web avec des informations détaillées:

  https://metpx.github.io/sarracenia

Par rapport à la v2, Sr3 apporte:

* Prise en charge native pour `mqtt <https://www.mqtt.org>`_ et
  `amqp <https://www.amqp.org>`_ (`rabbitmq <https://www.rabbitmq.com>`_ et les courtiers MQTT.)
  avec une implémentation modulaire qui permet des
  `message queueing protocols <https://metpx.github.io/sarracenia/Reference/code.html#module-sarracenia.moth>`_
  être pris en charge.

* L'`Algorithme de Flux <https://metpx.github.io/sarracenia/Explanation/Concepts.html#the-flow-algorithm>`_ unifie
  tous les composants en légères variations de ce
  `code commun unique. <https://metpx.github.io/sarracenia/Reference/code.html#module-sarracenia.flow>`_
  Ce refactoring a permis d’éliminer la duplication de code et de réduire le nombre total de lignes de
  code d’environ 30 % tout en ajoutant des fonctionnalités.

* Une nouvelle interface de ligne de commande centrée sur un point d’entrée unique: `sr3 <https://metpx.github.io/sarracenia/Reference/sr3.1.html#sr3-sarracenia-cli>`_

* Amélioration de Jupyter Notebook `Tutorials <https://metpx.github.io/sarracenia/Tutorials/index.html>`_

* Un nouveau `plugin API <https://metpx.github.io/sarracenia/Reference/flowcb.html>`_,
  ce qui permet la personnalisation pythonique du traitement des applications par défaut.

* Un nouveau `python API <https://metpx.github.io/sarracenia/Reference/code.html>`_,
  ce qui donne un accès complet à l’implémentation, permettant une extension élégante grâce à la sous-classification.

* Les applications peuvent appeler Sarracenia Python API à partir de leur ligne principale.
  (Dans la v2, il fallait écrire des rappels pour appeler le code de l’application, la ligne principale de l’application ne pouvait pas être utilisée.)

* Ajout d’un module de discussion GitHub, pour les questions et les clarifications de la communauté :
  https://github.com/MetPX/sarracenia/discussions

