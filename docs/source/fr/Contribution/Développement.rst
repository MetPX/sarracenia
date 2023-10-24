=====================================
Guide du développeur MetPX-Sarracenia
=====================================

:version: |release|
:date: |today|


Outillage
---------

Pour pirater la source Sarracenia, vous avez besoin de:

- Un environnement de développement Linux, soit un poste de travail, soit une machine virtuelle quelconque.
  La configuration à l’aide d’Ubuntu est automatisée, mais un ajustement pour d’autres distributions est possible.
  Le confort en ligne de commande est un must.

- python3. L’application est développée en Python et dépend des versions python >= 3.5.

- style: PEP8 sauf que la longueur maximale de la ligne est de 119, appliquée via
  `pycodestyle <https://pycodestyle.pycqa.org/en/latest/intro.html#disclaimer>`_
  pour VSCode, yapf3 ou un autre outil similaire.

- Un compte sur github.com aidera à soumettre des patches.

Les éléments qui seront installés par configuration automatisée :

- un tas d’autres modules python indiqués dans les dépendances (setup.py ou debian/control)

- Module Pyftpdlib python3, utilisé pour exécuter un serveur ftp sur un port élevé pendant le test de flux.

- git. afin de télécharger la source à partir du dépôt GitHub, et de préparer et soumettre
  changements.

- Un courtier RabbitMQ dédié, avec accès administratif, pour exécuter les tests sr_insects.
  Ceci est installé par des outils automatisés pour configurer l’environnement Linux.
  Le test de flux crée et détruit les échanges et perturbera tous les flux actifs sur le courtier.

après avoir cloné le code source::

    git clone -b development https://github.com/MetPX/sarracenia sr3
    git clone -b development https://github.com/MetPX/sarrac metpx-sr3c
    git clone https://github.com/MetPX/sr_insects insects
    cd sr3

Le reste du guide suppose que vous y êtes.

Documentation
-------------
`Normes de documentation <Documentation.rst>`_ existent dans /docs/Contribution/Documentation.rst.
Le processus pour la construction locale des documents sont là, ainsi que les méthodes
de maintenance du site Web en direct.

Où documenter les options
~~~~~~~~~~~~~~~~~~~~~~~~~

Les options sont documentées dans le style de dictionnaire sr3_options(7) par ordre alphabétique.
Si cela en valait la peine, des exemples d’utilisation pourraient être ajoutés à d’autres guides.

Développement
-------------

En général, le flux de travail de développement consiste à obtenir un ordinateur portable ou une machine
virtuelle où l’on peut exécuter les flow_tests (disponible auprès de http://github.com/MetPX/sr_insects ).
La première étape lors de la configuration d’un environnement de développement s’agit de s’assurer que les
tests de flux sr_insects fonctionnent, car ils fonctionnent comme une porte d’entrée pour les commits
dans les branches importantes.

Le développement est le plus souvent effectué sur la plate-forme Ubuntu > = 18.04.

Flux de travail v2
~~~~~~~~~~~~~~~~~~
Le travail de développement terminé pour la version 2 est engagé sur la branche v2_dev, qui est utilisée
pour produire des instantanés quotidiens. On ne devrait normalement pas engager de changements dans la
direction v2_dev, mais plutôt les fusionner à partir d’une branche de travail.

Les directions générales du développement sont nommées d’après la question qu’elles sont censées aborder
"v2_issue365", par exemple. S’il y a plusieurs tentatives pour résoudre un problème donné, utilisez le problème
comme préfixe de nom. Par exemple, il pourrait y avoir issue365, mais si nous décidons que ce n’est pas
une bonne façon d’aborder le problème, il pourrait y avoir une direction issue365_methodB.

**Avant de soumettre une demande d’extraction (Pull Request, PR), veuillez vous assurer que les tests de flow de
sr_insects ont été exécutés avec succès : au moins static_flow, flakey_broker et dynamic_flow**

Lorsqu’un PR est généré, le deuxième développeur peut l’examiner pour détecter des préoccupations.
Une fois satisfait de la nature du correctif, le deuxième développeur doit retirer la branche
et exécutez à nouveau les tests de flux (les trois mêmes) pour confirmer.  Seulement après que les tests de flux
ont été exécutés sur plusieurs machines qu'on peut ensuite fusionner avec main.

Les problèmes propres à la v2 doivent être étiquetés *v2only*.
sur Launchpad.net :

* Les paquets de référentiel quotidiens de v2 seront construits à partir de v2_dev

* Les paquets de référentiel de pré-version de v2 seront construits à partir de v2_dev

* Les packages de référentiel de versions sont générés à partir de v2_stable.


Flux de travail v3
~~~~~~~~~~~~~~~~~~

La prochaine version de Sarracenia est développée dans la branche development (travail en cours).
Comme la refactorisation majeure est pratiquement terminée, le travail restant est maintenant entièrement constructif
et tout le développement est coordonné par des issues exactement comme l’est la V2. Les problèmes propres à la v3
sont les régressions ou améliorations qui n’ont pas de sens à ajouter à v2, ont la balise *v3only*.
Les problèmes communs entre les versions sont marqués *v3*.

Le flux de travail avec v3 est similaire à v2 mais avec des branches différentes. 
Avoir tous les tests de flux
complétés avec assez de succès est un des critères d’acceptation dans development.

Pour exécuter les tests sr_insects, le référentiel doit être cloné avec la branche development.
Une porte pour la fusion à development est pour un deuxième développeur d’exécuter le flow_tests.
**Pour la v03, ces tests doivent exécuter : static_flow, flakey_broker, dynamic_flow, transform_flow**

Prévu d’ici le 11/04/2022 :

* Main sera fusionné à partir de development, donc la branche par défaut pour les nouveaux arrivants sera SR3.

* Launchpad aura de nouvelles recettes pour produire des paquets SR3 à partir de la branche principale.


sr_insects
~~~~~~~~~~

Le référentiel sr_insects a sa propre base de données de problèmes, et le travail sur sr_insects est encouragé.
Les versions 2 et 3 sont prises en charge sur la branche principale de sr_insects.  Cette branche devrait être
utilisé pour prendre en charge tout le développement dans les deux versions....

Installation locale
-------------------

Il existe de nombreuses façons d’installer des paquets python sur un ordinateur. Différents développeurs
préféreront différentes méthodes, et toutes les méthodes doivent être testées avant chaque version.
Avant d´installer le paquet il faut généralement une librarie pour communiquer avec le courtier
de messages (généralement rabbitmq/AMQP, mais ca peut être MQTT également)

* **Wheel** Lorsque les gens utilisent différents systèmes d’exploitation (non-Ubuntu, non-Debian),
  les gens installent des wheel, généralement qui ont été téléchargées sur pypi.python.org.  D’un
  autre côté, c’est un peu pénible / bruyant de télécharger chaque version de développement, donc
  nous ne téléchargeons que des versions, donc les tests de wheel se font en construisant des roues
  locales. Besoin de construire une nouvelle wheel chaque fois qu’un changement est apporté.
  *pip install amqp* sera également nécessaire pour le support rabbitmq.

* **pip install (pas -e)** tirerait une wheel vers le bas de pypi.python.org. Généralement pas utilisé
  pendant le développement de Sarracenia lui-même.
  *pip install amqp* sera également nécessaire pour le support rabbitmq.

* **pip install -e** ... vous permet de modifier le code source du package installé, idéal pour les
  problèmes de débogage, car il permet des modifications en direct de l’application sans avoir à passer
  par la construction et l’installation d’un nouveau package.
  *pip install amqp* sera également nécessaire pour le support rabbitmq.

* **apt install** installer le paquet Debian à partir de dépôts, de la même manière que pip install (pas -e),
  normalement les instantanés de développement ne sont pas téléchargés vers des dépôts, donc bien que ce soit
  la manière normale pour les utilisateurs de serveurs Ubuntu, il n’est pas disponible pendant le développement
  du paquet lui-même.
  *apt install python3-amqp* sera également nécessaire pour le support rabbitmq.

* **dpkg -i** construit un paquet Debian pour l’installation locale. C’est ainsi que les packages sont testés
  avant d’être téléchargés vers des référentiels.  Il peut également être utilisé pour soutenir le développement
  (il faut exécuter dpkg -i pour chaque changement de paquet).
  *apt install python3-amqp* sera également nécessaire pour le support rabbitmq.

Le test sr_insects appelle la version de metpx-sarracenia installée sur le système,
et non ce qui est dans l’arbre de développement.  Il est nécessaire d’installer le paquet sur
le système afin qu’il exécute les tests sr_insects.


Préparer une machine virtuelle Vanilla
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cette section décrit la création d’un environnement de test à utiliser dans un ordinateur virtuel. Une façon de
construire une machine virtuelle est d'utiliser Multipass (https://multipass.run) En supposant que ce soit
installé, on peut crée une machine virtuelle avec ::

 multipass launch -m 8G -d 30G --name flow

Vous devez faire fonctionner SSH LocalHost dans le conteneur MultiPass.  Peut le faire en copiant la clé privée
multipasse dans le conteneur::

 fractal% multipass list                                                         
 Name                    State             IPv4             Image
 primary                 Stopped           --               Ubuntu 20.04 LTS
 flow                    Running           10.23.119.56     Ubuntu 20.04 LTS
 keen-crow               Running           10.23.119.5      Ubuntu 20.04 LTS
 fractal% 

Problèmes étranges avec les clés ssh qui ne sont pas interprétées correctement par paramiko, solution de contournement,
( https://stackoverflow.com/questions/54612609/paramiko-not-a-valid-rsa-private-key-file )
::

 fractal% sudo cat /var/snap/multipass/common/data/multipassd/ssh-keys/id_rsa | sed 's/BEGIN .*PRIVATE/BEGIN RSA PRIVATE/;s/END .*PRIVATE/END RSA PRIVATE/' >id_rsa_container
 chmod 600 id_rsa_container
 scp -i id_rsa_container id_rsa_container ubuntu@10.23.119.175:/home/ubuntu/.ssh/id_rsa
                                                                   100% 1704     2.7MB/s   00:00    

 fractal% scp -i id_rsa_container id_rsa_container ubuntu@10.23.119.106:/home/ubuntu/.ssh/id_rsa
 The authenticity of host '10.23.119.106 (10.23.119.106)' can't be established.
 ECDSA key fingerprint is SHA256:jlRnxV7udiCBdAzCvOVgTu0MYJR5+kYzNwy/DIhkeD8.
 Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
 Warning: Permanently added '10.23.119.106' (ECDSA) to the list of known hosts.
 id_rsa_container                                                                                                                         100% 1712     9.4MB/s   00:00    
 fractal% multipass shell flow
 Welcome to Ubuntu 20.04.3 LTS (GNU/Linux 5.4.0-81-generic x86_64)
 
  * Documentation:  https://help.ubuntu.com
  * Management:     https://landscape.canonical.com
  * Support:        https://ubuntu.com/advantage
 
   System information as of Fri Aug 27 21:12:16 EDT 2021
 
   System load:  0.42              Processes:             112
   Usage of /:   4.4% of 28.90GB   Users logged in:       0
   Memory usage: 5%                IPv4 address for ens4: 10.23.119.106
   Swap usage:   0%
 
 
 1 update can be applied immediately.
 To see these additional updates run: apt list --upgradable
 
 
 To run a command as administrator (user "root"), use "sudo <command>".
 See "man sudo_root" for details.
 
 ubuntu@flow:~$ 

Invitez ensuite SSH à accepter la clé localhost::

 ubuntu@flow:~$ ssh localhost ls -a
 The authenticity of host 'localhost (127.0.0.1)' can't be established.
 ECDSA key fingerprint is SHA256:jlRnxV7udiCBdAzCvOVgTu0MYJR5+kYzNwy/DIhkeD8.
 Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
 Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
 .
 ..
 .bash_logout
 .bashrc
 .cache
 .profile
 .ssh
 ubuntu@flow:~$ 


Cela fournira un shell dans une machine virtuelle initialisée.  Pour le configurer::

 
  git clone -b development https://github.com/MetPX/sarracenia sr3
  cd sr3

Il existe des scripts qui automatisent l’installation de l’environnement nécessaire pour pouvoir exécuter des tests::

  travis/flow_autoconfig.sh
  travis/add_sr3.sh

ous devriez pouvoir voir une configuration vide::

  sr3 status

SR3C et SR3 sont maintenant installés et devraient être prêts à exécuter un test de débit à partir du module
sr_insects, qui a également été cloné ::

  cd ../sr_insects

La branche v03 de sr_insects prend en charge les tests des versions 2 et 3, et les deux versions sont maintenant
installées. Les tests de flux sont destinés à être exécutés pour confirmer la compatibilité entre v2 et v3,
et donc doivent également pouvoir tester la V2 ::

  ubuntu@flow:~/sr_insects$ dpkg -l | grep metpx
  ii  metpx-libsr3c                    3.21.08a1-0~202108270410~ubuntu20.04.1 amd64        C-Implementation of a Sarracenia Client
  ii  metpx-sarracenia                 2.21.08-0~202108241854~ubuntu20.04.1   all          Directory mirroring in real-time for users, file servers and web sites.
  ii  metpx-sr3                        3.00.008exp                            all          v3 Directory mirroring in real-time for users, file servers and web sites.
  ii  metpx-sr3c                       3.21.08a1-0~202108270410~ubuntu20.04.1 amd64        C-Implementation of a Sarracenia Client
  ubuntu@flow:~/sr_insects$ 

Le paquet v2 est metpx-sarracenia, tandis que le paquet v3 est metpx-sr3. Les tests de débit détecteront
quelle version est installée et testera v3 si les deux sont présents.  Pour remplacer cela ::

  ubuntu@flow:~/sr_insects$ export sarra_py_version=2.21.08
  ubuntu@flow:~/sr_insects$ 

Ensuite, on peut exécuter flow_tests à partir de ce shell normalement.

Python Wheel
~~~~~~~~~~~~

Si vous n’avez pas utilisé add_sr3.sh (qui construit un paquet debian), alors on peut utiliser cette procédure
Pour une installation locale sur un ordinateur avec un Python Wheel pour les tests et le développement::

    python3 setup.py bdist_wheel

ou... Sur les systèmes plus récents, utilisez build à la place ::

    python3 -m build --no-isolation

Doit construire un Wheel dans le sous-répertoire dist.
Ensuite, en tant que root, installez ce nouveau paquet::

       pip3 install --upgrade ...<path>/dist/metpx*.whl

Pip install locale
~~~~~~~~~~~~~~~~~~

Pour une installation locale sur un ordinateur, à l’aide d’un pip.
Pour les tests et le développement::

   pip3 install -e .
   export PATH=${HOME}/.local/bin:${PATH}

Utilisation du programme d’installation du package python local (PIP) pour créer une version modifiable localement.
Le code en dessus installera le paquet dans ~/.local/bin... Il faut donc s’assurer que le chemin comprend
ce répertoire.

Debian/Ubuntu
~~~~~~~~~~~~~

Pour une installation locale sur un ordinateur, en utilisant un paquet debian.
Ce processus construit un .deb local dans le répertoire parent en utilisant les mécanismes Debian standard.

* Vérifiez la ligne **build-depends** dans *debian/control* pour les dépendances qui pourraient être nécessaires
  pour construire à partir de source.
* Les étapes suivantes feront un build de sarracenia mais ne signeront pas les modifications ou le paquet source ::

    cd metpx/sarracenia
    sudo apt-get install devscripts
    debuild -uc -us
    sudo dpkg -i ../<the package just built>

qui accomplit la même chose en utilisant l’empaquetage Debian.
Les options sont détaillées ci-dessous :


Commit de Code
~~~~~~~~~~~~~~

Que faut-il faire avant de s’engager dans la branche principale?
Liste de contrôle:

- faire du développement sur une autre branche. Habituellement, la branche sera nommée d’après le problème
  adressée. Exemple : issue240. Si nous abandonnons une approche initiale et en commençons une autre,
  il peut y avoir issue240_2 pour une deuxième tentative. Il peut également y avoir des branches de fonctionnalités,
  telles que v03.
- **Les tests sr_insects fonctionnent** (Voir Tests) La branche principale doit toujours être fonctionnelle,
  ne validez pas de code si les tests sr_insects ne fonctionnent pas.
- Conséquence naturelle : si les changements de code signifient que les tests doivent changer, incluez le
  changement de test dans le commit.
- **Mettre à jour la doc/** Les pages de manuel devraient idéalement recevoir leurs mises à jour en même temps
  que le code.

Habituellement, il y aura beaucoup de cycles de ce type sur une branche de développement avant que l’un d’eux
ne soit prêt à émettre une pull request. Finalement, nous arrivons à `Commits vers la branche principale`_

Description des Tests sr_insects
--------------------------------

Avant de valider du code dans la branche principale, en tant que mesure d’assurance qualité, il faut exécuter
tous les autotests disponibles. On suppose que les modifications spécifiques apportées au code ont déjà passé
les tests unitaires. Veuillez ajouter des autotests appropriés à ce processus pour refléter les nouveaux.
D’une manière générale, il faut résoudre les problèmes au premier test qui échoue parce que chaque test
est plus compliqué que le précédent.

Il existe un dépôt git séparé contenant les tests les plus complexes https://github.com/MetPX/sr_insects

Un flux de travail de développement typique sera (N’essayez pas ceci, ceci est juste un aperçu des étapes qui seront
expliqué en détail dans les sections suivantes) ::

   git branch issueXXX
   git checkout issueXXX
   cd sarra ; *make coding changes*
   cd ..
   debuild -uc -us
   cd ../sarrac
   debuild -uc -us
   sudo dpkg -i ../*.deb
   cd ..

   git clone -b development https://github.com/MetPX/sr_insects
   cd sr_insects
   sr3 status  # make sure there are no components configured before you start.
               # test results will likely be skewed otherwise.
   for test in unit static_flow flakey_browser transform_flow dynamic_flow; do
      cd $test
      ./flow_setup.sh  # *starts the flows*
      ./flow_limit.sh  # *stops the flows after some period (default: 1000) *
      ./flow_check.sh  # *checks the flows*
      ./flow_cleanup.sh  # *cleans up the flows*
      cd ..
   done

   #assuming all the tests pass.
   git commit -a  # on the branch...


Unit
~~~~

Le test *unitaire* dans sr_insects est le plus court qui prend environ une minute et ne nécessite
pas beaucoup de configuration. Ce sont des tests de santé mentale du comportement du code. Prend
généralement une minute ou deux sur un ordinateur portable.

Static Flow
~~~~~~~~~~~

Les tests *static_flow* sont un peu plus compliqués, testant plus de composants, utilisant un seul
composants monothread de manière linéaire (toutes les données avancent uniformément.) Il devrait être
plus simple pour identifier les problèmes car il n’y a pas de suppression et donc cela se prête bien
à répéter des tests de sous-ensembles pour identifier les problèmes individuels. Cela prend environ
deux minutes sur un ordinateur portable.

Flakey Broker
~~~~~~~~~~~~~

Les tests *flakey_broker* sont les mêmes que les *static_flow*, mais ralentis de sorte qu’ils durent
quelques minutes de plus, et le courtier est arrêté et redémarré pendant que la publication se produit.
Notez que post_log imprime avant qu’un message de notification ne soit publié (parce que post_log est
un plugin on_post, et cette action, permet de modifier le message de notification, donc il doit être
avant que la publication ne se produise réellement.)


Dynamic Flow
~~~~~~~~~~~~

Le test *dynamic_flow* ajoute des fonctionnalités avancées : multi-instances, le composant winnow,
les tests logiques de nouvelle tentative, et inclut également les suppressions de fichiers. La majeure
partie de la documentation ici fait référence à l’exécution du dynamic_flow test, car c’est le plus
compliqué, et l’ancêtre des autres.  Le test unitaire a été séparé du début du test dynamic_flow,
et le static_flow est une version simplifiée du test de flux original.

D’une manière générale, il convient d’exécuter les tests en séquence et de s’assurer que les résultats des tests
antérieurs soient sont bons avant de passer aux tests suivant.

Notez que le système de développement doit être configuré pour que les tests sr_insects s’exécutent correctement.
Voir la suite pour les instructions de configuration. Pour le développement avec une nouvelle installation du
système d’exploitation, les étapes de configuration ont été automatisées et peuvent être appliquées avec le
flow_autoconfig.sh dans sr_insects (https://github.com/MetPX/sr_insects/blob/main/flow_autoconfig.sh).
L'exécution à l’aveugle de ce script sur un système fonctionnel peut entraîner des effets secondaires
indésirables; vous êtes prévenus !



La configuration que l’on essaie de répliquer :

.. image:: ../../Contribution/Development/Flow_test.svg

Le tableau suivant décrit ce que fait chaque élément du test de flux dynamique, et la couverture
du test montre les fonctionnalités couvertes.

+-------------------+--------------------------------------+-------------------------------------+
|                   |                                      |                                     | 
| Configuration     | Fait                                 | Couverture du test                  |
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| subscribe t_ddx   | copy from data mart to local broker  | lit le data mart public amqps (v02) |
|                   | posting notification messages to     | comme utilisateur ordinaire.        |
|                   | local xwinno00 and xwinnow01         |                                     |
|                   | exchanges.                           | fil d'attente partagé et plusieurs  |
|                   |                                      | processus                           |
|                   |                                      | 3 instances téléchargent de chaque q|
|                   |                                      | poster amqp à un échange local (v02)|
|                   |                                      | en tant qu'utilisatuer feeder       |
|                   |                                      | (admin)                             |
|                   |                                      | post_exchangeSplit à xwinnow0x      |
+-------------------+--------------------------------------+-------------------------------------+
| winnow t0x_f10    | traitement winnow qui publie pour    | Lire l’AMQP v02 local               |
|                   | l'échange xsarra pour le             | en tant qu’utilisateur de feeder.   |
|                   | téléchargement.                      |                                     |
|                   |                                      | Fonction de mise en cache complète  |
|                   | Comme deux sources identiques        | (Winnow)                            |
|                   | seulement la moitié des messages de  | post amqp v02 à l'échange local.    |
|                   | notifications sont postés au suivant |                                     |
+-------------------+--------------------------------------+-------------------------------------+
| sarra download    | Téléchargez les données Winnowed à   | Lire l’AMQP v02 local  (xsarra)     |
| f20               | partir du répertoire local data mart |                                     |
|                   | (TESTDOCROOT= ~/sarra_devdocroot)    | Télécharger à l’aide de Python      |
|                   |                                      | intégré                             |
|                   | Ajouter un en-tête au niveau de la   | fil d'attente partagé et plusieurs  |
|                   | couche d'application plus de 255     | processus                           |
|                   | caractères.                          | 5 instances téléchargent de chaque q|
|                   |                                      | télécharge avec accel_wget plugin   |
|                   |                                      |                                     | 
|                   |                                      | Troncature d’en-tête AMQP lors de   |
|                   |                                      | la publication.                     |
|                   |                                      | post amqp v02 à xpublic             |
|                   |                                      | en tant qu’utilisateur feeder       |
|                   |                                      | téléchargements HTTP depuis localhst|
+-------------------+--------------------------------------+-------------------------------------+
| subscribe t       | Télécharge en tant que client à      | lire amqp du courtier local         |
|                   | partir de localhost au repertoire    | en tant qu'utilisatuer/client       |
|                   | downloaded_by_sub_t.                 | ordinaire.                          |
|                   |                                      | fil d'attente partagé et plusieurs  |
|                   |                                      | processus                           |
|                   |                                      | 5 instances téléchargent de chaque q|
+-------------------+--------------------------------------+-------------------------------------+
| watch f40         | regarder downloaded_by_sub_t         | client v03 post du fichier local.   |
|                   | Publier chaque fichier qui y apparaît| (fichier: url)                      |
|                   |                                      |                                     | 
|                   | Plafond de mémoire réglé bas         | Redémarrage automatique au plafond  |
|                   |                                      | de la mémoire.                      |
+-------------------+--------------------------------------+-------------------------------------+
| sender            | lire fichier local, envoyer via sftp | client consomme des messages de     |
| tsource2send      | au répertoire sent_by_tsource2send   | notification v03                    |
|                   |                                      | Le consommateur lit le fichier local|
|                   | Publier sur xs_tsource_output        |                                     |
|                   |                                      | envoyer via sftp.                   |
|                   |                                      |                                     | 
|                   |                                      | plugin replace_dir                  | 
|                   |                                      |                                     | 
|                   |                                      | Affichage de l’URL sftp.            |
|                   |                                      | Post V02 (reconversion de V03.)     |
|                   |                                      |                                     | 
|                   |                                      | option test post_exchange_suffix.   |
+-------------------+--------------------------------------+-------------------------------------+
| subscribe         | Télécharger via sftp à partir de     | Téléchargement SFTP client.         |
| u_sftp_f60        | localhost en plaçant les fichiers    |                                     |
|                   | dans le répertoire                   | accel_sftp plugin.                  |
|                   | downloaded_by_sub_u                  |                                     |
+-------------------+--------------------------------------+-------------------------------------+
| post test2_f61    | Publier des fichiers dans            | Affichage explicite de fichiers     |
|                   | sent_by_tsource2send avec des URL    |                                     |
|                   | FTP dans l'échange xs_tsource_poll   | Publication d’URL ftp.              |
|                   |                                      |                                     | 
|                   | (Wrapper Script appelle post)        | option post_exchange_suffix         |
+-------------------+--------------------------------------+-------------------------------------+
| poll f62          | poller le répertoire                 | polling                             |
|                   | sent_by_tsource2send                 |                                     |
|                   | publication d’URL de téléchargement  |option post_exchange_suffix          |
|                   | sftp                                 |                                     |
+-------------------+--------------------------------------+-------------------------------------+
| subscribe ftp_f70 | Abonnez-vous aux publications        | Téléchargement d’URL FTP.           |
|                   | test2_f61 FTP.                       |                                     |
|                   | Télécharger des fichiers depuis      |                                     |
|                   | localhost au répertoire              |                                     |
|                   | downloaded_by_sub_u                  |                                     |
+-------------------+--------------------------------------+-------------------------------------+
| subscribe q_f71   | s’abonner au sondage, téléchargement | Confirmation de la qualité du poste |
|                   | sur recd_by_srpoll_test1             | de poll                             |
+-------------------+--------------------------------------+-------------------------------------+
| shovel pclean f90 | Nettoyez les fichiers pour qu’ils ne | fonction shovel.                    |
|                   | s’accumulent pas                     |                                     |
|                   | Simule les échecs pour forcer des    |                                     |
|                   | nouvelles tentatives                 | Logique de nouvelle tentative.      |
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| shovel pclean f91 | Nettoyez les fichiers pour qu’ils ne | shovel avec posting v03             |
|                   | s’accumulent pas                     |                                     |
|                   |                                      | Logique de nouvelle tentative.      |
+-------------------+--------------------------------------+-------------------------------------+
| shovel pclean f92 | Nettoyez les fichiers pour qu’ils ne | shovel avec consommation v03        |
|                   | s’accumulent pas                     |                                     |
|                   |                                      | posting v02.                        | 
|                   |                                      |                                     | 
|                   |                                      | Logique de nouvelle tentative.      |
+-------------------+--------------------------------------+-------------------------------------+

Hypothèse: l’environnement de test est un PC Linux, soit un ordinateur portable/de bureau, soit un serveur sur lequel on
peut démarrer un navigateur. Si vous travaillez également avec l’implémentation C, il existe également les éléments suivants
Flux définis :

.. image:: ../../Contribution/Development/cFlow_test.svg

   
Exécution de tests de Flux
--------------------------

Cette section documente ces étapes de manière beaucoup plus détaillée.
Avant de pouvoir effectuer les tests sr_insects, certaines conditions préalables doivent être prises en compte.
Notez qu’il existe une intégration Github Actions pour au moins la branche principale
pour vérifier la fonctionnalité sur une variété de versions de Python.  Consulter::

   https://github.com/MetPX/sarracenia/actions

.. Note::

  Pour les derniers résultats des tests. Notez que les résultats incluent des dizaines
  de tests et sont peu fiables, il peut généralement falloir quelques tentatives pour
  que cela fonctionne complètement (3 ou 4 échouent après la tentative initiale, puis
  réexécutez les échecs, puis peut-être un ou deux resteront, et le troisième passe, et le dernier passe.)

Installer des serveurs sur un poste de travail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour préparer un ordinateur à exécuter le test de flux, il faut installer des logiciels et des
configurations serveur. Ce même travail est effectué par travis/flow_autoconfig.sh
qui est exécuté dans `Préparer une machine virtuelle Vanilla`_ mais si vous devez le configurer
manuellement, voici le processus.

Installez un courtier localhost minimal et configurez les utilisateurs de test rabbitmq ::

    sudo apt-get install rabbitmq-server
    sudo rabbitmq-plugins enable rabbitmq_management

    mkdir ~/.config/sarra
    cat > ~/.config/sarra/default.conf << EOF
    declare env FLOWBROKER=localhost
    declare env MQP=amqp
    declare env SFTPUSER=${USER}
    declare env TESTDOCROOT=${HOME}/sarra_devdocroot
    declare env SR_CONFIG_EXAMPLES=${HOME}/git/sarracenia/sarra/examples
    EOF

    RABBITMQ_PASS=S0M3R4nD0MP4sS
    cat > ~/.config/sarra/credentials.conf << EOF
    amqp://bunnymaster:${RABBITMQ_PASS}@localhost/
    amqp://tsource:${RABBITMQ_PASS}@localhost/
    amqp://tsub:${RABBITMQ_PASS}@localhost/
    amqp://tfeed:${RABBITMQ_PASS}@localhost/
    amqp://anonymous:${RABBITMQ_PASS}@localhost/
    amqps://anonymous:anonymous@hpfx.collab.science.gc.ca
    amqps://anonymous:anonymous@hpfx1.collab.science.gc.ca
    amqps://anonymous:anonymous@hpfx2.collab.science.gc.ca
    amqps://anonymous:anonymous@dd.weather.gc.ca
    amqps://anonymous:anonymous@dd1.weather.gc.ca
    amqps://anonymous:anonymous@dd2.weather.gc.ca
    ftp://anonymous:anonymous@localhost:2121/
    EOF

    cat > ~/.config/sarra/admin.conf << EOF
    cluster localhost
    admin amqp://bunnymaster@localhost/
    feeder amqp://tfeed@localhost/
    declare source tsource
    declare subscriber tsub
    declare subscriber anonymous
    EOF

    sudo rabbitmqctl delete_user guest

    sudo rabbitmqctl add_user bunnymaster ${RABBITMQ_PASS}
    sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
    sudo rabbitmqctl set_user_tags bunnymaster administrator

    sudo systemctl restart rabbitmq-server
    cd /usr/local/bin
    sudo mv rabbitmqadmin rabbitmqadmin.1
    sudo wget http://localhost:15672/cli/rabbitmqadmin
    sudo chmod 755 rabbitmqadmin

    sr --users declare

.. Note::

    Veuillez utiliser d’autres mots de passe dans les informations d’identification pour votre configuration, juste au cas où.
    Les mots de passe ne doivent pas être hard-codés dans la suite d’autotests.
    Les utilisateurs bunnymaster, tsource, tsub et tfeed doivent être utilisés pour exécuter des tests.

    L’idée ici est d’utiliser tsource, tsub et tfeed comme comptes de courtier pour tous les
    auto-test des opérations et stocker les informations d’identification dans le fichier credentials.conf normal.
    Aucun mot de passe ou fichier clé ne doit être stocké dans l’arborescence source, dans le cadre d’une suite auto-test.

Configurer l’environnement de test de flux
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Une fois l’environnement serveur établi, les tests de flux utilisent des transferts sftp vers localhost.

Il est également nécessaire que l’accès ssh sans mot de passe soit configuré sur l’hôte de test
pour l’utilisateur de système qui exécutera le test de flux. Cela peut être fait en créant une
paire de clés ssh privée/publique pour l’utilisateur (s’il n’y en a pas déjà) et en copiant la
clé publique dans le fichier authorized_keys dans le même répertoire que les clés (~/.ssh).
Pour les commandes associées, reportez-vous à la section http://www.linuxproblem.org/art_9.html

Notez que sur les systèmes où les anciennes versions de Paramiko (< 2.7.2) sont installées,
et où la paire de clés ssh a été générée avec OpenSSH >= 6.5, tester manuellement la commande
ci-dessous fonctionnera, mais Paramiko ne pourra pas se connecter. C’est probablement le cas s
i le fichier ``~/.ssh/id_rsa`` contient ``BEGIN OPENSSH PRIVATE KEY``. Pour contourner ce problème,
convertissez le format de la clé privée en utilisant ``ssh-keygen -p -m PEM -f ~/.ssh/id_rsa``.

Pour confirmer que ce ssh sans mot de passe vers localhost fonctionne ::

   ssh localhost ls

Cela devrait s’exécuter et se terminer.  S’il vous demande un mot de passe, les tests de flux ne fonctionneront pas.

Vérifiez que le courtier focntionne::

   systemctl status rabbitmq-server

Une partie du test de flux exécute un serveur sftp et utilise des fonctions client sftp.
Besoin du package suivant pour cela::

    sudo apt-get install python3-pyftpdlib python3-paramiko

Le script d’installation démarre un serveur Web trivial, un serveur ftp et un démon que sr_post appelle.
Il teste également les composants C, qui doivent également avoir déjà été installés.
et définit certains clients de test fixes qui seront utilisés lors des auto-tests ::

    cd 
    git clone https://github.com/MetPX/sr_insects
    cd sr_insects
    cd static_flow
    . ./flow_setup.sh
    
    blacklab% ./flow_setup.sh
    cleaning logs, just in case
    rm: cannot remove '/home/peter/.cache/sarra/log/*': No such file or directory
    Adding flow test configurations...
    2018-02-10 14:22:58,944 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/cno_trouble_f00.inc to /home/peter/.config/sarra/cpump/cno_trouble_f00.inc.
    2018-02-10 09:22:59,204 [INFO] copying /home/peter/src/sarracenia/sarra/examples/shovel/no_trouble_f00.inc to /home/peter/.config/sarra/shovel/no_trouble_f00.inc
    2018-02-10 14:22:59,206 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpost/veille_f34.conf to /home/peter/.config/sarra/cpost/veille_f34.conf.
    2018-02-10 14:22:59,207 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/pelle_dd1_f04.conf to /home/peter/.config/sarra/cpump/pelle_dd1_f04.conf.
    2018-02-10 14:22:59,208 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/pelle_dd2_f05.conf to /home/peter/.config/sarra/cpump/pelle_dd2_f05.conf.
    2018-02-10 14:22:59,208 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/xvan_f14.conf to /home/peter/.config/sarra/cpump/xvan_f14.conf.
    2018-02-10 14:22:59,209 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/xvan_f15.conf to /home/peter/.config/sarra/cpump/xvan_f15.conf.
    2018-02-10 09:22:59,483 [INFO] copying /home/peter/src/sarracenia/sarra/examples/poll/f62.conf to /home/peter/.config/sarra/poll/f62.conf
    2018-02-10 09:22:59,756 [INFO] copying /home/peter/src/sarracenia/sarra/examples/post/shim_f63.conf to /home/peter/.config/sarra/post/shim_f63.conf
    2018-02-10 09:23:00,030 [INFO] copying /home/peter/src/sarracenia/sarra/examples/post/test2_f61.conf to /home/peter/.config/sarra/post/test2_f61.conf
    2018-02-10 09:23:00,299 [INFO] copying /home/peter/src/sarracenia/sarra/examples/report/tsarra_f20.conf to /home/peter/.config/sarra/report/tsarra_f20.conf
    2018-02-10 09:23:00,561 [INFO] copying /home/peter/src/sarracenia/sarra/examples/report/twinnow00_f10.conf to /home/peter/.config/sarra/report/twinnow00_f10.conf
    2018-02-10 09:23:00,824 [INFO] copying /home/peter/src/sarracenia/sarra/examples/report/twinnow01_f10.conf to /home/peter/.config/sarra/report/twinnow01_f10.conf
    2018-02-10 09:23:01,086 [INFO] copying /home/peter/src/sarracenia/sarra/examples/sarra/download_f20.conf to /home/peter/.config/sarra/sarra/download_f20.conf
    2018-02-10 09:23:01,350 [INFO] copying /home/peter/src/sarracenia/sarra/examples/sender/tsource2send_f50.conf to /home/peter/.config/sarra/sender/tsource2send_f50.conf
    2018-02-10 09:23:01,615 [INFO] copying /home/peter/src/sarracenia/sarra/examples/shovel/t_dd1_f00.conf to /home/peter/.config/sarra/shovel/t_dd1_f00.conf
    2018-02-10 09:23:01,877 [INFO] copying /home/peter/src/sarracenia/sarra/examples/shovel/t_dd2_f00.conf to /home/peter/.config/sarra/shovel/t_dd2_f00.conf
    2018-02-10 09:23:02,137 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cclean_f91.conf to /home/peter/.config/sarra/subscribe/cclean_f91.conf
    2018-02-10 09:23:02,400 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cdnld_f21.conf to /home/peter/.config/sarra/subscribe/cdnld_f21.conf
    2018-02-10 09:23:02,658 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cfile_f44.conf to /home/peter/.config/sarra/subscribe/cfile_f44.conf
    2018-02-10 09:23:02,921 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/clean_f90.conf to /home/peter/.config/sarra/subscribe/clean_f90.conf
    2018-02-10 09:23:03,185 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cp_f61.conf to /home/peter/.config/sarra/subscribe/cp_f61.conf
    2018-02-10 09:23:03,455 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/ftp_f70.conf to /home/peter/.config/sarra/subscribe/ftp_f70.conf
    2018-02-10 09:23:03,715 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/q_f71.conf to /home/peter/.config/sarra/subscribe/q_f71.conf
    2018-02-10 09:23:03,978 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/t_f30.conf to /home/peter/.config/sarra/subscribe/t_f30.conf
    2018-02-10 09:23:04,237 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/u_sftp_f60.conf to /home/peter/.config/sarra/subscribe/u_sftp_f60.conf
    2018-02-10 09:23:04,504 [INFO] copying /home/peter/src/sarracenia/sarra/examples/watch/f40.conf to /home/peter/.config/sarra/watch/f40.conf
    2018-02-10 09:23:04,764 [INFO] copying /home/peter/src/sarracenia/sarra/examples/winnow/t00_f10.conf to /home/peter/.config/sarra/winnow/t00_f10.conf
    2018-02-10 09:23:05,027 [INFO] copying /home/peter/src/sarracenia/sarra/examples/winnow/t01_f10.conf to /home/peter/.config/sarra/winnow/t01_f10.conf
    Initializing with sr_audit... takes a minute or two
    OK, as expected 18 queues existing after 1st audit
    OK, as expected 31 exchanges for flow test created.
    Starting trivial http server on: /home/peter/sarra_devdocroot, saving pid in .httpserverpid
    Starting trivial ftp server on: /home/peter/sarra_devdocroot, saving pid in .ftpserverpid
    running self test ... takes a minute or two
    sr_util.py TEST PASSED
    sr_credentials.py TEST PASSED
    sr_config.py TEST PASSED
    sr_cache.py TEST PASSED
    sr_retry.py TEST PASSED
    sr_consumer.py TEST PASSED
    sr_http.py TEST PASSED
    sftp testing start...
    sftp testing config read...
    sftp testing fake message built ...
    sftp sr_ftp instantiated ...
    sftp sr_ftp connected ...
    sftp sr_ftp mkdir ...
    test 01: directory creation succeeded
    test 02: file upload succeeded
    test 03: file rename succeeded
    test 04: getting a part succeeded
    test 05: download succeeded
    test 06: onfly_checksum succeeded
    Sent: bbb  into tztz/ddd 0-5
    test 07: download succeeded
    test 08: delete succeeded
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    /home/peter
    /home/peter
    test 09: bad part succeeded
    sr_sftp.py TEST PASSED
    sr_instances.py TEST PASSED
    OK, as expected 9 tests passed
    Starting flow_post on: /home/peter/sarra_devdocroot, saving pid in .flowpostpid
    Starting up all components (sr start)...
    done.
    OK: sr start was successful
    Overall PASSED 4/4 checks passed!
    blacklab% 

Lorsqu’il exécute le programme d’installation, il exécute également tous les unit_tests existants.
Ne passez aux tests flow_check que si tous les tests de flow_setup.sh réussissent.


Exécuter un test de Flux
~~~~~~~~~~~~~~~~~~~~~~~~

Le script flow_check.sh lit les fichiers journaux de tous les composants démarrés et compare
le nombre de messages de notification, à la recherche d’une correspondance dans les +- 10%.
Il faut quelques minutes pour que la configuration s’exécute avant qu’il y ait suffisamment
de données pour effectuer les mesures correctes ::

     ./flow_limit.sh

sample output::

    initial sample building sample size 8 need at least 1000 
    sample now   1021 
    Sufficient!
    stopping shovels and waiting...
    2017-10-28 00:37:02,422 [INFO] sr_shovel t_dd1_f00 0001 stopping
    2017-10-28 04:37:02,435 [INFO] 2017-10-28 04:37:02,435 [INFO] info: instances option not implemented, ignored.
    info: instances option not implemented, ignored.
    2017-10-28 04:37:02,435 [INFO] 2017-10-28 04:37:02,435 [INFO] info: report option not implemented, ignored.
    info: report option not implemented, ignored.
    2017-10-28 00:37:02,436 [INFO] sr_shovel t_dd2_f00 0001 stopping
    running instance for config pelle_dd1_f04 (pid 15872) stopped.
    running instance for config pelle_dd2_f05 (pid 15847) stopped.
        maximum of the shovels is: 1022


Ensuite, vérifiez avec flow_check.sh::

    TYPE OF ERRORS IN LOG :

      1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f14_001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan00' in vhost '/'
      1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f15_001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan01' in vhost '/'

    
    test  1 success: shovels t_dd1_f00 ( 1022 ) and t_dd2_f00 ( 1022 ) should have about the same number of items read
    test  2 success: sarra tsarra (1022) should be reading about half as many items as (both) winnows (2240)
    test  3 success: tsarra (1022) and sub t_f30 (1022) should have about the same number of items
    test  4 success: max shovel (1022) and subscriber t_f30 (1022) should have about the same number of items
    test  5 success: count of truncated headers (1022) and subscribed messages (1022) should have about the same number of items
    test  6 success: count of downloads by subscribe t_f30 (1022) and messages received (1022) should be about the same
    test  7 success: downloads by subscribe t_f30 (1022) and files posted by sr_watch (1022) should be about the same
    test  8 success: posted by watch(1022) and sent by sr_sender (1022) should be about the same
    test  9 success: 1022 of 1022: files sent with identical content to those downloaded by subscribe
    test 10 success: 1022 of 1022: poll test1_f62 and subscribe q_f71 run together. Should have equal results.
    test 11 success: post test2_f61 1022 and subscribe r_ftp_f70 1021 run together. Should be about the same.
    test 12 success: cpump both pelles (c shovel) should receive about the same number of messages (3665) (3662)
    test 13 success: cdnld_f21 subscribe downloaded (1022) the same number of files that was published by both van_14 and van_15 (1022)
    test 14 success: veille_f34 should post the same number of files (1022) that subscribe cdnld_f21 downloaded (1022)
    test 15 success: veille_f34 should post the same number of files (1022) that subscribe cfile_f44 downloaded (1022)
    test 16 success: Overall 15 of 15 passed!

    blacklab% 

Si le flow_check.sh est adopté, alors on a une confiance raisonnable dans la fonctionnalité globale de
Python, mais la couverture du test n’est pas exhaustive. C’est la porte la plus basse pour s’engager
à des modifications apportées à votre code Python dans la branche principale. Il s’agit d’un échantillonnage plus qualitatif
des cas d’utilisation courants plutôt qu’un examen approfondi de toutes les fonctionnalités. Bien que ce ne soit pas le cas
approfondie, il est bon de savoir que les flux fonctionnent.

Notez que l’abonné *fclean* examine les fichiers et les conserve suffisamment longtemps pour qu’ils puissent
parcourir tous les autres tests.  Il le fait en attendant un délai raisonnable (45 secondes, la dernière fois
vérifiée), puis il compare le fichier qui a été posté par sr_watch aux fichiers créés en téléchargeant à partir
de celui-ci.  Au fur et à mesure que le dénombrement *sample now* progresse, il imprime "OK" si les fichiers
téléchargés sont identiques à ceux postés par sr_watch. L’ajout de fclean et cfclean correspondant pour les
cflow_test sont cassés.  La configuration par défaut qui utilise *fclean* et *cfclean* garantit que seulement
quelques minutes d’espace disque sont utilisées à un moment donné et permettent des tests beaucoup plus longs.

Par défaut, le flow_test n’est que de 1000 fichiers, mais on peut lui demander de fonctionner plus longtemps,
comme ceci::

 ./flow_limit.sh 50000

Pour accumuler cinquante mille fichiers avant de terminer le test. Cela permet de tester les performances
à long terme, en particulier l’utilisation de la mémoire au fil du temps et des fonctions d’entretien
du traitement on_heartbeat.

Flow Cleanup
~~~~~~~~~~~~

Une fois le test terminé, exécutez le script ./flow_cleanup.sh, qui tuera les serveurs et les démons en cours
d’exécution et supprimera tous les fichiers de configuration installés pour le test de flux, toutes les files
d’attente, les échanges et les journaux. Cela doit également être fait entre chaque exécution du test de flux::

  blacklab% ./flow_cleanup.sh
  Stopping sr...
  Cleanup sr...
  Cleanup trivial http server... 
  web server stopped.
  if other web servers with lost pid kill them
  Cleanup trivial ftp server... 
  ftp server stopped.
  if other ftp servers with lost pid kill them
  Cleanup flow poster... 
  flow poster stopped.
  if other flow_post.sh with lost pid kill them
  Deleting queues: 
  Deleting exchanges...
  Removing flow configs...
  2018-02-10 14:17:34,150 [INFO] info: instances option not implemented, ignored.
  2018-02-10 14:17:34,150 [INFO] info: report option not implemented, ignored.
  2018-02-10 14:17:34,353 [INFO] info: instances option not implemented, ignored.
  2018-02-10 14:17:34,353 [INFO] info: report option not implemented, ignored.
  2018-02-10 09:17:34,837 [INFO] sr_poll f62 cleanup
  2018-02-10 09:17:34,845 [INFO] deleting exchange xs_tsource_poll (tsource@localhost)
  2018-02-10 09:17:35,115 [INFO] sr_post shim_f63 cleanup
  2018-02-10 09:17:35,122 [INFO] deleting exchange xs_tsource_shim (tsource@localhost)
  2018-02-10 09:17:35,394 [INFO] sr_post test2_f61 cleanup
  2018-02-10 09:17:35,402 [INFO] deleting exchange xs_tsource_post (tsource@localhost)
  2018-02-10 09:17:35,659 [INFO] sr_report tsarra_f20 cleanup
  2018-02-10 09:17:35,659 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:35,661 [INFO] deleting queue q_tfeed.sr_report.tsarra_f20.89336558.04455188 (tfeed@localhost)
  2018-02-10 09:17:35,920 [INFO] sr_report twinnow00_f10 cleanup
  2018-02-10 09:17:35,920 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:35,922 [INFO] deleting queue q_tfeed.sr_report.twinnow00_f10.35552245.50856337 (tfeed@localhost)
  2018-02-10 09:17:36,179 [INFO] sr_report twinnow01_f10 cleanup
  2018-02-10 09:17:36,180 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:36,182 [INFO] deleting queue q_tfeed.sr_report.twinnow01_f10.48262886.11567358 (tfeed@localhost)
  2018-02-10 09:17:36,445 [WARNING] option url deprecated please use post_base_url
  2018-02-10 09:17:36,446 [WARNING] use post_base_dir instead of document_root
  2018-02-10 09:17:36,446 [INFO] sr_sarra download_f20 cleanup
  2018-02-10 09:17:36,446 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:36,448 [INFO] deleting queue q_tfeed.sr_sarra.download_f20 (tfeed@localhost)
  2018-02-10 09:17:36,449 [INFO] exchange xpublic remains
  2018-02-10 09:17:36,703 [INFO] sr_sender tsource2send_f50 cleanup
  2018-02-10 09:17:36,703 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:36,705 [INFO] deleting queue q_tsource.sr_sender.tsource2send_f50 (tsource@localhost)
  2018-02-10 09:17:36,711 [INFO] deleting exchange xs_tsource_output (tsource@localhost)
  2018-02-10 09:17:36,969 [INFO] sr_shovel t_dd1_f00 cleanup
  2018-02-10 09:17:36,969 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2018-02-10 09:17:37,072 [INFO] deleting queue q_anonymous.sr_shovel.t_dd1_f00 (anonymous@dd.weather.gc.ca)
  2018-02-10 09:17:37,095 [INFO] exchange xwinnow00 remains
  2018-02-10 09:17:37,095 [INFO] exchange xwinnow01 remains
  2018-02-10 09:17:37,389 [INFO] sr_shovel t_dd2_f00 cleanup
  2018-02-10 09:17:37,389 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2018-02-10 09:17:37,498 [INFO] deleting queue q_anonymous.sr_shovel.t_dd2_f00 (anonymous@dd.weather.gc.ca)
  2018-02-10 09:17:37,522 [INFO] exchange xwinnow00 remains
  2018-02-10 09:17:37,523 [INFO] exchange xwinnow01 remains
  2018-02-10 09:17:37,804 [INFO] sr_subscribe cclean_f91 cleanup
  2018-02-10 09:17:37,804 [INFO] AMQP  broker(localhost) user(tsub) vhost(/)
  2018-02-10 09:17:37,806 [INFO] deleting queue q_tsub.sr_subscribe.cclean_f91.39328538.44917465 (tsub@localhost)
  2018-02-10 09:17:38,062 [INFO] sr_subscribe cdnld_f21 cleanup
  2018-02-10 09:17:38,062 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:38,064 [INFO] deleting queue q_tfeed.sr_subscribe.cdnld_f21.11963392.61638098 (tfeed@localhost)
  2018-02-10 09:17:38,324 [WARNING] use post_base_dir instead of document_root
  2018-02-10 09:17:38,324 [INFO] sr_subscribe cfile_f44 cleanup
  2018-02-10 09:17:38,324 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:38,326 [INFO] deleting queue q_tfeed.sr_subscribe.cfile_f44.56469334.87337271 (tfeed@localhost)
  2018-02-10 09:17:38,583 [INFO] sr_subscribe clean_f90 cleanup
  2018-02-10 09:17:38,583 [INFO] AMQP  broker(localhost) user(tsub) vhost(/)
  2018-02-10 09:17:38,585 [INFO] deleting queue q_tsub.sr_subscribe.clean_f90.45979835.20516428 (tsub@localhost)
  2018-02-10 09:17:38,854 [WARNING] extended option download_cp_command = ['cp --preserve=timestamps'] (unknown or not declared)
  2018-02-10 09:17:38,855 [INFO] sr_subscribe cp_f61 cleanup
  2018-02-10 09:17:38,855 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:38,857 [INFO] deleting queue q_tsource.sr_subscribe.cp_f61.61218922.69758215 (tsource@localhost)
  2018-02-10 09:17:39,121 [INFO] sr_subscribe ftp_f70 cleanup
  2018-02-10 09:17:39,121 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:39,123 [INFO] deleting queue q_tsource.sr_subscribe.ftp_f70.47997098.27633529 (tsource@localhost)
  2018-02-10 09:17:39,386 [INFO] sr_subscribe q_f71 cleanup
  2018-02-10 09:17:39,386 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:39,389 [INFO] deleting queue q_tsource.sr_subscribe.q_f71.84316550.21567557 (tsource@localhost)
  2018-02-10 09:17:39,658 [INFO] sr_subscribe t_f30 cleanup
  2018-02-10 09:17:39,658 [INFO] AMQP  broker(localhost) user(tsub) vhost(/)
  2018-02-10 09:17:39,660 [INFO] deleting queue q_tsub.sr_subscribe.t_f30.26453890.50752396 (tsub@localhost)
  2018-02-10 09:17:39,924 [INFO] sr_subscribe u_sftp_f60 cleanup
  2018-02-10 09:17:39,924 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:39,927 [INFO] deleting queue q_tsource.sr_subscribe.u_sftp_f60.81353341.03950190 (tsource@localhost)
  2018-02-10 09:17:40,196 [WARNING] option url deprecated please use post_base_url
  2018-02-10 09:17:40,196 [WARNING] use post_broker to set broker
  2018-02-10 09:17:40,197 [INFO] sr_watch f40 cleanup
  2018-02-10 09:17:40,207 [INFO] deleting exchange xs_tsource (tsource@localhost)
  2018-02-10 09:17:40,471 [INFO] sr_winnow t00_f10 cleanup
  2018-02-10 09:17:40,471 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:40,474 [INFO] deleting queue q_tfeed.sr_winnow.t00_f10 (tfeed@localhost)
  2018-02-10 09:17:40,480 [INFO] deleting exchange xsarra (tfeed@localhost)
  2018-02-10 09:17:40,741 [INFO] sr_winnow t01_f10 cleanup
  2018-02-10 09:17:40,741 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:40,743 [INFO] deleting queue q_tfeed.sr_winnow.t01_f10 (tfeed@localhost)
  2018-02-10 09:17:40,750 [INFO] deleting exchange xsarra (tfeed@localhost)
  2018-02-10 14:17:40,753 [ERROR] config cno_trouble_f00 not found.
  Removing flow config logs...
  rm: cannot remove '/home/peter/.cache/sarra/log/sr_audit_f00.log': No such file or directory
  Removing document root ( /home/peter/sarra_devdocroot )...
  Done!

Après la flow_cleanup.sh, pour vérifier qu’un test est terminé, utiliser::

   sr3 status 

ce qui devrait montrer qu’il n’y a pas de configurations actives.

Si le test static_flow fonctionne, réexécutez les autres tests : flakey_broker,
transform_flow, et dynamic_flow.

Longueur du test Dynamic Flow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alors que la plupart des tests ont une durée fixe, le test de flux dynamique interroge une serveur distant
et peut fonctionner pour n’importe quelle longueur souhaitée. La longueur du flow_test dynamique par défaut
est de 1000 fichiers circulant dans les cas de test. En cas de développement rapide,
on peut fournir un argument pour raccourcir cela::

  ./flow_limit.sh 200

Vers la fin d’un cycle de développement, des flow_tests plus longs sont conseillées::

  ./flow_limit.sh 20000 

pour identifier plus de problèmes. Exemple d’exécution à 100 000 entrées ::

  blacklab% ./flow_limit.sh 100000
  initial sample building sample size 155 need at least 100000 
  sample now 100003 content_checks:GOOD missed_dispositions:0s:0
  Sufficient!
  stopping shovels and waiting...
  2018-02-10 13:15:08,964 [INFO] 2018-02-10 13:15:08,964 [INFO] info: instances option not implemented, ignored.
  info: instances option not implemented, ignored.
  2018-02-10 13:15:08,964 [INFO] info: report option not implemented, ignored.
  2018-02-10 13:15:08,964 [INFO] info: report option not implemented, ignored.
  running instance for config pelle_dd2_f05 (pid 20031) stopped.
  running instance for config pelle_dd1_f04 (pid 20043) stopped.
  Traceback (most recent call last):ng...
    File "/usr/bin/rabbitmqadmin", line 1012, in <module>
      main()
    File "/usr/bin/rabbitmqadmin", line 413, in main
      method()
    File "/usr/bin/rabbitmqadmin", line 593, in invoke_list
      format_list(self.get(uri), cols, obj_info, self.options)
    File "/usr/bin/rabbitmqadmin", line 710, in format_list
      formatter_instance.display(json_list)
    File "/usr/bin/rabbitmqadmin", line 721, in display
      (columns, table) = self.list_to_table(json.loads(json_list), depth)
    File "/usr/bin/rabbitmqadmin", line 775, in list_to_table
      add('', 1, item, add_to_row)
    File "/usr/bin/rabbitmqadmin", line 742, in add
      add(column, depth + 1, subitem, fun)
    File "/usr/bin/rabbitmqadmin", line 742, in add
      add(column, depth + 1, subitem, fun)
    File "/usr/bin/rabbitmqadmin", line 754, in add
      fun(column, subitem)
    File "/usr/bin/rabbitmqadmin", line 761, in add_to_row
      row[column_ix[col]] = maybe_utf8(val)
    File "/usr/bin/rabbitmqadmin", line 431, in maybe_utf8
      return s.encode('utf-8')
  AttributeError: 'float' object has no attribute 'encode'
  maximum of the shovels is: 100008
  

While it is runnig one can run flow_check.sh at any time::

  NB retries for sr_subscribe t_f30 0
  NB retries for sr_sender 18
  
        1 /home/peter/.cache/sarra/log/sr_cpost_veille_f34_0001.log [ERROR] sr_cpost rename: /home/peter/sarra_devdocroot/cfr/observations/xml/AB/today/today_ab_20180210_e.xml cannot stat.
        1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f14_0001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan00' in vhost '/'
        1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f15_0001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan01' in vhost '/'
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0002.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/CA/CWAO/09/CACN00_CWAO_100857__WDK_10905 
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0002.log [ERROR] Failed to reach server. Reason: [Errno 110] Connection timed out
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0002.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/CA/CWAO/09/CACN00_CWAO_100857__WDK_10905. Type: <class 'urllib.error.URLError'>, Value: <urlopen error [Errno 110] Connection timed out>
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/SA/CYMM/09/SACN61_CYMM_100900___53321 
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Failed to reach server. Reason: [Errno 110] Connection timed out
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/SA/CYMM/09/SACN61_CYMM_100900___53321. Type: <class 'urllib.error.URLError'>, Value: <urlopen error [Errno 110] Connection timed out>
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/CS/CWEG/12/CSCN03_CWEG_101200___12074 
  more than 10 TYPES OF ERRORS found... for the rest, have a look at /home/peter/src/sarracenia/test/flow_check_errors_logged.txt for details

  test  1 success: shovels t_dd1_f00 (100008) and t_dd2_f00 (100008) should have about the same number of items read
  test  2 success: sarra tsarra (100008) should be reading about half as many items as (both) winnows (200016)
  test  3 success: tsarra (100008) and sub t_f30 (99953) should have about the same number of items
  test  4 success: max shovel (100008) and subscriber t_f30 (99953) should have about the same number of items
  test  5 success: count of truncated headers (100008) and subscribed messages (100008) should have about the same number of items
  test  6 success: count of downloads by subscribe t_f30 (99953) and messages received (100008) should be about the same
  test  7 success: same downloads by subscribe t_f30 (199906) and files posted (add+remove) by sr_watch (199620) should be about the same
  test  8 success: posted by watch(199620) and subscribed cp_f60 (99966) should be about half as many
  test  9 success: posted by watch(199620) and sent by sr_sender (199549) should be about the same
  test 10 success: 0 messages received that we don't know what happenned.
  test 11 success: sarra tsarra (100008) and good audit 99754 should be the same.
  test 12 success: poll test1_f62 94865 and subscribe q_f71 99935 run together. Should have equal results.
  test 13 success: post test2_f61 99731 and subscribe r_ftp_f70 99939 run together. Should be about the same.
  test 14 success: posts test2_f61 99731 and shim_f63 110795 Should be the same.
  test 15 success: cpump both pelles (c shovel) should receive about the same number of messages (160737) (160735)
  test 16 success: cdnld_f21 subscribe downloaded (50113) the same number of files that was published by both van_14 and van_15 (50221)
  test 17 success: veille_f34 should post twice as many files (100205) as subscribe cdnld_f21 downloaded (50113)
  test 18 success: veille_f34 should post twice as many files (100205) as subscribe cfile_f44 downloaded (49985)
  test 19 success: Overall 18 of 18 passed (sample size: 100008) !
  
  blacklab% 

Ce test a été lancé en fin de journée, car il prend plusieurs heures, et les résultats examinés le lendemain matin.

Échantillon à volume élevé
~~~~~~~~~~~~~~~~~~~~~~~~~~

Essayer le test de flux avec un volume plus élevé de messages de notification (c’est-à-dire 100 000)
est un pas de plus vers l’objectif d’avoir un test de flux exécuté en continu. Ceci est motivé par
nos objectifs de test.

Limitation
++++++++++
Ubuntu a une limitation qui surpasse les montres inotify et que nous avons rencontrée dans
`#204 <https://github.com/MetPX/sarracenia/issues/204>`_ . Nous pouvons surmonter cela en définissant la variable sysctl associée.
Tout d’abord, vérifiez quelle est la limite de votre système::

  $ sysctl fs.inotify.max_user_watches
  fs.inotify.max_user_watches = 8196

Si la limite est trop basse (c.-à-d. 8196), changez-la à un niveau plus approprié pour l’essai de débit::

  $ sudo sysctl fs.inotify.max_user_watches=524288

Pour rendre cette modification permanente, ajoutez cette ligne à ``/etc/sysctl.conf``::

  fs.inotify.max_user_watches=524288

Puis excuter ``sysctl -p`` Et le système devrait maintenant prendre en charge un volume élevé d’événements iNotify.

Flow Test Coincé
++++++++++++++++

Parfois, les tests de flux (en particulier pour les grands nombres) sont bloqués en raison de problèmes avec
le flux de données (où plusieurs fichiers obtiennent le même nom) et donc les versions antérieures suppriment
les versions ultérieures et les nouvelles tentatives échouent toujours. Finalement, nous réussirons à nettoyer
le flux dd.weather.gc.ca, mais pour l’instant, il arrive parfois qu’un flow_check reste bloqué à "Retrying".
Le test a exécuté tous les messages de notification requis et est à une phase de vidange des tentatives,
mais continue de réessayer pour toujours avec un nombre variable d’éléments qui ne tombe jamais à zéro.

Pour récupérer de cet état sans rejeter les résultats d’un test long, procédez comme suit::

  ^C to interrupt the flow_check.sh 100000
  blacklab% sr stop
  blacklab% cd ~/.cache/sarra
  blacklab% ls */*/*retry*
  shovel/pclean_f90/sr_shovel_pclean_f90_0001.retry        shovel/pclean_f92/sr_shovel_pclean_f92_0001.retry        subscribe/t_f30/sr_subscribe_t_f30_0002.retry.new
  shovel/pclean_f91/sr_shovel_pclean_f91_0001.retry        shovel/pclean_f92/sr_shovel_pclean_f92_0001.retry.state
  shovel/pclean_f91/sr_shovel_pclean_f91_0001.retry.state  subscribe/q_f71/sr_subscribe_q_f71_0004.retry.new
  blacklab% rm */*/*retry*
  blacklab% sr start
  blacklab% 
  blacklab%  ./flow_check.sh 100000
  Sufficient!
  stopping shovels and waiting...
  2018-04-07 10:50:16,167 [INFO] sr_shovel t_dd2_f00 0001 stopped
  2018-04-07 10:50:16,177 [INFO] sr_shovel t_dd1_f00 0001 stopped
  2018-04-07 14:50:16,235 [INFO] info: instances option not implemented, ignored.
  2018-04-07 14:50:16,235 [INFO] info: report option not
  implemented, ignored.
  2018-04-07 14:50:16,235 [INFO] info: instances option not implemented, ignored.
  2018-04-07 14:50:16,235 [INFO] info: report option not
  implemented, ignored.
  running instance for config pelle_dd1_f04 (pid 12435) stopped.
  running instance for config pelle_dd2_f05 (pid 12428) stopped.
  maximum of the shovels is: 100075
  

  blacklab% ./flow_check.sh

                   | dd.weather routing |
  test  1 success: sr_shovel (100075) t_dd1 should have the same number
  of items as t_dd2 (100068)
  test  2 success: sr_winnow (200143) should have the sum of the number
  of items of shovels (200143)
  test  3 success: sr_sarra (98075) should have the same number of items
  as winnows'post (100077)
  test  4 success: sr_subscribe (98068) should have the same number of
  items as sarra (98075)
                   | watch      routing |
  test  5 success: sr_watch (397354) should be 4 times subscribe t_f30 (98068)
  test  6 success: sr_sender (392737) should have about the same number
  of items as sr_watch (397354)
  test  7 success: sr_subscribe u_sftp_f60 (361172) should have the same
  number of items as sr_sender (392737)
  test  8 success: sr_subscribe cp_f61 (361172) should have the same
  number of items as sr_sender (392737)
                   | poll       routing |
  test  9 success: sr_poll test1_f62 (195408) should have half the same
  number of items of sr_sender(196368)
  test 10 success: sr_subscribe q_f71 (195406) should have about the
  same number of items as sr_poll test1_f62(195408)
                   | flow_post  routing |
  test 11 success: sr_post test2_f61 (193541) should have half the same
  number of items of sr_sender(196368)
  test 12 success: sr_subscribe ftp_f70 (193541) should have about the
  same number of items as sr_post test2_f61(193541)
  test 13 success: sr_post test2_f61 (193541) should have about the same
  number of items as shim_f63 195055
                   | py infos   routing |
  test 14 success: sr_shovel pclean_f90 (97019) should have the same
  number of watched items winnows'post (100077)
  test 15 success: sr_shovel pclean_f92 (94537}) should have the same
  number of removed items winnows'post (100077)
  test 16 success: 0 messages received that we don't know what happenned.
  test 17 success: count of truncated headers (98075) and subscribed
  messages (98075) should have about the same number of items
                   | C          routing |
  test 18 success: cpump both pelles (c shovel) should receive about the
  same number of messages (161365) (161365)
  test 19 success: cdnld_f21 subscribe downloaded (47950) the same
  number of files that was published by both van_14 and van_15 (47950)
  test 20 success: veille_f34 should post twice as many files (95846) as
  subscribe cdnld_f21 downloaded (47950)
  test 21 success: veille_f34 should post twice as many files (95846) as
  subscribe cfile_f44 downloaded (47896)
  test 22 success: Overall 21 of 21 passed (sample size: 100077) !
  
  NB retries for sr_subscribe t_f30 0
  NB retries for sr_sender 36
  

Donc, dans ce cas, les résultats sont toujours bons en dépit de ne pas être tout à fait
capable de résilier. S’il y avait un problème important, le cumul
l’indiquerait.

Flow tests avec MQTT
~~~~~~~~~~~~~~~~~~~~

Les tests de flux peuvent être exécutés lorsque certains composants utilisent le protocole MQTT, au lieu d’AMQP.

FIXME: étapes manquantes, plus de clarté requise.

* Le courtier MQTT est installé
* Les utilisateurs de BunnyMaster Tsource, Tfeed, Tsub sont définis et ont reçu des mots de passe (dépendants du courtier.)
* Pour chaque utilisateur : une ligne d’URL mqtt://user:pw@brokerhost est ajoutée à ~/.config/sr3/credentials.conf
* modifier la variable MQP dans ~/.config/sr3/default.conf, MQP est utilisée par les tests de flux.

La plupart des composants utiliseront MQTT au lieu d’amqp et peuvent être exécutés normalement.

Commits vers la branche principale
----------------------------------

A part les fautes de frappe, les corrections de langue dans la documentation et l’incrémentation
de la version, les développeurs ne sont pas censés s’engager sur Main (branche principale). Tous les travaux
se produisent sur les branches de développement, et tous les tests doivent réussir avant
de considerer d'affecter Main. Une fois le développement de la branche terminé,
ou qu'une unité de travaux en cours est jugée utile de fusionner avec la branche principale, on
doit résumer les modifications de la branche pour le journal des modifications de Debian,
demande sur GitHub.

::
   
   git checkout issueXXX  # v02_issueXXX  pour du travaille sur l´ancienne version.
   dch # résumer les changement dans changelog.
   vi doc/UPGRADING.rst # rarement en cas de changement visible dont l´usager doit prendre connaissance.
   vi doc/fr/UPGRADING.rst # bon... ceci est visible aux usagers, donc...
   git commit -a
   git push 
   # déclencher un *pull request* chez github.com

Un deuxième développeur examinera la demande d’extraction et le réviseur décidera si
la fusion est appropriée. On s’attend à ce que le développeur examine chaque validation, et
la comprenne dans une certaine mesure.

Le github Actions examine les pull requests et effectue des tests de flux sur celles-ci.
Si les tests réussissent, alors c’est un bon indicateur qualitatif, mais les tests sont un peu
fragile pour le moment, donc s’ils échouent, il serait idéal que le réviseur exécute
les tests dans leur propre environnement de développement. S’il passe dans l'environnement du développeur local
on peut approuver une fusion malgré les plaintes de Github Actions.


Branches Principales
--------------------

Il y a une longue discussion sur `Quelle version est stable <https://github.com/MetPX/sarracenia/issues/139>`_
La configuration actuelle est qu’il y a quatre branches principales:

* La branche principale est la version finale de SR3, fusionnant à partir de development. Utilisé pour créer des
  packages SR3 dans le référentiel `MetPX <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_.

* development ... La `version 3 <v03.rst>`_ La branche de travail en cours (WIP) est une prochaine version de Sarracenia
  en développement. La branche development est utilisée pour créer des packages sr3 pour le
  `Quotidien <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily>`_
  et les référentiels `Pre-Release <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-pre-release>`_
  sur launchpad.net.

* Les branches de issue à fusionner avec development, devraient s’appeler v3_issueXXX

* v2_dev ... La branche d’intégration pour la maintenance v2 utilisée avant la promotion à v2_stable.

* v2_stable ... Généralement, cette branche obtient du code via des fusions à partir de v2_dev, après
  que la pré-version a été testée sur autant de systèmes que possible. Utilisé pour construire des
  paquets sur la version stable: `MetPX <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_
  
* les branches issues à fusionner avec main doivent être appelées issueXXX.
  

Référentiels
------------

Pour les systèmes d’exploitation Ubuntu, le site launchpad.net est le meilleur moyen de fournir des packages
entièrement intégrés (construit par rapport aux niveaux de correctifs actuels de toutes les dépendances
(composants logiciels sur lesquels Sarracenia s’appuie) pour fournir toutes les fonctionnalités.)) Idéalement,
lors de l’exécution d’un serveur, on devrait utiliser l’un des référentiels, et permettre des correctifs
automatisés pour les mettre à niveau selon les besoins.

Référentiels:

* Quotidien https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily (Vivre sur le fil du rasoir... )
  La construction quotidienne automatisée des paquets SR3 se fait à partir de la branche *development*.

* Pré-release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-pre-release (pour les fonctionnalités
  les plus récentes.) De la branche *development*. Les développeurs déclenchent manuellement les builds ici lorsque
  cela semble approprié (tester du code prêt à être publié.)

* Release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx (pour une stabilité maximale)
  de la branche *v2_stable*.  Après avoir testé dans des systèmes souscrits à des versions préliminaires,
  les développeurs fusionnent la branche v2_dev à v2_stable et déclenchent manuellement une génération.

Pour plus de détails, voir `Quelle version est stable <https://github.com/MetPX/sarracenia/issues/139>`_



Création d’une version
----------------------

MetPX-Sarracenia est distribué de différentes manières, et chacun a son propre processus de construction.
Les versions packagées sont toujours préférables aux versions uniques, car elles sont reproductibles.

Lorsque le développement nécessite des tests sur une large gamme de serveurs, il est préférable de faire
une version alpha, plutôt que d’installer des paquets uniques.  Donc, le mécanisme préféré est
de construire les paquets Ubuntu et pip au moins, et les installer sur les machines de test en utilisant
les référentiels publics pertinents.

Pour publier une version, il faut :

- Définir la version.
- Télécharger la version sur pypi.org afin que l’installation avec PIP réussisse.
- Télécharger la version sur launchpad.net, afin que l’installation des paquets Debian
  qui utilise le référentiel réussisse.
- Télécharger les notes de version et les fichiers binaires sur github.com.
- incrémenter la version pour les futurs engagements à v2_dev ou development.

Schéma de contrôle de version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Chaque version sera versionnée en tant que ``<protocol version>.<YY>.<MM> <segment>``

Où:

- **version du protocole** est la version du message. Dans les messages de notification Sarra,
  ils sont tous préfixés par v02 (pour le moment).
- **YY** est les deux derniers chiffres de l’année de la sortie initiale de la série.
- **MM** est un numéro de mois à DEUX chiffres, c’est-à-dire pour avril: 04.
- **segment** est ce qui serait utilisé dans une série.
  De pep0440:
  X.YaN   # Version Alpha
  X.YbN   # Version Beta
  X.YrcN  # Version Candidate
  X.Y     # Version Final
  X.ypostN #ack! Version corrigé.

Actuellement, 3.00 est toujours stabilisé, de sorte que la convention année/mois n’est pas appliquée.
Les versions sont actuellement 3.00.iibj où:

  * ii -- nombre incrémentiel de versions préliminaires de 3.00
  * j -- incrément bêta.

À un moment donné, 3.00 sera complet et suffisamment solide pour que nous
reprenions la convention année/mois, espérons-le 3.22.

Les rejets sont classés comme suit :

Alpha
  Versions instantanées prises directement à partir de development, sans autres garanties qualitatives.
  Aucune garantie de fonctionnalité, certains composants peuvent être partiellement mis en œuvre,
  certaines bris peuvent survenir. Pas de corrections de bugs, problèmes résolus par la version ultérieure.
  Souvent utilisé pour les premiers tests de bout en bout (plutôt que d’installer une forme personnalisé
  à partir de l’arborescence sur chaque machine d’essai.)

Bêta
  Fonctionnalité terminée pour une version donnée.  Composants dans leur forme finale pour cette version.
  La documentation existe dans au moins une langue.
  Tous les bogues de blocage de version connus précédemment sont corrigés.
  Pas de corrections de bogues, problèmes résolus par la version ultérieure.

RC - Release Candidate.
  Implique qu’il est passé par la version bêta pour identifier et résoudre les problèmes majeurs.
  Documentation traduite disponible.
  Pas de corrections de bogues, problèmes résolus par la version ultérieure.

Les versions finales n’ont pas de suffixe et sont considérées comme stables et prises en charge.
Stable devrait recevoir des corrections de bogues si nécessaire de temps en temps.
On peut construire des python Wheels, ou des paquets Debian à des fins de test local
pendant le développement.

.. Note::
      Si vous modifiez les paramètres par défaut pour les échanges / files d’attente comme
      dans le cadre d’une nouvelle version, gardez à l’esprit que tous les composants doivent utiliser
      les mêmes paramètres ou la liaison échoueront et ils ne pourront pas
      se connecter.  Si une nouvelle version déclare des paramètres de fil d’attente ou d’échange différents,
      le moyen le plus simple de mettre à niveau (préserver les données) consiste à vider les files d’attente
      avant la mise à niveau, par exemple en définissant que l’accès à la ressource ne sera pas accordé par le serveur.
      (??? peut-être y a-t-il un moyen d’accéder à une ressource telle quelle... pas de déclaration)
      (??? devrait faire l’objet d’une enquête)

      La modification de la valeur par défaut nécessite la suppression et la recréation de la ressource.
      Cela a un impact majeur sur les processus...

Exemple:

La première version alpha en janvier 2016 serait versionnée comme suit : ``metpx-sarracenia-2.16.01a01``


Définir la version
~~~~~~~~~~~~~~~~~~

Ceci est fait pour *démarrer* le développement d’une version. D´habitude, on fais cela immédiatement
après que la version précedente a été relachée.

* git checkout development
* Modifier ``sarracenia/_version.py`` manuellement et définissez le numéro de version.
* Modifier CHANGES.rst pour ajouter une section pour la version.
* Exécuter dch pour démarrer le journal des modifications de la version actuelle.
  * assurer que UNRELEASED soit l'étiquette de status au lieu de *unstable* (peut-être automatiquement
    faite par dch) 
* git commit -a 
* git push

Si le développement se poursuit et que le temps passe sans que la libération ne se produise, alors
la version doit être définie à nouveau (ou écrasée).  Par exemple, un cycle développement commence
en août, la version principale sera 3.19.08b1... mais si le développement
continue en septembre, il faut utiliser cette procédure pour changer la version à 3.19.09b1.

Durant le dévéloppement, une paquet devrait être UNRELEASED. Lors de faire un release,
on change l´étiquette pour *unstable*, suivant les habitudes de Debian. En debian:

* unstable ... un logiciel qui change souvent (des mises-à-jour fréquents)
* testing ... un logiciel dont la version et gélé pour inclusion futur dans une version stable de Debian.
* stable ... un version de logiciel gélé, mise à part des rustines de sécurité.

Metpx-sr3 est encore trop dynamique pour qualifier comme un logiciel *stable* selon
la conventions de Debian, On n´a pas de version qui reste en utilisation durant plusieurs
années pour l´instant.


Releasing
~~~~~~~~~

Lorsque le développement d’une version est terminé. Les événements suivants doivent se produire :

Une balise doit être créée pour identifier la fin du cycle ::

   git checkout development
   git tag -a sarra-v3.16.01a01 -m "release 3.16.01a01"
   git push
   git push origin sarra-v3.16.01a01

Une fois que la balise est là dans la branche development, il faut promouvoir sur main::

   git checkout main
   git merge development
   git push

Une fois en main, les images docker seront automatiquement mises à niveau, mais nous devons ensuite mettre à jour
les différentes méthodes de distribution: `PyPI`_, et `Launchpad`_

Une fois la génération du package terminée, il faut `Création d´une version`_
dans development à l’incrément logique suivant pour s’assurer qu’aucun autre développement
identifié comme la version publiée ne se produit.


PyPi
~~~~

Pypi Credentials vont dans ~/.pypirc.  Exemple de contenu::

  [pypi]
  username: SupercomputingGCCA
  password: <get this from someone>

En supposant que les informations d’identification de téléchargement pypi sont en place, le téléchargement
d’une nouvelle version était auparavant une ligne unique::

    python3 setup.py bdist_wheel upload

sur des systèmes plus anciens ou plus récents::

   python3 -m build --no-isolation
   twine upload dist/metpx_sarracenia-2.22.6-py3-none-any.whl

Notez que le fichier CHANGES.rst est en texte restructuré et est analysé par pypi.python.org lors du téléchargement.

.. Note::

   Lors du téléchargement de packages en version préliminaire (alpha, bêta ou RC), PYpi ne les sert pas aux utilisateurs par défaut.
   Pour une mise à niveau transparente, les premiers testeurs doivent fournir le ``--pre`` switch à pip::

     pip3 install --upgrade --pre metpx-sarracenia

   À l’occasion, vous souhaiterez peut-être installer une version spécifique::

     pip3 install --upgrade metpx-sarracenia==2.16.03a9

   L’utilisation de setup.py par ligne de commande est déconseillée.  Remplacé par build and twine.

Launchpad
~~~~~~~~~

Build Automatisée
+++++++++++++++++

* Assurez-vous que le miroir de code est mis à jour en vérifiant les **Détails de l’importation** en vérifiant
  `Cette page pour Sarracenia <https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk>`_
* Si le code n’est pas à jour, faites **Import Now** , et attendez quelques minutes pendant qu’il est mis à jour.
* Une fois le référentiel à jour, procédez à la demande de build.
* Accédez à la recette `sarracenia release <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-release>`_
* Accédez à la recette `sr3 release <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-release>`_
* Cliquez sur le bouton **Request Build(s)** pour créer une nouvelle version.
* pour Sarrac, suivez la procédure `here <https://github.com/MetPX/sarrac#release-process>`_
* Les packages construits seront disponibles dans le
  `metpx ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_

Ubuntu 18.04
++++++++++++

Pour ubuntu 18.04 (bionique), il y a quelques problèmes. La recette s’appelle: metpx-sr3-daily-bionic, et il
prend la source à partir d’une branche différente : *v03_launchpad*. Pour chaque version, cette branche
doit être rebasée à partir de *development*

* git checkout v03_launchpad
* git rebase -i development
* git push
* import source
* Request build from *metpx-sr3-daily-bionic* Recipe.

En quoi cette branche *v03_launchpad* est-elle différente ? Elle:

* Supprime la dépendance sur python3-paho-mqtt car la version dans le *repository* d´ubuntu est trop ancienne.
* Suppression de la dépendance sur python3-dateparser, car ce paquet n’est pas disponible dans le *repository* d´ubuntu.
* remplacer la cible de test dans debian/rules, parce que tester sans les dépendances échoue ::

     override_dh_auto_test:
   	echo "disable on 18.04... some deps must come from pip"

The missing dependencies should be installed with pip3.



Création d’un programme d’installation Windows
++++++++++++++++++++++++++++++++++++++++++++++

On peut également construire un programme d’installation Windows avec cela
`script <https://github.com/MetPX/sarracenia/blob/main/generate-win-installer.sh>`_.
Il doit être exécuté à partir d’un système d’exploitation Linux (de préférence Ubuntu 18)
dans le répertoire racine de git de Sarracenia. 

déterminer la version de python::

    fractal% python -V
    Python 3.10.12
    fractal%


C'est donc python 3.10. Une seule version mineure aura le package intégré nécessaire
par pynsist pour construire l'exécutable. On valide chez::

   https://www.python.org/downloads/windows/

afin to confirmer que la version avec un binaire *embedded* pour 3.10 et le 3.10.11
Ensuite, à partir du shell, exécutez ::

 sudo apt install nsis
 pip3 install pynsist wheel
 ./generate-win-installer.sh 3.10.11 2>&1 > log.txt

Le paquet final doit être placé dans le répertoire build/nsis.


Builds quotidiennes
+++++++++++++++++++

Les builds quotidiennes sont configurées à l’aide de
`cette recette Python <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-daily>`_
et `cette recette pour C <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sarrac-daily>`_ et
sont exécutés une fois par jour lorsque des modifications sont apportées au référentiel.These packages are stored in the
Ces packages sont stockés dans le `metpx-daily ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily>`_.
On peut également **Request Build(s)** à la demande si vous le souhaitez.

Processus manuel
++++++++++++++++

Le processus de publication manuelle des packages sur Launchpad ( https://launchpad.net/~ssc-hpc-chp-spc )
implique un ensemble d’étapes plus complexes, et donc le script pratique ``publish-to-launchpad.sh`` sera
le moyen le plus simple de le faire. Actuellement, les seules versions prises en charge sont **trusty** et **xenial**.
La commande utilisée est donc la suivante ::

    publish-to-launchpad.sh sarra-v2.15.12a1 trusty xenial


Toutefois, les étapes ci-dessous sont un résumé de ce que fait le script :

- pour chaque distribution (precise, trusty, etc) mettez à jour ``debian/changelog`` pour refléter la distribution
- Générez le package source en utilisant ::

    debuild -S -uc -us

- signez les fichiers ``.changes`` et ``.dsc``::

    debsign -k<key id> <.changes file>

- Télécharger vers Launchpad::

    dput ppa:ssc-hpc-chp-spc/metpx-<dist> <.changes file>

**Remarque :** Les clés GPG associées au compte du tableau de bord doivent être configurées
afin de faire les deux dernières étapes.

Rétroportage d’une dépendance
+++++++++++++++++++++++++++++

Exemple::

  backportpackage -k<key id> -s bionic -d xenial -u ppa:ssc-hpc-chp-spc/ubuntu/metpx-daily librabbitmq


Création d’un RPM
+++++++++++++++++

Ce processus est actuellement un peu maladroit, mais il peut fournir des packages RPM utilisables.
Exemple de création d’une image multipasse pour fedora à construire avec::

  fractal% multipass launch -m 8g --name fed34 https://mirror.csclub.uwaterloo.ca/fedora/linux/releases/34/Cloud/x86_64/images/Fedora-Cloud-Base-34-1.2.x86_64.raw.xz
  Launched: fed34                                                                 
  fractal%

Basé sur https://www.redhat.com/sysadmin/create-rpm-package ...  installer les dépendances de build::

  sudo dnf install -y rpmdevtools rpmlint git
  git clone -b development https://github.com/MetPX/sarracenia sr3

On peut construire un type très limité de paquet rpm sur une distribution basée sur rpm
en utilisant les distutils python::

   python3 setup.py bdist_rpm

Cela échouera en essayant d’ouvrir un CHANGES.txt qui n'existe pas ... Une étrange incompatibilité. Alors,

  **Commentez les deux lignes de setup.py utilisées pour définir le long_description**,

Ces lignes::

   #long_description=(read('README.rst') + '\n\n' + read('CHANGES.rst') +
   #                   '\n\n' + read('AUTHORS.rst')),
 
Et puis la génération RPM se terminera. Malheureusement, il n’ajoute pas de dépendances appropriées,
on peut donc les installer manuellement.

Une façon de résoudre le problème de dépendance est de décoder les options de debian/control ::

   [ubuntu@fed34 sr3]$ grep Recommends debian/control | sed 's/Recommends: //;s/ //g'
   ncftp,wget
   [ubuntu@fed34 sr3]$ 

et répétez avec le fichier setup.py...  (Note: setup.py ne veut pas d’espaces autour des versions
pour les paquets python, mais l'option bdist_rpm les nécessite, alors corrigez cela... )::

   [ubuntu@fed34 sr3]$ tail -4 setup.py |  egrep -v '\[' | egrep -v ']' | tr '\n' ' ' | sed 's/ *//g;s/>=/ >= /g;s/^"/"python3-/;s/,"/,"python3-/g'
   "python3-amqp","python3-appdirs","python3-watchdog","python3-netifaces","python3-humanize","python3-jsonpickle","python3-paho-mqtt >= 1.5.1","python3-paramiko","python3-psutil >= 5.3.0"
   [ubuntu@fed34 sr3]$ 

Ensuite, copiez/collez les dépendances dans la ligne de construction RPM::

   python3 setup.py bdist_rpm --requires=ncftp,wget,"python3-amqp","python3-appdirs","python3-watchdog","python3-netifaces","python3-humanize","python3-jsonpickle","python3-paho-mqtt >= 1.5.1","python3-paramiko","python3-psutil >= 5.3.0"

On peut vérifier si les dépendances sont là comme ça::
  
  [ubuntu@fed34 sr3]$ rpm -qp dist/metpx-sr3-3.0.6-1.noarch.rpm --requires
  /usr/bin/python3
  ncftp
  python3-amqp
  python3-appdirs
  python3-humanize
  python3-jsonpickle
  python3-netifaces
  python3-paho-mqtt >= 1.5.1 
  python3-paramiko
  python3-psutil >= 5.3.0
  python3-watchdog
  rpmlib(CompressedFileNames) <= 3.0.4-1
  rpmlib(FileDigests) <= 4.6.0-1
  rpmlib(PartialHardlinkSets) <= 4.0.4-1
  rpmlib(PayloadFilesHavePrefix) <= 4.0-1
  rpmlib(PayloadIsZstd) <= 5.4.18-1
  wget
  [ubuntu@fed34 sr3]$

Vous pouvez voir toutes les dépendances python3 préfixées requises, ainsi que les paquets d’accellerator
binaires recommandés sont répertoriés. Ensuite, si vous installez avec dnf install, il les attirera tous.
Malheureusement, cette méthode ne permet pas de spécifier la version des dépendances python qui sont
supprimées. sur Fedora 34, ce n’est pas un problème, car toutes les versions sont assez récentes.
Un tel paquet devrait bien s’installer.


Un peu inélégant, et pas sûr que cela fonctionnera avec les anciennes versions::
`Aide recherchée  <https://github.com/MetPX/sarracenia/issues57>`_


github
------

Cliquez sur Releases, modifiez la release :

* Devrions-nous avoir des noms de sortie?
* copier/coller des modifications de CHANGES.rst
* copier/coller le bit d’installation à la fin d’une version précédente.
* Construire des paquets localement ou télécharger à partir d’autres sources.
  Glissez-déposez dans la version.

Cela nous donnera la possibilité d’avoir d’anciennes versions disponibles.
launchpad.net ne semble pas garder les anciennes versions.

Environnement de développement
------------------------------


Local Python
~~~~~~~~~~~~

Utilisation d’une version non packagée :

.. Note::

    python3 setup.py build
    python3 setup.py install


Windows
~~~~~~~

Installez winpython à partir de github.io version 3.4 ou supérieure.
Utilisez ensuite pip pour installer à partir de PyPI.



Conventions
-----------

Vous trouverez ci-dessous quelques pratiques de codage destinées à guider les développeurs lorsqu’il
contribuent à Sarracenia. Ce ne sont pas des règles strictes, juste des conseils.

Quand signaler
~~~~~~~~~~~~~~

sr_report(7) Les messages de notification doivent être émis pour indiquer la disposition finale des
données elles-mêmes, et non des notifications ou des messages de rapport (ne signalez pas les messages
de rapport, cela devient une boucle infinie!) Pour le débogage et d’autres informations, le fichier
journal local est utilisé.  Par exemple, sr_shovel n’émet aucun message sr_report(7), car aucune
donnée n’est transférée, seulement des messages.


Adding a New Dependency
-----------------------

Dependency Management is a complicated topic, because python has many different installation methods into disparate environments, and Sarracenia is multi-platform.  Standard python practice for dependencies is to make
them *required* by listing them in requirements.txt or setup.py, and require all users to install them.
In most python applications, if a dependency is missing, it just crashes with a import failure message
of some kind.

In Sr3, we have found that there are many different environments being deployed into where satisfying
dependencies can be more trouble than they are worth, so each of the dependencies in setup.py are also
dealt with in sarracenia/featuredetection, and the feature detection code allows the application to
keep working, just without the functionality provided by the missing module. This is called *degradation*
or *degraded mode*. The idea being to help the user do as much as they can, in the environment they have,
while telling them what is missing, and what would ideally be added.
  
La gestion des dépendances est un sujet compliqué, car python a de nombreuses méthodes d'installation 
différentes dans des environnements disparates, et Sarracenia est multi-plateforme. La pratique standard 
de python pour les dépendances consiste à faire les *nécessaires* en les listant dans requirements.txt 
ou setup.py, et demandez à tous les utilisateurs de les installer.  Dans la plupart des applications 
python, si une dépendance est manquante, elle se bloque simplement avec un message d'échec d'importation
de quelques sortes.

Dans Sr3, nous avons constaté qu'il existe de nombreux environnements différents déployés dans lesquels
les dépendances peuvent être plus gênantes qu'elles n'en valent la peine, donc chacune des dépendances 
dans setup.py est également traité dans sarracenia/featuredetection, et le code de détection de 
fonctionnalité permet à l'application de continuer à travailler, juste sans la fonctionnalité fournie 
par le module manquant. C'est ce qu'on appelle la *dégradation* ou *mode dégradé*. L'idée étant 
d'aider l'utilisateur à faire le maximum, dans l'environnement dont il dispose, tout en leur disant
ce qui manque, et ce qu'il faudrait idéalement ajouter.

pleine discussion (en anglais seulement): 

`Managing Dependencies (Discussion) <https://github.com/MetPX/sarracenia/issues/741>`_

version courte:

En plus de requirements.dev/setup.py, si vous devez ajouter une nouvelle bibliothèque qui ne fait pas partie de
*piles incluses*, généralement fournies par un package os ou pip séparé, alors vous voulez
prévoir que sr3 fonctionne toujours dans le cas où le package n'est pas disponible (bien que
sans la fonction que vous ajoutez) et pour ajouter un support pour expliquer ce qui manque en utilisant
le module sarracenia/featuredetection.py.

Dans ce module se trouve une structure de données *features*, où vous ajoutez une entrée expliquant 
l'importation nécessaire et les fonctionnalités qu'il apporte à Sr3. Vous ajoutez également les 
protections if feature['x']['present'] dans le code où vous utilisez la fonctionnalité, afin de 
permettre au code de se dégrader avec élégance.

Si la dépendance est ajoutée dans un plugin, alors il y a aussi une méthode pour celle décrite ici :

`Guide de Programmeur<../Explication/SarraPluginDev.html#ajout-de-dependance-python-dans-les-callbacks>`_
