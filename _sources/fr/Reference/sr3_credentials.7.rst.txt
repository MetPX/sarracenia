
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

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:De%3Aize@host  passive,binary,tls**
- **ftps://user8:%2fdot8@host:2121  active,ascii,tls,prot_p**
- **ftp://user8:%2fdot8@host:990  implicit_ftps**
- **https://ladsweb.modaps.eosdis.nasa.gov/ bearer_token=89APCBF0-FEBE-11EA-A705-B0QR41911BF4**

Dans d’autres fichiers de configuration ou sur la ligne de commande, l’url n’a tout simplement pas le
spécification du mot de passe ou de la clé. L’url donné dans les autres fichiers est recherchée
dans credentials.conf.

Identifiants et Details
-----------------------

Vous devrez peut-être spécifier des options supplémentaires pour des identifiants
spécifiques. Ces détails peuvent être ajoutés après la fin de l’URL, avec plusieurs
détails séparés par des virgules (voir les exemples ci-dessus).

Détails pris en charge :

- ``ssh_keyfile=<path>`` - (SFTP) Chemin du SSH keyfile
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

