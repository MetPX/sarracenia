========================
Réassemblage de fichiers
========================

Composants
----------

**sr_watch:** Vous pouvez utiliser sr_watch pour surveiller un répertoire pour les fichiers
de partition entrants (.Part) de sr_subscribe ou sr_sender, les deux ont la possibilité d’envoyer
un fichier dans des partitions. Dans le fichier de configuration pour sr_watch les paramètres
importants à inclure sont les suivants :

- chemin <chemin du répertoire à surveiller>
		- on_part /usr/lib/python3/dist-packages/sarra/plugins/part_file_assemble.py
		- accept \*.Part
		- accept_unmatch False # Fait qu’il ne fait qu’acccepter le modèle ci-dessus

**Part_File_Assemble (plugin):** Ce plugin est un plugin on_part qui déclenche le code assembleur dans **sr_file**

**sr_file:** Contient le code de réassemblage... L’algorithme est décrit ci-dessous


Algorithme
----------

Après avoir été déclenché par un fichier de pièce téléchargé :

 - si le target_file n’existe pas :

    - si le fichier de pièce téléchargé était la première partition (partie 0) :

        - créer un nouveau target_file vide

- trouver quel numéro de partition doit être inséré ensuite (i)

 - while i < Nombre total de blocs:
 
     - file_insert_part()
     
         - insère la part du fichier dans le fichier cible et calcule la somme de contrôle de la partie insérée

     - vérifier l’insertion en comparant les sommes de contrôle du fichier de partition et du bloc inséré dans le fichier
     - supprimer le fichier si vous êtes d’accord, sinon réessayer
     - déclencher on_file

Test
----

Créer un fichier de configuration sr_watch selon le modèle ci-dessus.
Démarrez le processus en tapant la commande suivante : ```sr_watch foreground path/to/config_file.cfg```

Ensuite, créez un fichier de configuration d’abonné et incluez ```inplace off``` afin que le fichier
soit téléchargé en plusieurs parties.
Démarrez l’abonné en tapant ```sr_subscribe foreground path/to/config_file.cfg```

Maintenant, vous devez envoyer des messages de publication du fichier pour l’abonné,
par exemple: ```./sr_post.py -pb amqp://tsource@localhost/ -pbu sftp://<user>@localhost/ -p /home/<user>/test_file -px xs_tsource  --blocksize 12M```


