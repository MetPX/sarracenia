
===========
SR3 OPTIONS
===========

------------------------------
SR3 Configuration File Format
------------------------------

:manual section: 7
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

::

  name value
  name value for use
  name value_${substitution}
  .
  .
  .     

DESCRIPTION
===========
Les options sont placées dans des fichiers de configuration, une par ligne, avec le format::

    option <value>

Par exemple::

    debug true
    debug

définit l’option *debug* pour activer un logging plus détaillée. Si aucune valeur n’est spécifiée,
la valeur true est assigné, donc les valeurs ci-dessus sont équivalentes. Un deuxième exemple::

  broker amqps://anonymous@dd.weather.gc.ca

Dans l’exemple ci-dessus, *broker* est le mot-clé de l’option, et le reste de la ligne est le
valeur attribué au paramètre. Les fichiers de configuration sont une séquence de paramètres,
avec un parametre par ligne.
Note:

* les fichiers sont lus de haut en bas, surtout pour *directory*, *strip*, *mirror*,
  et les options *flatten* s’appliquent aux clauses *accept* qui se trouvent dans la suite du fichier.

* La barre oblique (/) est utilisé comme séparateur de chemin dans les fichiers de configuration Sarracenia sur tous les
  systèmes d’exploitation. L'utilisation de la barre oblique inverse comme séparateur (\) (tel qu’utilisé dans la
  cmd shell de Windows) risque de ne pas fonctionner correctement. Lorsque des fichiers sont lu dans Windows, le chemin d’accès
  est immédiatement converti en utilisant la barre oblique. Ceci est pour s'assurer que les options *reject*, *accept*, et
  *strip* peuvent filtrer des expressions correctement. C'est pout cela qu'il est toujours important d'utiliser la barre
  oblique (/) quand un separateur est necessaire.

* **#** est le préfixe des lignes de descriptions non fonctionnelles de configurations ou de commentaires.
  C'est identique aux scripts shell et/ou python

* **Toutes les options sont sensibles aux majuscules et miniscules.** **Debug** n’est pas la même chose que **debug** ni **DEBUG**.
  Ces sont trois options sont différentes (dont deux n’existent pas et n’auront aucun effet et gereront un avertissement
  d'« option inconnue »).

Le fichier a un ordre important. Il est lu de haut en bas, donc les options qui sont assignee sur une ligne on tendence
a affecte les lignes qui suivent::

   mirror off
   directory /data/just_flat_files_here_please
   accept .*flatones.*

   mirror on
   directory /data/fully_mirrored
   accept .* 

In the above snippet the *mirror* setting is off, then the directoy value is set,
so files whose name includes *flatones* will all be place in the */data/just_flat_files_here_please* 
directory. For files which don't have that name, they will not be picked up
by the first accept, and so the mirror on, and the new directory setting will tak over,
and those other files will land in /data/fully_mirrored. A second example:

Dans l’extrait ci-dessus, le paramètre *mirror* est désactivé, et la valeur de *directory* est définie. Les fichiers
dont le nom inclut *flatones* seront donc tous placés dans le repoertoire */data/just_flat_files_here_please*.
Pour les fichiers qui n’ont pas ce nom, ils ne seront pas récupérés par le premier *accept*. Ensuite, avec le *mirror*
activé et le nouveau paramètre de *directory* définie, le restant des fichiers atterriront dans
/data/fully_mirrored. Un deuxième exemple :


séquence #1::

  reject .*\.gif
  accept .*


séquence #2::

  accept .*
  reject .*\.gif


.. note::
   FIXME: cela ne correspond-il qu'aux fichiers se terminant par 'gif' ou devrions-nous y ajouter un $ ?
   cela correspondra-t-il à quelque chose comme .gif2 ? y a-t-il un .* supposé à la fin ?

Dans la séquence #1, tous les fichiers se terminant par 'gif' sont rejetés. Dans la séquence #2, le
accept .* (qui accepte tout) est lu avant la déclaration du rejet,
donc le rejet n’a aucun effet. Certaines options ont une portée globale, plutôt que d’être
interprété dans l’ordre. Dans ces cas, la dernière déclaration remplace celle qu'il y avait plus tot dans le fichier..


Variables
=========

Il est possible de faire une substitutions dans la valeur d'une option. Les valeurs sont représentés par ${name}.
Le nom peut être une variable d’environnement ordinaire, ou choisi parmi un certain nombre de variables deja
intégrés:

**${YYYY}         annee actuelle**
**${MM}           mois actuel**
**${JJJ}          julian actuelle**
**${YYYYMMDD}     date actuelle**

**${YYYY-1D}      annee actuelle   - 1 jour**
**${MM-1D}        mois actuel  - 1 jour**
**${JJJ-1D}       julian actuelle - 1 jour**
**${YYYYMMDD-1D}  date actuelle   - 1 jour**

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

        directory /mylocaldirectory/${YYYYMMDD}/mydailies
        accept    .*observations.*

One can also specify variable substitutions to be performed on arguments to the directory
option, with the use of *${..}* notation:
Il est également possible de spécifier des substitutions de variables sur les arguments du parametre du *directory*,
avec l’utilisation de la notation *${..} * :


* SOURCE   - l’utilisateur amqp qui a injecté des données (extraites du message).
* BD       - le repertoire de base.
* BUP      - le composant du chemin de baseUrl (ou : baseUrlPath).
* BUPL     - le dernier element du chemin du baseUrl. (ou: baseUrlPathLast).
* PBD      - le "post base dir".
* YYYYMMDD - l’horodatage quotidien actuel.
* HH       - l’horodatage horaire actuel.
* *var*    - n'importe quelle variable d’environnement.
* BROKER_USER - le nom d’utilisateur pour l’authentification auprès du broker (par exemple, anonyme)
* PROGRAM     - le nom du composant (subscribe, shovel, etc...)
* CONFIG      - le nom du fichier de configuration en cours d'execution.
* HOSTNAME    - le hostname qui execute le client.
* RANDID      - Un ID aleatoire qui va etre consistant pendant la duration d'une seule invocation.


Les horodatages YYYYMMDD et HH font référence à l’heure à laquelle les données sont traitées par
le composant, ceci n’est pas décodé ou dérivé du contenu des fichiers livrés.
Toutes les dates/heures de Sarracenia sont en UTC.

Reportez-vous à *sourceFromExchange* pour un exemple d’utilisation. Notez que toute valeur deja inegree
dans sarracenia a priorite par rappart a une variable du même nom dans l’environnement.
Notez que les paramètres de *flatten* peuvent être modifiés entre les options de *directory*.


Substitutions Compatible Sundew
-------------------------------
Dans `MetPX Sundew <../Explanation/Glossary.html#sundew>`_, le format de la nomination de fichier est beaucoup plus
stricte, et est specialisee pour utilisation aves les donnees du World Meteorological Organization (WMO).
Notez que la convention du format des fichiers est antérieure, et n’a aucun rapport avec la convention de
dénomination des fichiers de WMO actuellement approuvée, mais est strictement un format interne. Les fichiers sont
séparés en six champs avec deux-points. Le premier champ, DESTFN, est le "Abbreviated Header Line (AHL)" de WMO
(style 386) ou les blancs sont remplace avec des traits de soulignement ::

   TTAAii CCCC YYGGGg BBB ...

(voir le manuel de WMO pour plus de détails) suivis de chiffres pour rendre le produit unique (cela est vrai en
theorie , mais pas en pratique vu qu'il existe un grand nombre de produits qui ont les mêmes identifiants).
La signification du cinquième champ est une priorité, et le dernier champ est un horodatage.
La signification des autres champs varie en fonction du contexte. Exemple de nom de fichier ::

   SACN43_CWAO_012000_AAA_41613:ncp1:CWAO:SA:3.A.I.E:3:20050201200339


Si un fichier est envoyé à sarracenia et qu’il est nommé selon les conventions de Sundew,
les champs de substitution suivants seront disponibles::

  ${T1}    remplacer par le bulletin T1
  ${T2}    remplacer par le bulletin T2
  ${A1}    remplacer par le bulletin A1
  ${A2}    remplacer par le bulletin A2
  ${ii}    remplacer par le bulletin ii
  ${CCCC}  rremplacer par le bulletin CCCC
  ${YY}    remplacer par le bulletin YY   (obs. jour)
  ${GG}    remplacer par le bulletin GG   (obs. heure)
  ${Gg}    remplacer par le bulletin Gg   (obs. minute)
  ${BBB}   remplacer par le bulletin bbb
  ${RYYYY} remplacer par l'annee de réception
  ${RMM}   remplacer par le mois de réception
  ${RDD}   remplacer par le jour de réception
  ${RHH}   remplacer par l'heure de réception
  ${RMN}   remplacer par la minute de réception
  ${RSS}   remplacer par la seconde de réception

The 'R' fields come from the sixth field, and the others come from the first one.
When data is injected into sarracenia from Sundew, the *sundew_extension* message header
will provide the source for these substitions even if the fields have been removed
from the delivered file names.

Les champs 'R' proviennent du sixième champ, et les autres viennent du premier champ.
Lorsque des données sont injectées dans sarracenia à partir de Sundew, l’en-tête du message *sundew_extension*
fournira la source de ces substitions même si les champs ont été supprimés des fichiers livrés.

SR_DEV_APPNAME
~~~~~~~~~~~~~~

La variable d’environnement SR_DEV_APPNAME peut être définie pour que la configuration de l’application et les répertoires
d’état sont créés sous un nom différent. Ceci est utilisé dans le développement pour pouvoir avoir de nombreuses configurations
actives à la fois. Cela permet de faire plus de tests au lieu de toujours travailler avec la configuration *réelle* du développeur.

Exemple : export SR_DEV_APPNAME=sr-hoho... lorsque vous démarrez un composant sur un système Linux, il
va rechercher les fichiers de configuration dans ~/.config/sr-hoho/ et va ecrire les fichiers d’état dans le
répertoire ~/.cache/sr-hoho.


TYPES D'OPTIONS
===============

Les options de sr3 ont plusieurs types :

count
    type de nombre entier.

duration
    un nombre à virgule flottante indique une quantité de secondes (0,001 est 1 miliseconde)
    modifié par un suffixe unitaire ( m-minute, h-heure, w-semaine ).

flag
    une option qui n’a que des valeurs Vrai ou Faux (une valeur booléenne).

float
    un nombre à virgule flottante.

list
    une liste de chaine de characteres, chaque occurrence successive se rajoute au total.
    Tout les options plugins de v2 sont declaree du type liste.

set
    un assortissement de chaine de characteres, chaque occurrence successive s'unionise au total.

size
    taille entière. Suffixes k, m et g pour les multiplicateurs kilo, mega et giga (base 2).

str
    une chaine de caracteres.
   

OPTIONS
=======

Les options actuelles sont énumérées ci-dessous. Notez qu’elles sont sensiblent aux majuscules, et
seulement un sous-ensemble est disponible sur la ligne de commande. Celles qui sont disponibles
sur la ligne de commande ont le même effet que lorsqu’elles sont spécifiés dans un fichier de configuration.

Les options disponibles dans les fichiers de configuration :

accelTreshold <size> defaut: 0 (désactiver.)
---------------------------------------------------

L'option accelThreshold indique la taille minimale d'un fichier transféré pour
qu'un téléchargeur binaire puisse etre lancé.

accelXxxCommand 
----------------
On peut spécifier d’autres fichiers binaires pour les téléchargeurs pour des cas particuliers,

+-----------------------------------+--------------------------------+
|  Option                           |  Valeur par Defaut                  |
+-----------------------------------+--------------------------------+
|  accelWgetCommand                 |  /usr/bin/wget %s -O %d        |
+-----------------------------------+--------------------------------+
|  accelScpCommand                  |  /usr/bin/scp %s %d            |
+-----------------------------------+--------------------------------+
|  accelCpCommand                   |  /usr/bin/cp  %s %d            |
+-----------------------------------+--------------------------------+
|  accelFtpgetCommand               |  /usr/bin/ncftpget %s %d       |
+-----------------------------------+--------------------------------+
|  accelFtpputCommand               |  /usr/bin/ncftpput %s %d       |
+-----------------------------------+--------------------------------+

utilisez %s pour remplacer le nom du fichier source et %d pour le fichier en cours d’écriture.
Un exemple de paramètre à remplacer ::

   accelCpCommand dd if=%s of=%d bs=4096k


accept, reject et acceptUnmatched
---------------------------------


- **accept     <modèle regexp> (optionel) [<mot-cles>]**
- **reject     <modèle regexp> (optionel)**
- **acceptUnmatched   <boolean> (defaut: False)**

Les options **accept** et **reject** traitent les expressions régulières (regexp).
Le regexp est appliqué à l’URL du message pour une correspondance.

Si l’URL d’un fichier correspond à un modèle **reject**, le message
est reconnu comme consommé par le broker et est ignoré.

Celui qui correspond à un modèle **accept** est traité par le composant.

Dans de nombreuses configurations, les options **accept** et **reject** sont melange
avec l’option **directory**.  Ces options associent les messages acceptés
à la valeur du **directory** sous laquelle ils sont spécifiés.

Une fois que toutes les options **accept** / **reject** sont traitées, normalement
le message est reconnu comme consommé et ignoré. Pour remplacer ce comportement,
il est possible de definir **acceptUnmatched** en ettant True. Les paramètres de **accept/reject**
sont interprétés dans l’ordre. Chaque option est traitée de manière ordonnée
de haut en bas. Par exemple:

séquence #1::

  reject .*\.gif
  accept .*

séquence #2::

  accept .*
  reject .*\.gif


Dans la séquence #1, tous les fichiers se terminant par 'gif' sont rejetés.  Dans la séquence #2,
le accept .* (qui accepte tout) est rencontré avant la déclaration de rejet, de sorte que le rejet n’a aucun effet.

Il est recommandé d’utiliser le filtrage côté serveur pour réduire le nombre d’annonces envoyées
au composant, et a la place, en envoyer un surensemble de ce qui est pertinent.
Aussi, et n’effectuez qu’un réglage #FIXME and perform only a fine-tuning with the
client side mechanisms, saving bandwidth and processing for all. More details on how
to apply the directives follow:

Plus de détails sur les directives:

Les options **accept** et **reject** utilisent des expressions régulières (regexp) pour trouver
une correspondance avec l’URL.
Ces options sont traitées séquentiellement.
L’URL d’un fichier qui correspond à un modèle **reject** n’est pas publiée.
Les fichiers correspondant à un modèle **accept** sont publiés.
Encore une fois, un *rename* peut être ajouté à l’option *accept*... les produits qui correspondent
a l'option *accept* seront renommé comme décrit... à moins que le *accept* corresponde a
un fichier, l’option *rename* doit décrire un répertoire dans lequel les fichiers
seront placé (en prefix au lieu de remplacer le nom du fichier).

L’option **permdefault** permet aux utilisateurs de spécifier un masque d'autorisation octal numérique
de style Linux::

  permdefault 040



signifie qu’un fichier ne sera pas publié à moins que le groupe ait l’autorisation de lecture
(sur une sortie ls qui ressemble à : ---r-----, comme une commande chmod 040 <fichier> ).
Les options **permdefault** spécifient un masque, c’est-à-dire que les autorisations doivent être
au moins ce qui est spécifié.

Le **regexp pattern** peut être utilisé pour définir des parties du répertoire si une partie du message est placée
entre parenthèses. **sender** peut utiliser ces parties pour générer le nom du répertoire.
Les chaînes de parenthèses entre les guillemets rst remplaceront le mot-clé **${0}** dans le nom du répertoire...
le second **{1} $ ** etc.

Exemple d’utilisation ::

      filename NONE

      directory /this/first/target/directory

      accept .*file.*type1.*

      directory /this/target/directory

      accept .*file.*type2.*

      accept .*file.*type3.*  DESTFN=file_of_type3

      directory /this/${0}/pattern/${1}/directory

      accept .*(2016....).*(RAW.*GRIB).*


Un message sélectionné par le premier *accept* sera remis inaltérée dans le premier répertoire.

Un message sélectionné par le deuxième *accept* sera remis inaltérée dans deuxième répertoire.

Un message sélectionné par le troisième *accept sera renommé « file_of_type3 » dans le deuxième répertoire.

Un message sélectionné par le quatrième *accept* sera remis inaltérée à un répertoire.

Ca sera appelé  */this/20160123/pattern/RAW_MERGER_GRIB/directory* si la notice du message ressemble a cela:

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**


acceptSizeWrong: <boolean> (defaut: False)
-------------------------------------------

Lorsqu’un fichier est téléchargé et que sa taille ne correspond pas à celle annoncée, il est
normalement rejeté, comme un échec. Cette option accepte le fichier même avec la mauvaise
taille. Cela est utile lorsque le fichier change fréquemment et qu’il y a une certaine file d’attente, donc
le fichier est modifié au moment de sa récupération.

attempts <count> (defaut: 3)
-----------------------------

L’option **attempts** indique combien de fois il faut tenter le téléchargement des données avant d’abandonner.
Le défaut de 3 tentatives est approprié
dans la plupart des cas.  Lorsque l’option **retry** a la valeur false, le fichier est immédiatement supprimé.

Lorsque l’option **attempts** est utilisé, un échec de téléchargement après le numéro prescrit
des **attempts** (ou d’envoi, pour un sender) va entrainer l’ajout du message à un fichier de file d’attente
pour une nouvelle tentative plus tard.  Lorsque aucun message n’est prêt à être consommé dans la file d’attente AMQP,
les requetes se feront avec la file d’attente de "retry".

baseDir <chemin> (defaut: /)
----------------------------

**baseDir** fournit le chemin d’accès au répertoire, et lorsqu’il est combiné avec le chemin d'acces relatif
de la notification sélectionnée, **baseDir** donne le chemin absolu du fichier à envoyer.
Le defaut est None, ce qui signifie que le chemin dans la notification est le chemin absolu.

Parfois, les senders s’abonnent à xpublic local, qui sont des URL http, mais le sender
a besoin d’un fichier local, alors le chemin d’accès local est construit en concaténant::

   baseDir + chemin d'acces relatif dans le baseUrl + relPath


baseUrl_relPath <flag> (defaut: off)
-------------------------------------

Normalement, le chemin d’accès relatif (baseUrl_relPath est False, ajouté au répertoire de base) pour
les fichiers téléchargés seront définis en fonction de l’en-tête relPath inclus
dans le message. Toutefois, si *baseUrl_relPath* est défini, le relPath du message va
être précédé des sous-répertoires du champ baseUrl du message.


batch <count> (defaut: 100)
----------------------------

L’option **batch** est utilisée pour indiquer le nombre de fichiers à transférer
sur une connexion, avant qu’elle ne soit démolie et rétablie.  Sur de très bas volume de
transferts, où des délais d’attente peuvent se produire entre les transferts, cela devrait être
ajuster à 1.  Pour la plupart des situations, le defaut est bien. Pour un volume plus élevé,
on pourrait l’augmenter pour réduire les frais généraux de transfert. Cette option est utilisé que pour les
protocoles de transfert de fichiers, pas non HTTP pour le moment.

blocksize <size> defaut: 0 (auto)
-----------------------------------

REMARQUE: **NON IMPLEMENTÉ pour sr3, devrait revenir dans la version future**
Cette option **blocksize** contrôle la stratégie de partitionnement utilisée pour publier des fichiers.
La valeur doit être l’une des suivantes ::

   0 - calcul automatiquement une stratégie de partitionnement appropriée (defaut).
   1 - envoyez toujours des fichiers entiers en une seule partie.
   <blocksize> - utilisé une taille de partition fixe (taille d’exemple : 1M ).

Les fichiers peuvent être annoncés en plusieurs parties.  Chaque partie a un checksum distinct (somme de contrôle).
Les parties et leurs checksums sont stockées dans la cache. Les partitions peuvent traverser
le réseau séparément et en parallèle.  Lorsque les fichiers changent, les transferts sont
optimisé en n’envoyant que les pièces qui ont changé.

L’option *outlet* permet à la sortie finale d’être autre qu’un post.
Voir `sr3_cpump(1) <sr3_cpump.1.html>`_ pour plus de détails.

broker
------

**broker [amqp|mqtt]{s}://<utilisateur>:<most-de-passe>@<brokerhost>[:port]/<vhost>**

Un URI est utilisé pour configurer une connexion à une pompe de messages, soit
un broker MQTT ou AMQP. Certains composants de Sarracenia fixent un defaut raisonnable pour
cette option. Il faut fournir l’utilisateur normal, l’hôte, le port des connexions.
Dans la plupart des fichiers de configurations,
le mot de passe est manquant. Le mot de passe est normalement inclus seulement dans le fichier
`credentials.conf <sr3_credentials.7.html>`_.

Le travail de Sarracenia n’a pas utilisé de vhosts, donc **vhost** devrait presque toujours être **/**.

pour plus d’informations sur le format URI AMQP: ( https://www.rabbitmq.com/uri-spec.html )

soit dans le fichier default.conf, soit dans chaque fichier de configuration spécifique.
L’option broker indique à chaque composant quel broker contacter.

**courtier [amqp|mqtt]{s}://<utilisateur>:<mot-de-passe>@<brokerhost>[:port]/<vhost>**

::
      (defaut: None et il est obligatoire de le définir )

Une fois connecté à un courtier AMQP, l’utilisateur doit lier une file d’attente
aux échanges et aux thèmes pour déterminer le messages en question.


byteRateMax <size> (defaut: 0)
--------------------------------

**byteRateMax** est supérieur à 0, le processus tente de respecter cette vitesse delivraison
 en kilo-octets par seconde... ftp,ftps,ou sftp)

**FIXME**: byteRateMax... uniquement implémenté par le sender ? ou subscriber aussi, données uniquement, ou messages aussi ?


declare 
-------

env NAME=Value
  On peut également référer a des variables d’environnement dans des fichiers de configuration,
  en utilisant la syntaxe *${ENV}*.  Si une routine de Sarracenia doit utiliser
  une variable d’environnement, elles peuvent être définis dans un fichier de configuration ::

    declare env HTTP_PROXY=localhost

exchange exchange_name
  à l’aide de l’URL d’administration, déclarez l’échange avec *exchange_name*

subscriber
  Un abonné (subsciber) est un utilisateur qui peut seulement s’abonner aux données et renvoyer des messages de rapport.
  Les abonnés n'ont pas le droit d’injecter des données.  Chaque abonné dispose d’un xs_<utilisateur> qui
  s'appelle "exchange" sur
  la pompe. Si un utilisateur est nommé *Acme*, l’échange correspondant sera *xs_Acme*.  Cet échange
  est l’endroit où un processus d’abonnement enverra ses messages de rapport.

  Par convention/defaut, l’utilisateur *anonyme* est créé sur toutes les pompes pour permettre l’abonnement sans abonnement
  a un compte spécifique.


source
  Un utilisateur autorisé à s’abonner ou à générer des données. Une source ne représente pas nécessairement
  une personne ou un type de données, mais plutôt une organisation responsable des données produites.
  Donc, si une organisation recueille et met à disposition dix types de données avec un seul contact,
  e-mail, ou numéro de téléphone, toute question sur les données et leur disponibilité par rapport aux
  activités de collect epeuvent alors en utilisant seul compte "source".

  Chaque source reçoit un échange xs_<utilisateur> pour l’injection de publications de données. Cela est comme un abonné
  pour envoyer des messages de rapport sur le traitement et la réception des données. La source peut également avoir
  un échange xl_<utilsateur> où, selon les configurations de routage des rapports, les messages de rapport des
  consommateurs seront envoyés.

feeder
  Un utilisateur autorisé à écrire à n’importe quel échange. Une sorte d’utilisateur de flux administratif, destiné à pomper
  des messages lorsque aucune source ou abonné ordinaire n’est approprié pour le faire. Doit être utilisé de
  préférence au lieu de comptes d’administrateur pour exécuter des flux.

Les informations d’identification de l’utilisateur sont placées dans le `credentials.conf <sr3_credentials.7.html>`_
et *sr3 --users declare* sera mis à jour
le courtier pour accepter ce qui est spécifié dans ce fichier, tant que le mot de passe d'administrateur est
déjà correct.


debug
-----

Definir l'option debug est identique a utilisé **logLevel debug**

delete <boolean> (defaut: off)
-------------------------------

Lorsque l’option **delete** est définie, une fois le téléchargement terminé avec succès, l’abonné
supprimera le fichier à la source. Par defaut l'option est false.


discard <boolean> (defaut: off)
--------------------------------

L’option **discard**, si elle est définie a true, supprime le fichier une fois téléchargé. Cette option peut être
utile lors du débogage ou pour tester une configuration.


directory <path> (defaut: .)
-----------------------------

L’option *directory* définit où placer les fichiers sur votre serveur.
Combiné avec les options **accept** / **reject**, l’utilisateur peut sélectionner
les fichiers d’intérêt et leurs répertoires de résidence (voir le **mirror**
pour plus de paramètres de répertoire).

Les options **accept** et **reject** utilisent des expressions régulières (regexp) pour trouver une correspondance avec l’URL.
Ces options sont traitées séquentiellement.
L’URL d’un fichier qui correspond à un modèle **reject** n’est jamais téléchargée.
Celui qui correspond à un modèle **accept** est téléchargé dans le répertoire
déclaré par l’option **directory** la plus proche au-dessus de l’option **accept** correspondante.
**acceptUnmatched** est utilisé pour décider quoi faire lorsque aucune clause de rejet ou d’acceptation n’est correspondante.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*


destfn_script <script> (defaut:None)
-------------------------------------

L'option de compatibilité Sundew définit un script à exécuter lorsque tout est prêt
pour la livraison du produit.  Le script reçoit une instance de la classe sender.
Le script prends le parent comme argument, et par exemple, une
modification de **parent.msg.new_file** changera le nom du fichier écrit localement.

download <flag> (defaut: True)
--------------------------------

utilisé pour désactiver le téléchargement dans le composant subscribe et/ou sarra.
Se definit a False par defaut dans les composants de pelle (shovel) ou de vanne (winnow).


durable <flag> (defaut: True)
----------------------------------

L’option AMQP **durable**, sur les déclarations de file d’attente. Si la valeur est True,
le courtier conservera la file d’attente lors des redémarrages du courtier.
Cela signifie que la file d’attente est sur le disque si le courtier est redémarré.


fileEvents <evenement,evenement,...>
----------------------------

Liste séparée par des virgules de types d'événements de fichiers à surveiller.
Événements de fichiers disponibles : créer, supprimer, lier, modifier

Les événements *create*, *modify* et *delete* reflètent ce qui est attendu : un fichier en cours de création,
de modification ou de suppression.
Si *link* est défini, des liens symboliques seront publiés sous forme de liens afin que les consommateurs puissent choisir
comment les traiter. S’il n’est pas défini, aucun événement de lien symbolique sera publié.

.. note::
   déplacer ou renommer des événements entraîne un modèle spécial de double publication, avec une publication en
   utilisant l'ancien nom et definissant le champ *newname*, et un deuxième message avec le nouveau nom, et un champ *oldname*.
   Cela permet aux abonnés d’effectuer un renommage réel et d’éviter de déclencher un téléchargement lorsque cela est possible.

FIXME : algorithme de renommage amélioré en v3 pour éviter l’utilisation de double post... juste


exchange <nom> (defaut: xpublic) et exchange_suffix
------------------------------------------------------

La norme pour les pompes de données est d’utiliser l’échange *xpublic*. Les utilisateurs peuvent établir un
flux de données privées pour leur propre traitement. Les utilisateurs peuvent déclarer leurs propres échanges
qui commencent toujours par *xs_<nom-d'utilisatueur>*. Pour éviter d’avoir à le spécifier a chaque
fois, on peut simplement régler *exchange_suffix kk* qui entraînera l’échange
a etre défini a *xs_<nom-d'utilisatueur>_kk* (en remplaçant le defaut *xpublic*).
Ces paramètres doivent apparaître dans le fichier de configuration avant le
Paramètres *topicPrefix* et *subtopic*.


exchangeDeclare <flag>
----------------------

Au démarrage, par defaut, Sarracenia redéclare les ressources et les liaisons pour s’assurer qu’elles
sont à jour. Si l’échange existe déjà, cet indicateur peut être défini a False,
donc aucune tentative d’échange de la file d’attente n’est faite, ou il s’agit de liaisons.
Ces options sont utiles sur les courtiers qui ne permettent pas aux utilisateurs de déclarer leurs échanges.


expire <duration> (defaut: 5m  == cinq minutes. RECOMMENDE DE REMPLACER)
----------------------------------------------------------------------
L'option *expire* est exprimee sous forme d'une duration... Ca fixe combien de temps
une file d’attente devrait vivre sans connexions.

Un entier brut est exprimé en secondes, si un des suffixe m,h,d,w
sont utilisés, puis l’intervalle est en minutes, heures, jours ou semaines. Après l’expiration de la file d’attente,
le contenu est supprimé et des differences peuvent donc survenir dans le flux de données de téléchargement.  Une valeur de
1d (jour) ou 1w (semaine) peut être approprié pour éviter la perte de données. Cela dépend de combien de temps
l’abonné est sensé s’arrêter et ne pas subir de perte de données.

si aucune unité n’est donnée, un nombre décimal de secondes peut être fourni, tel que
0,02 pour spécifier une durée de 20 millisecondes.

Le paramètre **expire** doit être remplacé pour une utilisation opérationnelle.
Le defaut est défini par une valeur basse car il définit combien de temps les ressources vont etre
assigne au courtier, et dans les premières utilisations (lorsque le defaut etait de de 1 semaine), les courtiers
étaient souvent surchargés de très longues files d’attente pour les tests restants.


filename <mots-clés> (defaut:WHATFN)
-----------------------------------

De **metpx-sundew**, le support de cette option donne toutes sortes de possibilités
pour définir le nom de fichier distant. Certains **keywords** sont basés sur le fait que
les noms de fichiers **metpx-sundew** ont cinq (à six) champs de strings séparées par des deux-points.

La valeur par defaut sur Sundew est NONESENDER, mais dans l’intérêt de décourager l’utilisation
de la séparation par des deux-points dans les fichiers, le defaut dans Sarracenia est WHATFN

Les mots-clés possibles sont :

**WHATFN**
 - la première partie du nom de fichier Sundew (chaîne avant la première :)

**HEADFN**
 - Partie EN-TETE du nom de fichier sundew

**SENDER**
 - le nom de fichier Sundew peut se terminer par une chaîne SENDER=<string> dans ce cas,
   la <string> sera le nom de fichier distant

**NONE**
 -  livrer avec le nom du fichier Sundew complet (sans :SENDER=...)

**NONESENDER**
 -  livrer avec le nom de fichier Sundew complet (avec :SENDER=...)

**TIME**
 - horodatage ajouté au nom de fichier. Exemple d’utilisation : WHATFN:TIME

**DESTFN=str**
 - déclaration str direct du nom de fichier

**SATNET=1,2,3,A**
 - Paramètres d’application satnet interne cmc

**DESTFNSCRIPT=script.py**
 - appeler un script (identique à destfn_script) pour générer le nom du fichier à écrire



flatten <string> (defaut: '/')
-------------------------------

L’option **flatten** permet de définir un caractère de séparation. La valeur par defaut ( '/' )
annule l’effet de cette option.  Ce caractère remplace le '/' dans l’url
et crée un nom de fichier « flatten » à partir de son chemin d’accès dd.weather.gc.ca.
Par exemple, récupérer l’URL suivante, avec les options ::


 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

entraînerait la création du chemin d’accès au fichier::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

follow_symlinks <flag>
----------------------

L’option *follow_symlinks* entraîne la traversée de liens symboliques. Si *follow_symlinks* est défini
et la destination d’un lien symbolique est un fichier, alors ce fichier de destination doit être publié ainsi que le lien.
Si la destination du lien symbolique est un répertoire, le répertoire doit être ajouté à ceux qui sont
surveillé par "watch". Si *follow_symlinks* est faux, alors aucune action liée à la destination du
lien symbolique est prise.

force_polling <flag> (defaut: False)
-------------------------------------

Par defaut, "watch" sélectionne une méthode optimale (dépendante du système d’exploitation) pour regarder un
répertoire.

Pour les grandes arborescence, la méthode optimale peut être plusieur fois (10x ou même
100x) plus rapide à reconnaître lorsqu’un fichier a été modifié. Dans certains cas
cependant, les méthodes optimales de plateforme ne fonctionnent pas (comme avec certains réseaux,
partages, ou systèmes de fichiers distribués), il faut donc utiliser un système plus lent mais avec une methode
de "polling" plus fiable et portable.  Le mot-clé *force_polling* oblige "watch" a sélectionner
la méthode de "polling" malgré la fait qu'il y ait une meilleur option de disponible.

Pour une discussion détaillée, voir:
 `Detecting File Changes <../Explanation/DetectFileHasChanged.html>`_

NOTE::

  Lorsque les répertoires sont consommés par des processus en utilisant l’option *delete* de l’abonné, ils restent vides, et
  chaque fichier doit être signalé à chaque passage.  Lorsque les abonnés n’utilisent pas *delete*, "watch" doit
  savoir quels fichiers sont nouveaux.  Il le fait en notant l’heure du début de la dernière passe du "polling".
  Les fichiers sont publiés si leur heure de modification est plus récente que cela. Cela se traduira par de
  nombreux posts de "watch", qui peuvent être minimisés avec l’utilisation de la cache. On pourrait même dépendre
  de la cache entièrement et activez l’option *delete*, ou "watch" pourra tenter de publier l’arborescence entiere
  à chaque fois (en ignorant mtime).

  **LIMITATION CONNUE** : Lorsque *force_polling* est défini, le paramètre *sleep* doit être
  au moins 5 secondes. À l’heure actuelle, on ne sait pas pourquoi.

header <name>=<valeur>
---------------------

Ajoutez une en-tête <name> avec la valeur donnée aux publicités. Utilisé pour transmettre des strings en tant
que métadonnées dans les publicités pour améliorer la prise de décision des consommateurs.  Doit être utilisé
avec parcimonie. Il y a des limites sur le nombre d’en-têtes pouvant être utilisés, et la réduction de la
taille des messages a des impacts importants sur la performance.

housekeeping <interval> (defaut: 300 secondes)
----------------------------------------------

L’option **housekeeping** définit la fréquence d’exécution du traitement périodique tel que déterminé par
la liste des plugins on_housekeeping. Par defaut, il imprime un message de journal à chaque intervalle de housekeeping.

include config
--------------

inclure une autre configuration dans cette configuration.


inflight <string> (defaut: .tmp ou NONE si post_broker est definit)
------------------------------------------------------------

L’option **inflight** définit comment ignorer les fichiers lorsqu’ils sont transférés
ou (en plein vol entre deux systèmes). Un réglage incorrect de cette option provoque des
transferts peu fiables, et des précautions doivent être prises.  Voir
`Delivery Completion <../Explanation/FileCompletion.html>`_ pour plus de détails.

La valeur peut être un suffixe de nom de fichier, qui est ajouté pour créer un nom temporaire pendant
le transfert.  Si **inflight** est défini a **.**, alors il s’agit d’un préfixe pour se conformer à
la norme des fichiers « cachés » sur unix/linux.
Si **inflight** se termine par / (exemple : *tmp/* ), alors il s’agit d’un préfixe, et spécifie un
sous-répertoire de la destination dans lequel le fichier doit être écrit pendant qu'il est en vol.

Si un préfixe ou un suffixe est spécifié, lorsque le transfert est
terminé, le fichier est renommé à son nom permanent pour permettre un traitement ultérieur.

Lors de la publication d’un fichier avec sr3_post, sr3_cpost ou sr3_watch, l’option **inflight**
peut également être spécifié comme une intervalle de temps, par exemple, 10 pour 10 secondes.
Lorsque l'option est défini sur une intervalle de temps, le processus de publication de fichiers attends
jusqu’à ce que le fichier n’ai pas été modifié pendant cet intervalle. Ainsi, un fichier
ne peux pas être traité tant qu’il n’est pas resté le même pendant au moins 10 secondes.
Si le message d’erreur suivant s’affiche ::

    inflight setting: 300, not for remote

C'est parce que le paramètre d’intervalle de temps n’est pris en charge que par sr3_post/sr3_cpost/sr3_watch.
En regardant les fichiers locaux avant de générer un message, il n’est pas utilisé comme prescrit, un moyen
de retarder l’envoi des fichiers.

Enfin, **inflight** peut être réglé a *NONE*. Dans ce cas, le fichier est écrit directement
avec le nom final, où le destinataire attendra pour recevoir un post pour notifier l’arrivée du fichier.
Il s’agit de l’option la plus rapide et la moins coûteuse lorsqu’elle est disponible.
C’est aussi le defaut lorsqu’un *post_broker* est donné, indiquant qu'un autre processus doit être
notifié après la livraison.

inline <flag> (defaut: False)
------------------------------

Lors de la publication de messages, l’option **inline** est utilisée pour avoir le contenu du fichier
inclus dans le post. Cela peut être efficace lors de l’envoi de petits fichiers sur un niveau élevé de
liens de latence, un certain nombre d’allers-retours peuvent être enregistrés en évitant la récupération
des données utilisant l’URL.  On ne devrait seulement utiliser *inline* pour des fichiers relativement petits.
Lorsque **inline** est actif, seuls les fichiers inférieurs à **inlineByteMax** octets
(defaut: 1024) auront reelement leur contenu inclus dans les messages de post.
Si **inlineOnly** est défini et qu’un fichier est plus volumineux que inlineByteMax, le fichier
ne sera pas affiché.

inlineByteMax <size>
--------------------
la taille maximale des messages à envoyer inline.

inlineOnly
----------
ignorer les messages si les données ne sont pas inline.

inplace <flag> (defaut: On)
----------------------------

Les fichiers volumineux peuvent être envoyés en plusieurs parties, plutôt que de tout en même temps.
Lors du téléchargement, si **inplace** est True, ces parties seront rajoutées au fichier
de manière ordonnée. Chaque partie, après avoir été insérée dans le fichier, est annoncée aux abonnés.
Cela peut être défini a False pour certains déploiements de sarracenia où une pompe
ne voie que quelques parties, et non l’intégralité de fichiers en plusieurs parties.

L’option **inplace** est True par defaut.
Dependamment de **inplace** et si le message était une partie, le chemin peut
modifier à nouveau (en ajoutant un suffixe de pièce si nécessaire).

The **inplace** option defauts to True.
Depending of **inplace** and if the message was a part, the path can
change again (adding a part suffix if necessary).


Instances
---------

Sometimes one instance of a component and configuration is not enough to process & send all available notifications.

**instances      <integer>     (defaut:1)**

The instance option allows launching several instances of a component and configuration.
When running sender for example, a number of runtime files are created.
In the ~/.cache/sarra/sender/configName directory::

  A .sender_configname.state         is created, containing the number instances.
  A .sender_configname_$instance.pid is created, containing the PID  of $instance process.

In directory ~/.cache/sarra/log::

  A .sender_configname_$instance.log  is created as a log of $instance process.

.. Note::

  While the brokers keep the queues available for some time, queues take resources on 
  brokers, and are cleaned up from time to time. A queue which is not accessed 
  and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications. A queue which is not accessed for a long (implementation dependent)
  period will be destroyed. 

integrity <string>
------------------

All file posts include a checksum.  It is placed in the amqp message header will have as an
entry *sum* with defaut value 'd,md5_checksum_on_data'.
The *sum* option tell the program how to calculate the checksum.
In v3, they are called Integrity methods::

         cod,x      - Calculate On Download applying x
         sha512     - do SHA512 on file content  (defaut)
         md5        - do md5sum on file content
         md5name    - do md5sum checksum on filename 
         random     - invent a random value for each post.
         arbitrary  - apply the literal fixed value.

v2 options are a comma separated string.  Valid checksum flags are :

* 0 : no checksum... value in post is a random integer (only for testing/debugging.)
* d : do md5sum on file content 
* n : do md5sum checksum on filename
* p : do SHA512 checksum on filename and partstr [#]_
* s : do SHA512 on file content (defaut)
* z,a : calculate checksum value using algorithm a and assign after download.

.. [#] only implemented in C. ( see https://github.com/MetPX/sarracenia/issues/117 )


logEvents ( defaut: after_accept,after_work,on_housekeeping )
--------------------------------------------------------------

emit standard log messages at the given points in message processing.
other values: on_start, on_stop, post, gather, ... etc...

logLevel ( defaut: info )
--------------------------

The level of logging as expressed by python's logging. Possible values are :  critical, error, info, warning, debug.

logReject ( defaut: False )
----------------------------

Normally, messages rejection is done silently. When logReject is True, a log message will be generated for
each message rejected, and indicating the basis for the rejection.

logStdout ( defaut: False )
----------------------------

The *logStdout* disables log management. Best used on the command line, as there is
some risk of creating stub files before the configurations are completely parsed::

       sr3 --logStdout start

All launched processes inherit their file descriptors from the parent. so all output is like an interactive session.

This is in contrast to the normal case, where each instance takes care of its logs, rotating and purging periodically.
In some cases, one wants to have other software take care of logs, such as in docker, where it is preferable for all
logging to be to standard output.

It has not been measured, but there is a reasonable likelihood that use of *logStdout* with large configurations (dozens
of configured instances/processes) will cause either corruption of logs, or limit the speed of execution of all processes
writing to stdout.


logRotateCount <max_logs> ( defaut: 5 )
----------------------------------------

Maximum number of logs archived.

logRotateInterval <interval>[<time_unit>] ( defaut: 1d )
---------------------------------------------------------

The duration of the interval with an optionel time unit (ie 5m, 2h, 3d)


messageCountMax <count> (defaut: 0)
------------------------------------

If **messageCountMax** is greater than zero, the flow will exit after processing the given
number of messages.  This is normally used only for debugging.

messageRateMax <float> (defaut: 0)
-------------------------------------

if **messageRateMax** is greater than zero, the flow attempts to respect this delivery
speed in terms of messages per second. Note that the throttle is on messages obtained or generated
per second, prior to accept/reject filtering. the flow will sleep to limit the processing rate.


messageRateMin <float> (defaut: 0)
-------------------------------------

if **messageRateMin** is greater than zero, and the flow detected is lower than this rate,
a warning message will be produced:


message_ttl <duration>  (defaut: None)
---------------------------------------

The  **message_ttl**  option set the time a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

mirror <flag> (defaut: off)
----------------------------

The  **mirror**  option can be used to mirror the dd.weather.gc.ca tree of the files.
If set to  **True**  the directory given by the  **directory**  option
will be the basename of a tree. Accepted files under that directory will be
placed under the subdirectory tree leaf where it resides under dd.weather.gc.ca.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
mirror settings can be changed between directory options.

no <count>
----------

Present on instances started by the sr3 management interface.
The no option is only used on the command line, and not intended for users.
It is an option for use by sr3 when spawning instances to inform each process
which instance it is. e.g instance 3 will be spawned with --no 3 

 
nodupe_ttl <off|on|999[smhdw]> 
------------------------------

When **nodupe_ttl** (also **suppress_duplicates*, and **cache** ) is set to a non-zero time 
interval, each new message is compared against ones received within that interval, to see if 
it is a duplicate. Duplicates are not processed further. What is a duplicate? A file with 
the same name (including parts header) and checksum. Every *hearbeat* interval, a cleanup 
process looks for files in the cache that have not been referenced in **cache** seconds, 
and deletes them, in order to keep the cache size limited. Different settings are 
appropriate for different use cases.

A raw integer interval is in seconds, if the suffix m,h,d, or w are used, then the interval
is in minutes, hours, days, or weeks. After the interval expires the contents are
dropped, so duplicates separated by a large enough interval will get through.
A value of 1d (day) or 1w (week) can be appropriate.  Setting the option without specifying
a time will result in 300 seconds (or 5 minutes) being the expiry interval.

**Use of the cache is incompatible with the defaut *parts 0* strategy**, one must specify an
alternate strategy.  One must use either a fixed blocksize, or always never partition files.
One must avoid the dynamic algorithm that will change the partition size used as a file grows.

**Note that the duplicate suppresion store is local to each instance**. When N
instances share a queue, the first time a posting is received, it could be
picked by one instance, and if a duplicate one is received it would likely
be picked up by another instance. **For effective duplicate suppression with instances**,
one must **deploy two layers of subscribers**. Use
a **first layer of subscribers (shovels)** with duplicate suppression turned
off and output with *post_exchangeSplit*, which route posts by checksum to
a **second layer of subscibers (winnow) whose duplicate suppression caches are active.**


nodupe_basis <data|name|path> (defaut: path)
---------------------------------------------

A keyword option (alternative: *cache_basis* ) to identify which files are compared for
duplicate suppression purposes. Normally, the duplicate suppression uses the entire path
to identify files which have not changed. This allows for files with identical
content to be posted in different directories and not be suppressed. In some
cases, suppression of identical files should be done regardless of where in
the tree the file resides.  Set 'name' for files of identical name, but in
different directories to be considered duplicates. Set to 'data' for any file,
regardless of name, to be considered a duplicate if the checksum matches.

This is implemented as an alias for:

 callback_prepend nodupe.name

or:

 callback_prepend nodupe.data

nodupe_fileAgeMax
-----------------

If files are older than this setting (defaut: 30d), then ignore them, they are too
old to post.


outlet post|json|url (defaut: post)
------------------------------------

The **outlet** option is used to allow writing of posts to file instead of
posting to a broker. The valid argument values are:

**post:**

  post messages to an post_exchange

  **post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
  **post_exchange     <name>         (MANDATORY)**
  **post_topicPrefix <string>       (defaut: "v03")**
  **on_post           <script>       (defaut: None)**

  The **post_broker** defauts to the input broker if not provided.
  Just set it to another broker if you want to send the notifications
  elsewhere.

  The **post_exchange** must be set by the user. This is the exchange under
  which the notifications will be posted.

**json:**

  write each message to standard output, one per line in the same json format used for
  queue save/restore by the python implementation.

**url:**

  just output the retrieval URL to standard output.

FIXME: The **outlet** option came from the C implementation ( *sr3_cpump*  ) and it has not
been used much in the python implementation.

overwrite <flag> (defaut: off)
-------------------------------

The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :

1- the file to be downloaded is already on the user's file system at the right place and

2- the checksum of the amqp message matched the one of the file.

The defaut is False.

path <path>
-----------

**post** evaluates the filesystem path from the **path** option
and possibly the **post_baseDir** if the option is used.

If a path defines a file then this file is watched.

If a path defines a directory then all files in that directory are
watched...

If this path defines a directory, all files in that directory are
watched and should **watch** find one (or more) directory(ies), it
watches it(them) recursively until all the tree is scanned.

The AMQP announcements are made of the tree fields, the announcement time,
the **url** option value and the resolved paths to which were withdrawn
the *post_baseDir* present and needed.


permdefault, permDirdefault, permLog, permCopy
----------------------------------------------

Permission bits on the destination files written are controlled by the *permCopy* directives.
*permCopy* will apply the mode permissions posted by the source of the file.
If no source mode is available, the *permdefault* will be applied to files, and the
*permLog* will be applied to directories. If no defaut is specified,
then the operating system  defauts (on linux, controlled by umask settings)
will determine file permissions. (Note that the *chmod* option is interpreted as a synonym
for *permdefault*, and *chmod_dir* is a synonym for *permDirdefault*).

When set in a posting component, permCopy has the effect of including or excluding
the *mode* header from the messages.

when set in a polling component, permdefault has the of setting minimum permissions for
a file to be accepted.
(on an ls output that looks like: ---r-----, like a chmod 040 <file> command).
The **permdefault** options specifies a mask, that is the permissions must be
at least what is specified.


post_baseDir <path> 
-------------------

The *post_baseDir* option supplies the directory path that, when combined (or found)
in the given *path*, gives the local absolute path to the data file to be posted.
The *post_baseDir* part of the path will be removed from the posted announcement.
For sftp urls it can be appropriate to specify a path relative to a user account.
Example of that usage would be: --post_baseDir ~user --url sftp:user@host
For file: url's, baseDir is usually not appropriate. To post an absolute path,
omit the --post_baseDir setting, and just specify the complete path as an argument.

post_baseUrl <url>
------------------

The **post_baseUrl** option sets how to get the file... it defines the protocol,
host, port, and optionelly, the user. It is best practice to not include
passwords in urls.

post_broker <url>
-----------------

the broker url to post messages to see `broker <#broker>`_ for details

post_exchange <name> (defaut: xpublic)
---------------------------------------

The **post_exchange** option set under which exchange the new notification
will be posted. when publishing to a pump as an administrator, a common
choice for post_exchange is 'xpublic'.

When publishing a product, a user can trigger a script, using
flow callback entry_points such as **after_accept**, and **after_work** 
to modify messages generated about files prior to posting.

post_exchangeSplit <count> (defaut: 0)
---------------------------------------

The **post_exchangeSplit** option appends a two digit suffix resulting from
hashing the last character of the checksum to the post_exchange name,
in order to divide the output amongst a number of exchanges.  This is currently used
in high traffic pumps to allow multiple instances of winnow, which cannot be
instanced in the normal way.  Example::

    post_exchangeSplit 5
    post_exchange xwinnow

will result in posting messages to five exchanges named: xwinnow00, xwinnow01,
xwinnow02, xwinnow03 and xwinnow04, where each exchange will receive only one fifth
of the total flow.

post_on_start
-------------

When starting watch, one can either have the program post all the files in the directories watched
or not.

post_topicPrefix (defaut: topicPrefix)
---------------------------------------

Prepended to the sub-topic to form a complete topic hierarchy. 
This option applies to publishing.  Denotes the version of messages published 
in the sub-topics. (v03 refers to `<sr3_post.7.html>`_) defauts to whatever
was received. 


prefetch <N> (defaut: 1)
-------------------------

The **prefetch** option sets the number of messages to fetch at one time.
When multiple instances are running and prefetch is 4, each instance will obtain up to four
messages at a time.  To minimize the number of messages lost if an instance dies and have
optimal load sharing, the prefetch should be set as low as possible.  However, over long
haul links, it is necessary to raise this number, to hide round-trip latency, so a setting
of 10 or more may be needed.

queueName|queue|queue_name|qn 
-----------------------------

* queueName <name>

By defaut, components create a queue name that should be unique. The
defaut queue_name components create follows the following convention:

   **q_<brokerUser>.<programName>.<configName>.<random>.<random>**

Where:

* *brokerUser* is the username used to connect to the broker (often: *anonymous* )

* *programName* is the component using the queue (e.g. *subscribe* ),

* *configName* is the configuration file used to tune component behaviour.

* *random* is just a series of characters chosen to avoid clashes from multiple
  people using the same configurations

Users can override the defaut provided that it starts with **q_<brokerUser>**.

When multiple instances are used, they will all use the same queue, for trivial
multi-tasking. If multiple computers have a shared home file system, then the
queue_name is written to:

 ~/.cache/sarra/<programName>/<configName>/<programName>_<configName>_<brokerUser>.qname

Instances started on any node with access to the same shared file will use the
same queue. Some may want use the *queue_name* option as a more explicit method
of sharing work across multiple nodes.

queueBind
---------

On startup, by defaut, Sarracenia redeclares resources and bindings to ensure they
are uptodate.  If the queue already exists, These flags can be
set to False, so no attempt to declare the queue is made, or it´s bindings.
These options are useful on brokers that do not permit users to declare their queues.


queueDeclare
------------

On startup, by defaut, Sarracenia redeclares resources and bindings to ensure they
are uptodate.  If the queue already exists, These flags can be
set to False, so no attempt to declare the queue is made, or it´s bindings.
These options are useful on brokers that do not permit users to declare their queues.

randomize <flag>
----------------

Active if *-r|--randomize* appears in the command line... or *randomize* is set
to True in the configuration file used. If there are several posts because the 
file is posted by block (the *blocksize* option was set), the block posts 
are randomized meaning that they will not be posted

realpath <flag>
---------------

The realpath option resolves paths given to their canonical ones, eliminating
any indirection via symlinks. The behaviour improves the ability of watch to
monitor trees, but the trees may have completely different paths than the arguments
given. This option also enforces traversing of symbolic links.

reconnect <flag>
----------------

Active if *-rc|--reconnect* appears in the command line... or
*reconnect* is set to True in the configuration file used.
*If there are several posts because the file is posted
by block because the *blocksize* option was set, there is a
reconnection to the broker everytime a post is to be sent.

rename <path>
-------------

With the *rename* option, the user can
suggest a destination path for its files. If the given
path ends with '/' it suggests a directory path...
If it doesn't, the option specifies a file renaming.


report and report_exchange
--------------------------

NOTE: **NOT IMPLEMENTEDin sr3, expected to return in future version**
For each download, by defaut, an amqp report message is sent back to the broker.
This is done with option :

- **report <flag>  (defaut: True)**
- **report_exchange <report_exchangename> (defaut: xreport|xs_*username* )**

When a report is generated, it is sent to the configured *report_exchange*. Administrative
components post directly to *xreport*, whereas user components post to their own
exchanges (xs_*username*). The report daemons then copy the messages to *xreport* after validation.

These reports are used for delivery tuning and for data sources to generate statistical information.
Set this option to **False**, to prevent generation of reports.


reset <flag> (defaut: False)
-----------------------------

When **reset** is set, and a component is (re)started, its queue is
deleted (if it already exists) and recreated according to the component's
queue options.  This is when a broker option is modified, as the broker will
refuse access to a queue declared with options that differ from what was
set at creation.  It can also be used to discard a queue quickly when a receiver
has been shut down for a long period. If duplicate suppression is active, then
the reception cache is also discarded.

The AMQP protocol defines other queue options which are not exposed
via sarracenia, because sarracenia itself picks appropriate values.


retryEmptyBeforeExit: <boolean> (defaut: False)
------------------------------------------------

Used for sr_insects flow tests. Prevents Sarracenia from exiting while there are messages remaining in the retry queue(s). By defaut, a post will cleanly exit once it has created and attempted to publish messages for all files in the specified directory. If any messages are not successfully published, they will be saved to disk to retry later. If a post is only run once, as in the flow tests, these messages will never be retried unless retryEmptyBeforeExit is set to True.


retry_ttl <duration> (defaut: same as expire)
----------------------------------------------

The **retry_ttl** (retry time to live) option indicates how long to keep trying to send
a file before it is aged out of a the queue.  defaut is two days.  If a file has not
been transferred after two days of attempts, it is discarded.

sanity_log_dead <interval> (defaut: 1.5*housekeeping)
------------------------------------------------------

The **sanity_log_dead** option sets how long to consider too long before restarting
a component.


shim_defer_posting_to_exit (EXPERIMENTAL)
-----------------------------------------

  (option specific to libsrshim)
  Postpones file posting until the process exits.
  In cases where the same file is repeatedly opened and appended to, this
  setting can avoid redundant posts.  (defaut: False)

shim_post_minterval *interval* (EXPERIMENTAL)
---------------------------------------------

  (option specific to libsrshim)
  If a file is opened for writing and closed multiple times within the interval,
  it will only be posted once. When a file is written to many times, particularly
  in a shell script, it makes for many posts, and shell script affects performance.
  subscribers will not be able to make copies quickly enough in any event, so
  there is little benefit, in say, 100 posts of the same file in the same second.
  It is wise set an upper limit on the frequency of posting a given file. (defaut: 5s)
  Note: if a file is still open, or has been closed after its previous post, then
  during process exit processing it will be posted again, even if the interval
  is not respected, in order to provide the most accurate final post.


shim_skip_parent_open_files (EXPERIMENTAL)
------------------------------------------

  (option specific to libsrshim)
  The shim_skip_ppid_open_files option means that a process checks
  whether the parent process has the same file open, and does not
  post if that is the case. (defaut: True)

sleep <time>
------------

The time to wait between generating events.  When files are written frequently, it is counter productive
to produce a post for every change, as it can produce a continuous stream of changes where the transfers
cannot be done quickly enough to keep up.  In such circumstances, one can group all changes made to a file
in *sleep* time, and produce a single post.

statehost <False|True> ( defaut: False )
-----------------------------------------

In large data centres, the home directory can be shared among thousands of
nodes. Statehost adds the node name after the cache directory to make it
unique to each node. So each node has it's own statefiles and logs.
example, on a node named goofy,  ~/.cache/sarra/log/ becomes ~/.cache/sarra/goofy/log.

strip <count|regexp> (defaut: 0)
---------------------------------

You can modify the relative mirrored directories with the **strip** option.
If set to N  (an integer) the first 'N' directories from the relative path
are removed. For example::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
when a regexp is provide in place of a number, it indicates a pattern to be removed
from the relative path.  For example if::

   strip  .*?GIF/

Will also result in the file being placed the same location.
Note that strip settings can be changed between directory options.

NOTE::
    with **strip**, use of **?** modifier (to prevent regular expression *greediness* ) is often helpful. 
    It ensures the shortest match is used.

    For example, given a file name:  radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.GIF
    The expression:  .*?GIF   matches: radar/PRECIP/GIF
    whereas the expression: .*GIF matches the entire name.

sourceFromExchange <flag> (defaut: off)
------------------------------------------

The **sourceFromExchange** option is mainly for use by administrators.
If messages received are posted directly from a source, the exchange used
is 'xs_<brokerSourceUsername>'. Such messages could be missing *source* and *from_cluster*
headings, or a malicious user may set the values incorrectly.
To protect against both problems, administrators should set the **sourceFromExchange** option.

When the option is set, values in the message for the *source* and *from_cluster* headers will then be overridden::

  self.msg.headers['source']       = <brokerUser>
  self.msg.headers['from_cluster'] = cluster

replacing any values present in the message. This setting should always be used when ingesting data from a
user exchange. These fields are used to return reports to the origin of injected data.
It is commonly combined with::

       *mirror true*
       *sourceFromExchange true*
       *directory ${PBD}/${YYYYMMDD}/${SOURCE}*

To have data arrive in the standard format tree.


subtopic <amqp pattern> (defaut: #)
------------------------------------

Within an exchange's postings, the subtopic setting narrows the product selection.
To give a correct value to the subtopic,
one has the choice of filtering using **subtopic** with only AMQP's limited wildcarding and
length limited to 255 encoded bytes, or the more powerful regular expression
based  **accept/reject**  mechanisms described below. The difference being that the
AMQP filtering is applied by the broker itself, saving the notices from being delivered
to the client at all. The  **accept/reject**  patterns apply to messages sent by the
broker to the subscriber. In other words,  **accept/reject**  are client side filters,
whereas **subtopic** is server side filtering.

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the
client side mechanisms, saving bandwidth and processing for all.

topicPrefix is primarily of interest during protocol version transitions,
where one wishes to specify a non-defaut protocol version of messages to
subscribe to.

Usually, the user specifies one exchange, and several subtopic options.
**Subtopic** is what is normally used to indicate messages of interest.
To use the subtopic to filter the products, match the subtopic string with
the relative path of the product.

For example, consuming from DD, to give a correct value to subtopic, one can
browse the our website  **http://dd.weather.gc.ca** and write down all directories
of interest.  For each directory tree of interest, write a  **subtopic**
option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#**

::

 where:  
       *                matches a single directory name 
       #                matches any remaining tree of directories.

note:
  When directories have these wild-cards, or spaces in their names, they
  will be URL-encoded ( '#' becomes %23 )
  When directories have periods in their name, this will change
  the topic hierarchy.

  FIXME:
      hash marks are URL substituted, but did not see code for other values.
      Review whether asterisks in directory names in topics should be URL-encoded.
      Review whether periods in directory names in topics should be URL-encoded.

One can use multiple bindings to multiple exchanges as follows::

  exchange A
  subtopic directory1.*.directory2.#

  exchange B
  subtopic *.directory4.#

Will declare two separate bindings to two different exchanges, and two different file trees.
While defaut binding is to bind to everything, some brokers might not permit
clients to set bindings, or one might want to use existing bindings.
One can turn off queue binding as follows::

  subtopic None

(False, or off will also work.)


timeCopy (defaut: on)
----------------------

On unix-like systems, when the *ls* commend or a file browser shows modification or
access times, it is a display of the posix *st_atime*, and *st_ctime* elements of a
struct struct returned by stat(2) call.  When *timeCopy* is on, headers
reflecting these values in the messages are used to restore the access and modification
times respectively on the subscriber system. To document delay in file reception,
this option can be turned off, and then file times on source and destination compared.

When set in a posting component, it has the effect of eliding the *atime* and *mtime*
headers from the messages.


timeout <interval> (defaut: 0)
-------------------------------

The **timeout** option, sets the number of seconds to wait before aborting a
connection or download transfer (applied per buffer during transfer).


tlsRigour (defaut: medium)
---------------------------

tlsRigour can be set to: *lax, medium, or strict*, and gives a hint to the
application of how to configure TLS connections. TLS, or Transport Level
Security (used to be called Secure Socket Layer (SSL)) is the wrapping of
normal TCP sockets in standard encryption. There are many aspects of TLS
negotiations, hostname checking, Certificate checking, validation, choice of
ciphers. What is considered secure evolves over time, so settings which, a few
years ago, were considered secure, are currently aggressively deprecated. This
situation naturally leads to difficulties in communication due to different
levels of compliance with whatever is currently defined as rigourous encryption.

If a site being connected to, has, for example, and expired certificate, and
it is nevertheless necessary to use it, then set tlsRigour to *lax* and
the connection should succeed regardless.


topicPrefix (defaut: v03)
--------------------------

prepended to the sub-topic to form a complete topic hierarchy. 
This option applies to subscription bindings.
Denotes the version of messages received in the sub-topics. (v03 refers to `<sr3_post.7.html>`_)

users <flag> (defaut: false)
-----------------------------

As an adjunct when the *declare* action is used, to ask sr3 to declare users
on the broker, as well as queues and exchanges.


vip - ACTIVE/PASSIVE OPTIONS
----------------------------

The **vip** option indicates that a configuration must be active on only 
a single node in a cluster at a time, a singleton. This is typically 
required for a poll component, but it can be used in senders or other
cases.

**subscribe** can be used on a single server node, or multiple nodes
could share responsibility. Some other, separately configured, high availability
software presents a **vip** (virtual ip) on the active server. Should
the server go down, the **vip** is moved on another server, and processing
then happens using the new server that now has the vip active.
Both servers would run an **sr3 instance**::

 - **vip          <string>          (None)**

When you run only one **sr3 instance** on one server, these options are not set,
and subscribe will run in 'standalone mode'.

In the case of clustered brokers, you would set the options for the
moving vip.

**vip 153.14.126.3**

When an **sr3 instance** does not find the vip, it sleeps for 5 seconds and retries.
If it does, it consumes and processes a message and than rechecks for the vip.

SEE ALSO
========

`sr3(1) <sr3.1.html>`_ - Sarracenia main command line interface.

`sr3_post(1) <sr3_post.1.html>`_ - post file announcements (python implementation.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - post file announcemensts (C implementation.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - C implementation of the shovel component. (copy messages)

**Formats:**

`sr3_post(7) <sr_post.7.html>`_ - the format of announcements.

**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: a real-time pub/sub data sharing management toolkit

