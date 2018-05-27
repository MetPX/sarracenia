
=============
 SR_Log2Save 
=============

-------------------------------------
Lire un fichier log pour créé un save 
-------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite

.. contents::

SYNOPSIS
========

 **sr_log2save**


DESCRIPTION
===========

Afin de renvoyer des articles à une destination donnée, on peut récupérer l'avis
pour un fichier donné, avec une entrée de fichier journal standard pour ce fichier.  
*sr_log2save* lit le journal et les écrire dans la sortie standard convertie (json)
dans le fichier enregistrer le format utilisable par *sr_shovel* avec *-restore_to_queue*.


EXEMPLE
-------

exemple::

   cat ~/test/save.conf <<EOT
       
   broker amqp://tfeed@localhost/
   topic_prefix v02.post
   exchange xpublic
    
   post_rate_limit 5
   on_post post_rate_limit 
    
   post_broker amqp://tfeed@localhost/
    
   EOT
    
   sr_log2save <log/sr_sarra_download_0003.log >shovel/save/sr_shovel_save_0000.save
   sr_shovel -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf 


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





