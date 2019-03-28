
==============
 SR_Subscribe 
==============

-------------------------------------------------
Sélectionner et télécharger les fichiers publiés
-------------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manuel group: la Suite Metpx-Sarracenia

SYNOPSIS
========

 **sr_subscribe** foreground|start|start|stop|restart|restart|reload|sanity|status fichierDeConfiguration

 **sr_subscribe** cleanup|declare|setup|setup|disable|enable|list|add|remove fichierDeConfiguration

DESCRIPTION
===========

[ `English version <../sr_subscribe.1.rst>`_ ]

.. contents::


Sr_subscribe est un programme pour télécharger des fichiers à partir de sites 
Web ou de serveurs de fichiers qui publient des *avis* en 
format `sr_post(7) <sr_post.7.rst>`_ dès que chaque fichier est disponible.
Les clients se connectent à un
*courtier* (souvent le même que le serveur lui-même) et s'abonnent aux 
*avis*. Le mécanisme de *sr_post* est du *push* véritable
pour les dossiers accessibles sur la toile  
(*web-accessible folders* - WAF), et sont beaucoup plus efficaces que le sondage
périodique des répertoires ou le style ATOM/RSS. Sr_subscribe
peut aussi être configuré pour publier un message une fois un fichier téléchargé 
afin d'informer d´autres processus locaux de la disponibilité de ce fichier.

**sr_subscribe** peut également être utilisé à d'autres fins que le téléchargement, 
(par exemple pour fournir un programme externe) en spécifiant le -n (*notify_only*, 
ou *no download*) pour prévenir le téléchargement et n'afficher que
l'URL sur la sortie standard.  La sortie standard peut être reliée à d'autres
processus dans le style classique d'un filtre de texte UNIX. Sr_subscribe est 
très configurable et constitue la base de plusieurs autres composants de Sarracenia:

 - `sr_report(1) <sr_report.1.rst>`_ - afficher les rapports de disposition des fichiers.
 - `sr_sender(1) <sr_sender.1.rst>`_ - envoyer des fichiers.
 - `sr_winnow(8) <sr_winnow.8.rst>`_ - supprimer les doublons
 - `sr_shovel(8) <sr_shovel.8.rst>`_ - copier des messages
 - `sr_sarra(8) <sr_sarra.8.rst>`_ - - S'abonner, acquérir, et recursivement Re-annoncer Ad nauseam.

Tous ces composants acceptent les mêmes options, avec les mêmes effets.
Il y a aussi `sr_cpump(1) <sr_cpump.1.rst>`_ qui est une version en C qui 
implémente un sous-ensemble des options qui, lorsqu'elles sont présentes,
ont le même effet.

La commande **sr_subscribe** requiert deux arguments : une action 
start|stop|stop|restart|reload|reload|status, suivi d'un fichier de configuration.

Lorsqu'un composant est invoqué, une action et un fichier de configuration sont
spécifiés. L'action est une de:

 - foreground: exécuter une seule instance au premier plan, écrivant le journal à l´erreur standard.
 - restart: arrêter puis démarrer la configuration.
 - sanity: recherche les instances qui se sont plantées ou ont bloqué et les redémarre.
 - start:  démarrer la configuration
 - status: vérifier si la configuration est en cours d'exécution.
 - stop: arrêter la configuration.

Notez que *sanity* est invoqué sur une base régulière par le traitement périodique *Heartbeat* dans
sr_audit. Les action restantes gèrent les ressources 
(échanges, files d'attente) utilisées par les composants sur le serveur 
rabbitmq, ou gèrent les configurations.

 - cleanup:      supprime les ressources du composant sur le serveur
 - declare:      crée les ressources du composant sur le serveur.
 - setup:        comme declare, fait en plus des liaisons de file d'attente.
 - add:          copie une configuration à la liste des configurations disponibles.
 - list:         Énumérer toutes les configurations disponibles.
 - list plugins: Énumérer toutes les *plugins* disponibles.
 - edit:         modifier une configuration existante.
 - remove:       Supprimer une configuration
 - disable:      marquer une configuration comme non éligible à l'exécution.
 - enable:       marquer une configuration comme éligible à l'exécution.


Par exemple: *sr_subscribe foreground dd* exécute une instance du composant sr_subscribe en avant plan
en se servant de la configuration dd.

L'action **foreground** est utilisée lors de la construction d'une 
configuration ou pour le débogage. L'instance **foreground** sera exécutée
indépendamment des autres instances qui sont en cours d'exécution.
Si des instances sont en cours d'exécution, il partage la même file d'attente
d'avis avec eux. Un utilisateur arrête l'instance **foreground** en
utilisant simplement <ctrl-c> sur linux. ou utilise d'autres moyens pour tuer le processus.

Les actions **cleanup**, **declare**, **setup** peuvent être utilisées pour gérer les 
ressources sur le courtier rabbitmq. Les ressources sont soit des files d'attente,
soit des échanges. **declare** crée les ressources. **setup** crée les files 
d'attente et les liaisons.

Les actions **add, remove, list, edit, enable & disable** sont utilisées pour gérer la liste
de configurations et *plugins*. On peut voir toutes les configurations disponibles en utilisant l´action **list**.
et les *plugins* disponibles avec **list plugins**.
En utilisant l'option **edit**, on peut travailler sur une configuration particulière.
Une configuration **disabled** ne sera pas démarrée ou redémarrée par les actions **start**
ou **restart**. Cela peut être utilisé pour mettre une configuration temporairement de côté.


Documentation
-------------

Bien que les pages du manuel fournissent des informations exhaustives, 
Les nouveaux utilisateurs à la recherche d´exemples et démonstrations
seront plus heureux avec les guides:

Utilisateurs :

* `Survol <sarra.rst>`_ - Introduction à l´application.
* `Installation <Install.rst>`_ - installation initiale.
* `Guide de l'abonné <subscriber.rst>`_ - téléchargement efficace à partir d'une pompe.
* `Guide source (incomplet) <source.rst>`_ - téléversement efficace vers une pompe.
* `Guide de programmation <Prog.rst>`_ - Programmation de plugins personnalisés pour l'intégration du flux de travail.

Administrateurs :

* `Guide d'administration <Admin.rst>`_ - Configuration des pompes.
* `Guide de mise à niveau <UPGRADING.rst>`_ - DOIT ÊTRE LU lors de la mise à niveau des pompes.

et les contributeurs :

* `Guide du développeur <Dev.rst>`_ - contribuant au développement de Sarracenia.

Pour tous les indexes de référence: `AUSSI VOIR`_. 

Pour assistance immédiate, lorsque qu'un composant est invoqué avec 
l'action *help*, ou *-help* ou **help**, une liste d'options valides 
est affichée. 


Configurations
--------------

Si on a une configuration prête à l'emploi appelée *q_f71.conf*, elle peut être
ajoutée à la liste des noms connus avec: :

  sr_subscribe add q_f71.conf


Dans ce cas-ci, q_f71.conf est inclus avec les exemples fournis, donc *add* le trouve
dans les exemples et le copie dans le répertoire des configurations actives.
Chaque fichier de configuration gère les consommateurs pour une seule file 
d'attente sur le courtier. Pour visualiser les configurations disponibles, 
utilisez::


  blacklab% sr_subscribe list

  packaged plugins: ( /usr/lib/python3/dist-packages/sarra/plugins ) 
         __pycache__       bad_plugin1.py       bad_plugin2.py       bad_plugin3.py     destfn_sample.py       download_cp.py 
      download_dd.py      download_scp.py     download_wget.py          file_age.py        file_check.py          file_log.py 
      file_rxpipe.py        file_total.py           harness.py          hb_cache.py            hb_log.py         hb_memory.py 
         hb_pulse.py         html_page.py          line_log.py         line_mode.py               log.py         msg_2http.py 
       msg_2local.py    msg_2localfile.py     msg_auditflow.py     msg_by_source.py       msg_by_user.py         msg_delay.py 
       msg_delete.py      msg_download.py          msg_dump.py        msg_fdelay.py msg_filter_wmo2msc.py  msg_from_cluster.py 
    msg_hour_tree.py           msg_log.py     msg_print_lag.py   msg_rename4jicc.py    msg_rename_dmf.py msg_rename_whatfn.py 
      msg_renamer.py msg_replace_new_dir.py          msg_save.py      msg_skip_old.py        msg_speedo.py msg_sundew_pxroute.py 
   msg_test_retry.py   msg_to_clusters.py         msg_total.py        part_check.py  part_clamav_scan.py        poll_pulse.py 
      poll_script.py    post_hour_tree.py          post_log.py    post_long_flow.py     post_override.py   post_rate_limit.py 
       post_total.py         watch_log.py 

  configuration examples: ( /usr/lib/python3/dist-packages/sarra/examples/subscribe ) 
            all.conf     all_but_cap.conf            amis.conf            aqhi.conf             cap.conf      cclean_f91.conf 
      cdnld_f21.conf       cfile_f44.conf        citypage.conf       clean_f90.conf            cmml.conf cscn22_bulletins.conf 
        ftp_f70.conf            gdps.conf         ninjo-a.conf           q_f71.conf           radar.conf            rdps.conf 
           swob.conf           t_f30.conf      u_sftp_f60.conf 

  user plugins: ( /home/peter/.config/sarra/plugins ) 
        destfn_am.py         destfn_nz.py       msg_tarpush.py 

  general: ( /home/peter/.config/sarra ) 
          admin.conf     credentials.conf         default.conf

  user configurations: ( /home/peter/.config/sarra/subscribe )
     cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf         ftp_f70.conf           q_f71.conf 
          t_f30.conf      u_sftp_f60.conf
  blacklab%

On peut ensuite le modifier à l'aide de: :

  sr_subscribe edit q_f71.conf

(La commande d'édition utilise la variable d'environnement EDITOR, si elle est présente.
Une fois les changements complétés, on peut démarrer la configuration avec: :

  sr_subscibe foreground q_f71.conf

Que contiennent les fichiers ? Voir la section suivante :


Syntaxe des options
-------------------

Les options sont placées dans les fichiers de configuration, une par ligne, ans le format suivant :

  option <valeur>******.

Par exemple::

  **debug true****
  **debug****

définit l'option *debug* pour activer une journalisation plus verbeuse.  Si aucune valeur n'est spécifiée,
la valeur true est implicite. Les exemples ci-dessus sont donc équivalents.  Un deuxième exemple
ligne de configuration::

  broker amqps://anonymous@dd.weather.gc.ca

Dans l'exemple ci-dessus, *broker* est le mot clé de l'option, et le reste de la 
ligne est la valeur qui lui est assignée. Les fichiers de configuration sont 
une séquence de réglages, un par ligne.  Notez que l'ordre des options est significatif, 
surtout pour les clauses *directory* et *accept*.
Exemple::

    directory A
    accept X

Place les fichiers correspondant à X dans le répertoire A.

versus::

    accept X
    directory A

Place les fichiers correspondant à X dans le répertoire de travail actuel, 
et le paramètre *directory A* ne fait rien par rapport à X.

Pour fournir une description non fonctionnelle de la configuration ou des 
commentaires, utilisez des lignes commençant par **#****.  Toutes les options
sont sensibles aux majuscules et minuscules. ** **Debug** n'est pas le même
que **debug** ou **DEBUG**. Il s'agit de trois options différentes (dont deux
n'existent pas et n'auront aucun effet, mais devrait générer une 
avertissement ´unknown option´).

Les options et les paramètres de ligne de commande sont équivalents.  Chaque 
paramètre de ligne de commande a une version longue correspondante commençant 
par'--'.  Par exemple, *-u* est la forme courte de *--url*. On peut
aussi spécifier cette option dans un fichier de configuration. Pour ce faire, 
utilisez la forme longue sans le'--', suivi de sa valeur séparée par un 
espace. Les éléments suivants sont tous équivalents :

  **post_base_url <url>**.
  **-pbu <url>**.
  **--post_base_url <url>**.

Les paramètres d'un fichier.conf individuel sont lus après le fichier *default.conf*.
et peuvent donc remplacer les valeurs par défaut. Les options spécifiées sur
la ligne de commande ont préséance sur le contenu des fichiers de configuration.

Les réglages sont interprétés dans l'ordre.  Chaque fichier est lu de haut en bas.
par exemple :

sequence #1::

  reject .*\.gif
  accept .*


sequence #2::

  accept .*
  reject .*\.gif



.. note::
   FIXME : est-ce que cela ne correspond qu'aux fichiers se terminant par'gif' ou devrions-nous y ajouter un $ ?
   correspondra-t-il à quelque chose comme.gif2 ? y a-t-il un .* supposé à la fin ?


Dans la séquence #1, tous les fichiers se terminant par 'gif' sont rejetés. Dans la séquence #2, le 
accept .* (qui accepte tout) est rencontré avant l'instruction *reject*, qui n'a donc aucun effet.

Si plusieurs options doivent être réutilisées dans différents fichiers de configuration, elle peuvent 
être regroupées dans un fichier. Dans chaque configuration où le sous-ensemble
d'options devrait être inclus, l'utilisateur spécifierait alors:

  **--include <IncludeConfigPath>**

IncludeConfigPath devrait normalement résider dans le même répertoire de 
configuration que son fichier configs maître. Il n'y a pas de restriction, 
n'importe quelle option peut être placée dans un fichier de configuration chargé via
l'optin **include**. L'utilisateur doit être conscient que, pour beaucoup d'options, 
multiples déclarations signifient que les occurrence subséquentes ont préséance sur les
valeurs rencontrées plus tôt.
FIXME : pas clair quelles options ont préséance.

Variables de plugin
~~~~~~~~~~~~~~~~~~~

Sarracenia utilise beaucoups de petits modules en python (appellés *plugins*)
afin de modifier le traitement. les *plugins* définisse et utilise des
options, qui ont le nom du plugin comme préfix::

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

L´option *msg_to_clusters* est utilisé par le plugin *msg_to_clusters* qui
est invoqué lors de chaque réception de message ( *on_message* )

Variables de l´environnement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On peut aussi utiliser des variables d´environnement avec le syntax
*${ENV}* ou *ENV* est le nom d´un variable de l´environnement. S´il faut
définir un variable d´environnement pour utilisation par Sarracenia,
on peut l´indiquer dans un fichier de configuration::

  declare env HTTP_PROXY=localhost



LOG FILES
---------

Comme sr_subscribe fonctionne généralement comme un démon (à moins d'être 
invoqué en mode *foreground*), on examine normalement son fichier journal pour
savoir comment se déroule le traitement.  Quand seulement une seule instance 
est en cours d'exécution, on peut normalement visualiser le journal du
processus en cours d'exécution de cette façon::

   sr_subscribe log *myconfig*

Où *myconfig* est le nom de la configuration en cours d'exécution. Les fichiers
journaux sont placés conformément à la spécification XDG Open Directory. Il y 
a un fichier journal pour chaque *instance* (processus de téléchargement) 
sr_subscribe exécutant la configuration *myconfig*::

   sur linux : ~/.cache/sarra/log/sr_subscribe_subscribe_myconfig_01.log

On peut outrepasser le placement sur linux en définissant la variable 
d'environnement XDG_CACHE_HOME.


IDENTIFICATION
--------------

Normalement, on ne spécifie pas de mots de passe dans les fichiers de 
configuration. Ils sont plutôt placés dans le fichier d´information d´identifcation::

   sr_subscribe edit credentials

Pour chaque url spécifié qui nécessite un mot de passe, on place une entrée
correspondante dans *credentials.conf*. L'option broker définit toutes les 
informations d'identification pour se connecter au serveur **RabbitMQ**.

  broker amqp{s}://<utilisateur>:<pw>@<brokerhost>[:port]/<vhost>****.

::

      (par défaut : amqps://anonymous:anonymous@dd.weather.gc.ca/)

Pour tous les programmes de **sarracenia**, les parties confidentielles 
des justificatifs d'identité sont stockées uniquement dans 
~/.config/sarra/credentials.conf. Cela comprend les mots de passe pour la destination 
et le courtier ainsi que les paramètres requis par les composants.  Une entrée par ligne.  Exemples :

- **amqp://user1:password1@host/**.
- **amqps://user2:password2@host:5671/dev**.

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22 ssh_keyfile=/users/local/.ssh/.ssh/id_dsa**

- **ftp://user7:password7@host passive,binaire**
- **ftp://user8:password8@host:2121 active,ascii**

- **ftp://user7:De%3Aolonize@host passive,binaire,tls***
- **ftps://user8:%2fdot8@host:2121 active,ascii,tls,prot_p**


Dans d'autres fichiers de configuration ou sur la ligne de commande, l'url 
n'inclut pas le mot de passe ou spécification de clé.  L'url donné dans les 
autres fichiers est utilisé comme clé de recherche pour credentials.conf.


Note: :
 Les informations d'identification SFTP sont optionnelles car 
 sarracenia cherchera dans le répertoire .ssh et utilisers les identifiants 
 SSH qui s'y trouvent.

 Ces chaînes sont codées par URL, donc si un compte a un mot de passe avec un
 mot de passe spécial. Son équivalent URL encodé peut être fourni.  Dans le 
 dernier exemple ci-dessus, %2f**** signifie que le mot de passe actuel 
 esti : **/dot8**
 L'avant-dernier mot de passe est :  **De:olonize**. ( %3a étant la valeur 
 codée en url d'un caractère deux-points. )


CONSOMMATEUR
============

La plupart des composants Metpx Sarracenia boucle sur la réception et la 
consommation de messages AMQP. Habituellement, les messages d'intérêt sont 
dans le format d´une *avis* `sr_post(7) <sr_post.7.rst>`_, annonçant la disponibilité 
d'un fichier en publiant l'URL pour l´accéder (ou une partie de celle-ci).
Il y a également le format *rappor* `sr_report(7) <sr_report.7.rst>`_ qui peuvent 
être traités avec les mêmes outils. Les messages AMQP sont publiés avec
un *exchange* comme destinataire.  Sur un courtier (serveur AMQP.) L'exchange 
délivre des messages aux files d'attente. Pour recevoir de messages,  
on doit fournir les informations d'identification pour se connecter au 
courtier (message AMQP).  Une fois connecté, un consommateur doit créer 
une file d'attente pour retenir les messages en attente. Le consommateur 
doit ensuite lier la file d'attente à une ou plusieurs échanges de manière
à ce qu'il mette dans sa file d'attente.

Une fois les liaisons (anglais: *bindings*) établies, le programme peut 
recevoir des messages. Lorsqu'un message est reçu, un filtrage 
supplémentaire est possible en utilisant des expressions régulières sur
les messages AMQP. Après qu'un message a passé avec succès ce processus
de sélection et d'autres validations internes, le processus peut exécuter
un script de plugin **on_message** pour traiter le message davantage
de façon spécialisé. Si ce plugin retourne False comme résultat, le 
message est rejeté. Si c'est vrai, le traitement du message se poursuit.

Les sections suivantes expliquent toutes les options pour régler cette 
partie " consommateur " de les programmes de Sarracenia.




Réglage du courtier 
-------------------

broker amqp{s}://<user>:<password>@<brokerhost>[:port]/<vhost>*****.

Un URI AMQP est utilisé pour configurer une connexion à une pompe à messages 
(AMQP broker). Certains composants de Sarracenia définissent une valeur par 
défaut raisonnable pour cette option. Vous fournissez l'utilisateur normal,
l'hôte, le port des connexions. Dans la plupart des fichiers de configuration,
le mot de passe est manquant. Le mot de passe n'est normalement inclus que dans
le fichier credentials.conf.

L´application Sarracenia n'a pas utilisé vhosts, donc **vhost** devrait toujours être **/**.

pour plus d'informations sur le format URI de l'AMQP : ( https://www.rabbitmq.com/uri-spec.html))


soit dans le fichier default.conf, soit dans chaque fichier de configuration spécifique.
L'option courtier indique à chaque composante quel courtier contacter.

broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>****.

::
      (par défaut : Aucun et il est obligatoire de le définir) 

Une fois connecté à un courtier AMQP, l'utilisateur doit lier une file d'attente.
à l´*exchange* et aux thèmes (*topics*) pour déterminer les messages intérêsseants.


Création de la file d'attente
-----------------------------

Une fois connecté à un courtier AMQP, l'utilisateur doit créer une file d'attente.

Mise en file d'attente sur broker :

- **queue <nom> (par défaut : q_<brokerUser>.<programName>.<configName>.<configName>)**
- **durable <boolean> (par défaut : False)**
- **expire <durée> (par défaut : 5m == cinq minutes. À OUTREPASSER)**
- **message-ttl <durée> (par défaut : Aucun)**
- **prefetch <N> (par défaut : 1)****
- **reset <boolean> (par défaut : False)**
- **restore <boolean> (par défaut : False)**
- **restore_to_queue <queuename> (par défaut : Aucun)**
- **save <boolean> (par défaut : False)**

Habituellement, les composants devinent des valeurs par défaut raisonnables pour
toutes ces valeurs et les utilisateurs n'ont pas besoin de les définir.  Pour 
les cas moins habituels, l'utilisateur peut avoir besoin a remplacer les valeurs
par défaut. La file d'attente est l'endroit où les avis sont conservés
sur le serveur pour chaque abonné.

[ queue|queue_name <nom> (par défaut : q_<brokerUser>.<programName>.<configName>.<configName>) ]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Par défaut, les composants créent un nom de file d'attente qui doit être unique.
Le nom_de_la_files_d'attente par défaut composants créent suit.. :  
**q_<brokerUser>.<programName>.<configName><configName>** . Les utilisateurs 
peuvent remplacer la valeur par défaut à condition qu'elle commence par 
**q_<brokerUser>****. Certaines variables peuvent aussi être utilisées dans 
le nom_de_la_file d'attente comme **${BROKER_USER},${PROGRAMME},${CONFIG},${HOSTNAME}******

Quand plusieurs processus (*instances*) roulent sur un même serveurs, ils 
partagent le même *home* alors ils vont tous partager le même fil.  On peut
explicitement spécifier le nom du fil d´attente pour être plus claire ou 
dans les cas ou on veut que le même queue soit partagé en dépit de ne pas
avoir de *home* partagé.


durable <boolean> (par défaut : False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **durable**, si elle est définie sur True, signifie que la file d'attente est écrite.
sur disque si le courtier est redémarré.

expire <durée> (par défaut : 5m == cinq minutes. À REGLER)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **expire** est exprimée sous forme de durée.... elle fixe la durée de vie...
une file d'attente sans connexions. Un entier brut est exprimé en secondes, si le suffixe m,h.d,w
sont utilisés, alors l'intervalle est en minutes, heures, jours ou semaines. Après 
l'expiration de la file d'attente, le contenu est supprimé, ce qui peut 
entraîner des lacunes dans le flux de données de téléchargement.  Une valeur de
1d (jour) ou 1w (semaine) peut être approprié pour éviter la perte de données. 
Ça dépend de combien de temps on s'attend à ce que l'abonné s'arrête et 
ne subisse aucune perte de données.

Le réglage **expire** doit être remplacé pour une utilisation opérationnelle.
La valeur par défaut est basse parce qu'elle définit la durée pendant laquelle
les ressources du courtier seront assignées, et au début de l'utilisation 
(lorsque le défaut était d'une semaine), les courtiers étaient souvent 
surchargés de très peu d'argent. de longues files d'attente pour les 
expériences restantes.

message-ttl <durée> (par défaut : Aucun)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **message-ttl** (*message time to live*) définit la durée de vie
d´un message dans la file d'attente. Passé ce délai, le message est retiré de 
la file d'attente par le courtier.

prefetch <N> (par défaut : 1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **prefetch** définit le nombre de messages à récupérer en une seule fois. 
Lorsque plusieurs instances sont en cours d'exécution et que prefetch est 4, 
chaque instance obtiendra jusqu'à quatre messages à la fois.  Pour réduire au 
minimum le nombre de messages perdus si une instance meurt et que vous avez
Partage optimal de la charge, le préréglage doit être réglé aussi bas que possible. 
Cependant, dans les cas de connexion longue distance, il est nécessaire d'augmenter 
ce nombre, afin de cacher la latence de l'aller-retour, donc un paramètre
de 10 ou plus peut être nécessaire.

reset <boolean> (par défaut : False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque **reset** est réglé et qu'un composant est (re)démarré, sa file d'attente 
est supprimé (s'il existe déjà) et recréé d'après les données du composant au démarrage.
C'est à ce moment qu'une option de courtier est modifiée, car le courtier va
refuser l'accès à une file d'attente déclarée avec des options différentes de ce qui a été déclaré
à sa création. Il peut également être utilisé pour éliminer rapidement une file 
d'attente lorsqu'un récepteur a été arrêtée pendant une longue période. Si la 
suppression des doublons est active, alors le cache de réception est également
effacé.

Le protocole AMQP définit d'autres options de file d'attente qui ne sont pas exposées.
via Sarracenia, car l´application choisit les valeurs appropriées.

save <boolean> (par défaut : False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **save** est utilisée pour lire les messages de la file d'attente, les écrire
dans un fichier local, afin de les sauvegarder pour un traitement ultérieur, au lieu de les traiter
immédiatement.  Voir la section " Destination de l'expéditeur non disponible " pour plus de détails.
L'option **restore** met en œuvre la fonction inverse, la lecture à partir du fichier.
pour traitement.

restore_to_queue <queuename> (par défaut : Aucun)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si **restore_to_queue** est spécifié, alors plutôt que de déclencher le mode local
les messages restaurés sont enregistrés dans un échange temporaire.
à la file d'attente donnée.  Pour un exemple, voir `Shovel Save/Restore`_.


Liaisons de file d´attente AMQP 
-------------------------------

Une fois qu'on a une file d'attente, elle doit être liée à un échange (exchange.)
Les utilisateurs ont presque toujours besoin de définir ces options. Une 
fois qu'une file d'attente existe sur le courtier, il doit être lié (*bound*) à 
une échange. Les liaisons (*bindings*) définissent ce que l'on entend par
les avis que le programme reçoit. La racine du thème
est fixe, indiquant la version du protocole et le type de l'arborescence.
(mais les développeurs peuvent l'écraser avec le **topic_prefix****.
option.)

Ces options définissent les messages (notifications URL) que le programme reçoit :


 - **exchange      <name>         (default: xpublic)** 
 - **exchange_suffix      <name>  (default: None)** 
 - **topic_prefix  <amqp pattern> (default: v02.post -- developer option)** 
 - **subtopic      <amqp pattern> (sousthème au choix de l´utilisateur)** 

exchange <nom> (defaut: xpublic) et exchange_suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La convention sur les pompes de données est d'utiliser l'échange *xpublic*. 
Les utilisateurs peuvent établir les flux de données privées pour leur propre 
traitement. Les utilisateurs peuvent déclarer leurs propres échanges,
qui commencent toujours par *xs_<nom_utilisateur>*. Pour éviter d'avoir à 
spécifier que chaque temps, on peut déclarer *exchange_suffix kk* qui se 
traduira résultera dans la déclaration de l´échange: *xs_<username>_kkk* (remplaçant 
la valeur par défaut *xpublic*).  Il faut établir la valeur de l´*exchange* auquel
on s´abonne avant de passer à *subtopic* pour les filtrer.

subtopic <patron amqp> (doit être spécifié)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On se sert de subtopic afin de raffiner la selection de produits parmi la gamme publié
sur un *exchange* donné. Plusieurs options de thème (*subtopic*) peuvent être déclarées. 
Donner une valeur correcte au sous-thème, On a le choix de filtrer en utilisant
**subtopic** avec seulement les *wildcard* (caractères 
de substitution) limité de l'AMQP et longueur limitée à 255 octets codés, ou bien les
expressions régulières plus puissantes, avec les options **accept/reject** décrits 
ci-dessous. Tandis que Le filtrage AMQP est appliqué par le courtier lui-même, 
ce qui permet d'éviter que les avis ne soient livrés au client du tout, les 
modèles **accepter/rejeter** s'appliquent aux messages envoyés par le du courtier 
à l´abonné. En d'autres termes, **accept/reject** sont des filtres côté client,
alors que **subtopic** est le filtrage côté serveur.

Il est préférable d'utiliser le filtrage côté serveur pour réduire le nombre 
de avis envoyées au client à un petit sur-ensemble de ce qui est pertinent, 
et n'effectuer qu'un réglage fin avec l'outil mécanismes côté client, économisant 
la bande passante et le traitement pour tous.

topic_prefix est principalement d'intérêt pendant les transitions de version 
de protocole, où l'on souhaite spécifier une version sans protocole par défaut 
des messages auxquels s'abonner, ou bien pour manipuler des rapports de disposition,
au lieu de avis ( *v02.report* )

Habituellement, l'utilisateur spécifie un échange et plusieurs options de sous-thèmes.
**subtopic** est ce qui est normalement utilisé pour indiquer les messages d'intérêt.
Pour utiliser le sous-thème pour filtrer les produits, faites correspondre la 
chaîne de sous-thèmes avec le chemin relatif dans l´arborescence de répertoires sur le serveur.

Par exemple, en consommant à partir de DD, pour donner une valeur correcte au sous-thème, on peut
Parcourez notre site Web **http://dd.weather.gc.ca**** et notez tous les annuaires.
d'intérêt.  Pour chaque arborescence de répertoires d'intérêt, écrivez un **subtopic****.
comme suit :


 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#**

::
  où :  
       - * (asterisk) remplace le nom d'un seul répertoire.
       - # (dièse) correspond a n´importe lequel restant d´arborescence.

Note :
  Lorsque les répertoires ont ces caractères génériques, ou des espaces dans leur nom, ils
  sera codé par URL ('#' devient %23)
  Lorsque les répertoires ont des points dans leur nom, cela changera.
  la hiérarchie des thèmes.

FIXME :
      les dièses sont encodés, mais pas vu le code pour les autres valeurs.
      Vérifiez si les astérisques dans les noms de répertoires des thèmes doivent être codés par URL.
      Vérifiez si les périodes dans les noms de répertoires dans les rubriques doivent être codées par URL.

On peut plusiers liaisons au plusieurs *exchange* :: 

  exchange A
  subtopic directory1.*.directory2.#

  exchange B
  subtopic *.directory4.#

ce qui déclare deux abonnements à deux arborescences publiés par deux *exchange*  distincts.



Filtrage Côté Client
--------------------

Nous avons sélectionné nos messages via **exchange**, **subtopic** et **subtopic**.
Le courtier met les messages correspondants dans notre file d'attente (*queue*).
Le composant télécharge ces messages.

Les clients Sarracenia implémentent un filtrage plus flexible côté client
en utilisant les expressions régulières.


Brève introduction aux expressions régulières
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les expressions régulières sont un moyen très puissant d'exprimer les correspondances de motifs. 
Ils offrent une flexibilité extrême, mais dans ces exemples, nous utiliserons seulement un
petit sous-ensemble : Le point (.) est un joker qui correspond à n'importe quel caractère 
unique. S'il est suivi d'un nombre d'occurrences, il indique le nombre de lettres 
qui correspondent. Le caractère * (astérisque), signifie un nombre quelconque d'occurrences.
alors :

 - .* signifie n'importe quelle séquence de caractères de n'importe quelle longueur. 
   En d'autres termes, faire correspondre n'importe quoi.
 - cap.* signifie toute séquence de caractères commençant par cap.
 - .*CAP.* signifie n'importe quelle séquence de caractères avec CAP quelque part dedans. 
 - .*CAP signifie toute séquence de caractères qui se termine par CAP.  
 - Dans le cas où plusieurs portions de la chaîne de caractères pourraient correspondre, la plus longue est sélectionnée.
 - .*?CAP comme ci-dessus, mais *non-greedy*, ce qui signifie que le match le plus court est choisi.
 - noter que l'implantaions de regexp en C n'inclu pas le *greediness*, alors certains expressions
   ne seront pas interpretés pareilles par les outils implanté en C: sr_cpost, sr_cpump, où libsrshim.

Veuillez consulter diverses ressources Internet pour obtenir de plus amples renseignements: 

 - `https://docs.python.org/fr/3/library/re.html <https://docs.python.org/fr/3/library/re.html>`_
 - `https://fr.wikipedia.org/wiki/Expression_r%C3%A9guli%C3%A8re <https://fr.wikipedia.org/wiki/Expression_r%C3%A9guli%C3%A8re>`_


accept, reject, accept_unmatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **accept <expression régulière (regexp)>  (facultatif)**.
- **reject <expression régulière (regexp)> (facultatif)**.
- **accept_unmatch <boolean> (par défaut : False (faux))**.

Les options **accept** et **reject** traitent des expressions régulières (regexp).
La regexp est appliquée à l'URL du message pour détecter une correspondance.

Si l'URL du message d'un fichier correspond à un motif **reject**, on informe
le courtier que le message a été consommé et on abandonne son traitement.

Celui qui correspond à un motif **accept** est traité par le composant.

Dans de nombreuses configurations, les options **accept** et **reject**
sont spécifiés ensembles, et avec l'option **directory**.  Ils relient 
ensuite les messages acceptés à la valeur **directory** sous laquelle 
ils sont spécifiés.

Après que toutes les options **accept** / **reject** sont traitées normalement.
l'accusé de réception du message tel qu'il a été consommé et ignoré. Pour 
outrepasser ce comportement de défaut, définissez **accept_unmatch** à True.   

Les **accept/rejet** sont interprétés dans l'ordre qu´ils apparaissent
dans le fichier de configuration.  Chaque option est traitée en ordre 
de haut en bas.  par exemple :

sequence #1::

  reject .*\.gif
  accept .*

sequence #2::

  accept .*
  reject .*\.gif


Dans la séquence #1, tous les fichiers se terminant par 'gif' sont rejetés.  
Dans la séquence #2, l'option accept .* (regexp qui veut dire accepte tout) est 
rencontré avant la déclaration de rejet, de sorte que le rejet n'a aucun effet.

Il est préférable d'utiliser le filtrage côté serveur pour réduire le nombre 
de avis envoyées au composant à un petit sur-ensemble de ce qui est 
pertinent, et n'effectuer qu'un réglage fin avec les mécanismes *accept/reject* 
côté client, économisant la bande passante et le traitement pour tous. 



OPTIONS DE LIVRAISON
--------------------

Ces options définissent quels fichiers l'utilisateur veut et où il sera placé,
et sous quel nom. (un `booléen <https://fr.wikipedia.org/wiki/Alg%C3%A8bre_de_Boole_(logique)>`_
est un option qui a une valeur logique: vrai/faux)

- **accept    <patron regexp>  (requis sauf si accept_unmatch est True)** 
- **accept_unmatch   <booléan> (défaut: False)**
- **attempts     <compte>      (défaut: 3)**
- **base_dir <chemin>          (défaut: /)**
- **batch     <compte>         (défaut: 100)**
- **default_mode     <octalint> (défaut: 0 - umask)**
- **default_dir_mode <octalint> (défaut: 0755)**
- **delete    <booléan>>       (défaut: False)**
- **directory <chemin>         (défaut: .)** 
- **discard   <booléan>        (défaut: false)**
- **flatten   <string>         (défaut: '/')** 
- **heartbeat <durée>          (défaut: 300 secondes)**
- **inline       <booléan>     (défaut: false)**
- **inline_max <compte>        (défaut: 1024)**
- **inplace       <booléan>    (défaut: true)**
- **kbytes_ps <count>          (défaut: 0)**
- **inflight  <chaine>         (défaut: .tmp où NONE si post_broker est setté)** 
- **mirror    <booléan>        (défaut: false)** 
- **outlet    post|json|url    (defaut: post)** 
- **overwrite <booléan>        (défaut: false)** 
- **recompute_chksum <booléan> (défaut: False)**
- **reject    <regexp pattern> (optional)** 
- **retry    <booléan>         (défaut: True)** 
- **retry_ttl    <durée>         (défaut: pareil que expire)** 
- **source_from_exchange  <booléan> (défaut: False)**
- **strip     <compte|regexp>   (défaut: 0)**
- **suppress_duplicates   <off|on|999>     (défaut: off)**
- **timeout     <numéro flottante>         (défaut: 0.0)**


attempts <compte> (défaut: 3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **attempts** indique combien de fois pour tenter de télécharger 
les données avant d'abandonner.  La valeur par défaut de 3 devrait être appropriée.
dans la plupart des cas.  Lorsque l'option **retry** est fausse, le fichier 
est alors immédiatement abandonné.

retry <booléan> (défaut: True)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque l'option **retry** est activée (par défaut), l'échec du 
téléchargement après les **attempts** tentatives (où d'envoi, dans un 
expéditeur) entraînera l'ajout du message dans un fichier de file d'attente,
pour réessayer plus tard.  Lorsqu'il n'y a pas de messages prêts à consommer 
dans la file d'attente de l'AMQP, la file d'attente de réessai sera interrogée.

retry_ttl <durée> (défaut: pareil que expire)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **retry_ttl** (temps de réessai à vivre) indique combien de 
temps il faut continuer à essayer d'envoyer.  Un fichier avant qu'il ne 
soit vieilli d'une file d'attente.  La valeur par défaut est de deux jours.
Si un fichier n'a pas de a été transféré après deux jours de tentatives, 
il est jeté.

timeout <numéro flottante> (défaut: 0.0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **timeout**, définit le nombre de secondes d'attente avant l'annulation d'un appel.
connexion ou transfert de téléchargement (appliqué par tampon pendant le transfert).

inflight <chaine> (défaut: .tmp où NONE si post_broker est setté)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **inflight** définit comment ignorer les fichiers lors de leur transfert
(*en vol* entre deux systèmes.) Un mauvais réglage de cette option provoque
des transferts peu corrompus, ou insertent de délais inutiles. alors il faut 
faire attention.  Voir `Assurer la livraison (inflight)`_ FIXME pour plus de détails.

La valeur peut être un suffixe de nom de fichier, qui est ajouté pour créer 
un nom temporaire lors de la création d'un nom de fichier.  Si **inflight** est 
réglé à **.**, alors il s'agit d'un préfixe, afin de se conformer à le standard 
pour les fichiers "cachés" sur unix/linux.  Si **inflight** se termine 
par **/** (exemple : *tmp/*), alors il s'agit d'un préfixe, et spécifie un
sous-répertoire de la destination dans laquelle le fichier doit être écrit 
pendant le vol.

Si un préfixe ou un suffixe est spécifié, quand le transfert est complet, le 
fichier est renommé en son nom permanent pour permettre un traitement ultérieur.

L'option **inflight** peut également être spécifiée comme intervalle de temps, 
par exemple, 10 pendant 10 secondes. Lorsqu'il est réglé sur un intervalle de 
temps, le lecteur d'un fichier s'assure que il attend que le fichier n'ait pas 
été modifié dans cet intervalle. Donc un fichier ne sera pas être traité tant 
qu'il n'est pas modifié pendant au moins 10 secondes.

Enfin, **inflight** peut être réglé sur *NONE*, auquel cas le fichier est 
écrit directement avec son nom final, où le destinataire attendra de recevoir
un message l'avisant de l'envoi de l'arrivée du fichier. Il s'agit de l'option
la plus rapide et la moins coûteuse lorsqu'elle est disponible.
C'est aussi la valeur par défaut lorsqu'un *post_broker* est donné, ce qui 
indique qu'un autre processus va être notifié après la livraison, par un
message publié au post_broker.

delete <booléan> (défaut: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque l'option **supprimer** est activée, une fois le téléchargement 
terminé avec succès, l'abonné supprimera le fichier à la source amont.  
utile pour des tests, mais la valeur par défaut est false.

L'option **batch** est utilisée pour indiquer le nombre de fichiers à 
transférer avec une connexion, avant qu'elle ne soit démolie et rétablie.
En cas de très faible volume de transferts, où des délais d'attente 
peuvent se produire entre les transferts, cela devrait être abaissé à 1.
Pour la plupart des situations habituelles, la valeur par défaut est très bien.
on pourrait l'augmenter pour réduire les frais généraux de transfert. 
Il ne sert que pour le fichiers les protocoles de transfert (e.g. SFTP), pas 
les protocoles HTTP pour le moment.

directory <chemin> (défaut: .)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L´option *directory* définit où placer les fichiers sur votre serveur.
Combiné avec les options **accept** / **reject**, l'utilisateur peut sélectionner 
les fichiers à télécharger et leurs répertoires de résidence. (voir **mirror**
pour plus de paramètres de répertoire).

Les options **accept** et **reject** utilisent des expressions régulières 
(regexp) pour correspondre à l'URL. Ces options sont traitées
séquentiellement. L'URL d'un fichier qui correspond à un motif **reject** n'est
jamais téléchargé.  Celui qui correspond à un patron **accept** est téléchargé
et placé dans le répertoire indiqué par l'option **directory** la plus proche 
au-dessus de l'option **accept** correspondante.

**accept_unmatch** est utilisé pour décider ce qu'il faut faire lorsqu'aucune 
clause de rejet ou d'acceptation ne correspond.


::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*


mirror <booléan> (défaut: false)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **mirror** peut être utilisée pour refléter l'arborescence dd.weather.gc.ca des fichiers.
Si réglé sur **True** le répertoire donné par l'option **directory**,
sera le nom de la racine d'un arborescence de répertoires. Les fichiers acceptés dans 
ce répertoire seront placés sous le sous-répertoire feuille d'arbre pareil que où 
il réside sous dd.weather.gc.gc.ca.  Par exemple en récupérant l'url suivante, 
avec des options::


 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*


se traduirait par la création des répertoires et du fichier
/mylocaldirectory/radar/PRECIP/GIF/WGJ/20131214141900_WGJ_PRECIP_PRECIP_SNOW.gif

Vous pouvez modifier les répertoires en miroir avec l'option **strip***.
S'il est réglé sur N (un entier), les premiers ´N´ répertoires sont retirés.
Par exemple ::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*


se traduirait par la création des répertoires et du fichier
/mylocaldirectory/WGJ/20131214141900_WGJ_PRECIP_PRECIP_SNOW.gif
lorsqu'un regexp est fourni à la place d'un nombre, il indique un motif à supprimer.
du chemin relatif. par exemple si: :


   strip  .*?GIF/


Le fichier sera également placé au même endroit.

NOTE::
    avec **strip**, l'utilisation de **?** modificateur (pour éviter l'expression 
    régulière *greediness*) est souvent utile. Il garantit l'utilisation de la 
    correspondance la plus courte.

    Par exemple, en donnant un nom de fichier : radar/PRECIP/GIF/WGJ/20131214141900_WGJ_PRECIP_SNOW.GIF
    L'expression : .*?GIF : radar/PRECIP/GIF
    alors que l'expression : .*GIF correspond au nom entier.


flatten <string> (défaut: '/')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **flatten** (aplatir) est utilisée pour définir un caractère de 
séparation. La valeur par défaut ('/') annule l'effet de cette option.  
Ce caractère remplace le'/' dans l'url.  et créer un fichier "flatten" à 
partir de son chemin dd.weather.gc.ca. Par exemple, en récupérant l'url suivante, avec des options::



 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

entraînerait la création du chemin d'accès au fichier::


 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2


On peut aussi spécifier des substitutions de variables à effectuer sur les arguments du répertoire.
avec l'utilisation de *${..}* notation::

   SOURCE - l'utilisateur amqp qui a injecté des données (tirées du message.)
   DR     - la *document root* (répertoir corréspondant à '/' sur un serveur web.)
   PBD    - le répertoire de la base lors de publication.
   YYYYMMDD - l'horodatage quotidien en cours. (Y-Année, M-Mois, D-Jour du mois)
   HH - l'horodatage horaire actuel.
   *var* - toute variable d'environnement.

Les horodatages YYYYYYMMDD et HH se réfèrent à l'heure à laquelle les données 
sont traitées par Sarracenia, c'est-à-dire à l'heure à laquelle les données sont traitées.
n'est pas décodé ou dérivé du contenu des fichiers livrés. Toutes les dates 
et heures en Sarracenia sont en UTC.

Référez-vous à *source_from_exchange* pour un exemple d'utilisation.  Notez que toute 
option explicite dans un fichier de confiuguration Sarracenia prime sur une variable 
du même nom dans l'environnement.

base_dir <chemin> (défaut: /)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**base_dir** fournit le chemin d'accès au répertoire qui, lorsqu'il est combiné avec 
le chemin d'accès relatif dans la notification donne le chemin absolu du fichier à envoyer.
La valeur par défaut est None, ce qui signifie que le chemin d'accès dans la 
notification est le chemin absolu.

**FIXME**: :
    ne peut pas expliquer cela.... je ne sais pas ce que c'est moi-même. Ceci est 
    pris de l'expéditeur.  Dans un sr_subscriber, si elle est définie.... est-ce 
    qu'elle se téléchargera ? ou supposera-t-elle qu'elle est locale ?
    dans un expéditeur.

inline
~~~~~~

Sur des liens qui ont une grande latence, il se peut que ca soit efficace d'inclure les
fichiers plus petit que *inline_max* octets (defaut: 1024) pour éviter 




inplace <booléan>  (défaut: true)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les fichiers volumineux peuvent être envoyés en une série de parties, plutôt que tous en même temps.
Lors du téléchargement, si **inplace** est vrai, ces parties seront ajoutées au fichier.
d'une manière ordonnée. Chaque partie, après son insertion dans le fichier, est publié aux abonnés.
Il peut être setté à *false* dans déploiements de Sarracenia où une seule pompe 
ne verra jamais que quelques pièces, pas l'intégralité, des fichiers en plusieurs parties.

L'option **inplace** est *True* par défaut.
En fonction de **inplace** et si le message était une partie, le chemin d'accès peut
changer à nouveau (en ajoutant un suffixe de pièce si nécessaire).

outlet post|json|url (defaut: post)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **outlet** est utilisée pour permettre l'écriture des messages dans un fichier au lieu de
l'affectation à un courtier. Les valeurs d'argument valables sont :

**post:**

  poster des messages sur un post_exchange

  amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>*****.
  post_exchange <nom> (OBLIGATOIRE)** **.
  on_post <script> (par défaut : Aucun)**.

  Le **post_broker** est par défaut le courtier d'entrée s'il n'est pas fourni.
  Il suffit de le définir à un autre courtier si vous voulez envoyer les notifications.
  ailleurs.

  Le **post_exchange** doit être défini par l'utilisateur. Il s'agit de l'échange où
  les avis qui seront publiés.

**json:**

  écrire chaque message à la sortie standard, un par ligne dans le même format json utilisé pour
  Sauvegarde/restauration de la file d'attente par l'implémentation python.

**url:**

  il suffit de sortir l'URL de récupération vers la sortie standard.

FIXME : L'option **outlet** est issue de l'implémentation C ( *sr_cpump*) et elle n'a pas
a été beaucoup utilisé dans l'implémentation de python. 


overwrite <booléan> (défaut: false)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **overwrite**,si elle est définie sur false, évite les téléchargements 
inutiles dans ces conditions:

1- le fichier à télécharger se trouve déjà sur le système de fichiers de l'utilisateur au bon endroit et au bon endroit

2- la somme de contrôle du message amqp correspond à celle du fichier.

La valeur par défaut est True (écraser sans vérifier).


discard <booléan> (défaut: false)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **discard**, si elle est réglée sur true, supprime le fichier une 
fois téléchargé. Cette option peut être utile pour déboguer ou tester une
configuration.

source_from_exchange <booléan> (défaut: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **source_from_exchange** est principalement destinée aux administrateurs.
Si les messages sont reçus directement d'une *source* de données, l'échange utilisé 
peut être 'xs_<brokerSourceUsername>'. Un tel message peut manqué l´en-tête *from_cluster*, 
ou un utilisateur malveillant peut définir les valeurs de manière incorrecte.
Pour se protéger contre les deux problèmes, les administrateurs sélectionnent 
l'option **source_from_exchange**.

Lorsque l'option est définie, les valeurs du message pour les en-têtes *source* 
et *from_cluster* seront alors remplacées par::

  self.msg.headers['source']       = <usager du courtier>
  self.msg.headers['from_cluster'] = cluster

primant sur toute valeur présente dans le message. Ce paramètre doit toujours 
être utilisé lors de l'acquisition de données provenant d'un fichier échange 
d'utilisateurs. Ces champs sont utilisés pour renvoyer les rapports à l'origine 
des données injectées. Il est généralement combiné avec: :

       *mirror true*
       *source_from_exchange true*
       *directory ${PBD}/${YYYYYYYMMDD}/${SOURCE}*
  
Pour que les données arrivent dans l'arbre de format standard.

heartbeat <durée> (défaut: 300 secondes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

L'option **heartbeat** définit la fréquence d'exécution du traitement périodique 
déterminé par la liste des plugins on_heartbeat. Par défaut, il imprime un message 
de journal à chaque intervale.

suppress_duplicates <off|on|999> (défaut: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque **suppress_duplicates** (aussi **cache**) est mis à une valeur non nulle, 
chaque nouveau message est comparé aux précédents reçus, pour voir s'il s'agit d'un 
doublon. Si le message est considéré comme un doublon, il est sauté. Qu'est-ce 
qu'un doublon? Un fichier portant le même nom (incluant en-tête des pièces) 
et la somme de contrôle. Chaque intervalle *hearbeat*, un processus de nettoyage
recherche les fichiers dans le répertoire qui n'ont pas été référencés dans 
**cache** secondes, et les efface, afin de les conserver.  la taille du cache
est limitée. Différents réglages sont appropriés pour différents cas d'utilisation.

FIXME L'utilisation du cache est incompatible avec la stratégie par défaut *blocksize 0*
Il faut sélectionner un autre stratégie. Il faut soit utiliser un bloc de
taille fixe, ou ne jamais partitionner les fichiers *(blocksize 1.)*  Il faut éviter
l'algorithme dynamique qui changera la taille de la partition utilisée au fur
et à mesure que le fichier grandit.

**La cache pour supprimer les doublons est locale à chaque instance** 

Lorsque N instances partagent une file d'attente, la première fois qu'un message
est reçu, il pourrait être choisi par une instance, et quand une copie sera 
reçue, il est probable qu'il sera pris en charge par une autre instance. Pour
une suppression efficace des doublons avec les instances**, il faut **déployer
deux couches d'abonnés**. Il faut une **première couche d'abonnés (sr_shovels)**
avec suppression des doublons désactivée, et l´option *post_exchange_split*
activé, ce qui route les messages aux instance selon leur checksum vers une 
**seconde couche de d´abonnés (sr_winnow) dont les caches de suppression de
doublons sont actives. 

Lorsque **kbytes_ps** est supérieur à 0, le processus tente de respecter
cette limite de vitesse en kilo-octets par seconde... ftp,ftps,ou sftp)

**FIXME** : kbytes_ps.... implémenté uniquement par l'expéditeur ? ou 
l'abonné également, uniquement les données, ou les messages également ?

default_mode, default_dir_mode, preserve_modes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les bits de permission sur les fichiers de destination écrits sont contrôlés 
par les directives *preserve_mode*.  *preserve_modes* appliquera les permissions de 
mode en viguer à la source du fichier. Si aucun mode source n'est disponible, le 
mode *default_mode* sera appliqué aux fichiers, et l'option *default_dir_dir_mode* sera 
appliqué aux répertoires. Si aucune valeur par défaut n'est spécifiée, alors le 
système d'exploitation par défaut (sur linux, contrôlé par les paramètres umask)
déterminera les permissions de fichiers. (notez que l'option *chmod* est 
interprétée comme un synonyme de *default_mode*, et *chmod_dir* est un 
synonyme de *default_dir_mode*).

recompute_chksum <booléan> (défaut: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour chaque téléchargement, la somme de contrôle est calculée lors du 
transfert. Si **recompute_chksum** est réglé sur Vrai, et la somme de contrôle
recalculée diffère de la somme de contrôle dans le message, la nouvelle 
valeur écrasera celle du message amqp entrant. Ceci est utilisé lorsqu'un 
fichier est extrait d'une source distante non Sarracenia, auquel cas un lieu
la somme de contrôle du titulaire 0 est spécifiée. Dès réception, une somme 
de contrôle appropriée devrait être placée dans le fichier pour les 
consommateurs en aval. On peut également utiliser cette méthode pour 
remplacer le choix de la somme de contrôle. Par exemple, les anciennes 
versions de la Sarracenia n'ont pas le support du hachage SHA-512, donc 
on pourrait les remplacer par les sommes de contrôle avec MD5.   Il y a 
aussi des cas où, pour diverses raisons, l'amont de l'activité de la Les 
sommes de contrôle sont tout simplement erronées et devraient être 
remplacées pour les consommateurs en aval.




Assurer la livraison (inflight)
-------------------------------

Le fait de ne pas établir correctement les protocoles de complétion de fichiers est 
une source commune d'incohérences intermittentes, difficile de diagnostiquer.
Pour des transferts de fichiers fiables, Il est essentiel que l'expéditeur et 
le destinataire s'entendent sur la façon de représenter un fichier qui n'est pas complet.
L'option *inflight* (c'est-à-dire qu'un fichier est *en vol* entre l'expéditeur et
le destinataire) s´offre pour accommoder différentes situations :


+--------------------------------------------------------------------------------------------+
|                                                                                            |
|            Protocoles d'assurance de la livraison (par ordre de préférence)                | 
|                                                                                            |
+-------------+---------------------------------------+--------------------------------------+
|Méthode      |Description                            |Application                           |
+=============+=======================================+======================================+
|             |Fichier envoyé avec le bon nom         |Envoyer à Sarracenia, et              |
| NONE        |message `sr_post(7) <sr_post.7.rst>`_  |publié quand le fichier est complet   |
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
| tmp/        |Déplacé au fin de transfert            |les suffixes                          |
| (subdir)    |                                       |                                      | 
|             |Même performance que Suffixe           |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |la convention Linux pour *masquer* les |Envoi à des systèmes qui n´acceptent  |
| .           |fichiers. renommé au fin de transfert  |les suffixes                          |
| (Préfixe)   |Préfixer les noms par '.'              |                                      | 
|             |Même performance que Suffixe           |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Âge minimum (temps de modification)    |Dernier choix, ne garantit un délai   |
| entier      |du fichier avant que le transfer soit  |que si aucun autre moyen peut servir  |
| (mtime)     |considéré Complèté.                    |                                      |
|             |                                       |Réception de ceux qui ne coopèrent pas|
|             |Retard tous les avis                   |                                      |
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
   


TRAITEMENT PÉRIODIQUE
=====================

La plupart des traitements ont lieu à la réception d'un message, mais il y a aussi
un traitement périodique, du travail qui se produit à chaque *battement de coeur* (par 
défaut est de 5 minutes.) Chaque *heartbeat*, tous les les *plugins* 
configurés *on_heartbeat* sont exécutés. Par défaut, il y en a trois :

 heartbeat_log - imprime "heartbeat" dans le journal.
 heartbeat_cache - vieillit par rapport aux anciennes entrées dans le cache, afin de minimiser sa taille.
 heartbeat_memory - vérifie l'utilisation de la mémoire de processus, et redémarre si elle est trop grande.
 heartbeat_pulse - confirme que la connectivité avec les courtiers est toujours bonne. Restauration si nécessaire.

Le journal contiendra les messages des trois plugins à chaque intervalle de battement de coeur, 
et si un traitement périodique supplémentaire est nécessaire, l'utilisateur peut ajouter davantage
de *plugins* à executer avec l'option *on_heartbeat*. 


REPRISE EN CAS D´ERREUR
=======================

Les outils sont conçus pour bien fonctionner sans surveillance, et lorsque des 
erreurs transitoires se produisent, l´application fait de leur mieux pour se rétablir les flots.
Il y a des délais d'attente sur toutes les opérations, et lorsqu'une panne est détecté, 
le problème est noté pour réessayer. Des erreurs peuvent se produire à plusieurs reprises :
 
 * Établissement d'un lien avec le courtier.
 * la perte d'une connexion avec le courtier
 * l'établissement d'une connexion au serveur de fichiers pour un fichier (à télécharger ou à télécharger.)
 * perte d'une connexion au serveur.
 * pendant le transfert de données.
 
Initialement, les programmes essaient de télécharger (ou d'envoyer) un fichier un 
nombre fixe (*attempts*, par défaut : 3) fois.  Si les trois tentatives de traitement du 
fichier échouent, le fichier est placé dans le fichier de réessai d'une instance.
Le programme poursuit ensuite le traitement des nouveaux postes. Lorsqu'il n'y a pas de 
nouveaux transfers en attente, le programme recherche un fichier à traiter dans la 
file d'attente de réessai. Il vérifie ensuite si le fichier est si vieux qu'il est 
au-delà de la *retry_expire* (par défaut : 2 jours.) Si le fichier n'est pas expiré, 
alors il déclenche une nouvelle série de tentatives de traitement du dossier. Si 
les tentatives échouent, il reste dans la file d'attente de réessai.

Cet algorithme garantit que les programmes ne sont pas bloqués sur un seul mauvais 
produit qui empêche le reste de la file d'attente et permet une récupération 
raisonnable et graduelle de l'ensemble de la file d'attente permettant la circulation 
préférentielle de données fraîches et l'envoi opportuniste d'anciennes données.
lorsqu'il y a des lacunes.

Bien qu'un traitement rapide de bonnes données soit très souhaitable, il est important 
de ralentir lorsque des erreurs se produisent.  Souvent, les erreurs sont liées à la 
charge, et le fait de réessayer rapidement ne fera qu'empirer les choses.  Sarracenia 
utilise un *exponentiel back-off* en de nombreux points pour éviter la surcharge d'un 
serveur lorsqu'il y a des erreurs. Le back-off peut s'accumuler jusqu'au point où les 
tentatives pourraient être séparées par une minute ou deux. Une fois que le serveur 
recommence à répondre normalement, les programmes reviendront à la vitesse normale
de traitement.


EXEMPLES
========

Voici un court exemple complet de fichier de configuration:: 

  broker amqps://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#.
  accept .*

Le fichier ci-dessus se connectera au courtier dd.weather.gc.ca, en tant que
*anonymous* avec mot de passe *anonymous* (par défaut) pour obtenir des 
avis à propos des fichiers qui arrivent dans le répertoire http://dd.weather.gc.ca/model_gem_global/25km/grib2.
Tous les fichiers qui arrivent dans ce répertoire ou en dessous seront téléchargés. 
dans le répertoire courant (ou simplement imprimé sur la sortie standard si l'option -n). 
a été spécifié.) 

Une variété d'exemples de fichiers de configuration sont disponibles ici :

 `https://github.com/MetPX/sarracenia/tree/master/sarra/examples <https://github.com/MetPX/sarracenia/tree/master/sarra/examples>`_



NOMMER LES ÉCHANGES ET LES FILES D'ATTENTE
==========================================

Alors que dans la plupart des cas, une bonne valeur est générée par l'application, dans certains cas,
c´est nécessaire de remplacer ces choix par une spécification utilisateur explicite.
Pour ce faire, il faut connaître les règles de nommage des files d'attente :

1. les noms de file d'attente commencent par q\_.
2. ceci est suivi de <amqpUserName> (le propriétaire/utilisateur du nom d'utilisateur du courtier de la file d'attente).
3. suivi d'un deuxième tiret de soulignement ( \_ )
4. suivi d'une chaîne de caractères au choix de l'utilisateur.

La longueur totale du nom de la file d'attente est limitée à 255 octets de caractères UTF-8.

Il en va de même pour les échanges.  Les règles sont les suivantes :

1. Les noms de échanges commencent par x
2. Les échanges qui se terminent par *public* sont accessibles (pour lecture) par tout utilisateur authentifié.
3. Les utilisateurs sont autorisés à créer des échanges avec le modèle : xs_<amqpUserName>_<<whatever> de tels échanges ne peuvent être écrits que par cet utilisateur. 
4. Le système (sr_audit ou administrateurs) crée l'échange xr_<amqpUserName> comme lieu d'envoi de rapports pour un utilisateur donné. Il n'est lisible que par cet utilisateur.
5. Les utilisateurs administratifs (rôles d'administrateur ou de serveur) peuvent poster ou s'abonner n'importe où.

Par exemple, xpublic n'a pas de xs\_ et un modèle de nom d'utilisateur, donc il ne peut être posté que par les utilisateurs admin ou feeder.
Puisqu'il se termine en public, n'importe quel utilisateur peut s'y lier pour s'abonner aux messages postés.
Les utilisateurs peuvent créer des échanges tels que xs_<amqpUserName>_public qui peut être écrit par cet utilisateur (par la règle 3), 
et lue par d'autres (par la règle 2.) Description du flux conventionnel de messages par le biais d'échanges sur une pompe.  
Les abonnés se lient généralement à l'échange public pour obtenir le flux de données principal. C'est la valeur par défaut dans sr_subscribe.

Un autre exemple, un utilisateur nommé Alice aura au moins deux échanges :

  xs_Alice l'échange où Alice poste ses notifications de fichiers et ses messages de rapports.(via de nombreux outils)
  xr_Alice l'échange où Alice lit ses messages de rapport (via sr_report).
  Alice peut créer un nouvel échange en y postant simplement (avec sr_post ou sr_cpost.) s'il répond aux règles de nommage.

généralement un sr_sarra exécuté par un administrateur de pompe lira à partir d'un échange tel que xs_Alice_mydata, 
récupérer les données correspondant au message Alice´s *post* et les mettre à disposition sur la pompe, 
en l'annonçant de nouveau sur l'échange public.





QUEUES - FILES D´ATTENTES et EXECUTION MULTIPLE
===============================================

Lorsqu'il est exécuté, **sr_subscribe** choisit un nom de file d'attente qu'il écrit
à un fichier nommé d'après le fichier de configuration donné en argument à sr_subscribe****.
avec un suffixe.queue ( ."nom de configuration".queue). 
Si sr_subscribe est arrêté, les messages publiés continuent de s'accumuler sur 
le courtier dans cette file d'attente (jusqu´a son *expire* -ation).  Lorsque le 
programme est redémarré, il utilise le nom de la file d'attente stocké dans ce 
fichier pour se connecter à la même file d'attente et ne pas perdre de messages.

Les téléchargements de fichiers peuvent être mis en parallèle en exécutant plusieurs 
processus sr_subscribe qui partageront la file d'attente, et chacun s´occupera d´une
fraction du travail à faire.  Lancez simplement plusieurs instances de sr_subscribe 
dans le même utilisateur/répertoire en utilisant le même fichier de configuration, 

Vous pouvez également exécuter plusieurs sr_subscribe avec différents fichiers 
de configuration pour avoir plusieurs flux de téléchargements ciblant le même répertoire,
et chaque flux de téléchargement peut utliser l´éxecution multiple.

.. Note: :

  Tandis que les courtiers gardent les files d'attente disponibles pendant un 
  certain temps, les files d'attente prennent les ressources suivantes et sont nettoyés 
  de temps à autre. Une file d'attente à laquelle on n'accède pas pour une longue 
  période (dépendant de la mise en œuvre) sera détruite. Une file d'attente qui 
  n'est pas accédé et a trop de fichiers (définis par l'implémentation) mis en 
  file d'attente seront détruits. Les processus qui meurent devraient être 
  redémarrés dans un délai raisonnable afin d'éviter la perte de notifications.
  Il faut aussi porter attention à l´option *expire*.


RAPPORTS
========

Pour chaque téléchargement, par défaut, un message de rapport amqp est renvoyé au courtier.
Ceci est fait avec l'option :

report_back <boolean> (par défaut : True)**. 
rapport_exchange <report_exchangename> (par défaut : xreport|xs_username* )****.

Lorsqu'un rapport est généré, il est envoyé au *report_exchange* configuré. 
les composants administratifs publient directement sur *xreport*, tandis que les 
composants utilisateur postent sur leur propre compte. Les démons de rapport
copient ensuite les messages dans *xreport* après validation.

Ces rapports sont utilisés pour le réglage de la livraison et pour les sources 
de données afin de générer des informations statistiques. Régler cette option à **Faux**, 
pour empêcher la génération de rapports. 


JOURNAUX
========

Les composants écrivent dans des fichiers journaux qui se trouvent par 
défaut dans ~/.cache/sarra/log/<component>_<config>_<config>_<instance>.log.
À la fin de la journée (à minuit), ces fichiers journaux sont tournés automatiquement
par les composants, et l'ancien journal obtient un suffixe de date.
Le répertoire dans lequel les fichiers journaux sont stockés peut être changé par 
l'option **log**, le nombre maximum de fichiers journaux retournés à conserver est défini par le
paramètre *logrotate* et cela continue pour les prochaines rotations. Lorsque le nombre maximum de rotations
a été atteint, le plus vieux fichier journal est supprimé.  Pour l'option d'intervalle, une durée est exprimée
par un nombre et peu prendre un suffixe d'unité de temps, tel que 'd\|D' pour les jours, 'h\|H' pour les heures ou 'm\|M'
pour les minutes. Sans unité, la rotation sera effectuée à minuit.

- debug
   L'option de déverminage **debug** est identique à l'utilisation de **loglevel debug**.

- log <dir> ( défaut: ~/.cache/sarra/log ) (sur Linux)
   Le répertoire ou les fichiers journaux seront placés.

- logrotate <max_logs> ( défaut: 5 )
   Nombre maximal de fichiers journaux archivés.

- logrotate_interval <durée>[<unité_de_temps>] ( défaut: 1 )
   La durée de l'intervalle spécifié et une unité de temps optionnelle (p.ex. 5m, 2h, 3d).

- loglevel ( défaut: info ) 
   Le niveau de journalisation exprimé par la journalisation de python. 
   Les valeurs possibles sont : critical, error, info, warning, debug.

- chmod_log ( défaut: 0600 )
   Les bits de permission qui seront établi pour les fichiers journaux.

Le placement est conforme à : `XDG Open Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_ définissant la variable d'environnement XDG_CACHE_HOME.


INSTANCES
=========

Parfois, une seule instance d'un composant et d'une configuration n'est pas suffisante pour 
traiter et envoyer toutes les notifications disponibles.

(par défaut : 1)**instances <entier> (par défaut : 1)**.

L'option instance permet de lancer plusieurs instances d'un composant et d'une configuration.
Lors de l'exécution de sr_sender par exemple, un certain nombre de fichiers d'exécution qui sont créés.
Dans le répertoire ~/.cache/sarra/sarra/sender/configName: :

  Un .sr_sender_configfigname.state est créé, contenant le nombre d'instances.
  Un .sr_sender_configuration_$instance.pid est créé, contenant le processus PID de $instance.

Dans le répertoire ~/.cache/sarra/var/log: :

  Un fichier.sr_sender_configuration_$instance.log est créé en tant que journal du processus $instance.

Les logs peuvent être écrits dans un autre répertoire que celui par défaut avec l'option :

Log <répertoire logpath> (par défaut : ~/.cache/sarra/var/log)**.

... note: :  
  CORRECTIF : indiquer l'emplacement des fenêtres aussi.... fichiers de points sur les fenêtres ?


.. Note::

  Tandis que les courtiers gardent les files d'attente disponibles pendant un 
  certain temps, les files d'attente prennent les ressources suivantes 
  et sont nettoyés de temps à autre.  Une file d'attente qui n'est pas
  accédé et a trop de fichiers (définis par l'implémentation) mis en file d'attente seront détruits.
  Les processus qui meurent devraient être redémarrés dans un délai raisonnable afin d'éviter
  la perte de notifications.  Une file d'attente qui n'est pas accessible pendant une longue période (dépendant de l'implémentation).
  la période sera détruite. 

.. Note::
   FIXME La dernière phrase n'est pas vraiment correcte. 
    sr_audit agit lorsqu'une file d'attente atteint la taille max_queue_size et ne s'exécute pas.



OPTIONS ACTIVE/PASSIVE 
----------------------

sr_subscribe** peut être utilisé sur un seul nœud de serveur ou sur plusieurs nœuds.
pourrait partager la responsabilité. D'autres, configurés séparément, haute disponibilité
présente un **vip** (ip virtuel) sur le serveur actif. Devrait
le serveur tombe en panne, le **vip** est déplacé sur un autre serveur.
Les deux serveurs fonctionneraient **sr_subscribe**. Les options suivants contrôle
de genre de comportement:

 - **vip <cordes> (Aucune)**.

Lorsque vous n'exécutez qu'un seul **sr_subscribe** sur un serveur, ces options ne 
sont pas définies et sr_subscribe fonctionnera en mode 'standalone'.

Dans le cas des courtiers en grappe, vous devez définir les options pour l'option
vip en mouvement.

**vip 153.14.126.126.3****

Lorsque **sr_subscribe** ne trouve pas le vip, il dort pendant 5 secondes et réessaie.
S´il possède le vip, il consomme et traite un message, puis revérifie le vip.




OPTIONS DE DEPECHE
==================

Lorsque des fichiers sont téléchargés pour ensuite les publiés aux consommateurs en aval, 
il faut indiquer un courtier on on enverra les avis.

L'option **post_broker** définit toutes les informations d'authentification 
pour se connecter à courtier sortie **AMQP**.

amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>*****.

Une fois connecté au courtier AMQP source, le programme construit des notifications après que
le téléchargement d'un fichier a eu lieu. Pour construire la notification et l'envoyer à
le courtier suivant, l'utilisateur définit les options suivantes :

 - **[--blocksize <valeur>]            (défaut: 0 (auto))**
 - **[--outlet <post|json|url>]            (défaut: post)**
 - **[-pbd|--post_base_dir <path>]     (optionelle)**
 - **post_exchange           <name>    (défaut: xpublic)**
 - **post_exchange_split   <number>    (défaut: 0)**
 - **post_base_url            <url>    (MANDATORY)**
 - **on_post               <script>    (défaut: None)**


[--blocksize <valeur>] (défaut: 0 (auto))
-----------------------------------------

L´option **blocksize** contrôle la stratégie de partitionnement utilisée pour poster des fichiers.
la valeur doit être l'une des valeurs suivantes: :

   0 - calcul automatique d'une stratégie de partitionnement appropriée (par défaut)
   1 - toujours envoyer des fichiers entiers en une seule partie.
   <taille du bloc> - utilisation d'une taille de partition fixe (exemple : 1M)

Les fichiers peuvent être publiés en plusieurs parties.  Chaque partie 
a une somme de contrôle séparée. Les pièces et leurs sommes de contrôle sont 
stockées dans le cache. Les cloisons peuvent traverser le réseau séparément, 
et en parallèle.  Lorsque les fichiers changent, les transferts sont 
optimisé en n'envoyant que des portions qui ont changé.

L'option *outlet*, implémentée uniquement dans *sr_cpump*, permet la sortie finale.
d'être autre chose qu'un message AMQP.  Voir `sr_cpump(1) <sr_cpump.1.rst>`_ pour 
plus de détails.

[-pbd|--post_base_dir <path>] (optionelle)
------------------------------------------

L'option *post_base_dir* fournit le chemin du répertoire qui, lorsqu'il est 
combiné (ou trouvé) dans le chemin d'accès donné, donne le chemin absolu local 
vers le fichier de données à enregistrer. La *post_base_dir* du chemin sera 
supprimée du avis. Pour sftp : url's il peut être approprié de spécifier un
chemin relatif à un compte utilisateur.  Un exemple de cette utilisation 
serait :  -pbd ~user -url sftp:user@host
pour file : url's, base_dir n'est généralement pas approprié.  Pour publier 
un chemin absolu, omettez le paramètre -pbd, et spécifiez simplement le chemin 
complet en argument.

post_base_url <url> (MANDATORY)
-------------------------------

L'option **post_base_url** définit comment obtenir le fichier.... il définit
le protocole, hôte, port, et optionnellement, l'utilisateur.  C'est une 
bonne pratique de ne pas inclure les mots de passe dans l´URL.

post_exchange <name> (défaut: xpublic)
--------------------------------------

L'option **post_exchange**, qui permet d'échanger la nouvelle notification.
sera publié.  Dans la plupart des cas, il s'agit d'un'xpublic'.

Chaque fois qu'une avis se produit pour un produit, un utilisateur peut 
définir de déclencher un script. L'option **on_post** serait utilisée pour faire 
une telle configuration.

post_exchange_split <number> (défaut: 0)
----------------------------------------

L'option **post_exchange_split** ajoute un suffixe à deux chiffres résultant d'une
division entière du dernier digit de la somme de contrôle, afin de répartir les 
avis entre un certain nombre d'échanges, selon la valeur de leur somme de contrôle.
C'est utilisé dans les pompes à trafic élevé pour permettre des instances 
multiples de sr_winnow, ce qui ne peut pas être instancié de la manière normale. exemple::

    post_exchange_split 5
    post_exchange xwinnow

se traduira par l'envoi de messages à cinq échanges nommées xwinnow00, xwinnow01,
xwinnow02, xwinnow03 et xwinnow04, où chaque échange ne recevra qu'un cinquième du flux total.
xinnow01 recevra tous les messages dont la reste quand sa somme de contrôle est divisé par 5 
est 1.


Configurations à distance
-------------------------

On peut spécifier des URI comme fichiers de configuration, plutôt que des fichiers locaux. Exemple :

  - **--config http://dd.weather.gc.ca/alerts/doc/cap.conf*****.

Au démarrage, sr_subscribe vérifie si le fichier local cap.conf existe dans le répertoire 
répertoire de configuration local.  Si c'est le cas, alors le fichier sera lu pour trouver
une ligne comme ça :

  **--remote_config_config_url http://dd.weather.gc.ca/alerts/doc/cap.conf*****.

Dans ce cas, il vérifiera l'URL distante et comparera le temps de modification.
du fichier distant contre le fichier local. Le fichier distant n'est pas plus récent ou ne peut pas être modifié.
est atteint, alors le composant continuera avec le fichier local.

Si le fichier distant est plus récent ou s'il n'y a pas de fichier local, il sera téléchargé, 
et la ligne remote_config_url_config_url y sera pré-pendue, de façon à ce qu'elle continue 
pour se mettre à jour à l'avenir.


POMPAGE
=======

*Ceci n'intéresse que les administrateurs*.

Les sources de données peuvent indiquer les grappes auxquelles elles aimeraient que les 
données soient envoyées. Le pompage est implanté par les administrateurs quand ils
arrange pour la copie de données entre des pompes. C´est accompli par moyen des 
plugins on_message qui sont fournis avec le paquet.

lorsque les messages sont publiés, si aucune destination n'est spécifiée, la 
livraison est présumée être seulement la pompe elle-même.  Pour spécifier les 
pompes de destination supplémentaires pour un fichier, les sources utilisent la 
commande l'option *to* quand on publie.  Cette option définit le champ 
to_clusters pour l'interprétation par les administrateurs de pompes en aval.

Les Pompes de données, lors de l'acquisition de données provenant d'autres 
pompes (en utilisant une pelle, un subscribe ou un sarra) devrait inclure le 
plugin *msg_to_clusters* et spécifier les clusters qui sont accessibles à partir 
de la pompe locale, dont les données devraient être copiées dans la pompe 
locale, en vue d'une diffusion ultérieure.
réglages de l'échantillon: :

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

Dans cet exemple, la pompe locale (appelée DDI) sélectionnerait les messages 
destinés aux clusters DD ou DDI, et les rejeter pour le DDSR, qui n'est pas 
dans la liste.  Cela implique que les données destinée au grappe DDI ou bien DD
devraient être accepter.

Ce qui précède s'occupe de l'acheminement des messages et des données vers 
les consommateurs de données.  Une fois que les consommateurs ont obtenus les données, 
ils génèrent des rapports, et ces rapports se propagent dans la direction opposée,
pas nécessairement par le même itinéraire, retour aux sources. Le routage des 
rapports se fait à l'aide de la fonction *from_cluster*.  en-tête.  Encore une 
fois, cette valeur par défaut est celle de la pompe où les données sont 
injectées, mais peut être remplacée par action de l'administrateur.

Les administrateurs configurent les pelles de routage de rapports à l'aide
du plugin msg_from_cluster. Exemple::

  msg_from_cluster DDI
  msg_from_cluster DD

  on_message msg_from_cluster_cluster

afin que le rapport d'acheminement des pelles obtienne des messages de la
part des consommateurs en aval et qu'il fasse à la disposition des sources en amont.

SCRIPTS PLUGIN
==============

On peut remplacer ou ajouter des fonctionnalités avec des scripts de plugins python.
Sarracenia est livré avec une variété de plugins d'exemple, et en utilise certains 
pour implémenter les fonctionnalités de base comme les fichiers journeaux (implémenté 
par défaut en utilisant msg_log, file_log, post_log, post_log plugins. ).

Les utilisateurs peuvent placer leurs propres scripts dans le sous-répertoire script.
de leur arborescence de répertoire de configuration ( sous Linux, le ~/.config/sarra/plugins.) 

Il y a deux variétés de scripts : do\_* et on\_*.  Les scripts Do\_* sont utilisés
pour remplacer des fonctions, en ajoutant ou en remplaçant des fonctionnalités intégrées, 
par exemple pour mettre en œuvre des protocoles de transfert supplémentaires.

do_download - pour implémenter des protocoles de téléchargement supplémentaires.

do_get - sous ftp/ftps/http/sftp, implémenter la partie get file du processus de téléchargement.

do_poll - do_poll - pour mettre en œuvre des protocoles et des processus d'interrogation supplémentaires.

do_put - sous ftp/ftps/http/sftp implémenter la partie fichier put du processus d'envoi.

do_send - pour mettre en œuvre des protocoles et processus d'envoi supplémentaires.

Ces scripts de protocole de transfert doivent être déclarés à l'aide de l'option **plugin**.
En plus de la ou des fonctions intégrées ciblées, un module **registered_as** qui définit
une liste des protocoles pris en charge par ces fonctions.  Exemple :

def registered_as(self) :
       return ['ftp','ftps']].

Enregistrer de cette façon un plugin, si la fonction **do_download** a été fournie dans ce plugin.
que pour tout téléchargement d'un message avec une url ftp ou ftps, c'est cette fonction qui serait appelée.

Les plugins On\_* sont utilisés plus souvent. Ils permettent d'insérer des actions pour 
augmenter la valeur par défaut. Pour divers cas d'utilisation spécialisée. Les scripts 
sont invoqués en ayant une valeur de spécifie une option on_<event>. L'événement peut être 
l'un des :

- plugin -- declarer un ensemble plugins pour réaliser une fonction collective.

- on_file -- Lorsque la réception d'un fichier est terminée, déclencher une action de suivi.
  L'option **on_file** est par défaut file_log, qui écrit un message d'état de téléchargement.

- on_heartbeat -- déclenche une action de suivi périodique (toutes les *heartbeat* secondes).
  par défaut à heatbeat_cache, et heartbeat_log. heartbeat_cache nettoie le cache périodiquement,
  et heartbeat_log imprime un message de journal (utile pour détecter la différence entre les problèmes).
  et l'inactivité. ) 

- on_html_page -- Dans **sr_poll**, transforme une page html en un dictionnaire python utilisé pour garder à l'esprit les éléments suivants
  les fichiers déjà publiés. Le paquet fournit un exemple de fonctionnement sous plugins/html_page.py.

- on_line -- Dans **sr_poll**, une ligne du ls de l'hôte distant est lue.

- on_message -- quand un message sr_post(7) a été reçu.  Par exemple, un message a été reçu.
  et d'autres critères sont en cours d'évaluation pour le téléchargement du fichier correspondant. si la commande on_msg
  retourne false, alors il n'est pas téléchargé.  (voir, par exemple, Discard_when_lagging.py,
  qui décide que des données trop anciennes ne valent pas la peine d'être téléchargées).

- on_part -- Les transferts de fichiers volumineux sont divisés en plusieurs parties.  Chaque pièce est transférée séparément.
  Lorsqu'une pièce terminée est reçue, on peut spécifier un traitement supplémentaire.

- on_post -- lorsqu'une source de données (ou sarra) est sur le point d'envoyer un message, autorisez la personnalisation du message.
  Ajustements du message. on_part a aussi pour valeur par défaut post_log, qui imprime un message.
  chaque fois qu'un fichier doit être publié.

- on_start - on_start -- s'exécute au démarrage, pour quand un plugin a besoin de récupérer son état.

- on_stop -- s'exécute au démarrage, pour quand un plugin a besoin d'enregistrer l'état.

- on_watch -- lorsque le rassemblement des événements **sr_watch** commence, le plugin on_watch est invoqué.
  Il pourrait être utilisé
  Il pourrait être utilisé pour mettre un fichier dans un des répertoires de surveillance 
  et le faire publier quand c'est nécessaire.




L'exemple le plus simple d'un plugin : Un script do_nothing.py pour **on_file**::

  class Transformer(object): 
      def __init__(self):
          pass

      def on_file(self,parent):
          logger = parent.logger

          logger.info("I have no effect but adding this log line")

          return True

  self.plugin = 'Transformer'

La dernière ligne du script est spécifique au type de plugin étant
écrit, et doit être modifié pour correspondre (on_file ou on_file ou on_file, on_message, on_message 
pour un message on_message, etc...) La pile de plugins. Par exemple, on peut avoir 
multiples *on_message* plugins spécifiés, et ils seront invoqués dans l'ordre. 
donnée dans le fichier de configuration. Si l'un de ces scripts renvoie False, 
le traitement du message/fichier s'arrêtera là. Le traitement n'aura lieu que 
continuer si tous les plugins configurés retournent True. On peut spécifier *on_message None* à 
réinitialiser la liste à aucun plugin (supprime msg_log, ce qui supprime 
l'enregistrement de la réception des messages).

Le seul argument que le script reçoit est **parent**, qui est une donnée.
structure contenant tous les paramètres, comme **parent.<setting>**, et
le contenu du message en tant que **parent.msg** et les en-têtes.
sont disponibles sous la forme **parent.msg[ <header> <header> ]**.  
Le chemin d'accès pour écrire un fichier to est disponible car il y a 
aussi **parent.msg.new_dir** / **parent.msg.new_file****.

Il y a aussi des plugins enregistrés utilisés pour ajouter ou écraser des plugins intégrés. 
scripts de protocole de transfert. Ils doivent être déclarés à l'aide de l'option **plugin**.
Ils doivent enregistrer le protocole (url scheme) pour lequel ils s'engagent à fournir des services.
Le script pour les protocoles de transfert sont :


- do_download - pour implémenter des protocoles de téléchargement supplémentaires.

- do_get  - sous ftp/ftps/http/sftp, implémenter la partie get du processus de téléchargement.

- do_poll - pour mettre en œuvre des protocoles et des processus d'interrogation supplémentaires.

- do_put  - sous ftp/ftps/http/sftp, implémenter la partie put du processus d'envoi.

- do_send - pour mettre en œuvre des protocoles et processus d'envoi supplémentaires.


L'enregistrement se fait avec un module nommé **registered_as****... Il définit
une liste des protocoles pris en charge par le module fourni.


Un exemple de plugin pour **on_file**::


  class Transformer(object): 
      def __init__(self):
          pass

      def on_put(self,parent):
          msg = parent.msg

          if ':' in msg.relpath : return None

          netloc = parent.destination.replace("sftp://",'')
          if netloc[-1] == '/' : netloc = netloc[:-1]

          cmd = '/usr/bin/scp ' + msg.relpath + ' ' +  netloc + ':' + msg.new_dir + os.sep + msg.new_file

          status, answer = subprocess.getstatusoutput(cmd)

          if status == 0 : return True

          return False

      def registered_as(self) :
          return ['sftp']

  self.plugin = 'Transformer'

Ce plugin s'enregistre pour sftp. Un expéditeur avec un tel plugin mettrait le produit en utilisant scp.
Il serait déroutant pour scp d'avoir le chemin de la source avec un ':' dans le nom de fichier,,  
Ici, le est géré en retournant None et en laissant python envoyer le fichier. Le **parent**
contient toutes les informations nécessaires sur le programme.
Quelques autres variables disponibles: :


  parent.msg.new_file : nom du fichier à écrire.
  parent.msg.new_dir : nom du répertoire dans lequel écrire le fichier.
  parent.msg.local_offset : position du décalage dans le fichier local.
  parent.msg.offset : position de décalage du fichier distant
  parent.msg.length : longueur du fichier ou de la partie de fichier
  parent.msg.in_partfile : Fichier T/F temporaire dans le fichier partiel
  parent.msg.local_url : url pour une nouvelle avis


Voir le `Guide de programmation <Prog.rst>`_ pour plus de détails.



File d'attente Sauvegarde/Restauration
======================================


Destination non-disponible
--------------------------

Si le serveur auquel les fichiers sont envoyés est indisponible pour
une période prolongée, et il ya un grand nombre de messages à leur envoyer, 
la file d'attente s'accumulera sur le courtier. Comme la performance de l'ensemble du courtier
est affecté par de grandes files d'attente, il faut les minimiser. 

Les options *-save* et *-restore* servent à éloigner les messages du courtier
quand une file d'attente trop longue s'accumulera certainement.
L'option *-save* copie les messages dans un fichier disque (par instance) (dans le même répertoire).
qui stocke les fichiers state et pid), sous forme de chaînes codées json, une par ligne.
Quand une file d'attente s'accumule: :

   sr_sender stop <config> 
   sr_sender -save start <config> 


Et exécutez l'expéditeur en mode *save* (qui écrit continuellement les messages entrants sur le disque).
dans le journal, une ligne pour chaque message écrit sur le disque: :

  2017-03-03 12:14:51,386 [INFO] sr_sender saving 2 message topic: v02.post.home.peter.sarra_devdocroot.sub.SASP34_LEMM_031630__LEDA_60215

Continuez dans ce mode jusqu'à ce que le serveur absent soit à nouveau disponible.  A ce moment-là::

   sr_sender stop <config> 
   sr_sender -restore start <config> 

Lors de la restauration à partir du fichier disque, des messages tels que les suivants apparaîtront dans le journal::

  2017-03-03 12:15:02,969 [INFO] sr_sender restoring message 29 of 34: topic: v02.post.home.peter.sarra_devdocroot.sub.ON_02GD022_daily_hydrometric.csv

Après le dernier::

  2017-03-03 12:15:03,112 [INFO] sr_sender restore complete deleting save file: /home/peter/.cache/sarra/sender/tsource2send/sr_sender_tsource2send_0000.save 


et le sr_sender fonctionnera normalement par la suite.






Shovel Save/Restore
-------------------

Si une file d'attente s'accumule sur un courtier parce qu'un abonné n'est pas en mesure 
de traiter sa demande. La performance globale du courtier en souffrira si on laisse ainsi 
la file d'attente traîner. En tant qu'administrateur, on pourrait conserver une 
configuration::


  % more ~/tools/save.conf
  broker amqp://tfeed@localhost/
  topic_prefix v02.post
  exchange xpublic

  post_rate_limit 50
  on_post post_rate_limit
  post_broker amqp://tfeed@localhost/


La configuration repose sur l'utilisation d'un compte d'administrateur ou d'alimentation.
Notez la file d'attente qui contient des messages, dans ce cas q_tsub.sr_subscribe.t.99524171.43129428.  Invoquer la pelle en mode de sauvegarde des messages des consommateurs de la file d'attente.
et les sauvegarder sur disque::

  % cd ~/tools
  % sr_shovel -save -queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf

  2017-03-18 13:07:27,786 [INFO] sr_shovel start
  2017-03-18 13:07:27,786 [INFO] sr_sarra run
  2017-03-18 13:07:27,786 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:07:27,788 [WARNING] non standard queue name q_tsub.sr_subscribe.t.99524171.43129428
  2017-03-18 13:07:27,788 [INFO] Binding queue q_tsub.sr_subscribe.t.99524171.43129428 with key v02.post.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:07:27,790 [INFO] report_back to tfeed@localhost, exchange: xreport
  2017-03-18 13:07:27,792 [INFO] sr_shovel saving to /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save for future restore
  2017-03-18 13:07:27,794 [INFO] sr_shovel saving 1 message topic: v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:07:27,795 [INFO] sr_shovel saving 2 message topic: v02.post.hydrometric.doc.hydrometric_StationList.csv
          .
          .
          .
  2017-03-18 13:07:27,901 [INFO] sr_shovel saving 188 message topic: v02.post.hydrometric.csv.ON.hourly.ON_hourly_hydrometric.csv
  2017-03-18 13:07:27,902 [INFO] sr_shovel saving 189 message topic: v02.post.hydrometric.csv.BC.hourly.BC_hourly_hydrometric.csv

  ^C2017-03-18 13:11:27,261 [INFO] signal stop
  2017-03-18 13:11:27,261 [INFO] sr_shovel stop


  % wc -l /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  189 /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  % 

Les messages sont écrits dans un fichier dans le répertoire de mise en cache 
pour une utilisation future, avec les éléments suivants le nom du fichier 
étant basé sur le nom de configuration utilisé. le fichier est dans le 
répertoire format json, un message par ligne (les lignes sont très 
longues) et apte au filtrage avec d'autres outils.
Notez qu'un seul fichier de sauvegarde par fichier la configuration est 
automatiquement définie, de sorte que pour sauvegarder plusieurs files 
d'attente, il faudrait une seule configuration.  par file d'attente à 
enregistrer. Une fois que l'abonné est de nouveau en service, on peut
replacer les messages qui avaient enregistré dans un fichier dans la file d'attente
d´origine::

  % sr_shovel -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf

  2017-03-18 13:15:33,610 [INFO] sr_shovel start
  2017-03-18 13:15:33,611 [INFO] sr_sarra run
  2017-03-18 13:15:33,611 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:15:33,613 [INFO] Binding queue q_tfeed.sr_shovel.save with key v02.post.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:15:33,615 [INFO] report_back to tfeed@localhost, exchange: xreport
  2017-03-18 13:15:33,618 [INFO] sr_shovel restoring 189 messages from save /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 
  2017-03-18 13:15:33,620 [INFO] sr_shovel restoring message 1 of 189: topic: v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:15:33,620 [INFO] msg_log received: 20170318165818.878 http://localhost:8000/ observations/swob-ml/20170318/CPSL/2017-03-18-1600-CPSL-AUTO-swob.xml topic=v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml lag=1034.74 sundew_extension=DMS:WXO_RENAMED_SWOB:MSC:XML::20170318165818 source=metpx mtime=20170318165818.878 sum=d,66f7249bd5cd68b89a5ad480f4ea1196 to_clusters=DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM parts=1,5354,1,0,0 toolong=1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß from_cluster=DD atime=20170318165818.878 filename=2017-03-18-1600-CPSL-AUTO-swob.xml 
     .
     .
     .
  2017-03-18 13:15:33,825 [INFO] post_log notice=20170318165832.323 http://localhost:8000/hydrometric/csv/BC/hourly/BC_hourly_hydrometric.csv headers={'sundew_extension': 'BC:HYDRO:CSV:DEV::20170318165829', 'toolong': '1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß', 'filename': 'BC_hourly_hydrometric.csv', 'to_clusters': 'DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM', 'sum': 'd,a22b2df5e316646031008654b29c4ac3', 'parts': '1,12270407,1,0,0', 'source': 'metpx', 'from_cluster': 'DD', 'atime': '20170318165832.323', 'mtime': '20170318165832.323'}
  2017-03-18 13:15:33,826 [INFO] sr_shovel restore complete deleting save file: /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 


  2017-03-18 13:19:26,991 [INFO] signal stop
  2017-03-18 13:19:26,991 [INFO] sr_shovel stop
  % 

Tous les messages enregistrés sont renvoyés au *return_to_to_queue* nommé. Notez que 
l'utilisation de la limite *post_rate_limit* empêche la file d'attente d'être inondée 
de centaines de messages par seconde. La limite de taux d'utilisation aura besoin de
d'être accordé dans la pratique.

par défaut, le nom du fichier de sauvegarde est choisi 
dans ~/.cache/sarra/shovel/<config>_<instance>.save.
Pour choisir une destination différente, l'option *save_file* est disponible::

  sr_shovel -save_file `pwd`/here -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428./save.conf foreground

créera les fichiers de sauvegarde dans le répertoire courant nommé here_000x.save où x est le numéro d'instance (0 pour le foreground).


ROLES
=====


*d'intérêt uniquement pour les administrateurs*

Les options d'administration sont définies à l'aide de::

  sr_subscribe edit admin

L'option *feeder* spécifie le compte utilisé par défaut pour les transferts 
système pour les composants tels que sr_shovel, sr_sarra et sr_sender (lors de publication).

-- **feeder amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>** (valeur par défaut : Aucun)
-- **admin <nom> (par défaut : Aucun)**

Lorsqu'elle est définie, l'option admin permet à sr de démarrer le démon sr_audit. 
FIXME: a cet heure, tout le monde roule sr_audit... 
La plupart des utilisateurs sont définis à l'aide de l'option *déclarer*.

-- **declare <rôle> <nom> (pas de valeurs par défaut)**.

subscriber
----------

  Un *subscriber* (abonné) est un utilisateur qui ne peut s'abonner qu'aux données 
  et renvoyer des messages de rapport. Les abonnés ne sont pas autorisés à injecter des données.
  Chaque abonné a un central xs_<user>nommé sur la pompe, où si un utilisateur est 
  nommé *Acme*, l'échange correspondant sera *xs_Acme*.  Cet échange
  est l'endroit où un processus sr_subscribe enverra ses messages de rapport.

  Par convention/défaut, l'utilisateur *anonyme* est créé sur toutes les pompes pour 
  permettre l'abonnement sans un compte spécifique.


source
------


  Un utilisateur autorisé à s'abonner ou à générer des données. Une source ne représente 
  pas nécessairement une personne ou un type de données, mais plutôt une organisation 
  responsable des données produites. Ainsi, si une organisation recueille et met à 
  disposition dix types de données avec un seul interlocuteur email ou numéro de 
  téléphone pour des questions sur les données et leur disponibilité, alors tous les
  ces activités de recouvrement pourraient utiliser un seul compte " source ".

  Chaque source reçoit un échange xs_<user> pour l'injection de postes de données 
  et, comme un abonné.  pour envoyer des messages de rapport sur le traitement et 
  la réception des données. la source peut aussi avoir un xl_<utilisateur>>.  échange 
  où, selon les configurations d'acheminement des rapports, les messages de rapport 
  des consommateurs seront envoyés.

Les identifiants d'utilisateur sont placés dans les fichiers d'identifiants, 
et *sr_audit* mettra à jour. Le courtier va être aligner avec ce qui est spécifié dans 
ce fichier, à condition que le mot de passe administrateur soit déjà correct.
(L´alignement se fait avec sr_audit --users foreground)



FICHIERS DE CONFIGURATION
=========================

Alors qu'on peut gérer les fichiers de configuration à l'aide de la fonction *add*, *remove*,
*list*, *edit*, *disable*, et *enable* actions, on peut aussi tout faire.
des mêmes activités manuellement en manipulant les fichiers dans les paramètres.
dans l'annuaire de l'entreprise.  Les fichiers de configuration pour une configuration sr_subscribe. 
appelé *myflow* serait ici :

 - linux : ~/.config/sarra/subscribe/myflow.conf (selon : XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.rst>`_ ) 

 - Windows : %AppDir%/science.gc.ca/sarra/myflow.conf, cela pourrait être :
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\sarra\myflow.conf

 - MAC : FIXME.

Le sommet de l'arborescence a *~/.config/sarra/default.conf* qui contient les paramètres suivants
sont lus par défaut pour tout composant au démarrage. Dans le même répertoire, *~/.config/sarra/credentials.conf* contient des informations d'identification (mots de passe) à utiliser par sarracenia ("CREDENTIALS" pour plus de détails. ).

On peut également définir la variable d'environnement XDG_CONFIG_HOME pour remplacer 
le placement par défaut, ou bien Les fichiers de configuration individuels peuvent 
être placés dans n'importe quel répertoire et invoqués avec la commande chemin complet.
Lorsque des composants sont invoqués, le fichier fourni est interprété comme un fichier 
(avec un suffixe.conf conf supposé.) S'il n'est pas trouvé comme chemin d'accès au 
fichier, alors l'option recherchera dans le répertoire de configuration du 
composant ( **config_dir** / **component******) pour un fichier.conf correspondant.

S'il n'est toujours pas trouvé, il le recherchera dans le répertoire de configuration du site.
(linux : /usr/share/default/sarra/**component**).

Enfin, si l'utilisateur a défini l'option **remote_config** sur True et s'il 
dispose de sites web configurés où l'on peut trouver des configurations 
(option **remote_config_config_url**), Le programme essaiera de télécharger 
le fichier nommé à partir de chaque site jusqu'à ce qu'il en trouve un.
En cas de succès, le fichier est téléchargé dans **config_dir/Downloads** et 
interprété par le programme à partir de là.  Il y a un processus similaire 
pour tous les *plugins* qui peuvent être interprété et exécuté à l'intérieur 
des composantes de la Sarracenia.  Les composants chercheront en premier lieu
dans le répertoire *plugins* dans l'arbre de configuration des 
utilisateurs, puis dans le site, puis dans le paquet sarracenia lui-même, 
et finalement il regardera à distance.







AUSSI VOIR
==========

**commandes usager:**

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés.

`sr_post(1) <sr_post.1.rst>`_ - publier les avis de fichiers.

`sr_watch(1) <sr_watch.1.rst>`_ -  sr_post(1) en boucle, veillant sur les répertoires.

`sr_sender(1) <sr_sender.1.rst>`_ - s'abonne aux avis des fichiers locaux, envoie les aux systèmes distants, et les publier à nouveau.

`sr_report(1) <sr_report.1.rst>`_ - messages de rapport de processus.

**commandes administratives:**

`sr_shovel(8) <sr_shovel.8.rst>`_ - copier des avis (pas les fichiers).

`sr_winnow(8) <sr_winnow.8.rst>`_ - une sr_shovel(1) avec *cache* pour vaner (séparer le blé de l'ivraie.)

`sr_sarra(8) <sr_sarra.8.rst>`_ - Outil pour S´abonner, acquérir, et renvoyer récursivement ad nauseam.

`sr_audit(8) <sr_audit.8.rst>`_ - daémon de surveillance, configuration de pompe, repart de composantes malades.

`sr_log2save(8) <sr_log2save.8.rst>`_ - convertisseur de fichiers journeaux en fichier de sauvegarde pour renvoi de messages.


**formats:**

`sr_post(7) <sr_post.7.rst>`_ - Le format des avis (messages d'annonce AMQP)

`sr_report(7) <sr_report.7.rst>`_ - le format des messages de rapport.

`sr_pulse(7) <sr_pulse.7.rst>`_ - Le format des messages d'impulsion.

**page d´acceuil:**

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe est un composant de MetPX-Sarracenia, la pompe de données basée sur AMQP.


COMPATIBILITE avec SUNDEW
=========================


Pour la compatibilité avec sundew, il existe des options de livraison supplémentaires qui peuvent être spécifiées.

**destfn_script <script <script> (par défaut : Aucun)**.

Cette option définit un script à exécuter lorsque tout est prêt.
pour la livraison du produit.  Le script reçoit la classe sr_sender.
de l'instance.  Le script prend le parent comme un argument, et par exemple, n'importe quel
modification de **parent.msg.new_file** changera le nom du fichier écrit localement.

**filename <mot-clé> (par défaut:WHATFN)**

De **metpx-sundew** le support de cette option offre toutes sortes de possibilités.
pour régler le nom de fichier distant. Certains **mots-clés** sont basés sur le fait que
Les noms de fichiers **metpx-sundew** sont des chaînes de cinq (à six) champs séparés 
par des deux-points.  Les mots-clés possibles sont:

*WHATFN**
 - la première partie du nom de fichier sundew (chaîne de caractères avant le premier :)

**HEADFN**
 - HEADER fait partie du nom de fichier sundew.

**SENDER**
 - le nom de fichier sundew peut se terminer par une chaîne de caractères SENDER=<<string> dans ce cas, la chaîne <string> sera le nom de fichier distant.

**NONE**
 - Livraison avec le nom complet du fichier sundew (sans :SENDER=....)

**NONESENDER**
 - Livraison avec le nom complet du fichier sundew (avec :SENDER=....)

**TIME**
 - l'horodatage ajouté au nom du fichier. Exemple d'utilisation : WHATFN:TIME

**DESTFN=str**
 - déclaration directe du nom de fichier str


**accept <expression régulière> [<keyword>]**

un mot clé peut être ajouté à l'option **accept**. Le mot-clé est l'un des options **FILENAME**.
Un message qui correspond au *accept* regexp, On appliqera l´option indiqué.
Ce mot-clé a priorité sur le mot-clé précédent **filename**.

Le motif **regexp** peut être utilisé pour définir les parties du répertoire si 
une partie du message est mise en place.  à la parenthèse. **sr_sender** peut utiliser 
ces parties pour construire le nom du répertoire. Les premières chaînes de parenthèses 
jointes remplaceront le mot-clé **${0}****$ dans le nom du répertoire
le second **${1}**** etc.

exemple d'utilisation: :

      filename NONE

      directory /this/first/target/directory

      accept .*file.*type1.*

      directory /this/target/directory

      accept .*file.*type2.*

      accept .*file.*type3.*  DESTFN=file_of_type3

      directory /this/${0}/pattern/${1}/directory

      accept .*(2016....).*(RAW.*GRIB).*


Un message sélectionné par la première acceptation serait livré inchangé dans le premier répertoire.

Un message sélectionné par la deuxième acceptation serait livré inchangé dans le deuxième répertoire.

Un message sélectionné par le troisième accept serait renommé "file_of_type3" dans le deuxième répertoire.

Un message sélectionné par le quatrième accepter serait livré inchangé dans un répertoire nommé

*/this/20160160123/pattern/RAW_MERGER_GRIB/directory* si le message aurait une notice comme :

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**




Substitutions OMM
-----------------


Dans MetPX Sundew, il y a une norme de nommage de fichiers beaucoup plus stricte, 
spécialisée pour une utilisation avec Données de l'Organisation météorologique mondiale (OMM).   
Notez que la convention d'appellation de fichier est antérieure, et n'a aucun rapport 
avec la convention de dénomination des fichiers de l'OMM actuellement approuvée, 
mais il s'agit strictement d'une convention interne.  Les fichiers sont séparés en 
six champs par des caractères deux-points.  Le premier champ, DESTFN, inclue un
nom familier aux experts des données de  l'OMM (style 386), un *Abbreviated Header Line (AHL)* 
avec des soulignements remplaçant les blancs::

   TTAAii CCCC YYGGGGg BBB....  

(voir les manuel 386 et 306 de l'OMM pour plus de détails) suivi de chiffres pour rendre le 
produit unique car dans la pratique, (en contraste avec la théorie) il y a un grand nombre 
de produits qui ont les mêmes identificateurs. 
La signification du cinquième champ est une priorité, et le dernier champ est un horodatage.
La signification des autres champs varie selon le contexte.  
Si un fichier est envoyé à Sarracenia et il est nommé selon les conventions Sundew, 
alors les champs de sous-partition suivants sont disponibles::

  ${T1}    remplacer par T1 du bulletin.
  ${T2}    remplacer par le bulletin T2 du bulletin T2
  ${A1}    remplacer par l'A1 du bulletin.
  ${A2}    remplacer par A2 du bulletin.
  ${ii}    remplacer par ii du bulletin.
  ${CCCC}  remplacer par le CCCC du bulletin.
  ${YY}    remplacer par YY du bulletin (jour du mois)
  ${GG}    remplacer par le GG du bulletin (heure du jour, UTC)
  ${gg}    remplacer par le Gg du bulletin (minute de l´heure.)
  ${BBBB}  remplacer par bbb du bulletin.
  ${RYYYY} remplacer par l'année de réception.
  ${RMM}   remplacer par le mois de réception
  ${RDD}   remplacer par le jour de réception
  ${RHH}   Remplacer par l'heure de réception.
  ${RMM}   remplacer par minutes de réception.
  ${RSS}   remplacer par réception seconde


Les champs 'R' du sixième champ, et les autres champs proviennent du premier champs.
Lorsque des données sont injectées dans la Sarracenia à partir de 
Sundew, l'en-tête de message *sundew_extension* est inclu. Cet entête fournira la 
source de ces sous-titres même si les champs ont été supprimés dans les noms
de fichiers actuels utilisés sur le serveur.



PARAMÈTRES OBSOLÈTES
---------------------

Ces paramètres concernent les versions précédentes du client et ont été supplantées.

- **host          <hôte du courtier> (inclue dans broker)**
- **amqp-user     <usager du courtier>  (inclue dans broker)**
- **amqp-password <mot de pass pour l´usage du courtier>  (inclue dans broker)**
- **http-user     <usager pour http>  (inclue dans credentials.conf)**
- **http-password <mot de passe pour http>  (inclu dans credentials.conf)**
- **topic         <amqp pattern> (remplacé par topic_prefix et subtopic)**
- **exchange_type <type>         (default: topic)**
- **exchange_key  <patron AMQP> (calculé par topic_prefix et subtopic)**
- **lock      <locktext>         (changer de nom à inflight)**



Histoire
========

Dd_subscribe a été initialement conçu pour **dd.weather.gc.ca**, un site 
Web d'Environnement Canada où une grande variété de produits météorologiques 
sont mis à la disposition du public. C'est de le nom de ce site que la suite
Sarracenia prend le préfixe dd\_ pour ses outils.  La première a été 
déployée en 2013 à titre expérimental. L'année suivante, prise en charge 
des sommes de contrôle a été ajouté, et à l'automne 2015, les flux ont 
été mis à jour en v02. dd_subscribe still works, mais il utilise les 
paramètres obsolètes décrits ci-dessus.  Il est implémenté en 
python2, alors qu'il est implémenté en python2.  La boîte à outils 
Sarracenia est en python3.

En 2007, lorsque le MetPX était à l'origine open source, le personnel 
responsable faisait partie de Environnement Canada.  En l'honneur de 
la Loi sur les espèces en péril (LEP), afin de mettre en lumière la 
situation critique. d'espèces en voie de disparition qui ne sont pas 
à fourrure (les espèces à fourrure reçoivent toute l'attention) et
parce que les moteurs de recherche trouveront plus facilement des 
références à des noms plus inhabituels, le commutateur MetPX WMO 
original a été nommé d'après une plante carnivore sur l'espèce At
Registre des risques :  Le *Thread-leaved Sundew*.

L'organisation à l'origine de Metpx a depuis déménagé à Services 
partagés Canada.  Il est venu le temps de nommer un nouveau module, 
nous avons gardé avec un thème de plantes carnivores, et a choisi 
un autre indigène dans certaines régions du Canada : *Sarracenia* 
N'importe laquelle d'une variété de sarracénies insectivores. 
Nous aimons les plantes qui mangent de la viande !


dd_subscribe Renommage
----------------------

Le nouveau module (MetPX-Sarracenia) a de nombreux composants, est 
utilisé pour plus que et plus d'un site web, et cause de la confusion pour la
pensée sys-admins.  il est associé à la commande dd(1) (pour convertir et 
copier des fichiers).  Donc, on a échangé tous les composants pour utiliser
le préfixe sr\_.


