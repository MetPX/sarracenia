
====================================
 MetPX-Sarracenia Developer's Guide
====================================

:version: @Version@
:date: @Date@

.. contents::



Outillage
---------

Pour travailler sur la source de la sarracénie, il faut :

- python3. L'application est développée en et dépend des versions de python > 3.
- certains bindings python-amqp (comme python-amqplib pour les implémentations courantes)
- un tas d'autres modules indiqués dans les dépendances (setup.py ou debian/control)
- paramiko. Pour le support de SSH/SFTP, vous devez installer le paquet python-paramiko (lequel
  fonctionne avec python3 même si la documentation dit qu'il s'agit de python2).
- python3 pyftpdlib module, utilisé pour faire tourner un serveur ftps sur un port haut pendant le test de flux.
- git. afin de télécharger les sources depuis le dépôt github.
- un courtier rabbitmq dédié, avec accès administratif, pour exécuter le flow_test.
  Le test de flux crée et détruit les échanges et perturbera tout flux actif sur le courtier.

après avoir cloné le code source::


    git clone https://github.com/MetPX/sarracenia sarracenia
    git clone https://github.com/MetPX/sarracenia sarrac
    cd sarracenia

Le reste du guide suppose que vous y êtes.


Documentation
-------------

Le processus de développement consiste à écrire ce que l'on a l'intention 
de faire ou de faire faire en un fichier texte restructuré dans le 
sous-répertoire doc/design.  Les fichiers qui s'y trouvent fournissent une base
de discussion. Idéalement, l'information qui s'y trouve agit comme un ensemble
de pièces qui peuvent être édité dans la documentation des fonctionnalités au 
fur et à mesure qu'elles sont implémentées.  Généralement le dév sur se
projet se fait en anglais, avec une traduction une fois qu´on a finalisé 
(mais l´inverse est parfaitement possible aussi.)

Chaque nouveau composant sr\_whatever, devrait avoir des pages de manuel 
pertinentes mises en œuvre. Les guides devraient également être révisés pour
tenir compte des ajouts ou des changements :

- `Installer.rst <Install.rst>`_ (Installation)
- `Dev.rst <Dev.rst>`_ (ce guide pour les développeurs)
- `subscriber.rst <subscriber.rst>`_ (un guide pour savoir comment lire les données d'une pompe.).
- `source.rst <source.rst>`_ (un guide pour ceux qui publient des données vers une pompe.).
- `Admin.rst <Admin.rst>`_ (un guide Admininistrator´s).

Lorsqu'il y a de nouvelles sections, elles devraient probablement commencer 
par la conception/ et après passer à la documentation principale.

La documentation française a les mêmes noms de fichiers que la documentation 
anglaise, mais elle a placé sous le sous-répertoire fr/.  C'est plus facile 
si la documentation est produite dans le format les deux langues en même temps. 
Utilisez au moins une traduction automatique aussi (par exemple www.deepl.com) 
pour fournir un point de départ. (et la même procédure à l'envers pour les 
francophones).


Où documenter les options 
~~~~~~~~~~~~~~~~~~~~~~~~~

La plupart des options sont documentées dans sr_subscribe(1), qui est une sorte de *parent* de tous les autres composants de consommation.
Toute option utilisée par plusieurs composants doit y être documentée. Les options qui sont uniques à un
doit être documenté dans la page de manuel de ce composant.

Lorsque la valeur par défaut d'une option varie d'un composant à l'autre, la page de manuel de chaque composant doit indiquer 
l'option par défaut pour ce composant. Sr_sarra, sr_winnow, sr_shovel, et sr_reportent les composants suivants
n'existent que parce qu'ils utilisent la base sr_subscribe avec des valeurs par défaut différentes. Il n'y a pas de différence de code
entre eux.




Développement
-------------

Le développement se produit sur la branche maître, qui peut être dans n'importe quel état à n'importe quel endroit donné.
et on ne devrait pas s'y fier.  De temps en temps, les versions sont étiquetées, et
la maintenance aboutit à une branche.  Les rejets sont classés comme suit :

Alpha
  des instantanés pris directement du master, sans autres garanties qualitatives.
  aucune garantie de fonctionnalité, certains composants peuvent être partiellement implémentés, d'autres non.
  une rupture peut se produire.
  pas de corrections de bogues, problèmes traités par la version suivante.
  Souvent utilisé pour les tests de bout en bout (plutôt que d'installer une version personnalisée à partir de l'arborescence sur
  chaque machine d'essai.

Bêta
  Fonctionnalité Complète pour une version donnée.  Composants dans leur forme finale pour cette version.
  La documentation existe dans au moins une langue.
  Tous les bogues de blocage de version connus précédemment ont été corrigés.
  pas de corrections de bogues, problèmes traités par la version suivante.

RC - Candidat à la libération.
  implique qu'il est passé par la version bêta pour identifier et traiter les principaux problèmes.
  Documentation traduite disponible.
  pas de corrections de bogues, problèmes traités par la version suivante.

Les versions finales n'ont pas de suffixe et sont considérées comme stables et supportées.
Stable devrait recevoir des corrections de bogues si nécessaire de temps en temps.
On peut construire des roues python, ou des paquets debian à des fins de tests locaux.
pendant le développement.

.. Note:: Si vous modifiez les paramètres par défaut pour les échanges / 
      files d'attente en tant que partie d'une nouvelle version, gardez à 
      l'esprit que tous les composants doivent utiliser les mêmes paramètres 
      ou le bind échouera, et ils ne seront pas en mesure de pour se connecter. 
      Si une nouvelle version déclare une file d'attente ou un échange différent.
      le moyen le plus simple de mise à niveau (préservation des données) consiste
      à drainer les files d'attente avant la mise à niveau, par exemple en
      l'accès à la ressource ne sera pas accordé par le serveur.
      ( ????? peut-être qu'il y a un moyen d'avoir accès à une ressource telle quelle... pas de déclaration)
      ( ????? doit faire l'objet d'une enquête)

      La modification de la valeur par défaut nécessite la suppression et la reconstitution de la ressource.
      Cela a un impact majeur sur les processus.....


Python Wheel
~~~~~~~~~~~~

Pour les tests et le développement::

    python3 setup.py bdist_wheel

devrait construire une roue dans le sous-répertoire dist.


Debian/Ubuntu
~~~~~~~~~~~~~

Ce processus construit un fichier.deb local dans le répertoire parent en 
utilisant les mécanismes debian standard. Vérifier la ligne **build-depends** 
dans *debian/control* pour les dépendances qui pourraient être nécessaires 
pour construire à partir des sources. Les étapes suivantes construiront
Sarracenia mais ne signeront pas les changements ou le paquet source::

    cd sarracenia
    sudo apt-get install devscripts install devscripts
    debuild -uc -uc -us
    sudo dpkg -i.../<le paquet qui vient d'être construit>>.


Soumettre des changements
~~~~~~~~~~~~~~~~~~~~~~~~~

Que faut-il faire avant de s'engager dans la branche master ?
Liste de contrôle :

- On développe dans une autre branche. Habituellement la branche sera nommée d'après l'*issue* qu´on traite. Exemple: *issue240*, si on change d´approche et on se reprend, on peut avoir un *issue240_2*. Il est aussi possible qu´on travaille sur des branches plus stratégiques, tel que *v03*. 
- La branche maître doit toujours être fonctionnelle, ne pas soumettre de code (sur master) si le *flow_test* ne fonctionne pas.
- Conséquence naturelle : si le changement de code signifie que les tests doivent changer, inclure le changement de test(s) dans le commit.
- La documentation devrait idéalement recevoir ses mises à jour en même temps que le code.

Il y aura, habituellement, un cycle dévéloppement sur la branche pendant un certain temps. Eventuellement, on va avoir du travail prêt à être incorporé dans la branche principale. La procédure se trouve ici: `Modification à master`_


Tests
-----

Avant de livrer du code à la branche maître, comme mesure de contrôle qualité, il faut exécuter tous les auto-tests disponibles. À cette étape, on présume que les modifications spécifiques du code ont déjà été appliquées à l'unité testée. Ce contrôle réduira les possibilités de régression de la qualité de Sarracenia. Il est aussi essentiel de modifier les autotests afin de bien contrôler les changements qui ont été effectués au code et dans l'optique que ce code test sera réutilisé comme mesure de contrôle pour de futurs changements.

La configuration que l'on essaie de répliquer:

.. image:: ../Flow_test.svg

Hypothèse : l'environnement de test est un PC linux, soit un ordinateur portable/desktop, soit un serveur sur lequel un serveur
peut démarrer un navigateur. Si vous travaillez avec l'implémentation c, le flux suivant est aussi défini:

.. image:: ../cFlow_test.svg

Un flux de travail de développement typique sera::

   git branch issueXXX
   git checkout issueXXX
   cd sarra ; *changements au code*
   cd ..
   debuild -uc -us
   cd ../../sarrac
   debuild -uc -us
   sudo dpkg -i ../*.deb
   cd test
   ./flow_cleanup.sh
   rm directories with state (indicated by flow_cleanup.sh)
   ./flow_setup.sh  # *starts the flows*
   ./flow_check.sh  # *checks the flows*
   ./flow_cleanup.sh  # *cleans up the flows*
   git commit -a # sur la branch issueXXX 

On peut alors étudier les résultats et déterminer le prochain cycle de modifications à apporter. Le reste de cette section documente ces étapes de façon beaucoup plus détaillée. Avant de pouvoir exécuter le flow_test, certains pré-requis doivent être pris en compte.

Installation locale sur le poste de travail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Le flow_test invoque la version de metpx-sarracenia qui est installée sur le système, et non pas ce qu'il y a dans l'arbre de développement.  Il est nécessaire d'installer le paquet sur le système afin qu'il exécute le flow_test.

Dans votre arbre de développement....
On peut soit créer une roue en cours d'exécution soit::

       python3 setup.py bdist_wheel_bdist_wheel

qui crée un paquet de roues sous dist/metpx*.whl.
puis en tant que root installez ce nouveau paquet::

       pip3 install --upgrade ....<path>/dist/metpx*.whl

ou on peut utiliser l'emballage debian::

       debuild -us -uc -uc
       sudo dpkg -i ../python3-metpx-.....

qui accomplit la même chose en utilisant l'empaquetage debian.

Installer les serveurs sur le poste de travail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Installez un minimum localhost broker, configurez les utilisateurs de test avec les informations d'identification stockées pour localhost::


     sudo apt-get install rabbitmq-server
     sudo rabbitmq-plugins enable rabbitmq_management
     echo "amqp://bunnymaster:MaestroDelConejito@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tsource:TestSOUrCs@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tsub:TestSUBSCibe@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tfeed:TestFeeding@localhost/" >>~/.config/sarra/credentials.conf

     cat >~/.config/sarra/default.conf <<EOT

     broker amqp://tfeed@localhost/
     cluster localhost
     admin amqp://bunnymaster@localhost/
     feeder amqp://tfeed@localhost/
     declare source tsource
     declare subscribe tsub
     EOT

     sudo rabbitmqctl delete_user guest
     sudo rabbitmqctl add_user bunnymaster MaestroDelConejito
     sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
     sudo rabbitmqctl set_user_tags bunnymaster administrator
     cd /usr/local/bin
     sudo wget http://localhost:15672/cli/rabbitmqadmin
     chmod 755 rabbbitmqadmin
     sr_audit --users foreground


.. Note::

    Veuillez utiliser d'autres mots de passe dans les informations d'identification pour votre configuration, juste au cas où. Les mots de passe ne doivent pas être codés en dur dans la suite d'auto-test. Les utilisateurs bunnymaster, tsource, tsub et tfeed doivent être utilisés pour l'exécution des tests.

    L'idée ici est d'utiliser tsource, tsub et tfeed comme comptes pour les *broker* et de stocker leurs informations d'identification dans le fichier normal credentials.conf. Aucun mot de passe ou fichier clé ne doit être stocké dans l'arborescence des sources, dans le cadre d'une suite d'auto-test.

Configuration de l'environnement de test de débit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Une partie du test de flux exécute un serveur sftp et utilise les fonctions client sftp.
Besoin du paquet suivant pour cela::

    sudo apt-get install python3-pyftpdlib python3-paramiko

Le script d'installation démarre un serveur web trivial, un serveur ftp et un démon qui invoque sr_post.
Il teste également les composants C, qui doivent être déjà installés.
et définit quelques clients de test fixes qui seront utilisés lors des auto-tests::


    cd sarracenia/test
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


Comme il exécute le setup, il exécute également tous les unit_tests existants.
Ne passez aux tests flow_check que si tous les tests dans flow_setup.sh passent avec succès.


Rouler le flow_test
~~~~~~~~~~~~~~~~~~~

Le script flow_check.sh lit les fichiers journaux de tous les composants 
démarrés, et compare les nombres de messages, à la recherche d'une correspondance 
dans un délai de +- 10% pour exécuter la configuration avant qu'il y ait assez 
de données pour effectuer les bonnes mesures::

     ./flow_check.sh

sortie::


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

    TYPE OF ERRORS IN LOG :

      1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f14_001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan00' in vhost '/'
      1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f15_001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan01' in vhost '/'
    blacklab% 


si le fichier flow_check.sh passe, alors on a une confiance raisonnable dans la fonctionnalité globale du fichier
application python, mais la couverture de test n'est pas exhaustive. c'est la porte la plus basse pour commettre un commit.
change ton code python en branche maître. Il s'agit d'un échantillonnage plus qualitatif du plus grand nombre d'entre eux.
des cas d'utilisation commune plutôt qu'un examen approfondi de toutes les fonctionnalités. Même si ce n'est pas le cas
Il est bon de savoir que les flux fonctionnent.

(à partir de nov. 2017) NOTE : les paquets (deb+pip) sont créés avec une dépendance pour python3-amqplib pour le support AMQP.
Nous voulons migrer vers python3-pika. Par conséquent, les programmes soutiennent maintenant les deux AMQP api. Si vous avez python3-pika
installé, il sera utilisé par défaut. Si vous avez installé amqplib et pika, vous pouvez utiliser l'option::

*use_pika [true/false]*

Utiliser ou non pika. Si vous définissez use_pika sur True et que python3-pika n'est pas installé, les programmes retomberont sur
amqplib.  Les développeurs devraient tester les deux API jusqu'à ce que nous soyons totalement migrés vers PIKA.

Notez que l'abonné *fclean* regarde les fichiers et conserve les fichiers assez longtemps pour qu'ils puissent passer par tous les autres.
tests.  Il le fait en attendant un temps raisonnable (45 secondes, la dernière fois vérifiée) puis il compare le fichier.
qui ont été postées par sr_watch dans les fichiers créés par téléchargement.  Au fur et à mesure que le comptage *sample now* se poursuit,
il imprime "OK" si les fichiers téléchargés sont identiques à ceux postés par sr_watch.   L'ajout de fclean et de fclean
les cfclean correspondants pour le cflow_test, sont cassés.  La configuration par défaut qui utilise *fclean* et *cfclean* garantit que
que seules quelques minutes d'espace disque sont utilisées à un moment donné, ce qui permet des tests beaucoup plus longs.

Par défaut, le flow_test n'est que de 1000 fichiers, mais on peut lui demander de s'exécuter plus longtemps, comme ceci::

 ./flow_check.sh 50000

Accumuler cinquante mille fichiers avant la fin du test.  Ceci permet de tester les performances à long terme, en particulier
l'utilisation de la mémoire au fil du temps et les fonctions d'entretien ménager du traitement on_heartbeat.

Nettoyage du flux
~~~~~~~~~~~~~~~~~

Une fois les tests terminés, le script ./flow_cleanup.sh, qui tuera les serveurs et daemons en cours d'exécution, et
supprimer tous les fichiers de configuration installés pour le test de flux, toutes les files d'attente, les échanges et les journaux.  C'est aussi
doit être effectuée entre chaque exécution de l'essai de débit::
  
  
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



Longueur de l'essai de débit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La longueur de flow_test par défaut est de 1000 fichiers en cours d'exécution à travers les cas de test. dans rapid
développement, on peut fournir un argument pour raccourcir ce qui suit::

  ./flow_test 200

Vers la fin d'un cycle de développement, des flow_tests plus longs sont conseillés::

  ./flow_test 2000000 

pour identifier d'autres problèmes. échantillonnage jusqu'à 100 000 entrées::


  blacklab% ./flow_check.sh 100000
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
  blacklab% 

Ce test a été lancé à la fin de la journée, car cela prend plusieurs heures, et les résultats ont été examinés le lendemain matin.


Test Poigné
~~~~~~~~~~~

Parfois, les tests de flux (en particulier pour les grands nombres) sont bloqués en raison de problèmes avec le flux de données (où plusieurs fichiers se retrouvent
le même nom, et donc les versions antérieures suppriment les versions ultérieures et les tentatives échoueront toujours.  Éventuellement, nous réussirons à nettoyer.
en haut du flux dd.weather.gc.ca, mais pour l'instant un flow_check se bloque parfois'Retrying'. Le test a exécuté tous les messages requis,
et est à une phase de vider les tentatives, mais continue d'essayer de nouveau pour toujours avec un nombre variable d'articles qui ne tombe jamais à zéro.::



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
  Traceback (most recent call last):ing...
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
  AttributeError: 'float' object has no attribute 'encode'
  
  maximum of the shovels is: 100075
  
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
  test 20 success: veille_f34 should post twice as many files (95846) as
  subscribe cdnld_f21 downloaded (47950)
  test 21 success: veille_f34 should post twice as many files (95846) as
  subscribe cfile_f44 downloaded (47896)
  test 22 success: Overall 21 of 21 passed (sample size: 100077) !
  
  NB retries for sr_subscribe t_f30 0
  NB retries for sr_sender 36



Ainsi, dans ce cas, les résultats sont encore bons, même s'ils ne sont pas tout à fait satisfaisants.
capable d'y mettre fin. S'il y a eu un problème important, le cumul
l'indiquerait.


Modification à master
---------------------

Avec l´exception des fautes de frappe, ou de grammaire et/ou style, ou incrémentation
de version, on s´attend que personne fasse des changements directement dans la branche 
master. Tout le travail se fait dans les branches de dévéloppement, et on s´attend que tout 
les tests soient réussis avant d´accepter de modifier master. Si le travail sur une branche 
est fini, ou bien s´il y a un sous-ensemble qu´on estime mérite inclusion, on devrait 
sommariser le travail faite dans la branch, et ensuite soumettre un *pull request* sur github::

::

  git checkout issueXXX
  vi CHANGES.rst # créér une sommaire des changements
  dch  # copie/coller des changements, avec l´ajout d´un espace au début de la ligne.
  vi doc/UPGRADING.rst # si l´usager doit comprendre ou agir en fonction du changement.
  vi doc/fr/UPGRADING.rst # et ou!
  git commit -a
  git push
  # créér un pull request sur github. 
  
Un deuxième dév va réviser la reuête et peut accepter le requête. On s´attend que chaque
*commit* soit révisé afin de le comprendre de façon générale.

Travis-CI note les demandes de *pull* et roule des vérifications d´intégration.  Si ceux-ci
fonctionnent c´est une bonne indication de qualité. Actuellement ces vérifcations sont un
peu fragiles, alors s´ils ne marchent pas, celui qui révise devrait reproduire la configuration
dans son environnement et rouler les tests.  Si ca marche dans un deuxième environnement
de dév, on peut le *merger* en dépit des plaintes de Travis.


Bâtir un *release*
------------------

MetPX-Sarracenia est distribué de différentes manières, et chacun a son propre processus de construction.
Les versions empaquetées sont toujours préférables aux versions uniques, parce qu'elles sont reproductibles.

Lorsque le développement nécessite des tests sur une large gamme de serveurs, il est préférable d'effectuer les opérations suivantes
une version alpha, plutôt que d'installer un seul paquet.  Les mécanismes préférés sont donc les suivants
pour construire les paquets ubuntu et pip au moins, et l'installer sur les machines de test à l'aide de
les dépôts publics pertinents.

Pour publier une version, il faut le faire :

- Définir la version.
- télécharger la version sur pypi.org pour que l'installation avec pip réussisse.
- télécharger la version sur launchpad.net, afin que l'installation des paquets debian
  l'utilisation du référentiel réussit.
- incrémenter la version en master.

Schéma de versionnement
~~~~~~~~~~~~~~~~~~~~~~~

Chaque version sera versionnée en tant que ``<version du protocole>.<YY>.<MMM> <segment>``

Où :

La version protocole est la version message. Dans les messages Sarra, ils 
sont tous préfixés avec v02 (pour le moment).  **YYYY** est les deux derniers
chiffres de l'année de la sortie initiale de la série.  **MM** est un numéro
de mois à DEUX chiffres, c'est-à-dire pour le mois d'avril : 04.
Le segment est ce qui serait utilisé au sein d'une série.  de PEP0440 ::

  X.YaN # Alpha release
  X.YbN # Lancement de la version bêta
  X.YrcN # Release Candidate
  X.Y # Libération finale


Réglage de la version
~~~~~~~~~~~~~~~~~~~~~

Afin de partir la dévéloppement d´une version:

* git checkout master
* Editez ``sarra/__init__init__.py`` manuellement et réglez le numéro de version.
* rajouter une section dans CHANGES.rst pour la nouvelle version.
* dch afin de partir les changements debian pour la nouvelle version.
* git commit -a
* git push 

Si on dévéloppe pendant un mois sans éffectuer un *release*, on devrait
modifier la version dans master pour le garder à jour. Par exemple, 
Si on a commencé en août, et on continue en septembre, pour devrait 
modifier la version en master de 2.19.08b1 à 2.19.09b1 ...


Un *Release*
~~~~~~~~~~~~

Quand on décide qu´il faut publier une nouvelle version (faire un *Release*)
Il faut créér une étiquette en git pour indiquer la fin du cycle de 
dévéloppement::

  git checkout master
  git tag -a sarra-v2.16.01a01 -m "release 2.16.01a01"
  git push
  git push origin sarra-v2.16.01a01

En suite, il faut publier la version avec les procédures suivants: `PyPI`_, and `Launchpad`_

Une fois la génération de paquets complété, on devrait incrementer la version
dans master afin d´eviter la confusion avec la version publier
en incrémentant la version en master avec: `Réglage de la version`



PyPi
~~~~

Pypi Credentials go in ~/.pypirc.  Contenu de l'échantillon: :

  [pypi]
  nom d'utilisateur : SupercomputingGCCA
  mot de passe : <obtenir ceci de quelqu'un>>.

En supposant que les identifiants de téléchargement de pypi sont en place, 
le téléchargement d'une nouvelle version n'était qu'un liner::

    python3 setup.py bdist_wheel 

Cela fonctionne toujours avec setuptools > 24, mais ubuntu 16 n'a que 
la version 20, donc il ne peut plus y être utilisé.  Au lieu de cela, on 
est censé utiliser le paquet *twine*::

   python3 setup.py bdist_wheel_bdist_wheel 
   twine upload dist/metpx_sarracenia-2.17.7a2-py3-none-any.whlhl

Notez que la même version ne peut jamais être téléchargée deux fois.

Un script de commodité a été créé pour construire et publier le fichier *wheel*. Il suffit d'exécuter ``publish-to-pypi.sh`` et il vous guidera dans cette voie.

.. Note ::

   Lorsque vous téléchargez des paquets pré-version (alpha, bêta ou RC), PYpi
   ne les met pas à la disposition des utilisateurs par défaut.
   Pour une mise à niveau sans faille, les premiers testeurs doivent fournir le
   commutateur ``-précédent`` à pip::

       pip3 install --upgrade --pre metpx-sarracenia 

   A l'occasion, vous pouvez souhaiter installer une version spécifique::

     pip3 install --upgrade metpx-sarracenia===2.16.03.03a9


Launchpad
~~~~~~~~~

Construction automatisée
++++++++++++++++++++++++

Assurez-vous que le miroir de code est mis à jour en vérifiant les détails
**Import** en vérifiant `cette page pour la sarracénie 
<https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk>`_
Si le code n'est pas à jour, faites **Import Now**, et attendez quelques 
minutes pendant qu'il est mis à jour. Assurez-vous que le miroir de code est
mis à jour en vérifiant les détails **Import** en vérifiant `cette page pour
sarrac <https://code.launchpad.net/~ssc-hpc-chp-chp-spc/metpx-sarrac/+git/master>`__`.
Si le code n'est pas à jour, faites **Import Now**, et attendez quelques
minutes pendant qu'il est mis à jour.  Une fois que le référentiel est à jour,
procéder à la demande de compilation.  Allez 
au `sarracenia release <https://code.launchpad.net/~ssc-hpc-hpc-chp-spc/+recipe/sarracenia-release>`_ recette (*recipe*)
et similairement pour sarrac.

Constructions quotidiennes
++++++++++++++++++++++++++

Les constructions quotidiennes sont configurées
en utilisant `cette recette pour python <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-daily>`_`https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-daily
et `cette recette pour C <https://code.launchpad.net/~ssc-hpc-chp-chp-spc/+recipe/metpx-sarrac-daily>`_ et
sont exécutés une fois par jour lorsque des modifications sont apportées au référentiel. Ces paquets sont stockés dans le `metpx-daily ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily>`_.
On peut aussi **Demander la construction(s) sur demande si désiré.**



Processus manuel
++++++++++++++++

Le processus de publication manuelle des paquets sur Launchpad ( https://launchpad.net/~ssc-hpc-chp-spc) implique un ensemble plus complexe d'étapes, et donc le script de commodité ``publish-to-launchpad.sh`` sera le moyen le plus facile de le faire. Actuellement, les seules versions supportées sont **trusty** et **xenial**. La commande utilisée est donc::

    publish-to-launchpad.sh sarra-v2.15.12a1 trusty xenial trusty


Cependant, les étapes ci-dessous sont un résumé de ce que fait le script :

pour chaque distribution (précise, fiable, etc) mettre à jour ``debian/changelog`` pour refléter la distribution.
construire le paquet source en utilisant::

    debuild -S -uc -uc -us

signer les fichiers ``.changes`` et ``.dsc``::

    debsign -k<key id> <.changes file>> fichier debsign -k<key id> <.changes

upload sur launchpad::

    dput ppa:ssc-hpc-chp-spc/metpx-<dist> <.changes file> fichier>.

Note:** Les clés GPG associées au compte launchpad doivent être configurées pour effectuer les deux dernières étapes.

Rétroportage d'une dépendance
+++++++++++++++++++++++++++++

Exemple::

  backportpackage -k<key id> -s bionic -d xenial -d xenial -u ppa:ssc-hpc-chip-chp-spc/ubuntu/metpx-daily librabbitmq librabbitmq



Mise à jour du site Web du projet
---------------------------------

Avant mars 2018, le site Web principal du projet était metpx.sf.net.
Ce site MetPX a été construit à partir de la documentation des différents modules.
dans le projet. Il construit en utilisant tous les fichiers **.rst** trouvés
dans le répertoire **sarracénie/doc** ainsi que *certains* des fichiers 
**.rst** trouvés dans le fichier **Sundew/doc**. Au printemps 2018, le 
développement a été transféré sur github.com.  Ce site rend .rst lors de 
l'affichage des pages, donc un traitement séparé pour le transformer n'est 
plus nécessaire.

Sur le site Web actuel, la mise à jour se fait en validant les modifications
apportées aux fichiers.rst directement sur Github. Il n'y a pas de 
post-traitement requis. Comme les liens sont tous les liens et d'autres 
services tels que gitlabl supportent également ce type d'interprétation, 
l'application *website* est portable à gitlab.science, etc....  Et le 
point d'entrée est de le fichier README.rst à la racine de chaque référentiel.

Bâtir Localement
~~~~~~~~~~~~~~~~

Afin de construire les pages HTML, les logiciels suivants doivent être disponibles sur votre poste de travail :

* `dia <http://dia-installer.de/>`_
* `docutils <http://docutils.sourceforge.net/>`_
* `groff <http://www.gnu.org/software/groff/>`_

A partir d'un shell de commande::

  cd site
  fabriquer

note: : le fichier makefile contient une ligne commentée *sed qui remplace.rst par.html dans les fichiers.
Pour construire les pages localement, ce sed est nécessaire, donc ne le commentez pas, mais n'engagez pas le changement.
parce qu'il brisera la procédure de *mise à jour du site Web*.

Mise à jour du site Web
~~~~~~~~~~~~~~~~~~~~~~~

Aujourd'hui, il suffit d'éditer les pages dans le dépôt git, et elles 
seront actives dès qu'elles seront poussées à la branche principale.

Pour publier le site à sourceforge (mise à jour de metpx.sourceforge.net), vous 
devez avoir un compte sourceforge.net et avoir les permissions requises 
pour modifier le site.  A partir d'un shell, lancez::

  make SFUSER=myuser deploy deploy

Seules les pages index-f.html et index-f.html sont utilisées sur le site sf.net.
aujourd'hui. A moins que vous ne vouliez changer ces pages, cette opération est inutile.
Pour toutes les autres pages, les liens vont directement dans les différents fichiers.rst sur
github.com.



Environnement de développement
------------------------------


Python local
~~~~~~~~~~~~

Travailler avec une version non empaquetée :

notes: :

    python3 setup.py build.py build
    python3 setup.py install.py installer


Windows
~~~~~~~

Installez winpython à partir de la version 3.4 ou supérieure de github.io.  Utilisez ensuite pip pour installer à partir de PyPI.


Conventions
-----------

Vous trouverez ci-dessous quelques pratiques de codage destinées à guider les développeurs lorsqu'ils contribuent à la sarracénie.
Il ne s'agit pas de règles strictes et rapides, mais simplement de directives.


Quand fair un *report*
~~~~~~~~~~~~~~~~~~~~~~

sr_report(7) les messages doivent être émis pour indiquer la disposition finale des données elles-mêmes, et non pas la disposition finale.
toute notification ou message de rapport (ne rapportez pas les messages de rapport, cela devient une boucle infinie !
Pour le débogage et d'autres informations, le fichier journal local est utilisé.  Par exemple, sr_shovel fait ce qui suit
n'émettent aucun message sr_report(7), car aucune donnée n'est transférée, seulement des messages.


Ajout d'algorithmes de somme de contrôle


... note: :
   Le fait que l'ajout d'une somme de contrôle nécessite une modification du code est considéré comme une faiblesse.
   Il y aura une API pour être en mesure de plugin checksums à un certain point.  Ce n'est pas encore fait.

Pour ajouter un algorithme de checksum, il faut ajouter une nouvelle classe à sr_util.py, puis modifier sr_config.py.
pour l'associer à une étiquette.  La lecture de sr_util.py rend cela assez clair.
Chaque algorithme a besoin :
un initialisateur (le met à 0)
un sélecteur d'algorithme.
une mise à jour pour ajouter les informations d'un bloc donné à une somme existante,
get_value pour obtenir le hash (généralement après que tous les blocs l'aient mis à jour).

Ceux-ci sont appelés par le code au fur et à mesure que les fichiers sont téléchargés, de sorte que le traitement et le transfert se chevauchent.

Par exemple, pour ajouter l'encodage SHA-2::

  from hashlib import sha256

  class checksum_r(object):
      """
      checksum the entire contents of the file, using SHA256.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = self.filehash.hexdigest()
          return self.value

      def update(self,chunk):
          self.filehash.update(chunk)

      def set_path(self,path):
          self.filehash = sha256()

ensuite en sr_config.py, on le rajoute ainsi::

      if flgs == 'c':
          self.sumalgo = checksum_r()


On peut vouloir ajouter 'r' à la liste des sommes valides dans 
validate_sum( aussi.

Il est prévu pour une future version de faire une interface de plugin pour cela de sorte que l'ajout de sommes de contrôle devient une activité de programmeur d'application.

