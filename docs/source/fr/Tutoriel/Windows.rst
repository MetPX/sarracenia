===============================
Manuel de l’utilisateur Windows
===============================

.. no section-numbering::

Ce document enseigne aux utilisateurs novices de Python sur Windows comment ils pourraient facilement exécuter Sarracenia de différentes manières.
Les captures d’écran ont été prises à partir de l’édition *Windows Server 2012 R2 Standard*. N’hésitez pas à créer des issues si
vous croyez que ce document pourrait être enrichi d’un (ou de plusieurs) cas important(s).


Exécution de Sarracenia avec une invite de commandes
----------------------------------------------------

Dans le menu Démarrer :
~~~~~~~~~~~~~~~~~~~~~~~
Cliquez sur Sarracenia (il exécutera *sr3.exe redémarrer*):

.. image:: ../../Tutorials/Windows/start-menu-1.png

Cela fera apparaître l’invite de commande de Sarracenia, démarrera les processus Sarracenia comme indiqué par vos configurations et affichera les informations de journalisation.

.. image:: Windows/01_prompt_cmd.png

Gardez cette fenêtre en vie jusqu’à ce que vous en ayez fini avec Sarracenia. Le fermer ou taper ctrl-c tuera tous les
processus Sarracenia. Vous pouvez également redémarrer Sarracenia qui arrêtera ces processus proprement.

À partir d’une session Windows Powershell :
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Lancez une session Powershell |powershell| et tapez cette commande à l’invite ::

 sr3 restart

.. |powershell| image:: Windows/powershell.png

Cela démarrera les processus Sarracenia comme indiqué par vos configurations et affichera les informations de journalisation

.. image:: Windows/02_prompt_powershell.png 

Gardez cette session Powershell en vie jusqu’à ce que vous ayez terminé avec Sarracenia. Pour arrêter Sarracenia, vous pouvez taper::

 sr3 stop

Cela arrêtera tous les processus Sarracenia proprement, comme le ferait un redémarrage. La fermeture de cette fenêtre tuera également tous les processus.

À partir de l’invite Anaconda :
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Exécutez cette commande ::

 activate sr3 && s3r restart

Exécution de Sarracenia sans invite de commandes
------------------------------------------------

Voici un cas où quelqu’un (comme un administrateur de système) doit exécuter Sarracenia sans invite de commande et
s’assurer que le système démarre au démarrage de Windows.
La façon évidente de le faire serait à partir du Planificateur de tâches.

À partir du Planificateur de tâches :
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ouvrez le Planificateur de tâches :

.. image:: Windows/03_task_scheduler.png

Sélectionnez *Créer une tâche de base...* dans le panneau d’action à droite :

.. image:: Windows/04_create_basic_task.png

Cela lancera *l’assistant de création de tâche de base* où vous ...

 Remplissez le nom :

 .. image:: Windows/05_fill_the_name.png

 Choisissez le déclencheur :

 .. image:: Windows/06_choose_trigger.png

 Choisissez l’action :
 
 .. image:: Windows/07_choose_action.png
 
 Définissez l’action :
 
 .. image:: Windows/08_define_action.png
 
 Passez en revue la tâche et choisissez *Terminer* :
 
 .. image:: Windows/09_finish.png

Ouvrez la boîte de *dialogue propriétés* et choisissez *Exécuter, que l’utilisateur soit connecté ou non* et
*Exécuter avec les privilèges les plus élevés* :
 
.. image:: Windows/10_properties_dialog.png

La tâche doit maintenant apparaître dans votre *Bibliothèque du Planificateur de tâches* avec l’état *Prêt*.

.. image:: Windows/12_task_scheduler_ready.png

Ensuite, vous pouvez l’exécuter immédiatement avec le bouton |run_action| .

.. |run_action| image:: Windows/run_action.png
