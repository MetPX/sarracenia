
===============
SR3 CREDENTIALS
===============

---------------------------------
SR3 Credential: Format du Fichier
---------------------------------

:manual section: 7
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia

CONFIGURATION
=============

Normalement, les mots de passe ne sont pas spécifiés dans les fichiers de configuration. Ils sont plutôt placés
dans le fichier d'identification (credentials) ::

   edit ~/.config/sr3/credentials.conf

Pour chaque URL spécifiée qui nécessite un mot de passe, on place une entrée correspondante dans credentials.conf.
L’option Broker définit toutes les informations d’identification pour se connecter au serveur **RabbitMQ**

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (défaut: amqps://anonymous:anonymous@dd.weather.gc.ca/ )

Pour tous les programmes **sarracenia**, les parties confidentielles des identifiants sont stockées
uniquement dans ~/.config/sarra/credentials.conf.  Cela inclut la destination et le mot de passe du broker
ainsi que les paramètres nécessaires aux composants.  Le format est d'une entrée par ligne.  Exemples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **amqps://usern:passwd@host/ login_method=PLAIN**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**
- **sftp://user5:password5@host  sftp_compat_mode**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:De%3Aize@host  passive,binary,tls**
- **ftps://user8:%2fdot8@host:2121  active,ascii,tls,prot_p**
- **ftp://user8:%2fdot8@host:990  implicit_ftps**
- **https://ladsweb.modaps.eosdis.nasa.gov/ bearer_token=89APCBF0-FEBE-11EA-A705-B0QR41911BF4**

- **s3://nom-du-compartiment s3_anonymous**
- **s3://ID_de_clé_d'accès:clé_d'accès_secrète@nom-du-compartiment**
- **s3://ID_de_clé_d'accès:clé_d'accès_secrète@nom-du-compartiment s3_session_token=une_grande_chaîne**
- **s3://ID_de_clé_d'accès:clé_d'accès_secrète@nom-du-compartiment s3_endpoint=https://my-endpoint.com/**

- **azure://nom_du_compte:clé_de_compte@votre_compte_de_stockage.blob.core.windows.net/**
    - Tous les caractères spéciaux dans account_key doivent être codés en URL (%) lors de l'utilisation de ce format.
- **azure://votre_compte_de_stockage.blob.core.windows.net/ azure_storage_credentials=clé_de_compte**

Dans d’autres fichiers de configuration ou sur la ligne de commande, l’url n’a tout simplement pas le
spécification du mot de passe ou de la clé. L’url donné dans les autres fichiers est recherchée
dans credentials.conf.

Identifiants et Details
-----------------------

Vous devrez peut-être spécifier des options supplémentaires pour des identifiants
spécifiques. Ces détails peuvent être ajoutés après la fin de l’URL, avec plusieurs
détails séparés par des virgules (voir les exemples ci-dessus).

Détails pris en charge :

- ``ssh_keyfile=<path>`` - (SFTP) Chemin du SSH keyfile. Pour SFTP, préférer plutôt une entrée
  dans ``~/.ssh/config``, voir `SFTP et ~/.ssh/config`_ plus bas. ``ssh_keyfile`` n'est pas
  vu par la commande ``scp`` utilisée pour les transferts accélérés.
- ``passive`` - (FTP) Utiliser le mode passif
- ``active`` - (FTP) Utiliser le mode actif
- ``binary`` - (FTP) Utiliser le mode binaire
- ``ascii`` - (FTP) Utiliser le mode ASCII
- ``ssl`` - (FTP) Utiliser le mode SSL/FTP standard
- ``tls`` - (FTP) Utiliser FTPS avec TLS
- ``prot_p`` - (FTPS) Utiliser une connexion de données sécurisée pour les connexions TLS (sinon, du texte clair est utilisé)
- ``bearer_token=<token>`` (ou ``bt=<token>``) - (HTTP) Jeton Bearer pour l’authentification
- ``login_method=<PLAIN|AMQPLAIN|EXTERNAL|GSSAPI>`` - (AMQP) Par défaut, la méthode de connexion sera automatiquement
- ``implicit_ftps`` - (FTPS) Utilisez FTPS implicite (sinon, FTPS explicite est utilisé). Définir ceci définira également ``tls`` sur True.
- ``sftp_compat_mode`` - (SFTP) Désactiver certaines améliorations de performances (lecture préchargée, écritures pipelinées) susceptibles d'entraîner des problèmes de compatibilité avec certains serveurs SFTP.
- Détails du protocole S3:
    - ``s3_endpoint=<url>`` - utiliser un point de terminaison spécifique, comme un service non Amazon S3.
    - ``s3_session_token=<string>`` - lors de la spécification des informations d'identification pour S3, le champ du nom d'utilisateur est utilisé comme « ID de clé d'accès », le mot de passe comme « clé d'accès secrète ». Parfois, un jeton de session est également requis et peut être fourni avec cette option.
    - ``s3_anonymous`` - ne pas signer les demandes (accès anonyme). Équivalent à « --no-sign-request » lors de l'utilisation de la CLI S3.
- Détails du Stockage Blob Azure:
    - ``azure_storage_credentials=<string>`` - votre clé de compte. Il s'agit d'une alternative à l'utilisation de ``azure://nom_du_compte:clé_de_compte@votre_compte_de_stockage.blob.core.windows.net/``.

déterminée. Cela peut être remplacé en spécifiant une méthode Particulière de connexion, ce qui peut être
nécessaire si un broker prend en charge plusieurs méthodes et qu’une méthode incorrecte est automatiquement
sélectionnée.

Note::

 Les informations d’identification SFTP sont facultatives. Sarracenia cherchera dans le répertoire .ssh
 et va utiliser les informations d’identification SSH normales qui s’y trouvent.

 Ces chaînes sont encodées en URL, donc si il y a un compte avec un mot de passe qui contient un caractère spécial,
 son équivalent encodé par URL peut être fourni. Dans le dernier exemple, **%2f** signifie que le
 mot de passe réel est: **/dot8**. L’avant-dernier mot de passe est : **De:olonize**.
 ( %3a étant la valeur encodée url pour un caractère deux-points. )

SFTP et ~/.ssh/config
---------------------

Pour SFTP, mettre les paramètres de connexion dans ``~/.ssh/config`` plutôt que dans
``credentials.conf``, et omettre complètement l'entrée dans ``credentials.conf``.

Sarracenia a deux façons de transférer un fichier par SFTP. Les transferts ordinaires
utilisent la bibliothèque paramiko, que Sarracenia configure à partir de ``credentials.conf``.
Les transferts plus gros que ``accelThreshold`` sont confiés à la commande ``scp`` (voir
``accelScpCommand``). ``scp`` lit ``~/.ssh/config`` et ne connaît pas ``credentials.conf``,
donc tout ce qui n'est inscrit que là lui est invisible. Une clé indiquée par ``ssh_keyfile``
fonctionne pour les transferts ordinaires et manque silencieusement aux transferts accélérés,
ce qui se présente comme une configuration qui fonctionne jusqu'à ce qu'un fichier dépasse
``accelThreshold``.

Les paramètres dans ``~/.ssh/config`` évitent ce problème, parce que les deux chemins les
lisent : ``scp`` nativement, et paramiko parce que Sarracenia cherche lui-même l'hôte dans
``~/.ssh/config`` et en prend ``HostName``, ``User``, ``Port`` et ``IdentityFile``. Ce sont
les quatre seuls paramètres qu'il lit, et seulement le premier ``IdentityFile``. Tout autre
paramètre de la section, comme ``IdentitiesOnly`` ci-dessous, ne s'applique qu'à ``scp``.

Définir une section qui nomme l'hôte, le compte et la clé::

    Host weather-pump
        HostName sftp.example.com
        User sarra
        IdentityFile ~/.ssh/id_ecdsa_weather_pump
        IdentitiesOnly yes

Puis utiliser l'alias comme nom d'hôte dans l'URL::

    sendTo sftp://weather-pump/

et ne rien ajouter à ``credentials.conf`` pour celui-ci.

Un alias ne fonctionne que là où l'URL vient de la configuration : ``sendTo`` pour un sender
et ``pollUrl`` pour un poll. Lorsqu'un subscriber ou un sarra télécharge, l'hôte vient du
``baseUrl`` dans le message de notification, donc le ``Host`` de la section doit être le nom
d'hôte annoncé par l'éditeur, ou il doit y avoir une entrée correspondante dans
``credentials.conf``. Un alias défini seulement localement n'a aucun effet sur les
téléchargements.

L'alias est une étiquette, pas un nom d'hôte, donc un serveur accessible de plusieurs façons
peut avoir une section par façon, chacune avec son propre alias, et pour un serveur qui
déménage, il suffit de modifier sa section.

Ne pas mettre de numéro de port dans l'URL. Donner plutôt le port dans la section::

    Host weather-pump-alt
        HostName sftp.example.com
        Port 2222
        User sarra
        IdentityFile ~/.ssh/id_ecdsa_weather_pump

Un port dans l'URL n'est pas transmis correctement à ``scp``, donc un transfert accéléré vers
``sftp://sarra@host:2222/`` échoue alors qu'un transfert ordinaire vers la même URL réussit.

Note::
 Sarracenia ne consulte ``~/.ssh/config`` que lorsque l'identifiant ne répond pas déjà à la
 question : lorsqu'aucun utilisateur n'est connu, ou lorsque ni clé ni mot de passe n'a été
 fourni. Une entrée de ``credentials.conf`` qui contient un utilisateur et un secret (un mot
 de passe ou un ``ssh_keyfile``) a priorité et la section n'est pas lue. Omettre l'entrée
 est la façon fiable de faire appliquer ``~/.ssh/config``.


VOIR AUSSI
==========



`sr3(1) <sr3.1.html>`_ - Sarracenia ligne de commande principale.

`sr3_post(1) <sr3_post.1.html>`_ - poste des annoncements de fichiers (implémentation en Python.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - poste des annoncements de fichiers (implémentation en C.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - implémentation en C du composant shovel. (Copie des messages)

**Formats:**

`sr3_options(7) <sr_options.7.html>`_ - Les options de configurations

`sr3_post(7) <sr_post.7.html>`_ - Le formats des annonces.

**Page d'Accueil:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia : une boîte à outils de gestion du partage de données pub/sub en temps réel

