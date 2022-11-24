
Modifications apportées pour créer la v03
==========================

Le format réel est défini `ici <../../Reference/sr_post.7.html>`_
Une explication de la motivation des changements est ci-dessous:

Différences par rapport à v02
-----------------------------
La version 03 est un changement d’encodage, mais la sémantique des champs
sont inchangés par rapport à la version 02. Les modifications sont limitées à la façon dont les champs
sont placés dans les messages. Dans v02, les en-têtes AMQP étaient utilisés pour stocker la valeur des
paires nom-valeur

   * Les en-têtes v03 ont une longueur pratiquement illimitée. Dans la v02, individuel
     Les paires nom-valeur sont limitées à 255 caractères. Cela a prouvé
     limitant dans la pratique. Dans v03, la limite n’est pas définie par le standard JSON,
     mais par des implémentations d’analyseur spécifiques. Les limites
     dans les analyseurs commun sont suffisamment élevés pour ne pas causer de problèmes pratiques.

   * L’utilisation de la charge utile des messages pour stocker les en-têtes permet d’envisager
     d’autres protocoles de messagerie, tels que MQTT 3.1.1, à l’avenir.

   * Dans la version v03, la charge utile JSON pure simplifie les implémentations, réduit la
     documentation requise et la quantité d’analyse à implémenter. L’utilisation d’un format couramment
     implémenté permet d’utiliser des analyseurs optimisés existants.

   * Dans la v03, l’encodage JSON de l’ensemble de la charge utile réduit les fonctionnalités requises
     pour qu’un protocole transfère les messages Sarracenia. Par exemple, on pourrait envisager d’utiliser
     Sarracenia avec des courtiers MQTT v3.11 qui sont plus standardisés et donc plus facilement
     interopérables que AMQP.

   * Les champs fixes v02 sont maintenant des clés "pubTime", "baseURL" et "relPath"
     dans l’objet JSON qui est le corps du message.

   * L’en-tête v02 *sum* avec valeur codée hexadécimale, est remplacé par l’en-tête v03 *integrity* avec codage base64.

   * L’en-tête v03 *content* permet l’intégration du contenu du fichier.

   * Changement de frais généraux... Environ +75 octets par message (variable.)

     * Objet JSON marquant les accolades '{' '}', virgules et guillemets pour
       trois champs fixes. net: +10

     * La section AMQP *Propriétés de l’application* n’est plus incluse dans la charge utile, ce qui permet d’économiser
       un en-tête de 3 octets (remplacé par 2 octets de charge utile entre accolades ouvertes et fermées.)
       net: -1 octet

     * chaque champ a un en-tête d’un octet pour indiquer l’entrée de table dans un paquet AMQP
       contre 4 guillemets, un deux-points, un espace et probablement une virgule : 7 au total.
       Le changement net est donc de +6 caractères, par en-tête. La plupart des messages v02 ont 6 en-têtes,
       net : +36 octets

     * les champs fixes sont maintenant nommés : pubTime, baseUrl, relPath, en ajoutant 10 caractères
       chaque. +30 octets.

   * Dans v03, le format des fichiers de sauvegarde est le même que la charge utile du message.
     Dans v02, il s’agissait d’un tuple json qui incluait un champ de sujet, le corps et les en-têtes.

   * Dans v03, le format de rapport est un message de publication avec un en-tête, plutôt que
     d'être analysé différemment. Cette spécification unique s’applique donc aux deux.