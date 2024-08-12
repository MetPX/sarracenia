=======================================
Publier une Version de MetPX-Sarracenia
=======================================

:version: |release|
:date: |today|


Processus de Pre-Publication
----------------------------

Pour publier une nouvelle version, on commence avec une *pre-release*, et, après une période 
de vérification, la publication d´une version stable. MetPX-Sarracenia est distribué de 
différentes manières, et chacune a son propre processus de construction.  Les versions 
packagées sont toujours préférables aux versions uniques, car elles sont reproductibles.

Pour publier une pré-version, il faut :

- en commençant par la branche développement (pour sr3) ou v2_dev (pour v2.)
- exécuter le processus d'assurance qualité sur tous les systèmes d'exploitation à la recherche de régressions sur les anciens systèmes basés sur 3.6.

   - github exécute des tests de flux pour Ubuntu 20.04 et 22.04, examinez ces résultats.
   - github exécute des tests unitaires (ne fonctionne que sur les versions les plus récentes de Python.), examinez ces résultats.
   - trouver le serveur Ubuntu 18.04. créez un package local, exécutez des tests de flux.
   - trouver le serveur Redhat 8. package de construction : *python3 setup.py bdist_rpm*, exécutez des tests de flux
   - recherchez le serveur Redhat 9, construisez le package : *python3 -m build --no-isolation*. exécuter des tests de flux

- examinez Debian/changelog et mettez-le à jour en fonction de toutes les fusions (merge) vers la branche depuis la version précédente.
- Définissez la balise (tag) de pré-version.
- commettre ce qui précède.

- pypi.org

   - pour assurer la compatibilité avec python3.6, mettre à jour une branche python3.6 (pour redhat 8 et/ou ubuntu 18.)
   - utilisez la branche python3.6 pour publier sur pypi (car la compatibilité ascendante fonctionne, mais pas vers le bas.)
   - téléchargez la pré-version pour que l'installation avec pip réussisse.


- launchpad.org :

   * assurez-vous que les deux branches sont prêtes sur github.
       * Branche préliminaire prête.
       * Branche pre-release_py36 prête.
   * mettre à jour le référentiel git (importer maintenant) : https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk
       * faire : **Import Now**
   * exécutez la recette pour l'ancien système d'exploitation (18.04, 20.04) https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-pre-release-old
       * faire : **Request Build** (sur Focal et Bionic)
   * exécutez la recette pour le nouveau système d'exploitation (22.04, 24.04) https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-pre-release
       * faire : **Request Build** (au moins sur Jammy and Noble)

- créer des packages RedHat.

   - trouver le serveur Redhat 8. package de construction : python3 setup.py bdist_rpm
   - trouver le serveur Redhat 9, package de construction : python3 -m build --no-isolation

- sur github : rédiger une version.

   - créez des notes de version lorsque vous y êtes invité.
   - copiez les instructions d'installation d'une version précédente (principalement pour Ubuntu.)
   - attacher:
     - roue construite sur python3.6 sur Ubuntu 18 (téléchargée sur pypi.org)
     - Windows binaire.
     - des redhat 8 et 9 tours étiquetés comme tels.

- encourager les tests de pré-version, attendre un certain temps pour les bloqueurs, le cas échéant.


Processus de Publication de Version Stable
------------------------------------------

Une version stable est simplement une version préliminaire qui a été
re-étiqueté comme stable après une certaine période d'attente pour les problèmes
se lever. Puisque tous les tests ont été effectués pour la pré-version,
la version stable ne nécessite aucun test explicite.

* fusionner de la pre-release à la version stable : :

  git checkout stable
  git merge pre-release
  # il y aura des conlits à résoudre pour les fichier: debian/changelog and sarracenia/_version.py
  # Pour le changelog:
  #   - joindre les changements pour tous les rcX dans une seule block pour la version stable.
  #   - assurer que la version en haut du block est juste et étiqueté: *unstable*
  #   - editer la signature pour avoir le bon responsable et date pour le relache.
  # pour sarracenia/_version.py
  #   - ajuster pour qu´il contienne la bonne version.
  git tag -a v3.xx.yy -m "v3.xx.yy"
  git push origin v3.xx.yy

* fusionner de la pre-release_py36 à stable_36::

  git checkout stable_py36
  git merge pre-release_py36
  # les mêmes ajustements que pour la version stable.
  git tag -a o3.xx.yy -m "o3.xx.yy"
  git push origin v3.xx.yy

* sur Launchpad.net

  * Branche stable prête.
  * Branche stable_py36 prête.
  * https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk
  * faire : **Import Now**
  * https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-old
  * faire : **Request Build** (sur Focal et Bionic)
  * https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3
  * faire : **Request Build** (au moins sur Jammy and Noble)

* sur re
  * go on redhat 8, build rpm::

  git checkout stable_py36
  python3 setup.py bdist_rpm

* go on redhat 9, build rpm::

  git checkout stable_py36
  rpmbuild --build-in-place -bb metpx-sr3.spec


* Sur github.com, *Create a Release from a tag*

  * copie/coller procédure d´installation d´un vieux relâche.
  * télécharger en pièce-jointe: un .whl 
  * télécharger en pièce-jointe:  redhat 8 rpm
  * télécharger en pièce-jointe:  redhat 9 rpm
  * télécharger en pièce-jointe:  windows.exe


Detailles
---------


Assurance de Qualité
~~~~~~~~~~~~~~~~~~~~

Le processus d'assurance qualité (AQ) se déroule principalement dans la branche développement.
avant d'accepter une contribution, et sauf exceptions connues,

* Les tests d'assurance qualité déclenchés automatiquement par les demandes de pull vers 
  la branche de développement devraient tous réussir.
   (Toutes les actions github associées.)
   tests : static, no_mirror, flakey_broker, restart_server,dynamic_flow sont inclus dans "flow.yml"

* Créez une machine virtuelle Ubuntu 18.04 et exécutez les tests de flux pour vous assurer qu'elle fonctionne.
   (méthode d'installation : clonage depuis le développement sur github.)
   tests : statique, no_mirror, flakey_broker, restart_server, Dynamic_flow

* Créez une machine virtuelle Redhat 8 et exécutez le test de flux pour vous assurer qu'il fonctionne.
   (méthode d'installation : clonage depuis le développement sur github.)
   tests : statique, no_mirror, flakey_broker, restart_server, Dynamic_flow

* Créez une machine virtuelle Redhat 9 et exécutez le test de flux pour vous assurer qu'il fonctionne.

* construire un exécutable Windows... tester ?

Pour une discussion approfondie, voir : https://github.com/MetPX/sarracenia/issues/139

Une fois les étapes ci-dessus terminées, le processus de pré-version peut continuer.


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
  X.ypN   #ack! Version corrigé.

Actuellement, 3.00 est toujours stabilisé, de sorte que la convention année/mois n’est pas appliquée.
Les versions sont actuellement 3.00.iibj où:

  * ii -- nombre incrémentiel de versions préliminaires de 3.00
  * j -- incrément bêta.

À un moment donné, 3.00 sera complet et suffisamment solide pour que nous
reprenions la convention année/mois, espérons-le 3.24.

Les versions finales n'ont pas de suffixe et sont considérées comme stables.
Stable devrait recevoir des corrections de bugs si nécessaire de temps en temps.

.. Remarque : Si vous modifiez les paramètres par défaut pour les échanges/files d'attente comme
       partie d'une nouvelle version, gardez à l'esprit que tous les composants doivent utiliser
       les mêmes paramètres ou la liaison échoueront et ils ne pourront pas
       se connecter. Si une nouvelle version déclare une file d'attente ou un échange différent
       paramètres, le moyen le plus simple de mise à niveau (en préservant les données) est de
       vider les files d'attente avant la mise à niveau, par exemple en
       paramètre, l’accès à la ressource ne sera pas accordé par le serveur.
       (??? il existe peut-être un moyen d'accéder à une ressource telle quelle... pas de déclaration)
       (??? devrait faire l'objet d'une enquête)

       La modification de la valeur par défaut nécessite la suppression et la recréation de la ressource.
       Cela a un impact majeur sur les processus...


Définir la version
~~~~~~~~~~~~~~~~~~

Ceci est fait pour *démarrer* le développement d’une version. D´habitude, on fais cela immédiatement
après que la version précedente a été relachée.

* git checkout development
* Modifier ``sarracenia/_version.py`` manuellement et définissez le numéro de version.
* Modifier CHANGES.rst pour ajouter une section pour la version.
* Exécuter dch pour démarrer le journal des modifications de la version actuelle.

  * assurer que UNRELEASED soit l'étiquette de status au lieu de *unstable* (peut-être automatiquement faite par dch) 

* git commit -a 
* git push


Branches Git pour la pré-publication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avant la publication, assurez-vous que tous les tests d'assurance qualité de la section ci-dessus ont été réussis.
Lorsque le développement d’une version est terminé. Les événements suivants devraient se produire :

Un tag doit être créé pour identifier la fin du cycle ::

   git checkout development
   git tag -a v3.16.01rc1 -m "release 3.16.01rc1"
   git push
   git push origin v3.16.01rc1

Une fois la balise (tag) dans la branche de développement, promouvez-la en stable ::

   git checkout pre-release
   git merge development
   git push


Une fois *stable* est mis à jour sur github, les images du docker seront automatiquement mises à jour, mais
il faut ensuite mettre à jour les différentes méthodes de distribution : `PyPI`_, et `Launchpad`_

Une fois la génération du package terminée, il faut « Définir la version »_
en développement jusqu'au prochain incrément logique pour garantir qu'il n'y ait aucun développement ultérieur
se produit et est identifié comme la version publiée.




Configurer une branche compatible Python3.6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Canonical, la société derrière Ubuntu, fournit Launchpad pour permettre à des tiers de créer des applications.
packages pour leurs versions de système d’exploitation. Il s'avère que les versions les plus récentes du système d'exploitation ont des dépendances
qui ne sont pas disponibles sur les anciens. La branche de développement est donc configurée pour s'appuyer sur des versions plus récentes.
versions, mais une branche distincte doit être créée lors de la création de versions pour Ubuntu Bionic (18.04) et
focal (20.04.) La même branche peut être utilisée pour construire sur Redhat 8 (une autre distribution qui utilise Python 3.6)

Après Python 3.7.?, la méthode d'installation passe du setup.py obsolète à l'utilisation de pyproject.toml,
et les outils python *hatch*. Avant cette version, Hatchling n'est pas pris en charge, donc setup.py doit être utilisé.
Cependant, la présence de pyproject.toml trompe setup.py en lui faisant croire qu'il peut l'installer. À
pour obtenir une installation correcte il faut :

* supprimez pyproject.toml (car setup.py est confus.)

* supprimer le dépôt "pybuild-plugin-prproject" de debuan

en détail::

  # on ubuntu 18.04 or redhat 8 (or some other release with python 3.6 )

  git checkout pre-release
  git branch -D pre-release_py36
  git branch stable_py36
  git checkout stable_py36
  vi debian/control
  # remove pybuild-plugin-pyproject from the "Build-Depends"
  git rm pyproject.toml
  # remove the new-style installer to force use of setup.py
  git commit -a -m "adjust for older os"

Ca se peut qu´une *--force* soit requis à un moment donné. e.g.::

  git push origin stable_py36 --force

Une fois la branche mise à jour, procedez aux instructions de Launchpad.


PyPi
~~~~

Parce ce que les pacquets Python sont compatibles vers le haut, mais pas vers le bas, il faut
les créer sur Ubuntu 18.04 (la plus ancienne version de Python et du système d'exploitation 
en utilisation.) afin que les installations pip fonctionnent sur la plus grande varieté
de systèmes.

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



Launchpad.net
-------------

Généralités sur l'utilisation de Launchpad.net (site pour génerer les paquets pour Ubuntu)  pour MetPX-Sarracenia.

Dépôts et recettes
~~~~~~~~~~~~~~~~~~

Pour les systèmes d'exploitation Ubuntu, le site launchpad.net est le meilleur moyen de fournir 
des pacquets entièrement intégrés (construit avec les niveaux de correctifs actuels de toutes 
les dépendances (composants logiciels sur lesquels Sarracenia s'appuie) pour fournir toutes les 
fonctionnalités.)) Idéalement, lors de utilisation d'un serveur, celui-ci devrait utiliser 
l'un des Dépôts, et installer les correctifs automatisés pour les mettre à niveau si nécessaire.

Avant chaque build d'un package, il est important de mettre à jour le miroir du dépôt git sur le tableau de bord.

* https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk
* do: **Import Now**

Attendez que ca soit fini (quelques minutes.)

Dépôts :

* Quotidien https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily (vivant sur dev... )
   devrait, en principe, toujours être correct, mais des régressions se produisent et tous les 
   tests ne sont pas effectués avant chaque contribution dans les branches de développement.
   Recettes:

   * metpx-sr3-daily -- la construction quotidienne automatisée des packages sr3 s'effectue à partir de la branche *development*.
   * sarracenia-daily -- la construction quotidienne automatisée des packages v2 s'effectue à partir de la branche *v2_dev*

* Pré-Release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-pre-release (pour les fonctionnalités les plus récentes.)
   de la branche *développement*. Les développeurs déclenchent manuellement les builds ici lorsque cela semble approprié (tests
   code prêt à être publié.)

   * metpx-sr3-pre-release -- créez à la demande des packages sr3 à partir de la branche de *pre_release*.
   * metpx-sr3-pre-release-old -- build à la demande des packages sr3 à partir de la branche *pre-release_py36*.
   * metpx-sarracenia-pre-release -- build à la demande des packages sr3 à partir de la branche *v2_dev*.

* Release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx (pour une stabilité maximale)
   de la branche *v2_stable*. Après avoir testé sur des systèmes abonnés aux pré-versions, les développeurs
   fusionner de la branche v2_dev dans celle de v2_stable et déclencher manuellement une construction.

   * metpx-sr3 -- à la demande, créez des packages sr3 à partir de la branche *stable*.
   * metpx-sr3-old -- créez à la demande des packages sr3 à partir de la branche *stable_py36*.
   * sarracenia-release -- sur deman, construisez les packages v2 à partir de la branche *v2_stable*.



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
`script <https://github.com/MetPX/sarracenia/blob/stable/generate-win-installer.sh>`_.
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



ubuntu 18
---------

Problème rencontre lors de géneration de pacque pour pypi.org sur ubuntu 18::

  buntu@canny-tick:~/sr3$ twine upload dist/metpx_sr3-3.0.53rc2-py3-none-any.whl
  /usr/lib/python3/dist-packages/requests/__init__.py:80: RequestsDependencyWarning: urllib3 (1.26.18) or chardet (3.0.4) doesn't match a supported version!
    RequestsDependencyWarning)
  Uploading distributions to https://upload.pypi.org/legacy/
  Uploading metpx_sr3-3.0.53rc2-py3-none-any.whl
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████| 408k/408k [00:00<00:00, 120kB/s]
  HTTPError: 400 Client Error: '2.0' is not a valid metadata version. See https://packaging.python.org/specifications/core-metadata for more information. for url: https://upload.pypi.org/legacy/
  ubuntu@canny-tick:~/sr3$ 

On a générer via redhat8 à la place.  Il semble que la version de twine de ubuntu 18 ne soit plus
en mésure de communiquer avec pypi.org. installation avec pip3 aura peut-être aussi regler le bobo.
