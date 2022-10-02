==============================
 MetPX-Sarracenia Installation
==============================


Revision Record
---------------

:version: @Version@
:date: @Date@


Installation Client
-------------------

Le logiciel est construit pour python version 3.4 ou supérieure. Sur les systèmes où
ils sont disponibles, les paquets debian sont recommandés. On peut les obtenir à partir du répertoire « launchpad ». Si vous ne pouvez pas utiliser les paquets debian, alors considérez les paquets pip.
disponibles chez PyPI. Dans les deux cas, les autres paquets python (ou dépendances) nécessaires seront installés automatiquement par le gestionnaire de paquets.


Ubuntu/Debian (apt/dpkg)
~~~~~~~~~~~~~~~~~~~~~~~~

Sur la version Ubuntu >= 18.04 et dérivées::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install python3-metpx-sarracenia  # supporte seulement HTTP/HTTPS
  sudo apt-get install python3-paramiko   # rajoute les transferts SFTP
  sudo apt-get install sarrac # client binaire (C) optionnel

optionnel::

  sudo apt install python3-dateparser 

Ca se peut qu'avant 22.04 il n'y a pas de paquet debian pour date parser. Dans ce cas, on peut
installer avec pip::

  pip install dateparser

Si dateparser n'est pas installé, le composant *poll* ne va pas être fonctionnel.  Mais le reste
des composantes seront correctes.

Redhat/Suse distros (rpm based)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Le module distutils de python ne génère, est ne gère pas bien les dépendences de paquets,
alors il faut les installer manuelement::
 
  sudo dnf install python3-amqplib
  sudo dnf install python3-appdirs
  sudo dnf install python3-watchdog
  sudo dnf install python3-netifaces
  sudo dnf install python3-humanize
  sudo dnf install python3-psutil
  sudo dnf install python3-paramiko   # rajoute SFTP 

  sudo dnf install python3-dateparser # peux ne pas être disponible.

  # dateparser le seul de ces paquets qui est optionnel. la manque va
  # empêcher le composant *poll* de marcher, mais les reste des composants
  * ne seront pas affectés.

  sudo dnf install python3-setuptools # needed to build rpm package.

Là, on peut générer le paquet RPM::

  git clone https://github.com/MetPX/sarracenia
  cd sarracenia

  python3 setup.py bdist_rpm
  sudo rpm -i dist/*.noarch.rpm

Et voilà.  Le C manque à l´appel, par exemple.
Veuillez consulter la documentation de l´implantation C pour de détails
sur l´installation de celui-ci.

PIP
~~~

Sur Windows, ou d'autres distributions linux où les paquets système ne sont pas disponibles, les procédures ci-dessus ne s’appliquent pas. Il y a aussi des cas particuliers, comme l'utilisation de
python dans virtual env, où il est plus pratique d'installer le paquet en utilisant la commande
pip (paquet d'installation de python) de `<http://pypi.python.org/>`_. Pour cela, c'est très simple:

  sudo pip install metpx-sarracenia

et à mettre à jour après l'installation initiale::

  sudo pip uninstall metpx-sarracenia
  sudo pip install metpx-sarracenia


NOTE:: 
    
   Sur de nombreux systèmes où les versions pythons 2 et 3 sont installées, vous pouvez avoir besoin de spécifier
   pip3 plutôt que pip.


Windows
~~~~~~~

N'importe quelle installation native python fera l'affaire, mais les dépendances dans le python.org standard
nécessite l'installation d'un compilateur C, donc ça devient un peu compliqué. Si vous avez 
une installation python existante qui fonctionne avec c-modules etc, alors, le paquet au complet (pip) devrait s’installer avec toutes les fonctionnalités.

Si vous n'avez pas un environnement python à portée de main, alors le plus facile à utiliser.
est winpython, qui inclut de nombreux modules scientifiquement pertinents, et installera facilement toutes les dépendances pour Sarracenia. Vous pouvez obtenir winpython à partir 
de `<http://winpython.github.io/>`_ (note : sélectionnez python version >3) Puis on peut 
installer avec pip (comme ci-dessus).



Paquets
~~~~~~~

Les paquets Debian et les librairies python peuvent être téléchargés directement à partir 
de: `launchpad <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx/+packages>`_

Source
------

Le code source de chaque module est disponible sur `<https://github.com/MetPX>`_:


 git clone https://github.com/MetPX/sarracenia sarracenia
 cd sarracenia


Le développement se fait sur la branche *master*.  On veut probablement une vraie version,
donc lancez git tag, et vérifiez la dernière version stable:

  blacklab% git tag
    
  .
  .
  .
  v2.18.04b2
  v2.18.04b3
  v2.18.04b4
  v2.18.04b5
  v2.18.05b1
  v2.18.05b2
  v2.18.05b3
  v2.18.05b4

  blacklab% git checkout v2.18.05b4
  blacklab% python3 setup.py bdist_wheel
  blacklab%  pip3 install dist/metpx_sarracenia-2.18.5b4-py3-none-any.whl



Sarrac
------

Le client C est disponible dans les binaires pré-construits des dépôts launchpad avec les paquets python:

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install sarrac 

Dans toutes les versions récentes de Ubuntu, librabbitmq-0.8.8.0 a été rétroporté dans la dépendance PPA de Sarrac.
Pour d'autres architectures ou distributions, on peut construire à partir des sources::

  git clone https://github.com/MetPX/sarrac 

sur n'importe quel système linux, tant que la dépendance librabbitmq est satisfaite. Notez que le paquet ne fonctionne sur aucun systèmes non linux.

Bâtir sur d'anciens systèmes
-----------------------

Sarracenia nécessite python3, et python lui-même ne supporte pas python3 plus vieux que 3.4. Quelques distributions 
plus agées de Linux n'ont pas de python3 ou ont une version tellement ancienne qu'il est difficile d’installer  les dépendances nécessaires.

Sur Ubuntu 12.04:

  apt-get install python3-dev
  apt-get install python3-setuptools
  easy_install3 pip==1.5.6
  pip3 install paramiko==1.16.0
  pip3 install metpx_sarracenia==<latest version>

.. note::
  **Pourquoi utiliser une version spécifique avec des anciennes distributions**

   pip > 1.5.6 ne supporte pas python < 3.2 ce qui est le python de défaut sur Ubuntu 12.04.

   Les versions plus récentes de paramiko requièrent le module *cryptography*
   qui est incompatible avec python 3.2 alors il faut utiliser une veille version de paramiko avec pyCrypto.

Sarracenia fonctionne toujours en python 3.2, mais il y a des fonctionnalités cosmétiques réduites.
Lorsque vous avez du mal à installer la Sarracenia, vous pouvez considérer le client C
client (sarrac) car il a moins de dépendances et devrait être plus facile à construire sur 
des systèmes plus anciens.











