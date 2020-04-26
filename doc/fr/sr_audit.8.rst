
==============
 SR_Audit 
==============

-------------------------------------
Vérifier La Configuration d´une Pompe
-------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite

.. contents::

SYNOPSIS
========

 **sr_audit** configfile foreground|start|stop|restart|reload|status

 **sr_audit** --pump  foreground configfile

 **sr_audit** --users foreground configfile

DESCRIPTION
===========


Sr_audit est un démon qui s'exécute périodiquement pour examiner ce qui est
en cours d'exécution sur un système pour résoudre les problèmes qu'il voit.
Lorsqu'il est exécuté en tant qu'utilisateur non administrateur, il 
recherche les composants dont les fichiers d'état indiquent qu'ils sont 
en cours d'exécution, mais dont il manque au processus correspondant.  Il
les redémarre. N'importe lequel en cours d'exécution devrait écrire au 
moins un message Heartbeat de temps à autre dans son journal.  Donc,
si le fichier journal est trop ancien, le composant sera présumé gelé 
et redémarré.

Lorques qu´il est parti par un administrateur, Sr_audit configure un courtier
pour refléter les configurations de Sarracenia.  **Sr_audit** prend un 
argument : l'action à effectuer.  On peut aussi régler quelques options dans un
fichier de configuration : **debug**, **max_queue_size**.

Lorsque **Sr_audit** est démarré (avec *start*), il se connecte au courtier en 
utilisant le compte **admin**.  Il dort le temps nécessaire pour déclencher
le prochain battement de cœur.

Le comportement par défaut de **sr_audit** est de gérer et de contrôler les files 
d'attente sur le courtier. Les files d'attente sont validées et supprimées s'il n'y 
a pas de client qui y est connecté et qu'il y en a plus que **max_queue_size** 
messages en attente ou S'il y a des files d'attente ou des échanges qui ne sont pas 
conformes aux conventions de nommage de sarracenia (les noms de file d'attente commencent 
par **q_"brokerusername"** où "brokerusername" est un utilisateur valide sur le courtier).

Lors de la configuration d'une pompe, il existe d'autres façons d'utiliser **sr_audit**.
Lorsque **sr_audit** est invoqué avec **--pompe**, cela aide à configurer la pompe.
Lorsqu'il est invoqué avec **--utilisateurs**, le programme gère les utilisateurs, 
les permissions et les échanges.


CONFIGURATION
=============

En général, les options de cette composante sont décrites dans le manuel de l
`sr_subscribe(1) <sr_sr_subscribe.1.rst>`_ page qui doit être lue en premier.
Il explique en détail la langue de configuration de l'option, et comment trouver
les paramètres de l'option.

Il y a très peu d'options que **sr_audit** utilise :


- **admin          <user>    (OBLIGATOIRE: broker admin user, detailed in credentials.conf)**

- **debug          <booléen> (default: False)**

- **reset          <booléen> (default: False)**

- **set_passwords  <booléen> (default: True)**

- **max_queue_size <int>     (default: 25000 nbr messages in queue)**

- **dry_run  <booléen> (default: False)**

L'option **admin** doit être définie, elle est normalement définie dans le fichier **default.conf**.
et les détails de l'accréditation se trouveraient dans le fichier **credentials.conf**.
Normalement, lors de la création des utilisateurs, les mots de passe 
pour les communications avec le courtier sont définis par les valeurs 
trouvées dans le fichier d'informations d'identification ( *credentials.conf* )

Lorsque l'option *reset* est donnée, les mots de passe et permissions des 
utilisateurs seront réinitialisés à leur valeurs attendues.  
Normalement, les permissions d'un utilisateur existant sont 
laissées intactes par un audit.

L'option *dry_run* permet de voir ce que va faire **sr_audit**, sans
éffectuer de changement sur le courtier. 

VÉRIFIER LES RÉGLAGES DE LA POMPE
=================================

Utilisez **sr_audit** invoquer avec **--pump** pour valider sa configuration.  
Il s'assure que l'utilisateur **feeder**, et **admin** sont définis et valides.  

**sr_audit** s'assure que les utilisateurs configurés dans les configurations 
sarracenia sont présents sur le broker. Les utilisateurs manquants sont ajoutés.... 
avec les permissions requises pour leur rôle. Utilisateurs supplémentaires,
non configurés dans Sarracenia, sont supprimés. 

Pour vérifier les échanges des utilisateurs, **sr_audit** obtient la liste des 
échanges présentes sur le courtier.  A partir des utilisateurs et des rôles, **sr_audit** 
détermine les échanges qui devraient être présents et crée ceux qui manquent.
Les échanges supplémentaires sont supprimés si leur nom ne commence pas par'x'.

Lors de l'ajout ou de la suppression d'un utilisateur, l'administrateur du courtier 
ajoute ou supprime la déclaration de rôle d'un utilisateur dans le 
fichier **default.conf.**  Puis il lance **sr_audit --users foreground configfile**.
La sortie standard du journal indiquerait à l'administrateur quelles sont les 
ressources de courtiers ajouté/supprimé (utilisateur, échanges, file d'attente, etc.).




AUSSI VOIR
==========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés.

`sr_shovel(8) <sr_shovel.8.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(8) <sr_winnow.8.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - messages de rapport de processus.

`sr_post(1) <sr_post.1.rst>`_ - publier les avis de fichiers.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Outil pour S´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.


