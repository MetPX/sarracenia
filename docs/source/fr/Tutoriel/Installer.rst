
=================================
 Installation de MetPX Sarracenia
=================================


Enregistrement de révision
--------------------------

:version: |release|
:date: |today|

L’avez-vous déjà?
-----------------

Si vous êtes sur un serveur avec celui-ci déjà installé, vous pouvez l’appeler comme suit::

    fractal% sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
          total running configs:   0 ( processes: 0 missing: 0 stray: 0 )
    fractal%

Si cela fonctionne, alors vous n’avez pas besoin de l’installer. En supposant que ce n’est pas déjà fait
installé, le package doit-il être installé à l’échelle du système ? ou seulement pour
un seul utilisateur ?  Pour une utilisation par un seul utilisateur, la méthode python  `<#PIP>`_ doit fonctionner,
donnant accès à sr3 a toutes les bibliothèques nécessaires à l’accès programmatique.

Pour une utilisation opérationnelle, un accès administratif peut être nécessaire pour l’installation du package,
et l’intégration avec systemd. Quelle que soit la façon dont il est installé, du traitement
périodique (sur Linux généralement connu sous le nom de *cron jobs*) peut également avoir besoin d’être configuré.

Des fois, Sarracenia peut être partiellement installé. Pour voir un inventaire des modules de Sarracenia
qui sont disponible, on peut se servir de *sr3 features*::

    fractal% sr3 features

    Status:    feature:   python imports:      Description:
    Installed  amqp       amqp                 can connect to rabbitmq brokers
    Installed  appdirs    appdirs              place configuration and state files appropriately for platform (windows/mac/linux)
    Installed  filetypes  magic                able to set content headers
    Installed  ftppoll    dateparser,pytz      able to poll with ftp
    Installed  humanize   humanize             humans numbers that are easier to read.
    Absent     mqtt       paho.mqtt.client     cannot connect to mqtt brokers
    Installed  redis      redis,redis_lock     can use redis implementations of retry and nodupe
    Installed  sftp       paramiko             can use sftp or ssh based services
    Installed  vip        netifaces            able to use the vip option for high availability clustering
    Installed  watch      watchdog             watch directories
    Installed  xattr      xattr                on linux, will store file metadata in extended attributes
    MISSING    clamd      pyclamd              cannot use clamd to av scan files transferred

     state dir: /home/peter/.cache/sr3
     config dir: /home/peter/.config/sr3

    fractal%

le sens de chaque *feature* est expliqué (en anglais) et le modules python nécessaire pour 
permettre cette fonctionalité sont indiqué dans la troisième colonne.

Dans l´exemple on peut voir que pyclamd manque à l´appel, tandis que *paramiko* nécessaire
pour la fonctionallité SFTP est disponible.

Installation Client
-------------------

Le package est conçu pour python version 3.6 ou supérieure. Sur les systèmes où
ils sont disponibles, les paquets debian sont recommandés. Ceux-ci peuvent être obtenus auprès du
référentiel launchpad. Si vous ne pouvez pas utiliser les paquets Debian, envisagez les paquets pip
avialable de PyPI. Dans les deux cas, les autres paquets python (ou dépendances) nécessaires
seront installé automatiquement par le gestionnaire de paquets.

Notez que dans certains cas, le système d'exploitation ne fournit pas tous les
fonctionnalité pour toutes les fonctionnalités, de sorte que l'on peut compléter avec des packages pip, qui
peut être installé à l'échelle du système, dans l'environnement d'un utilisateur ou même dans
venv. Tant que *sr3 features* signale la fonctionnalité comme disponible, elle
être utilisé.



Ubuntu/Debian (apt/dpkg) **Recommandé**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sur Ubuntu 22.04 et dérivés du même::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt update
  sudo apt install metpx-sr3  # pacquet principale.
  sudo apt install metpx-sr3c # client binaire (en C) .
  sudo apt install python3-amqp  # support optionnel pour les courtiers AMWP (rabbitmq)
  sudo apt install python3-paramiko  # support optionnel pour SFTP/SSH 
  sudo apt install python3-magic  # support optionnel pour les entêtes "content-type" dans les messages
  sudo apt install python3-paho-mqtt  # support optionnel pour les courtiers MQTT 
  sudo apt install python3-netifaces # support optionnel pour les vip (haut-disponibilité)
  sudo apt install python3-dateparser python3-pytz # support optionnel pour les sondages ftp. 

Si les paquets ne sont pas disponibles, on peut les remplacer en utilisant python install package (pip)
Actuellement, seuls les paquets Debian incluent des pages de manuel. Les guides sont seulement
disponible dans le référentiel de source. Pour les versions antérieures d’Ubuntu, installez
via pip est requis en raison de dépendances manquantes dans l’environnement python
livré avec des systèmes d’exploitation antérieurs.

Si une option n’est pas installée, mais est nécessaire pour une configuration donnée, alors sr3 le
détectera et se plaindra, et il faut installer le support manquant::


    fractal% sr3 foreground subscribe/data-ingest
    .2022-04-01 13:44:48,551 [INFO] 2428565 sarracenia.flow loadCallbacks plugins to load: ['sarracenia.flowcb.post.message.Message', 'sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'sarracenia.flowcb.log.Log']
    2022-04-01 13:44:48,551 [CRITICAL] 2428565 sarracenia.moth ProtocolPresent support for amqp missing, please install python packages: ['amqp']
    2022-04-01 13:44:48,564 2428564 [CRITICAL] root run_command subprocess.run failed err=Command '['/usr/bin/python3', '/home/peter/Sarracenia/sr3/sarracenia/instance.py', '--no', '0', 'foreground', 'subscribe/data-ingest']' returned non-zero exit status 1.
    
    fractal% 
    fractal% 
    fractal% sudo apt install python3-amqp
    [sudo] password for peter: 
    Reading package lists... Done
    Building dependency tree... Done
    Reading state information... Done
    The following packages were automatically installed and are no longer required:
      fonts-lyx g++-9 libblosc1 libgdk-pixbuf-xlib-2.0-0 libgdk-pixbuf2.0-0 libjs-jquery-ui liblbfgsb0 libnetplan0 libqhull-r8.0 libstdc++-9-dev python-babel-localedata
      python-matplotlib-data python-tables-data python3-alabaster python3-brotli python3-cycler python3-decorator python3-et-xmlfile python3-imagesize python3-jdcal python3-kiwisolver
      python3-lz4 python3-mpmath python3-numexpr python3-openpyxl python3-pandas-lib python3-protobuf python3-pymacaroons python3-pymeeus python3-regex python3-scipy python3-sip
      python3-smartypants python3-snowballstemmer python3-sympy python3-tables python3-tables-lib python3-tornado python3-unicodedata2 python3-xlrd python3-xlwt sphinx-common
      unicode-data
    Use 'sudo apt autoremove' to remove them.
    Suggested packages:
      python-amqp-doc
    The following NEW packages will be installed:
      python3-amqp
    0 upgraded, 1 newly installed, 0 to remove and 1 not upgraded.
    Need to get 0 B/43.2 kB of archives.
    After this operation, 221 kB of additional disk space will be used.
    Selecting previously unselected package python3-amqp.
    (Reading database ... 460430 files and directories currently installed.)
    Preparing to unpack .../python3-amqp_5.0.9-1_all.deb ...
    Unpacking python3-amqp (5.0.9-1) ...
    Setting up python3-amqp (5.0.9-1) ...
    fractal% 
    
On peut satisfaire les exigences manquantes en utilisant des paquets Debian ou pip.  pour utiliser les courtiers mqtt avec
ubuntu 18.04, il faut obtenir la bibliothèque via pip, car les paquets debian sont pour une version trop ancienne.::


    fractal% pip3 install paho-mqtt
    Defaulting to user installation because normal site-packages is not writeable
    Collecting paho-mqtt
      Using cached paho_mqtt-1.6.1-py3-none-any.whl
    Installing collected packages: paho-mqtt
    Successfully installed paho-mqtt-1.6.1
    fractal% 


Distributions Redhat/Suse (basées sur rpm)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python distutils sur les distributions basées sur le gestionnaire de paquets redhat ne gère pas les dépendances
avec l’emballage actuel, il faut donc les installer manuellement.
Par exemple, sur fedora 28 obligatoirement::

  $ sudo dnf install python3-appdirs
  $ sudo dnf install python3-humanize
  $ sudo dnf install python3-psutil
  $ sudo dnf install python3-watchdog

Facultatifs::

  $ sudo dnf install python3-paramiko  # support pour SFTP/SSH
  $ sudo dnf install python3-amqp   # support pour les messages AMQP (couriers rabbitmq)
  $ sudo dnf install python3-magic   # support optionnel pour le champs ¨content-type¨  
  $ sudo dnf install python3-netifaces # support optionnel pour l´optio vip
  $ sudo dnf install python3-paho-mqtt # support optionnel pour les courtiers MQTT 

  $ sudo dnf install python3-setuptools # needed to build rpm package.

Si les paquets ne sont pas disponibles, l’un peut remplacer en utilisant python install package (pip)

Une fois les dépendances en place, on peut construire un fichier RPM en utilisant ``setuptools``::

  $ git clone https://github.com/MetPX/sarracenia
  $ cd sarracenia

  $ python3 setup.py bdist_rpm
  $ sudo rpm -i dist/*.noarch.rpm

Cette procédure installe uniquement l’application python (pas celle en C).
Aucune page de manuel ni aucune autre documentation n’est installée non plus.

PIP
~~~

Sur les distributions Windows ou Linux où les packages de système ne sont pas
disponible, ou d’autres cas particuliers, tels que l’utilisation de python dans un virtual env, où
il est plus pratique d’installer le paquet en utilisant pip (python install package)
de `<http://pypi.python.org/>`_.

Il est simple de le faire juste l’essentiel::

  $ pip install metpx-sr3

on pourrait aussi ajouter les extras::

  $ pip install metpx-sr3[amqp,mqtt,vip]  

Si veut avoir tous les extras::

  $ pip install metpx-sr3[all]  

et à mettre à niveau après l’installation initiale::

  $ pip install metpx-sr3

* Pour installer à l’échelle du serveur sur un serveur Linux, préfixez avec *sudo*

NOTE::

  * Sur de nombreux systèmes sur lesquels pythons 2 et 3 sont installés, vous devrez peut-être spécifier pip3 plutôt que pip.

  * En Windows, pour que la fonction de type de fichier fonctionne, il faut manuellement *pip install python-magic-bin*
    Pour plus de détails : https://pypi.org/project/python-magic/

Démarrage et arrêt du système
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si l’intention est d’implémenter une pompe de données, il s’agit d’un serveur ayant un rôle à jouer dans la réalisation
de grandes quantités de transferts de données, alors la convention est de créer une application *sarra*
et de l'organiser pour qu’elle soit démarré au démarrage et arrêté à l’arrêt.

Lorsque Sarracenia est installé à l’aide d’un paquet Debian :

* Le fichier d'unité `SystemD <https://systemd.io>`_ est installé au bon endroit.
* l’utilisateur sarra est créé,

Si vous effectuez l’installation à l’aide de méthodes python3 (pip), ce fichier doit être installé :

    https://github.com/MetPX/sarracenia/blob/development/debian/metpx-sr3.service

au bon endroit. Il peut être installé dans::

    /lib/systemd/system/metpx-sr3.service

une fois installé, il peut être activé de la manière normale. Il s’attendait à un utilisateur de sarra
pour exister, qui pourrait être créé comme ça::

   groupadd sarra
   useradd --system --create-home sarra

Les répertoires doivent être read/write pour sarra.  Les préférences iront dans
~sarra/.config, et les fichiers d’état seront dans ~sarra/.cache, et le
le traitement périodique (voir la prochaine session) doit également être mis en œuvre.

Traitement périodique/Tâches Cron
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Quelle que soit la façon dont il est installé, un traitement périodique supplémentaire peut être nécessaire:

  * pour exécuter *sr3 sanity* pour s’assurer que les processus appropriés sont en cours d’exécution.
  * pour nettoyer les anciens répertoires et éviter de remplir le systèmes de fichiers.

exemples::

  # tuer les processus errants ou redémarrer ceux qui auraient pu mourir.
  # en évitant le haut de l’heure ou le bas.
  7,14,21,28,35,42,49,56 * * * sr3 sanity
  # exemple de travaux de nettoyage de répertoire, le script est inclus dans exemples / sous-répertoire.
  17 5,11,17,23 * * *    IPALIAS='192.168.1.27';RESULT=`/sbin/ip addr show | grep $IPALIAS|wc|awk '{print $1}'`; if [ $RESULT -eq 1 ]; then tools/old_hour_dirs.py 6 /Projects/web_root ; fi  






Windows
~~~~~~~

Sous Windows, il existe 2 (autres) options possibles :

**Sans Python**
 Téléchargez le fichier d’installation de Sarracenia à partir de `here <https://hpfx.collab.science.gc.ca/~pas037/Sarracenia_Releases>`_,
 exécutez-le et suivez les instructions.
 N’oubliez pas d’ajouter *Le répertoire Python de Sarracenia* à votre *PATH*.

**Avec Anaconda**
 Créez votre environnement avec le `file <../windows/sarracenia_env.yml>`_ suggéré par ce référentiel.
 L’exécution de cette commande à partir de l’invite Anaconda devrait tout installer::

  $ conda env create -f sarracenia_env.yml

Voir `Windows user manual <Windows.rst>`_ pour plus d’informations sur la façon d’exécuter Sarracenia sous Windows.

Paquets
~~~~~~~

Les paquets Debian et les roues python peuvent être téléchargés directement
De: `launchpad <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx/+packages>`_


Source
------

Le code source de chaque module est disponible `<https://github.com/MetPX>`_::

  $ git clone https://github.com/MetPX/sarracenia sarracenia
  $ cd sarracenia

Le développement se fait sur la branche principale.  On veut probablement une vraie release,
alors exécutez git tag et faites un checkout de la dernière (la dernière version stable)::

  $ git tag
    .
    .
    .
    v2.18.05b3
    v2.18.05b4
  $ git checkout v2.18.05b4
  $ python3 setup.py bdist_wheel
  $ pip3 install dist/metpx_sarracenia-2.18.5b4-py3-none-any.whl



Sarrac
------

Le client C est disponible dans des binaires prédéfinis dans les launchpad référentiels aux côtés des paquets python ::

  $ sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  $ sudo apt-get update
  $ sudo apt-get install metpx-sr3c 

Pour toute version récente d’ubuntu. Le librabbitmq-0.8.0 a été rétroporté dans le PPA.
la dépendance de sarrac. Pour d’autres architectures ou distributions, on peut construire à partir de la source ::

  $ git clone https://github.com/MetPX/sarrac 

sur n’importe quel système Linux, tant que la dépendance librabbitmq est satisfaite. Notez que le package ne peux
pas se construire ou s'exécuter sur des systèmes non-Linux.

