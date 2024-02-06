
===============================
Assurer la livraison (inflight)
===============================

Le fait de ne pas établir correctement les protocoles de complétion de fichiers est
une source commune d'incohérences intermittentes, difficile de diagnostiquer.
Pour des transferts de fichiers fiables, Il est essentiel que l'expéditeur et
le destinataire s'entendent sur la façon de représenter un fichier qui n'est pas complet.
L'option *inflight* (c'est-à-dire qu'un fichier est *en vol* entre l'expéditeur et
le destinataire) s´offre pour accommoder différentes situations :


Tableau de Inflight
-------------------

+--------------------------------------------------------------------------------------------+
|                                                                                            |
|            Protocoles d'assurance de la livraison (par ordre de préférence)                |
|                                                                                            |
+-------------+---------------------------------------+--------------------------------------+
|Méthode      |Description                            |Application                           |
+=============+=======================================+======================================+
|             |Fichier envoyé avec le bon nom         |Envoyer à Sarracenia, et              |
| NONE        |message`sr3_post(7) <sr3_post.7.rst>`_ |publié quand le fichier est complet   |
|             |AMQP après que le transfert.           |                                      |
|             |                                       | (Meilleur quand disponible)          |
|             | - moins d´aller-retours               | défaut pour sr_sarra.                |
|             | - plus efficace / vite                | défaut sur sr_subscribe et sender    |
|             |                                       | quand post_broker est spécifié.      |
+-------------+---------------------------------------+--------------------------------------+
|             |avec un suffixe *.tmp*.                |Envoi à la plupart des autres systèmes|
| .tmp        |Lorsqu'il est complet, renommé au fin  |(.tmp intégré)                        |
| (Suffixe)   |Le suffixe réel est réglable.          |Utiliser pour envoyer à Sundew.       |
|             |                                       |                                      |
|             | -voyages aller-retour supplémentaires |(généralement un bon choix)           |
|             |  pour renommer (un peu plus lent)     | - défaut quand il n´y a pas de       |
|             |                                       |   post_broker                        |
+-------------+---------------------------------------+--------------------------------------+
|             |Fichier placés dans un sous-répertoire |Envoi à des systèmes qui n´acceptent  |
| tmp/        |ou répertoire. Déplacé au fin de       |les suffixes                          |
| (subdir)    |transfert                              |                                      |
| /repertoie  |Même performance que Suffixe           |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |la convention Linux pour *masquer* les |Envoi à des systèmes qui n´acceptent  |
| .           |fichiers. renommé au fin de transfert  |les suffixes                          |
| (Préfixe)   |Préfixer les noms par '.'              |                                      |
|             |Même performance que Suffixe           |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Âge minimum (temps de modification)    |Dernier choix, ne garantit un délai   |
| entier      |du fichier avant que le transfer soit  |que si aucun autre moyen peut servir  |
| (mtime)     |considéré Complèté. (fileAgeMin pareil)|                                      |
|             |                                       |Réception de ceux qui ne coopèrent pas|
| fileAgeMin  |Retarde tous les avis                  |                                      |
|             |Vulnérable aux pannes de réseau.       | (choix acceptable pour PDS)          |
|             |Vulnérable aux horloges en désaccord   |                                      |
+-------------+---------------------------------------+--------------------------------------+

Par défaut ( quand aucune option *inflight* n'est donnée), si le post_broker est défini,
alors une valeur de NONE est utilisée parce qu'on suppose qu'elle est livrée à un autre
courtier. S´il n´y a pas de post_broker est définie, la valeur de '.tmp' est supposée être
la meilleure option.

NOTES :

  Sur les versions de sr_sender antérieures à 2.18, la valeur par défaut était AUCUNE, mais
  était documentée par '.tmp''. Pour assurer la compatibilité avec les versions ultérieures,
  il est probablement préférable d'écrire explicitement le réglage *inflight*.

  *inflight* a été renommé de l'ancienne option *lock* en janvier 2017. Pour la compatibilité avec
  les versions plus anciennes, peuvent utiliser *lock*, mais le nom est obsolète.

  L'ancien logiciel *PDS* (qui précède MetPX Sundew) ne supporte que le FTP. Le protocole d'achèvement
  utilisé par *PDS* était d'envoyer le fichier avec la permission 000 dans un premier temps, puis chmod à un fichier
  fichier lisible. Ceci ne peut pas être implémenté avec le protocole SFTP, et n'est pas supporté du tout.
  par Sarracenia.


Erreurs de configuration fréquentes
-----------------------------------

**Réglage de NONE lors de l'envoi à Sundew.**

   Le réglage correct ici est '.tmp'.  Sans cela, presque tous les fichiers passeront correctement,
   mais les dossiers incomplets seront parfois ramassés par Sundew.

**utilisant la méthode mtime pour recevoir de Sundew ou Sarracenia**

   L'utilisation de mtime est un dernier recours. Cette approche injecte du retard
   et ne devrait être utilisée que lorsque qu´on n'a aucune influence
   pour que l'autre extrémité du transfert utilise une meilleure méthode.

   mtime est vulnérable aux systèmes dont les horloges diffèrent (fichiers incomplets).
   mtime est vulnérable aux transferts lents, où les fichiers incomplets peuvent être
   ramassés à cause d'un problème de réseautage interrompant ou retardant les transferts.

**utilisant NONE lors de la livraison à une destination autre que Sarracenia**

   NONE doit être utilisé seulement lorsqu'il existe d'autres moyens de déterminer si un fichier
   est livré. Par exemple, lors de l'envoi à une autre pompe, l'expéditeur informera
   le destinataire le fichier est complet en publiant l´avis à ce courtier après
   sa livraison, il n'y a donc aucun danger d'être ramassé trop tôt.

   Lorsqu'il est mal-utilisé, il arrive que des fichiers incomplets soient traitée
   par la réception.
