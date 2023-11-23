
===========
OPTIONS SR3
===========

--------------------------------------
Format de fichier de configuration SR3
--------------------------------------

:section de manuel: 7
:Date: |today|
:Version: |release|
:group de Manuel: MetPX-Sarracenia

SYNOPSIS
========

::

  nom valeur
  nom valeur d’utilisation
  nom valeur_${substitution}
  .
  .
  .     

DESCRIPTION
===========

Les options sont placées dans des fichiers de configuration, une par ligne, avec le format::

    option <valeur>

Par exemple::

    debug true
    debug

définit l’option *debug* pour activer une sortie d'éxécution plus détaillée. Si aucune valeur n’est spécifiée,
la valeur true est assigné, donc les valeurs ci-dessus sont équivalentes. Un deuxième exemple::

  broker amqps://anonymous@dd.weather.gc.ca

Dans l’exemple ci-dessus, *broker* est le mot-clé de l’option, et le reste de la ligne est la
valeur attribuée au paramètre. Les fichiers de configuration sont une séquence de paramètres,
avec un paramètre par ligne.
Remarque:

* les fichiers sont lus de haut en bas, surtout pour *directory*, *strip*, *mirror*,
  et les options *flatten* s’appliquent aux clauses *accept* qui se trouvent dans la suite du fichier.

* La barre oblique (/) est utilisée comme séparateur de chemin dans les fichiers de configuration Sarracenia sur tous les
  systèmes d’exploitation. L'utilisation de la barre oblique inverse comme séparateur (\) (tel qu’utilisé dans la
  cmd shell de Windows) risque de ne pas fonctionner correctement. Lorsque des fichiers sont lu dans Windows, le chemin d’accès
  est immédiatement converti en utilisant la barre oblique. Ceci est pour s'assurer que les options *reject*, *accept*, et
  *strip* peuvent filtrer des expressions correctement. C'est pour cela qu'il est toujours important d'utiliser la barre
  oblique (/) quand un séparateur est nécessaire.

* **#** est le préfixe des lignes de descriptions non fonctionnelles de configurations ou de commentaires.
  C'est identique aux scripts shell et/ou python

* **Toutes les options sont sensibles aux majuscules et minuscules.** **Debug** n’est pas la même chose que **debug** ni **DEBUG**.
  Ces trois options sont différentes (dont deux n’existent pas et n’auront aucun effet et créeront un avertissement
  d'« option inconnue »).

Le fichier a un ordre important. Il est lu de haut en bas, donc les options qui sont assignée sur une ligne on tendance
a affecter les lignes qui suivent::

   mirror off
   directory /data/just_flat_files_here_please
   accept .*flatones.*

   mirror on
   directory /data/fully_mirrored
   accept .*


Dans l’extrait ci-dessus, le paramètre *mirror* est désactivé, et la valeur de *directory* est définie. Les fichiers
dont le nom inclut *flatones* seront donc tous placés dans le répertoire */data/just_flat_files_here_please*.
Pour les fichiers qui n’ont pas ce nom, ils ne seront pas récupérés par le premier *accept*. Ensuite, avec le *mirror*
activé et le nouveau paramètre de *directory* défini, le restant des fichiers atterrira dans
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
interprété dans l’ordre. Dans ces cas, la dernière déclaration remplace celle qu'il y avait plus tôt dans le fichier..


Variables
=========

Il est possible de faire une substitution dans la valeur d'une option. Les valeurs sont représentées par ${name}.
Le nom peut être une variable d’environnement ordinaire, ou choisi parmi un certain nombre de variables déjà
intégrés:


::

        varTimeOffset -5m
        directory /monrépertoirelocal/${%Y%m%d_%Hh%m:%S.%f}/mydailies
        accept    .*observations.*

        rename lala_${%o-1h%Y%m%d%H%m%S.%f}

Il est possible les substitution de date et heure, avec des décalage, dans le premier cas avec varTimeOffset,
un décalage de 5 minutes dans le passé, dans le deuxième cas, c'est une heure dans le passé. 
Il est également possible de spécifier des substitutions de variables sur les arguments du paramètre du *directory*
en utilisant la notation *${..} * :

* %...     - un patron tel qu'accepté par `datetime.strftime() <https://docs.python.org/fr/3/library/datetime.html#datetime.date.strftime>`_ 

    * avec l'ajout du décalage au début avec o+- et une durée.
    * exemple:  ${%Y/%m/%d_%Hh%M:%S.%f} --> 2022/12/04_17h36:34.123479

* SOURCE   - l’utilisateur amqp qui a injecté des données (extraites du message d'annonce).
* BD       - le répertoire de base.
* BUP      - le composant du chemin de baseUrl (ou : baseUrlPath).
* BUPL     - le dernier élément du chemin du baseUrl. (ou: baseUrlPathLast).
* PBD      - le "post base dir".
* *var*    - n'importe quelle variable d’environnement.
* BROKER_USER - le nom d’utilisateur pour l’authentification auprès du courtier (par exemple, anonyme)
* POST_BROKER_USER - le nom d’utilisateur pour l’authentification auprès du courtier de destination (post_broker)
* PROGRAM     - le nom du composant (subscribe, shovel, etc...)
* CONFIG      - le nom du fichier de configuration en cours d'exécution.
* HOSTNAME    - le hostname qui exécute le client.
* RANDID      - Un ID aléatoire qui va être consistant pendant la duration d'une seule invocation.


Les horodatages %Y%m%d et %H font référence à l’heure à laquelle les données sont traitées par
le composant, ceci n’est pas décodé ou dérivé du contenu des fichiers livrés.
Toutes les dates/heures de Sarracenia sont en UTC. Le paramètre varTimeOffset peut spécifier
une déviation par rapport à l'heure actuelle.

note::

   Lorsque les substitutions de date ${% sont présentes, l'interprétation des modèles % dans les noms de fichiers
   par strftime, peut signifier qu'il faut leur échapper les caractères précédents via le doublage : %%

Référez  à *sourceFromExchange* pour un exemple d’utilisation. Notez que toute valeur déjà intégrée
dans Sarracenia a priorité par rapport à une variable du même nom dans l’environnement.
Notez que les paramètres de *flatten* peuvent être modifiés entre les options de *directory*.


Substitutions Compatible Sundew
-------------------------------

Dans `MetPX Sundew <../Explication/Glossary.html#sundew>`_, le format de la nomination de fichier est beaucoup plus
stricte, et est spécialisée pour une utilisation aves les données du World Meteorological Organization (WMO).
Notez que la convention du format des fichiers est antérieure, et n’a aucun rapport avec la convention de
dénomination des fichiers de WMO actuellement approuvée, et est utilisé strictement comme format interne. Les fichiers sont
séparés en six champs avec deux points. Le premier champ, DESTFN, est le "Abbreviated Header Line (AHL)" de WMO
(style 386) ou les blancs sont remplacé avec des traits de soulignement ::

   TTAAii CCCC YYGGGg BBB ...

(voir le manuel de WMO pour plus de détails) suivis de chiffres pour rendre le produit unique (cela est vrai en
théorie, mais pas en pratique vu qu'il existe un grand nombre de produits qui ont les mêmes identifiants).
La signification du cinquième champ est une priorité, et le dernier champ est un horodatage.
La signification des autres champs varie en fonction du contexte. Exemple de nom de fichier ::

   SACN43_CWAO_012000_AAA_41613:ncp1:CWAO:SA:3.A.I.E:3:20050201200339

Si un fichier est envoyé à Sarracenia et qu’il est nommé selon les conventions de Sundew,
les champs de substitution suivants seront disponibles::

  ${T1}    remplacer par le bulletin T1
  ${T2}    remplacer par le bulletin T2
  ${A1}    remplacer par le bulletin A1
  ${A2}    remplacer par le bulletin A2
  ${ii}    remplacer par le bulletin ii
  ${CCCC}  remplacer par le bulletin CCCC
  ${YY}    remplacer par le bulletin YY   (obs. jour)
  ${GG}    remplacer par le bulletin GG   (obs. heure)
  ${Gg}    remplacer par le bulletin Gg   (obs. minute)
  ${BBB}   remplacer par le bulletin bbb
  ${RYYYY} remplacer par l'année de réception
  ${RMM}   remplacer par le mois de réception
  ${RDD}   remplacer par le jour de réception
  ${RHH}   remplacer par l'heure de réception
  ${RMN}   remplacer par la minute de réception
  ${RSS}   remplacer par la seconde de réception
  ${YYYY}         année actuelle (utilisé %Y est préféré)
  ${MM}           mois actuel (utilisé %M est préféré)
  ${JJJ}          julian actuelle (utilisé %j est préféré)
  ${YYYYMMDD}     date actuelle (utilisé %Y%M%D est préféré)


Les champs 'R' proviennent du sixième champ, et les autres viennent du premier champ.
Lorsque des données sont injectées dans Sarracenia à partir de Sundew, l’en-tête du message d'annonce *sundew_extension*
fournira la source de ces substitions même si ces champs ont été supprimés des fichiers livrés.

note::
   les versions périmés de spécification temporelles éventuellement vont cessé d´être interprétés
   ands une version ultérieur.

SR_DEV_APPNAME
~~~~~~~~~~~~~~

La variable d’environnement SR_DEV_APPNAME peut être définie pour que la configuration de l’application et les répertoires
d’état soient créés sous un nom différent. Ceci est utilisé dans le développement pour pouvoir avoir de nombreuses configurations
actives à la fois. Cela permet de faire plus de tests au lieu de toujours travailler avec la configuration *réelle* du développeur.

Exemple : export SR_DEV_APPNAME=sr-hoho... lorsque vous démarrez un composant sur un système Linux, il
va rechercher les fichiers de configuration dans ~/.config/sr-hoho/ et va placer les fichiers d’état dans le
répertoire ~/.cache/sr-hoho.


TYPES D'OPTIONS
===============

Les options de sr3 ont plusieurs types :

count
    type de nombre entier.

duration
    un nombre à virgule flottante qui indique une quantité en secondes (0.001 est 1 milliseconde)
    modifié par un suffixe unitaire ( m-minute, h-heure, w-semaine ).

flag
    une option qui a la valeur soit Vrai (True ou on) ou Faux (False ou off) (une valeur booléenne).

float
    un nombre à virgule flottante, (séparateur de décimale étant un point.)

list
    une liste de chaîne de caractères, chaque occurrence successive se rajoute au total.
    Tous les options plugins de v2 sont déclarée du type list.

set
    un assortissement de chaîne de caractères, chaque occurrence successive s'unionise au total.

size
    taille entière. Suffixes k, m et g pour les multiplicateurs kilo, méga et giga (base 2).

str
    une chaîne de caractères.


OPTIONS
=======

Les options actuelles sont énumérées ci-dessous. Notez qu’elles sont sensibles aux majuscules, et
seulement un extrait est disponible sur la ligne de commande. Celles qui sont disponibles
sur la ligne de commande ont le même effet que lorsqu’elles sont spécifiés dans un fichier de configuration.

Les options disponibles dans les fichiers de configuration :

accelTreshold <size> défaut: 0 (désactiver.)
---------------------------------------------------

L'option accelThreshold indique la taille minimale d'un fichier transféré pour
qu'un téléchargeur binaire puisse être lancé.

accelXxxCommand
----------------
On peut spécifier d’autres fichiers binaires pour les téléchargeurs pour des cas particuliers,

+-----------------------------------+--------------------------------+
|  Option                           |  Valeur par Défaut             |
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


- **accept     <modèle regexp> (optionnel) [<mot-clés>]**
- **reject     <modèle regexp> (optionnel)**
- **acceptUnmatched   <booléen> (défaut: True)**

Les options **accept** et **reject** traitent les expressions régulières (regexp).
Le regexp est appliqué à l’URL du message d'annonce pour trouver une correspondance.

Si l’URL d’un fichier correspond à un modèle **reject**, le message d'annonce
est reconnu comme consommé par le courtier et est ignoré.

Celui qui correspond à un modèle **accept** est traité par le composant.

Dans de nombreuses configurations, les options **accept** et **reject** sont mélangé
avec l’option **directory**.  Ces options associent les messages d'annonce acceptés
à la valeur du **directory** sous laquelle elles sont spécifiées.

Une fois que toutes les options **accept** / **reject** sont traitées, normalement
le message d'annonce est accepté. Pour changer ce comportement,
il est possible de définir **acceptUnmatched** à False. Les paramètres de **accept/reject**
sont interprétés dans l’ordre. Chaque option est traitée de manière ordonnée
de haut en bas. Par exemple:

séquence #1::

  reject .*\.gif
  accept .*

séquence #2::

  accept .*
  reject .*\.gif


Dans la séquence #1, tous les fichiers se terminant par 'gif' sont rejetés.  Dans la séquence #2,
le accept .* (qui accepte tout) est lu avant la déclaration de reject, de sorte que le reject n’a aucun effet.

Il est recommandé d’utiliser le filtrage côté serveur pour réduire le nombre d’annonces envoyées au composant,
et a la place, envoyer un sur ensemble de ce qui est pertinent, et de seulement régler les mécanismes côté client,
économisant du bandwidth et du traitement pour tous. Plus de détails sur les directives:

Les options **accept** et **reject** utilisent des expressions régulières (regexp) pour trouver
une correspondance avec l’URL.
Ces options sont traitées séquentiellement.
L’URL d’un fichier qui correspond à un modèle **reject** n’est pas publiée.
Les fichiers correspondant à un modèle **accept** sont publiés.
Encore une fois, un *rename* peut être ajouté à l’option *accept*... les produits qui correspondent
a l'option *accept* seront renommé comme décrit... à moins que le *accept* corresponde à
un fichier, l’option *rename* doit décrire un répertoire dans lequel les fichiers
seront placé (en préfix au lieu de remplacer le nom du fichier).

L’option **permDefault** permet aux utilisateurs de spécifier un masque d'autorisation octal numérique
de style Linux::

  permDefault 040


signifie qu’un fichier ne sera pas publié à moins que le groupe ait l’autorisation de lecture
(sur une sortie ls qui ressemble à : ---r-----, comme une commande chmod 040 <fichier> ).
Les options **permDefault** spécifient un masque, c’est-à-dire que les autorisations doivent être
au moins ce qui est spécifié.

Le **regexp pattern** peut être utilisé pour définir des parties du répertoire si une partie du message d'annonce est placée
entre parenthèses. **sender** peut utiliser ces parties pour générer le nom du répertoire.
Les chaînes de parenthèses entre les guillemets rst remplaceront le mot-clé **${0}** dans le nom du répertoire...
le second **{1} $ ** etc.

Exemple d’utilisation ::

      filename NONE

      directory /ce/premier/répertoire/ciblé

      accept .*fichier.*type1.*

      directory /ce/répertoire/ciblé

      accept .*fichier.*type2.*

      accept .*fichier.*type3.*  DESTFN=fichier_de_type3

      directory /ce/${0}/modèle/${1}/répertoire

      accept .*(2016....).*(RAW.*GRIB).*


Un message d'annonce sélectionné par le premier *accept* sera remis inaltérée dans le premier répertoire.

Un message d'annonce sélectionné par le deuxième *accept* sera remis inaltérée dans deuxième répertoire.

Un message d'annonce sélectionné par le troisième *accept sera renommé « fichier_de_type3 » dans le deuxième répertoire.

Un message d'annonce sélectionné par le quatrième *accept* sera remis inaltérée à un répertoire.

Ça sera appelé  */ce/20160123/modèle/RAW_MERGER_GRIB/répertoire* si la notice du message d'annonce ressemble à cela:

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**


acceptSizeWrong: <booléen> (défaut: False)
-------------------------------------------

Lorsqu’un fichier est téléchargé et que sa taille ne correspond pas à celle annoncée, il est
normalement rejeté, comme un échec. Cette option accepte le fichier même avec la mauvaise
taille. Cela est utile lorsque le fichier change fréquemment, et qu’il passe en fil d’attente, donc
le fichier est modifié au moment de sa récupération.

attempts <count> (défaut: 3)
-----------------------------

L’option **attempts** indique combien de fois il faut tenter le téléchargement des données avant d’abandonner.
Le défaut de 3 tentatives est approprié dans la plupart des cas.  Lorsque l’option **retry** a la valeur false,
le fichier est immédiatement supprimé.

Lorsque l’option **attempts** est utilisé, un échec de téléchargement après le numéro prescrit
des **attempts** (ou d’envoi, pour un sender) va entrainer l’ajout du message d'annonce à un fichier de fil d’attente
pour une nouvelle tentative plus tard.  Lorsque aucun message d'annonce n’est prêt à être consommé dans la fil d’attente AMQP,
les requêtes se feront avec la fil d’attente de "retry".

baseDir <chemin> (défaut: /)
----------------------------

**baseDir** fournit le chemin d’accès au répertoire, et lorsqu’il est combiné avec le chemin d'accès relatif
de la notification sélectionnée, **baseDir** donne le chemin absolu du fichier à envoyer.
Le défaut est None, ce qui signifie que le chemin dans la notification est le chemin absolu.

Parfois, les senders s’abonnent à xpublic local, qui sont des URL http, mais le sender
a besoin d’un fichier local, alors le chemin d’accès local est construit en concaténant::

   baseDir + chemin d'accès relatif dans le baseUrl + relPath


baseUrl_relPath <flag> (défaut: off)
-------------------------------------

Normalement, le chemin d’accès relatif (baseUrl_relPath est False, ajouté au répertoire de base) pour
les fichiers téléchargés seront définis en fonction de l’en-tête relPath inclus
dans le message d'annonce. Toutefois, si *baseUrl_relPath* est défini, le relPath du message d'annonce va
être précédé des sous-répertoires du champ baseUrl du message d'annonce.


batch <count> (défaut: 100)
----------------------------

L’option **batch** est utilisée pour indiquer le nombre de fichiers à transférer
sur une connexion, avant qu’elle ne soit démolie et rétablie.  Sur de très bas volume de
transferts, où des délais d’attente peuvent se produire entre les transferts, cela devrait être
ajuster à 1.  Pour la plupart des situations, le défaut est bien. Pour un volume plus élevé,
on pourrait l’augmenter pour réduire les frais généraux de transfert. Cette option est seulement utilisé pour les
protocoles de transfert de fichiers, et non HTTP pour le moment.

blocksize <size> défaut: 0 (auto)
-----------------------------------

REMARQUE: **NON IMPLEMENTÉ pour sr3, devrait revenir dans la version future**
Cette option **blocksize** contrôle la stratégie de partitionnement utilisée pour publier des fichiers.
La valeur doit être l’une des suivantes ::

   0 - calcul automatiquement une stratégie de partitionnement appropriée (défaut).
   1 - envoyez toujours des fichiers entiers en une seule partie.
   <blocksize> - utiliser une taille de partition fixe (taille d’exemple : 1M ).

Les fichiers peuvent être annoncés en plusieurs parties.  Chaque partie à un somme de contrôle (checksum) distinct.
Les parties et leurs somme de contrôle sont stockées dans la cache. Les partitions peuvent traverser
le réseau séparément et en parallèle. Lorsque les fichiers changent, les transferts sont
optimisé en n’envoyant que les pièces qui ont changé.

L’option *outlet* permet à la sortie finale d’être autre qu’un poste.
Voir `sr3_cpump(1) <sr3_cpump.1.html>`_ pour plus de détails.

Broker
------

**broker [amqp|mqtt]{s}://<utilisateur>:<mot-de-passe>@<hoteDuCourtier>[:port]/<vhost>**

Un URI est utilisé pour configurer une connexion à une pompe de messages d'annonce, soit
un courtier MQTT ou AMQP. Certains composants de Sarracenia fixent un défaut raisonnable pour
cette option. Il faut fournir l’utilisateur normal, l’hôte, et le port de connexion.
Dans la plupart des fichiers de configurations,
le mot de passe est manquant. Le mot de passe est normalement inclus seulement dans le fichier
`credentials.conf <sr3_credentials.7.html>`_.

Le travail de Sarracenia n’a pas utilisé de vhosts, donc **vhost** devrait presque toujours être **/**.

pour plus d’informations sur le format URI AMQP: ( https://www.rabbitmq.com/uri-spec.html )

soit dans le fichier default.conf, soit dans chaque fichier de configuration spécifique.
L’option broker indique à chaque composant quel courtier contacter.

**broker [amqp|mqtt]{s}://<utilisateur>:<mot-de-passe>@<hoteDuCourtier>[:port]/<vhost>**

::
      (défaut: None et il est obligatoire de le définir )

Une fois connecté à un courtier AMQP, l’utilisateur doit lier une fil d’attente
aux échanges et aux thèmes pour déterminer le messages d'annonce en question.


byteRateMax <size> (défaut: 0)
------------------------------

**byteRateMax** est supérieur à 0, le processus tente de respecter cette vitesse de livraison
 en kilo-octets par seconde... ftp,ftps,ou sftp)

**FIXME**: byteRateMax... uniquement implémenté par le sender ? ou subscriber aussi, données uniquement, ou messages d'annonce aussi ?

callback <SpéficationDeClass>
-----------------------------

La plupart des traitements personnalisables ou de la logique "plugin" sont implémentés à l'aide de la classe de flowCallback ("rappel de flux.") À différents stades du traitement des messages de notification, les classes de flowCallback définissent
points d'entrée qui correspondent à ce point de traitement. pour chaque point de ce type dans le traitement,
il existe une liste de routines de rappel de flux à appeler.

 `flowCallback Reference (anglais) <../../Reference/flowcb.html>`_

Le *SpécificationDeClass* est similaire à une instruction *import* de python. 
Il utilise le chemin de recherche standard pour les modules python, et inclut également ~/.config/sr3/plugins. 
Il y a un raccourci pour faire usage plus court pour les cas courants. par exemple::

  callback log

Sarracenia tentera d'abord de faire précéder *log* de *sarracenia.flowcb.log* puis
instancier l'instance de rappel en tant qu'élément de la classe sarracenia.flowcb.log.Log. 
S'il ne trouve pas une telle classe, alors il tentera de trouver un nom de classe *log*, et instanciera un
objet *log.Log.*

Pour plus de détails sur ce genre de recherche, consulter (en anglais) 
`FlowCallback load_library <../../Reference/flowcb.html#sarracenia.flowcb.load_library>`_

callback_prepend <SpécificationDeClass>
---------------------------------------

Identique à *callback* mais rajoute la class au début de la liste (pour éxecuter avant les point
d´entrée des autres classes FlowCB)


dangerWillRobinson (default: omis)
-------------------------------------

Cette option n'est reconnue qu'en tant qu'option de ligne de commande. Il est spécifié quand une opération 
aura des effets irréversiblement destructeurs ou peut-être inattendus. par exemple::

   sr3 stop

arrêtera d'exécuter les composants, mais pas ceux qui sont exécutés au premier plan. Arrêter ceux
peut surprendre les analystes qui les examineront, donc ce n'est pas fait par défaut ::

  sr3 --dangerWillRobinson stop

arrête arrête tous les composants, y compris ceux de premier plan. Un autre exemple serait le *nettoyage*
action. Cette option supprime les files d'attente et les échanges liés à une configuration, qui peuvent être
destructeur pour les flux. Par défaut, le nettoyage ne fonctionne que sur une seule configuration à la fois.
On peut spécifier cette option pour faire plus de ravages.


declare
-------

env NAME=Value
  On peut également référer à des variables d’environnement dans des fichiers de configuration,
  en utilisant la syntaxe *${ENV}*.  Si une routine de Sarracenia doit utiliser
  une variable d’environnement, elles peuvent être définis dans un fichier de configuration ::

    declare env HTTP_PROXY=localhost

exchange exchange_name
  à l’aide de l’URL d’administration, déclarez l’échange avec *exchange_name*

subscriber
  Un abonné (subsciber) est un utilisateur qui peut seulement s’abonner aux données et renvoyer des messages de rapport.
  Les abonnés n'ont pas le droit d’injecter des données. Chaque abonné dispose d’un xs_<utilisateur> qui
  s'appelle "exchange" sur la pompe. Si un utilisateur est nommé *Acme*, l’échange correspondant sera *xs_Acme*.
  Cet échange est l’endroit où un processus d’abonnement enverra ses messages de rapport.

  Par convention/défaut, l’utilisateur *anonyme* est créé sur toutes les pompes pour permettre l’abonnement sans abonnement
  a un compte spécifique.


source
  Un utilisateur autorisé à s’abonner ou à générer des données. Une source ne représente pas nécessairement
  une personne ou un type de données, mais plutôt une organisation responsable des données produites.
  Donc, si une organisation recueille et met à disposition dix types de données avec un seul contact,
  e-mail, ou numéro de téléphone, toute question sur les données et leur disponibilité par rapport aux
  activités de collecte peuvent alors utiliser un seul compte "source".

  Chaque source reçoit un échange xs_<utilisateur> pour l’injection de publications de données. Cela est comme un abonné
  pour envoyer des messages de rapport sur le traitement et la réception des données. La source peut également avoir
  un échange xl_<utilisateur> où, selon les configurations de routage des rapports, les messages de rapport des
  consommateurs seront envoyés.

feeder
  Un utilisateur autorisé à écrire à n’importe quel échange. Une sorte d’utilisateur de flux administratif, destiné à pomper
  des messages d'annonce lorsque aucune source ou abonné ordinaire n’est approprié pour le faire. Doit être utilisé de
  préférence au lieu de comptes d’administrateur pour exécuter des flux.

Les informations d’identification de l’utilisateur sont placées dans le `credentials.conf <sr3_credentials.7.html>`_
et *sr3 --users declare* mettra à jour le courtier pour accepter ce qui est spécifié dans ce fichier, tant que le
mot de passe de l'administrateur est déjà correct.

debug
-----

Définir l'option debug est identique a utilisé **logLevel debug**

delete <booléen> (défaut: off)
-------------------------------

Lorsque l’option **delete** est définie, une fois le téléchargement terminé avec succès, l’abonné
supprimera le fichier à la source. Par défaut, l'option est false.


discard <booléen> (défaut: off)
-------------------------------

L’option **discard**, si elle est définie a true, supprime le fichier une fois téléchargé. Cette option peut être
utile lors du débogage ou pour tester une configuration.


directory <chemin> (défaut: .)
------------------------------

L’option *directory* définit où placer les fichiers sur votre serveur.
Combiné avec les options **accept** / **reject**, l’utilisateur peut sélectionner
les fichiers d’intérêt et leurs répertoires de résidence (voir le **mirror**
pour plus de paramètres de répertoire).

Les options **accept** et **reject** utilisent des expressions régulières (regexp) pour trouver une correspondance avec l’URL.
Ces options sont traitées séquentiellement.
L’URL d’un fichier qui correspond à un modèle **reject** n’est jamais téléchargée.
Celui qui correspond à un modèle **accept** est téléchargé dans le répertoire
déclaré par l’option **directory** la plus proche au-dessus de l’option **accept** correspondante.
**acceptUnmatched** est utilisé pour décider quoi faire lorsque aucune clause de rejet ou d’acceptation corresponde.

::

  ex.   directory /monrépertoirelocal/mesradars
        accept    .*RADAR.*

        directory /monrépertoirelocal/mesgribs
        reject    .*Reg.*
        accept    .*GRIB.*


destfn_script <script> (défaut: None)
-------------------------------------

L'option de compatibilité Sundew définit un script à exécuter lorsque tout est prêt
pour la livraison du produit.  Le script reçoit une instance de la classe sender.
Le script prends le parent comme argument, et par exemple, une
modification de **parent.msg.new_file** changera le nom du fichier écrit localement.

download <flag> (défaut: True)
------------------------------

utilisé pour désactiver le téléchargement dans le composant subscribe et/ou sarra.
Se définit a False par défaut dans les composants de shovel ou de winnow.


dry_run <flag> (défaut: False)
------------------------------

Exécuter en mode simulation par rapport aux transferts de fichiers. Se connecte toujours à un courtier et télécharge et traite
les messages d´annonce, mais les transferts de fichiers corréspondants sont désactivés, à utiliser lors du test d'un expéditeur 
ou d'un téléchargeur, par exemple pour s'exécuter en parallèle avec un fichier existant, et comparez les journaux pour voir 
si l'expéditeur est configuré pour envoyer les mêmes fichiers que l'ancien (implémenté avec un autre système.)

durable <flag> (défaut: True)
-----------------------------

L’option AMQP **durable**, sur les déclarations de fil d’attente. Si la valeur est True,
le courtier conservera la fil d’attente lors des redémarrages du courtier.
Cela signifie que la fil d’attente est sur le disque si le courtier est redémarré.


fileEvents <évènement, évènement,...>
-------------------------------------

ensemble séparée par des virgules de d'événements de fichiers à surveiller.
Événements de fichiers disponibles : *create, delete, link, modify, mkdir, rmdir*
Si on commence la liste avec plus (+) ca signifie un rajout à l´ensemble actuel
Les événements *create*, *modify* et *delete* reflètent ce qui est attendu : un fichier en cours de création,
de modification ou de suppression.
Si *link* est défini, des liens symboliques seront publiés sous forme de liens afin que les consommateurs puissent choisir
comment les traiter. S’il n’est pas défini, aucun événement de lien symbolique sera publié.

.. note::
   déplacer ou renommer des événements entraîne un modèle spécial de double publication, avec une publication en
   utilisant l'ancien nom et définissant le champ *newname*, et un deuxième message d'annonce avec le nouveau nom, et un champ *oldname*.
   Cela permet aux abonnés d’effectuer un renommage réel et d’éviter de déclencher un téléchargement lorsque cela est possible.

FIXME : algorithme de renommage amélioré en v3 pour éviter l’utilisation de double post...


exchange <nom> (défaut: xpublic) et exchangeSuffix
--------------------------------------------------

La norme pour les pompes de données est d’utiliser l’échange *xpublic*. Les utilisateurs peuvent établir un
flux de données privées pour leur propre traitement. Les utilisateurs peuvent déclarer leurs propres échanges
qui commencent toujours par *xs_<nom-d'utilisatueur>*. Pour éviter d’avoir à le spécifier à chaque
fois, on peut simplement régler *exchangeSuffix kk* qui entraînera l’échange
à être défini a *xs_<nom-d'utilisatueur>_kk* (en remplaçant le défaut *xpublic*).
Ces paramètres doivent apparaître dans le fichier de configuration avant les paramètres *topicPrefix* et *subtopic*.


exchangeDeclare <flag>
----------------------

Au démarrage, par défaut, Sarracenia redéclare les ressources et les liaisons pour s’assurer qu’elles
sont à jour. Si l’échange existe déjà, cet indicateur peut être défini a False,
donc aucune tentative d’échange de la fil d’attente n’est faite, ou il s’agit de liaisons.
Ces options sont utiles sur les courtiers qui ne permettent pas aux utilisateurs de déclarer leurs échanges.


expire <duration> (défaut: 5m  == cinq minutes. RECOMMENDE DE REMPLACER)
------------------------------------------------------------------------
L'option *expire* est exprimée sous forme d'une duration... ça fixe combien de temps une fil d’attente devrait
vivre sans connexions.

Un entier brut est exprimé en secondes, et si un des suffixe m,h,d,w est utilisés, l’intervalle est en minutes,
heures, jours ou semaines respectivement. Après l’expiration de la fil d’attente, le contenu est supprimé et
des différences peuvent donc survenir dans le flux de données de téléchargement.  Une valeur de
1d (jour) ou 1w (semaine) peut être approprié pour éviter la perte de données. Cela dépend de combien de temps
l’abonné est sensé s’arrêter et ne pas subir de perte de données.

Si aucune unité n’est donnée, un nombre décimal de secondes peut être fourni, tel que
0,02 pour spécifier une durée de 20 millisecondes.

Le paramètre **expire** doit être remplacé pour une utilisation opérationnelle.
Le défaut est défini par une valeur basse car il définit combien de temps les ressources vont être
assigné au courtier, et dans les premières utilisations (lorsque le défaut était de de 1 semaine), les courtiers
étaient souvent surchargés de très longues files d’attente pour les tests restants.


filename <mots-clé> (défaut:None)
-----------------------------------

De **MetPX Sundew**, le support de cette option donne toutes sortes de possibilités
pour définir le nom de fichier distant. Certains **keywords** sont basés sur le fait que
les noms de fichiers **MetPX Sundew** ont cinq (à six) champs de chaîne de caractères séparés par des deux-points.

La valeur par défaut sur Sundew est NONESENDER, mais dans l’intérêt de décourager l’utilisation
de la séparation par des deux-points dans les fichiers, le défaut dans Sarracenia est WHATFN.

Les mots-clés possibles sont :

**None**
 - Aucune modification du nom de fichier (enlever toute interprétation de style Sundew)
   N.B. différent de NONE décrit plus loin.

**WHATFN**
 - la première partie du nom de fichier Sundew (chaîne de caractères avant le premier : )

**HEADFN**
 - Partie EN-TETE du nom de fichier Sundew

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



flatten <string> (défaut: '/')
-------------------------------

L’option **flatten** permet de définir un caractère de séparation. La valeur par défaut ( '/' )
annule l’effet de cette option. Ce caractère remplace le '/' dans l’url
et crée un nom de fichier « flatten » à partir de son chemin d’accès dd.weather.gc.ca.
Par exemple, récupérer l’URL suivante, avec les options ::


 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /monrépertoirelocal
   accept    .*model_gem_global.*

entraînerait la création du chemin d’accès au fichier::

 /monrépertoirelocal/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2


flowMain (défaut: None)
-----------------------

Par défaut, un flux exécutera la classe sarracenia.flow.Flow, qui implémente l'algorithme Flow de manière générique.
La version générique ne transfère pas de données, crée et manipule uniquement des messages. Cela convient pour
pelle, vanner, poster et surveiller les composants, mais les composants qui transfèrent ou transforment les données ont besoin
pour définir un comportement supplémentaire en sous-classant Flow. Exemples : sarracenia.flow.sender, sarracenia.flow.poll, sarracenia.flow.subscribe.

L'option **flowMain** permet à une configuration de flux d'exécuter une sous-classe de flux, au lieu du parent par défaut
classer. Exemple::

   flowMain subscribe

Dans un fichier de configuration de flux générique, le flux sera configuré pour agir en tant que composant d'abonné (subscribe.)
On peut créer des composants personnalisés en sous-classant Flow et en utilisant la directive **flowMain** pour invoquer
la nouvelle sous-classe.

follow_symlinks <flag>
----------------------

L’option *follow_symlinks* entraîne la traversée de liens symboliques. Si *follow_symlinks* est défini
et la destination d’un lien symbolique est un fichier, alors ce fichier de destination doit être publié ainsi que le lien.
Si la destination du lien symbolique est un répertoire, le répertoire doit être ajouté à ceux qui sont
surveillé par « watch ». Si *follow_symlinks* est false, alors aucune action liée à la destination du
lien symbolique est prise.

force_polling <flag> (défaut: False)
------------------------------------

Par défaut, « watch » sélectionne une méthode optimale (dépendante du système d’exploitation) pour regarder un
répertoire.

Pour les grandes arborescences, la méthode optimale peut être plusieurs fois (10x ou même
100x) plus rapide à reconnaître lorsqu’un fichier a été modifié. Dans certains cas, 
les méthodes optimales de plateforme ne fonctionnent pas (comme avec certains réseaux,
partages, ou systèmes de fichiers distribués), il faut donc utiliser un système plus lent mais avec une méthode
de « polling » plus fiable et portable.  Le mot-clé *force_polling* oblige « watch » a sélectionner
la méthode de « polling » malgré le fait qu'il y ait une meilleur option de disponible.

Pour une discussion détaillée, voir:
 `Detecting File Changes <../Explication/DetectFileHasChanged.html>`_

REMARQUE::

  Lorsque les répertoires sont consommés par des processus en utilisant l’option *delete* de l’abonné, ils restent vides, et
  chaque fichier doit être signalé à chaque passage.  Lorsque les abonnés n’utilisent pas *delete*, « watch » doit
  savoir quels fichiers sont nouveaux.  Il le fait en notant l’heure du début de la dernière passe du « polling ».
  Les fichiers sont publiés si leur heure de modification est plus récente que cela. Cela se traduira par de
  nombreux postes de « watch », qui peuvent être minimisés avec l’utilisation de la cache. On pourrait même dépendre
  de la cache entièrement et activez l’option *delete*, ou « watch » pourra tenter de publier l’arborescence entière
  à chaque fois (en ignorant mtime).

  **LIMITATION CONNUE** : Lorsque *force_polling* est défini, le paramètre *sleep* doit être
  au moins 5 secondes. À l’heure actuelle, on ne sait pas pourquoi.

header <nom>=<valeur>
---------------------

Ajoutez un en-tête <nom> avec la valeur donnée aux publicités. Utilisé pour transmettre des chaîne de caractères en tant
que métadonnées dans les publicités pour améliorer la prise de décision des consommateurs. Doit être utilisé
avec parcimonie. Il y a des limites sur le nombre d’en-têtes pouvant être utilisés, et la réduction de la
taille des messages d'annonce a des impacts importants sur la performance.

housekeeping <intervalle> (défaut: 300 secondes)
------------------------------------------------

L’option **housekeeping** définit la fréquence d’exécution du traitement périodique tel que déterminé par
la liste des plugins on_housekeeping. Par défaut, il imprime un message de journal à chaque intervalle de housekeeping.

include config
--------------

inclure une autre configuration dans cette configuration.


inflight <string> (défaut: .tmp ou NONE si post_broker est définit)
-------------------------------------------------------------------

L’option **inflight** définit comment ignorer les fichiers lorsqu’ils sont transférés
ou (en plein vol entre deux systèmes). Un réglage incorrect de cette option provoque des
transferts peu fiables, et des précautions doivent être prises.  Voir
`Delivery Completion <../Explication/FileCompletion.html>`_ pour plus de détails.

La valeur peut être un suffixe de nom de fichier, qui est ajouté pour créer un nom temporaire pendant
le transfert.  Si **inflight** est défini a **.**, alors il s’agit d’un préfixe pour se conformer à
la norme des fichiers « cachés » sur unix/linux.
Si **inflight** se termine par / (exemple : *tmp/* ), alors il s’agit d’un préfixe, et spécifie un
sous-répertoire de la destination dans lequel le fichier doit être écrit pendant qu'il est en vol.

Si un préfixe ou un suffixe est spécifié, lorsque le transfert est
terminé, le fichier est renommé à son nom permanent pour permettre un traitement ultérieur.

Lors de la publication d’un fichier avec sr3_post, sr3_cpost, watch, ou poll, l’option **inflight**
peut également être spécifié comme une intervalle de temps, par exemple, 10 pour 10 secondes.
Lorsque l'option est défini sur une intervalle de temps, le processus de publication de fichiers attends
jusqu’à ce que le fichier n’ai pas été modifié pendant cet intervalle. Ainsi, un fichier
ne peux pas être traité tant qu’il n’est pas resté le même pendant au moins 10 secondes.

Enfin, **inflight** peut être réglé a *NONE*. Dans ce cas, le fichier est écrit directement
avec le nom final, où le destinataire attendra de recevoir un poste pour notifier l’arrivée du fichier.
Il s’agit de l’option la plus rapide et la moins coûteuse lorsqu’elle est disponible.
C’est aussi le défaut lorsqu’un *post_broker* est donné, indiquant qu'un autre processus doit être
notifié après la livraison.

NOTE::

     Lors de l'écriture d'un fichier, si vous voyez le message d'erreur ::

     paramètre en vol : 300, pas pour les téléchargements

     C'est parce que le réglage de l'intervalle de temps est uniquement pour la lecture des fichiers. Le processus
     qui écrit le fichier, ne peut pas contrôler combien de temps un processus lecteur ultérieur attendra pour 
     regarder un fichier en cours téléchargé, il est donc inapproprié de spécifier un temps de modification minimum.
     en regardant les fichiers locaux avant de générer un post, ça ne sert pas comme disons, un moyen
     de retarder l'envoi des fichiers.

inline <flag> (défaut: False)
-----------------------------

Lors de la publication de messages d'annonce, l’option **inline** est utilisée pour avoir le contenu du fichier
inclus dans le post. Cela peut être efficace lors de l’envoi de petits fichiers sur un niveau élevé de
liens de latence, un certain nombre d’allers-retours peuvent être enregistrés en évitant la récupération
des données utilisant l’URL. On ne devrait seulement utiliser *inline* pour des fichiers relativement petits.
Lorsque **inline** est actif, seuls les fichiers inférieurs à **inlineByteMax** octets
(défaut: 1024) auront réellement leur contenu inclus dans les messages d'annonce.
Si **inlineOnly** est défini et qu’un fichier est plus volumineux que inlineByteMax, le fichier
ne sera pas affiché.

inlineByteMax <taille>
----------------------

la taille maximale des fichiers dont le contenu est à inclure dans un messages d'annonce (envoyé inline.)

inlineOnly
----------
ignorer les messages d´annonce si les données ne sont pas inline.

inplace <flag> (défaut: On)
---------------------------

Les fichiers volumineux peuvent être envoyés en plusieurs parties, plutôt que de tout en même temps.
Lors du téléchargement, si **inplace** est True, ces parties seront rajoutées au fichier
de manière ordonnée. Chaque partie, après avoir été insérée dans le fichier, est annoncée aux abonnés.
Cela peut être défini a False pour certains déploiements de Sarracenia où une pompe
ne voie que quelques parties, et non l’intégralité de fichiers en plusieurs parties.

L’option **inplace** est True par défaut.
Dépendamment de **inplace** et si le message d´annonce était une partie, le chemin peut
encore changer (en ajoutant un suffixe de pièce si nécessaire).

Instances
---------

Parfois, une instance d’un composant et d’une configuration ne suffit pas pour traiter et envoyer toutes
les notifications disponibles.

**instances <entier> (défaut:1)**

L’option d’instance permet de lancer plusieurs instances d’un composant et d’une configuration.
Lors de l’exécution d'un sender par exemple, un nombre de fichiers d’exécution sont créés dans
le répertoire ~/.cache/sarra/sender/nomDeConfig ::

  A .sender_nomDeConfig.state         est créé, contenant le nombre d’instances.
  A .sender_nomDeConfig_$instance.pid est créé, contenant le PID du processus $instance .

Dans le répertoire ~/.cache/sarra/log:

  Un .sender_nomDeConfig_$instance.log  est créé en tant que journal du processus $instance.

.. NOTE::

  Alors que les courtiers gardent les files d’attente disponibles pendant un certain temps, les files d’attente
  prennent des ressources sur les courtiers, et sont nettoyés de temps en temps. Une fil d’attente qu'on
  n’accède pas et a trop de fichiers (définis par l’implémentation) en fil d’attente seront détruits.
  Les processus qui meurent doivent être redémarrés dans un délai raisonnable pour éviter la
  perte de notifications. Une fil d’attente qu'on n’accède pas pendant une longue période
  (dépendant de l’implémentation) sera détruite.

identity <string>
------------------

Tous les postes de fichiers incluent une somme de contrôle. Elle est placée dans l’en-tête du message amqp
et aura comme entrée *sum* avec la valeur de défaut 'd,md5_checksum_on_data'.
L’option *sum* indique au programme comment calculer la somme de contrôle.
Dans la v3, elles sont appelées Identity methods (méthodes d’intégrité) ::

         cod,x      - Calculer On Download en appliquant x
         sha512     - faire SHA512 sur le contenu du fichier (défaut)
         md5        - faire md5sum sur le contenu du fichier
         md5name    - faire la somme de contrôle md5sum sur le nom du fichier
         random     - inventer une valeur aléatoire pour chaque poste.
         arbitrary  - appliquer la valeur fixe littérale.

Les options v2 sont une chaîne de caractères séparée par des virgules.  Les indicateurs de somme de contrôle valides sont :

* 0 : aucune somme de contrôle... la valeur dans le poste est un entier aléatoire (uniquement pour tester/débugger).
* d : faire md5sum sur le contenu du fichier
* n : faire la somme de contrôle md5sum sur le nom du fichier
* p : faire la somme de contrôle SHA512 sur le nom du fichier et sur partstr [#]_
* s : faire SHA512 sur le contenu du fichier (défaut)
* z,a : calculer la valeur de la somme de contrôle en utilisant l'algorithme a et l'assigner après le téléchargement.

.. [#] seulement implémenter en C. ( voir https://github.com/MetPX/sarracenia/issues/117 )


logEvents ( défaut: after_accept,after_work,on_housekeeping )
-------------------------------------------------------------

l´ensemble des moments durant le traitement des message de notification ou on veut émettre des 
messages de journal. Autres valeurs : on_start, on_stop, post, gather, ... etc...
On peut débuter la valeur avec un plus (+) pour signifier un ajout au valeurs actuels.
la valeur moins (-) signifie la soustraction des valeurs de l´ensemble actuel. 

logLevel ( défaut: info )
-------------------------
Niveau de journalisation exprimé par la journalisation de python. Les valeurs possibles sont :
critical, error, info, warning, debug.

logMetrics ( default: False )
-----------------------------

écrire des métriques dans un fichier de quotidien pour la collecte de statistiques. 
le fichier sera dans le même répertoire que les logs, et aura une suffix avec la date.

logReject ( défaut: False )
---------------------------

Normalement, le rejet des messages d´annonce se fait en silence. Lorsque logReject a la valeur True, un message
de journal est généré pour chaque message d´annonce rejeté et indiquant la raison du rejet.

logStdout ( défaut: False )
---------------------------

*logStdout* désactive la gestion des journaux. Il vaut mieux l’utiliser sur la ligne de commande, car il y a
certains risques de créer des fichiers stub avant que les configurations ne soient complètement analysées ::

       sr3 --logStdout start

Tous les processus lancés héritent leurs descripteurs de fichier du parent. Donc toutes les sorties sont
comme une session interactive.

Cela contraste avec le cas normal, où chaque instance prend soin de ses journaux, en tournant et en purgeant
périodiquement. Dans certains cas, on veut que d’autres logiciels s’occupent de la journalisation, comme dans docker,
où c’est préférable que toute la journalisation soit une sortie standard.

Ça n’a pas été mesuré, mais il est probable que l’utilisation de *logStdout* avec de grandes configurations
(des dizaines d'instances configurés/processus) entraînera soit une corruption des journaux, ou limitera
la vitesse d’exécution de tous les processus qui écrivent à stdout.

logRotateCount <max_logs> ( défaut: 5 )
---------------------------------------

Nombre maximal de journaux de messages (logs) et statistiques (metrics) archivés.

logRotateInterval <intervalle>[<unité_de_temps>] ( défaut: 1d )
---------------------------------------------------------------

La durée de l’intervalle avec une unité de temps optionnel (soit 5m, 2h, 3d)
entre chaque changement de fichier journal (de messages et statistiques)

messageCountMax <count> (défaut: 0)
-----------------------------------

Si **messageCountMax** est supérieur à zéro, le flux se ferme après avoir traité le nombre de messages d´annonce spécifié.
Ceci est normalement utilisé pour le débogage uniquement.

messageRateMax <float> (défaut: 0)
----------------------------------

Si **messageRateMax** est supérieur à zéro, le flux essaye de respecter cette vitesse de livraison en termes de
messages d´annonce par seconde. Notez que la limitation est sur les messages d´annonce obtenus ou générés par seconde, avant le
filtrage accept/reject. Le flux va dormir pour limiter le taux de traitement.


messageRateMin <float> (défaut: 0)
----------------------------------

Si **messageRateMin** est supérieur à zéro et que le flux détecté est inférieur à ce taux,
un message d´annonce sera produit :

message_ttl <duration>  (défaut: None)
--------------------------------------

L’option **message_ttl** définit un temps pour lequel un message d´annonce peut vivre dans la fil d’attente.
Après ce temps, le message d´annonce est retiré de la fil d’attente par le courtier.

mirror <flag> (défaut: off)
---------------------------

L’option **miroir** peut être utilisée pour mettre en miroir l’arborescence des fichiers de dd.weather.gc.ca.
Si l'option est défini a **True** le répertoire donné par l’option **directory** sera le nom de base
de l'arborescence. Les fichiers acceptés sous ce répertoire seront placé sous le sous-répertoire
de l'arborescence où il réside dans dd.weather.gc.ca.
Par exemple, récupérer l’URL suivante, avec des options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /monrépertoirelocal
   accept    .*RADAR.*

entraînerait la création des répertoires et du fichier
/monrépertoirelocal/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
Les paramètres de mirror peuvent être modifiés entre les options de répertoire.

no <count>
----------

Présent sur les instances démarrées par l’interface de gestion sr3.
L’option no est seulement utilisée sur la ligne de commande et n’est pas destinée aux utilisateurs.
Il s’agit d’une option à utiliser par sr3 lors de la génération (spawning) d’instances pour informer chaque processus
de quelle instance il s’agit. Par exemple, l’instance 3 sera générée avec --no 3


nodupe_basis <donnes|nom|chemin> (défaut: chemin)
-------------------------------------------------

Une option sous forme de mot-clé (alternative: *cache_basis* ) pour identifier quels fichiers sont comparés
à des fins de suppression des doublons. Normalement, la suppression des doublons utilise l’intégralité du
chemin d’accès pour identifier les fichiers qui n’ont pas été modifiés. Cela permet aux fichiers avec un contenu
identique d'être publié dans différents répertoires et de ne pas être supprimé. Dans certains cas
cas, la suppression de fichiers identiques devrait être effectuée quel que soit l’endroit où se trouve
le fichier.  Définissez 'nom' pour les fichiers de nom identique, mais qui sont dans des répertoires
différents pour qu'ils puissent être considéré comme des doublons. Définissez 'données' pour n’importe quel fichier,
quel que soit le nom, pour qu'il puisse être considéré comme un doublon si la somme de contrôle correspond.

Ceci est implémenté en tant qu’alias pour :

 callback_prepend nodupe.name

ou:

 callback_prepend nodupe.data


Pour plus d´information: `Supprimer les doublons <../Explication/SupprimerLesDoublons.html>`_

nodupe_fileAgeMax
-----------------

Si les fichiers sont plus anciens que ce paramètre (défaut: 30d), ignorez-les, ils sont trop
ancien pour qu'il puisse être posté.

nodupe_fileAgeMin
-----------------

Si les fichiers sont plus neuf que ce paramètre (défaut: 0 ... désactivé), ignorez-les, ils sont trop
neufs pour qu'ils puissent être postés.

nodupe_ttl <off|on|999[smhdw]>
------------------------------

Lorsque **nodupe_ttl** est défini à une intervalle de temps
qui est différente de zéro, chaque nouveau message d´annonce est comparé à ceux reçus dans cette intervalle, pour vérifier si
c’est un doublon. Les doublons ne sont pas traités ultérieurement. Qu’est-ce qu’un doublon ? Un fichier avec
le même nom (y compris l’en-tête des pièces) et la même somme de contrôle. A chaque intervalle de *hearbeat*, un
processus de nettoyage recherche les fichiers dans la cache qui n’ont pas été consultés pendant **cache** secondes,
et les supprime, afin de limiter la taille de la cache. De différents paramètres sont approprié pour de différents
cas d’utilisation.

Un intervalle d'entier brut est en secondes sauf si le suffixe m, h, d ou w est utilisé. Dans ce cas l’intervalle
est en minutes, heures, jours ou semaines respectivement. Après l’expiration de l’intervalle, le contenu est
abandonné, de sorte que les doublons séparés par une intervalle suffisamment grande passeront.
Une valeur de 1d (jour) ou 1w (semaine) est appropriée.  Définir l’option sans spécifier
un temps correspondra à 300 secondes (ou 5 minutes) comme intervalle d’expiration.

**L’utilisation de la cache est incompatible avec la stratégie de défaut *parts 0***, il faut spécifier une
stratégie alternative.  Il faut utiliser soit une taille de bloc fixe, ou ne jamais partitionner les fichiers.
Il faut éviter l’algorithme dynamique qui modifiera la taille de la partition utilisée au fur et à
mesure qu’un fichier grandit.

**Notez que le stockage de suppression de doublons est local à chaque instance**. Lorsqu’un nombre N d'instances partagent
une fil d’attente, la première fois qu’une publication est reçue, elle peut se faire choisir par une instance,
et si un doublon est ensuite reçu, il sera probablement choisi par une autre instance.
**Pour une suppression efficace des doublons avec les instances**, il faut **déployer deux couches d’abonnés**.
Utiliser une **première couche d’abonnés (shovels)** avec la suppression de doublons éteinte et
utiliser *post_exchangeSplit* pour la sortie. Cela achemine les publications en utilisant la somme de contrôle vers
une **deuxième couche d’abonnés (winnow) dont les caches de suppression des doublons sont actives.**


outlet post|json|url (défaut: post)
-----------------------------------

REMARQUE: **PAS IMPLEMENTÉ dans sr3, devrait revenir dans la version future**
L’option **outlet** est utilisée pour permettre l’écriture d'un poste a un fichier au lieu de
l'afficher à un courtier. Les valeurs d’argument valides sont les suivantes :


**post:**

  poster un messages d´annonce a un post_exchange

  **post_broker amqp{s}://<utilisateur>:<mot-de-passe>@<hoteDuCourtier>[:port]/<vhost>**
  **post_exchange     <nom>         (OBLIGATOIRE)**
  **post_topicPrefix <string>       (défaut: "v03")**
  **on_post           <script>       (défaut: None)**

  Si aucun courtier n'est fourni, le **post_broker** sera défini par le courtier d'entrée par défaut.
  Il suffit de définir l'option a un autre courtier si vous souhaitez envoyer les notifications
  ailleurs.

  Le **post_exchange** doit être défini par l’utilisateur. C’est l’échange sous lequel
  les notifications seront publiées.

**json:**

  écrire chaque message d´annonce en sortie standard, un par ligne dans le même format json que celui utilisé pour
  l'enregistrement et la restauration de la fil d’attente par l’implémentation python.

**url:**

  il suffit de sortir l’URL de récupération vers la sortie standard.

FIXME: L’option **outlet** provient de l’implémentation C ( *sr3_cpump* ) et elle n’a pas
a été beaucoup utilisé dans l’implémentation python.


overwrite <flag> (défaut: off)
------------------------------

L’option **overwrite**, si définie a false, évite les téléchargements inutiles sous ces conditions :

1- le fichier à télécharger se trouve déjà dans le système de fichiers de l’utilisateur et est au bon endroit

2- la somme de contrôle du message amqp correspond à celle du fichier.

Le défaut est False.

path <chemin>
-------------

**post** évalue le chemin d’accès du système de fichiers à partir de l’option **path**
et éventuellement **post_baseDir** si cette option est utilisée.

Si un chemin d’accès définit un fichier, ce fichier est surveillé.

Si ce chemin définit un répertoire, tous les fichiers de ce répertoire sont
surveillé et si **watch** trouve un (ou plusieurs) répertoire(s), il
les regarde de manière récursive jusqu’à ce que toute l'arborescence soit scanné.

Les annonces AMQP consistent des champs de l’arborescence, de l’heure d’annonce,
la valeur de l’option **url**, et FIXME: and the resolved paths to which were withdrawn
the *post_baseDir* present and needed.


permDefault, permDirDefault, permLog, permCopy
----------------------------------------------

Les bits d’autorisation sur les fichiers de destination écrits sont contrôlés par les directives *permCopy*.
*permCopy* appliquera les autorisations de mode publiées par la source du fichier.
Si aucun mode de source est disponible, le *permDefault* sera appliqué aux fichiers et le
*permLog* sera appliqué aux répertoires. Si aucun défaut est spécifié, les défauts du système d’exploitation
(sur linux, contrôlé par les paramètres umask) déterminera les autorisations du fichier.
(Notez que l’option *chmod* est interprétée comme un synonyme pour *permDefault*,
et *chmod_dir* est un synonyme de *permDirDefault*).

Lorsqu’il est défini dans un composant de posting, permCopy peut soit inclure ou exclure
l’en-tête *mode* des messages d´annonce.

lorsqu’il est défini dans un composant de polling, permDefault définit les autorisations minimales pour
qu'un dossier puis être accepté.

(sur une sortie ls qui ressemble à : ---r-----, comme une commande chmod 040 <fichier> ).
Les options **permDefault** spécifient un masque, c’est-à-dire que les autorisations doivent être
au moins ce qui est spécifié.

pollUrl
-------

Spécification de ressources d´une serveur à sonder
Voir `Guide de ligne de commande <../Explication/GuideLigneDeCommande.html>`_ pour plus 
d´informations.



post_baseDir <chemin>
---------------------

L’option *post_baseDir* fournit le chemin d’accès au répertoire qui, lorsqu’il est combiné (ou trouvé)
dans le *path* donné, donne le chemin absolu local au fichier de données à publier.
La partie *post_baseDir* du chemin d’accès sera supprimée de l’annonce publiée.
Pour les URL sftp, il peut être approprié de spécifier un chemin d’accès relatif à un compte d’utilisateur.
Exemple de cette utilisation serait: --post_baseDir ~utilisateur --url sftp:utilisateur@hote
Pour les fichiers : url, baseDir n’est généralement pas approprié. Pour publier un chemin absolu,
omettez le paramètre --post_baseDir et spécifiez simplement le chemin d’accès complet en tant qu’argument.

post_baseUrl <url>
------------------

L’option **post_baseUrl** définit comment obtenir le fichier... il définit le protocole,
l'hôte, le port et, l’utilisateur (facultatif). Il est recommandé de ne pas inclure de
mots de passe dans les URLs.

post_broker <url>
-----------------

l’URL du courtier pour publier des messages d'annonce. Voir `broker <#broker>`_ pour plus de détails.

post_exchange <name> (défaut: xpublic)
--------------------------------------

FIXME: L’option **post_exchange** est définie sous quelle échange la nouvelle notification
sera affiché. Lors de la publication sur une pompe en tant qu’administrateur, un
choix commun pour post_exchange est 'xpublic'.

Lors de la publication d’un produit, un utilisateur peut démarrer un script en utilisant
un point d'entrée de rappel de flux (flow callback) tels que **after_accept** et **after_work**
pour modifier les messages d'annonce générés à propos des fichiers avant leur publication.


post_exchangeSplit <compte> (défaut: 0)
---------------------------------------

L’option **post_exchangeSplit** ajoute un suffixe à deux chiffres qui est crée en hachant le dernier caractère
de la somme de contrôle avec le nom de post_exchange, afin de répartir la production entre un certain nombre d’échanges.
Ceci est actuellement utilisé dans les pompes à trafic élevé pour avoir plusieurs instances de winnow,
qui ne peuvent pas être instancié de la manière normale.  Exemple::

    post_exchangeSplit 5
    post_exchange xwinnow

entraînera la publication de messages d'annonce sur cinq échanges nommés : xwinnow00, xwinnow01,
xwinnow02, xwinnow03 et xwinnow04, où chaque échange ne recevra qu’un cinquième
du flux total.

post_format <name> (défaut: v03)
--------------------------------

Définit le format de message pour les messages publiés. les valeurs actuellement incluses sont :

* v02 ... utilisé par toutes les pompes de données existantes dans la plupart des cas.
* v03 ... par défaut au format sr3 JSON plus facile à utiliser.
* wis ... un format expérimental geoJSON en flux pour l'Organisation météorologique mondiale

Lorsqu'elle est fournie, cette valeur remplace tout ce qui peut être déduit de post_topicPrefix.


post_on_start
-------------

Lors du démarrage de watch, on peut soit demander au programme de publier tous les fichiers dans les répertoires
surveillés, ou pas. (pas implanté en sr3_cpost)

post_topic <chaine>
-------------------

Définissez explicitement une chaîne de sujet de publication, en remplaçant l'habituel
groupe de paramètres. Pour les pompes de données Sarracenia, cela ne devrait jamais être nécessaire,
car l'utilisation de *post_exchange*, *post_topicPrefix* et le *relPath* construit normalement le bon
valeur pour les sujets à la fois pour la publication et la liaison.


post_topicPrefix (défaut: topicPrefix)
--------------------------------------

Rajouter au subtopic pour former une hiérarchie complète des sujets.
Cette option s’applique à la publication.  Elle indique la version des messages d'annonce publiés
dans les subtopics. (v03 fait référence à `<sr3_post.7.html>`_) Cette valeur par défaut est défini par tout ce qui
a été reçue.

prefetch <N> (défaut: 1)
------------------------

L’option **prefetch** définit le nombre de messages d'annonce à récupérer en même temps.
Lorsque plusieurs instances sont en cours d’exécution et que prefetch est égale à 4, chaque instance obtient jusqu’à quatre
messages d'annonce à la fois.  Pour réduire le nombre de messages d'annonce perdus si une instance meurt et qu'elle a le
partage de charge optimal, prefetch doit être réglée le plus bas possible.  Cependant, sur des long haul links (FIXME),
il faut augmenter ce nombre pour masquer la latence d'aller-retour, donc un réglage de 10 ou plus est nécessaire.

queueName|queue|queue_name|qn
-----------------------------

* queueName <nom>

Par défaut, les composants créent un nom de fil d’attente qui doit être unique. Par défaut, le
queue_name crée par les composants suit la convention suivante :

   **q_<utilisateurDeCourtier>.<nomDuProgramme>.<nomDeConfig>.<aléatoire>.<aléatoire>**

Ou:

* *utilisateurDeCourtier* est le nom d’utilisateur utilisé pour se connecter au courtier (souvent: *anonymous* )

* *nomDuProgramme* est le composant qui utilise la fil d’attente (par exemple *subscribe* ),

* *nomDeConfig* est le fichier de configuration utilisé pour régler le comportement des composants.

* *aléatoire* n’est qu’une série de caractères choisis pour éviter les affrontements quand plusieurs
  personnes utilisent les mêmes configurations

Les utilisateurs peuvent remplacer le défaut à condition qu’il commence par **q_<utilisateurDeCourtier>**.

Lorsque plusieurs instances sont utilisées, elles utilisent toutes la même fil d’attente, pour faire plusieurs
taches simples à la fois. Si plusieurs ordinateurs disposent d’un système de fichiers domestique partagé, le
queue_name est écrit à :

 ~/.cache/sarra/<nomDuProgramme>/<nomDeConfig>/<nomDuProgramme>_<nomDeConfig>_<utilisateurDeCourtier>.qname

Les instances démarrées sur n’importe quel nœud ayant accès au même fichier partagé utiliseront la
même fil d’attente. Certains voudront peut-être utiliser l’option *queue_name* comme méthode plus explicite
de partager le travail sur plusieurs nœuds.

queueBind
---------

Au démarrage, par défaut, Sarracenia redéclare les ressources et les liaisons pour s’assurer qu’elles sont à jour.
Si la fil d’attente existe déjà, ces indicateurs peuvent être défini a False, afin qu’aucune tentative de déclaration
ne soit effectuée pour fil d’attente ou pour ses liaisons. Ces options sont utiles sur les courtiers qui ne
permettent pas aux utilisateurs de déclarer leurs files d’attente.

queueDeclare <flag> (défaut: True)
----------------------------------

Avec l´option queueDeclare à *True*, un composant déclare un fil d´attente pour accumuler des messages d'annonce lors
de chaque démarrage. Des fois les permissions sont restrictifs sur les courtiers, alors on ne peut pas
faire de tels déclarations de ressources. Dans ce cas, il faut supprimer cette déclaration.

randomize <flag>
----------------

Actif si *-r|--randomize* apparaît dans la ligne de commande... ou *randomize* est défini
à True dans le fichier de configuration utilisé. S’il y a plusieurs postes parce que
le fichier est publié par bloc (l’option *blocksize* a été définie), les messages d'annonce de bloc
sont randomisés, ce qui signifie qu’ils ne seront pas affichés.

realpathAdjust <compte> (Experimental) (défaut: 0)
--------------------------------------------------

L'option realpathAdjust ajuste le nombre d'éléments de chemin de fichier résolus avec la routine realpath
provenant du bibliotech standard C. Le nombre indique combien d'éléments de chemin doivent être ignorés, en comptant
depuis le début du chemin avec des nombres positifs, ou la fin avec des nombres négatifs. Le défaut est zéro
indiquant que le chemin au complet est résolu.


realpathFilter <flag> (Expérimentale)
-------------------------------------

l'option realpathFilter résout les chemins à l'aide de la routine de bibliothèque **realpath** standard C,
mais uniquement dans le but d'appliquer des filtres d'acceptation de rejet. Ceci est utilisé uniquement pendant
affectation.

Cette option est utilisée pour étudier certains cas d'utilisation et pourrait disparaître à l'avenir.

Implémenté en C, mais pas python actuellement.


realpathPost <flag> (Expérimentale)
-----------------------------------

L’option realpathPost résout les chemins donnés à leurs chemins canoniques, éliminant ainsi
toute indirection via des liens symboliques. Le comportement améliore la capacité de watch à
surveiller l'arborescence, mais l'arborescence peut avoir des chemins complètement différents de ceux des arguments
donné. Cette option impose également la traversée de liens symboliques.

Cette option est utilisée pour étudier certains cas d'utilisation et pourrait disparaître à l'avenir.

sendTo <url>
---------------

Specification du serveur auquel on veut livrer des données (dans un *sender*) 


rename <chemin>
---------------

Avec l’option *renommer*, l’utilisateur peut suggérer un chemin de destination pour ses fichiers. Si le
chemin se termine par '/' il suggère un chemin de répertoire...  Si ce n’est pas le cas, l’option 
spécifie un changement de nom de fichier.

report et report_exchange
-------------------------

REMARQUE: **PAS IMPLEMENTÉ dans sr3, devrait revenir dans la version future**
Pour chaque téléchargement, par défaut, un message de rapport amqp est renvoyé au courtier.
Cela se fait avec l’option :

- **rapport <flag> (défaut: True)**
- **report_exchange <report_exchangename> (défaut: xreport|xs_*nomUtilisateur* )**

Lorsqu’un rapport est généré, il est envoyé au *report_exchange* configuré. Les composants administratifs
publient directement sur *xreport*, tandis que les composants d'utilisateur publient sur leur
échanges (xs_*nomUtilisateur*). Les démons de rapport copient ensuite les messages dans *xreport* après validation.

Ces rapports sont utilisés pour le réglage de la livraison et pour les sources de données afin de générer des
informations statistiques. Définissez cette option a **False**, pour empêcher la génération de ces rapports.

reset <flag> (défaut: False)
----------------------------

Lorsque **reset** est défini et qu’un composant est (re)démarré, sa fil d’attente est
supprimé (si elle existe déjà) et recréé en fonction des options de fil d’attente.
C’est à ce moment-là qu’une option de courtier est modifiée, car le courtier refusera
l’accès à une fil d’attente déclarée avec des options différentes de celles qui étaient
défini à la création.  Cette option peut également être utilisé pour supprimer rapidement une fil d’attente
lorsqu’un récepteur a été fermé pendant une longue période de temps. Si la suppression des doublons est active, alors
la cache de réception est également supprimé.

Le protocole AMQP définit d’autres options de fil d’attente qui ne sont pas exposées
via Sarracenia, parce que Sarracenia choisit soi-même des valeurs appropriées.

retryEmptyBeforeExit: <booléen> (défaut: False)
-----------------------------------------------

Utilisé pour les tests de flux de sr_insects. Empêche Sarracenia de quitter lorsqu’il reste des messages d'annonce dans la file
d’attente de nouvelles tentatives (retry queue). Par défaut, une publication quitte proprement une fois qu’elle a
créé et tenté de publier des messages d'annonce pour tous les fichiers du répertoire spécifié. Si des messages d'annonce ne sont pas
publiés avec succès, ils seront enregistrés sur le disque pour réessayer ultérieurement. Si une publication n’est
exécutée qu’une seule fois, comme dans les tests de flux, ces messages d'annonce ne seront jamais réessayés, sauf si
retryEmptyBeforeExit est défini à True.

retry_ttl <duration> (défaut: identique à expire)
-------------------------------------------------

L’option **retry_ttl** (nouvelle tentative de durée de vie) indique combien de temps il faut continuer à essayer d’envoyer
un fichier avant qu’il ne soit  rejeté de la fil d’attente.  Le défaut est de deux jours.  Si un fichier n’a pas
été transféré après deux jours de tentatives, il est jeté.

sanity_log_dead <interva;le> (défaut: 1.5*housekeeping)
-------------------------------------------------------

L’option **sanity_log_dead** définit la durée à prendre en compte avant de redémarrer un composant.

shim_defer_posting_to_exit (EXPERIMENTAL)
-----------------------------------------

(option spécifique à libsrshim)
Reporte la publication des fichiers jusqu’à ce que le processus se ferme.
Dans les cas où le même fichier est ouvert et modifiée à plusieurs reprises, ceci
peut éviter les publications redondantes.  (défaut: False)

shim_post_minterval *interval* (EXPERIMENTAL)
---------------------------------------------

(option spécifique à libsrshim)
Si un fichier est ouvert pour écriture et fermé plusieurs fois dans l’intervalle,
il ne sera affiché qu’une seule fois. Lorsqu’on écrit dans un fichier plusieurs fois, en particulier
dans un script shell, de nombreux postes sont créés, et les scripts shell affecte la performance.
Dans tous les cas, les abonnés ne seront pas en mesure de faire des copies assez rapidement, donc
il y a peu d’avantages à avoir 100 messages d'annonce du même fichier dans la même seconde pa exemple.
Il est prudent de fixer une limite maximale à la fréquence de publication d’un fichier donné. (défaut: 5s)
Remarque: si un fichier est toujours ouvert ou a été fermé après son post précédent, alors
pendant le traitement de sortie du processus, il sera à nouveau publié, même si l’intervalle
n’est pas respecté, afin de fournir le message d'annonce final le plus précis.

shim_skip_parent_open_files (EXPERIMENTAL)
------------------------------------------

(option spécifique à libsrshim)
L’option shim_skip_ppid_open_files signifie qu’un processus vérifie si le processus parent a le même fichier
ouvert et ne poste pas si c’est le cas. (défaut: Vrai)

sleep <temps>
-------------

Temps d’attente entre la génération d’événements. Lorsqu'on écrit fréquemment à des fichiers, c’est inutile
de produire un poste pour chaque changement, car il peut produire un flux continu de changements où les transferts
ne peut pas être fait assez rapidement pour suivre le rythme.  Dans de telles circonstances, on peut regrouper toutes
les modifications apportées à un fichier pendant le temps de *sleep*, et produire un seul poste.

statehost <booléen> ( défaut: False )
-------------------------------------

Dans les grands centres de données, le répertoire de base peut être partagé entre des milliers de
nœuds. Statehost ajoute le nom du nœud après le répertoire de cache pour le rendre
unique à chaque nœud. Ainsi, chaque nœud a ses propres fichiers d’état et journaux.
Par exemple, sur un nœud nommé goofy, ~/.cache/sarra/log/ devient ~/.cache/sarra/goofy/log/.

strip <count|regexp> (défaut: 0)
--------------------------------

Il est possible de modifier les répertoires en miroir relatifs à l’aide de l’option **strip**.
Si elle est défini à N (un entier), les premiers répertoires 'N' du chemin relatif
sont supprimés. Par exemple::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /monrépertoirelocal
   accept    .*RADAR.*

entraînerait la création des répertoires et du fichier
/monrépertoirelocal/WGJ/201312141900_WGJ_PRECIP_SNOW.gif.
Lorsqu’un regexp est fourni à la place d’un nombre, cela indique un modèle à supprimer
du chemin relatif. Par exemple, si ::

   strip  .*?GIF/

Le fichier sera aussi placé au même emplacement.
Notez que les paramètres de strip peuvent être modifiés entre les options de répertoire.

REMARQUE::
    avec **strip**, l’utilisation du modificateur **?** (pour éviter l’expression régulière *greediness*) est souvent utile.
    Cela garantit que le match le plus court est utilisé.

    Par exemple, avec un nom de fichier : radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.GIF
    L’expression : .*?GIF correspond à : radar/PRECIP/GIF
    alors que l’expression : .*GIF correspond au nom entier.

sourceFromExchange <flag> (défaut: off)
---------------------------------------

L’option **sourceFromExchange** est principalement destinée aux administrateurs.
Si les messages d'annonce reçus sont postés directement à partir d’une source, l’échange utilisé
est «xs_<nomUtilisateurSourceDuCourtier>». Ces messages d'annonce pourraient manquer les en-têtes *source* et *from_cluster*,
ou un utilisateur malveillant peut définir des valeurs incorrectes.
Pour se protéger contre ces deux problèmes, les administrateurs doivent définir l’option **sourceFromExchange**.

Lorsque l’option est définie, les valeurs des en-têtes de *source* et *from_cluster* du message d'annonce seront alors remplacées ::

  self.msg.headers['source']       = <utilsateurDuCourtier>
  self.msg.headers['from_cluster'] = cluster

Cela va remplacer toutes les valeurs présentes dans le message d'annonce. Ce paramètre doit toujours être utilisé
lors de l’ingestion de données à partir d’un échange d’utilisateur. Ces champs sont utilisés pour renvoyer
les rapports à l’origine des données injectées. Cela est généralement combiné avec::

       *mirror true*
       *sourceFromExchange true*
       *répertoire ${PBD}/${YYYYMMDD}/${SOURCE}*

Pour que les données arrivent dans l’arborescence de format standard.

subtopic <modèle  amqp> (défaut: #)
-----------------------------------

Dans les publications d’un échange, le paramètre de subtopic restreint la sélection du produit.
Pour donner la bonne valeur au subtopic, on a le choix de filtrer en utilisant **subtopic** seulement avec le
wildcarding limité d’AMQP et une longueur limitée à 255 octets encodés, ou de manière plus puissante, les expressions régulière
basés sur les mécanismes **accept/reject** décrits ci-dessous. La différence est que le
le filtrage AMQP est appliqué par le courtier lui-même, ce qui évite que les avis soient livrés.
aux clients. Les modèles **accept/reject** s’appliquent aux messages d'annonce envoyés par le
courtier à l’abonné. En d’autres termes, **accept/reject** sont des filtres côté client,
alors que **subtopic** est le filtrage côté serveur.

Il est recommandé d’utiliser le filtrage côté serveur pour réduire le nombre d’annonces envoyées
au client et envoyer seulement ce qui est pertinent, et seulement régler les mécanismes côté client,
économisant du bandwidth et du traitement pour tous.

topicPrefix est principalement utilisé lors des transitions de version de protocole,
où l’on souhaite spécifier une version de protocole non-commune des messages d'annonce auquel s’abonner.

Normalement, l’utilisateur spécifie un échange et plusieurs options de subtopic. **subtopic** est ce qui est
normalement utilisé pour indiquer les messages d'annonce d'intérêt. Pour utiliser **subtopic** pour filtrer les produits,
il faut que la chaîne de caractère subtopic corresponde au chemin relatif du produit.

Par exemple, en consommant à partir de DD, pour donner la bonne valeur au subtopic, il est possible de
parcourir le site Web **http://dd.weather.gc.ca** et noter tous les répertoires
d’intérêt.  Pour chaque arborescence de répertoires d’intérêt, il faut écrire une option de **subtopic**
comme cela:

**subtopic  repertoire1.*.sous-repertoire3.*.sous-repertoire5.#**

::

 ou:
       *                correspond à un nom de répertoire unique
       #                correspond à toute arborescence de répertoires restants

Remarque:
  Lorsque les répertoires ont ces wild-cards, ou espaces dans leurs noms, ils
  sera encodé par l'URL ( '#' devient %23 ).
  Lorsque les répertoires ont des points dans leur nom, cela changera
  la hiérarchie des sujets.

  FIXME:
      les marques de hachage sont substituées à l’URL, mais n’ont pas vu le code pour les autres valeurs.
      Vérifiez si les astérisques dans les noms de répertoire dans les rubriques doivent être encodés par l'URL.
      Vérifiez si les points dans les noms de répertoire dans les rubriques doivent être encodés par l'URL.

On peut utiliser plusieurs liaisons à plusieurs échanges comme cela::

  échange A
  subtopic repertoire1.*.repertoire2.#

  échange B
  subtopic *.repertoire4.#

Cela va déclarer deux liaisons différentes à deux échanges différents et deux arborescences de fichiers différentes.
Alors que la liaison par défaut consiste à se lier à tout, certains courtiers pourraient ne pas permettre aux
clients à définir des liaisons, ou on peut vouloir utiliser des liaisons existantes.
On peut désactiver la liaison de fil d’attente comme cela::

  subtopic None

(False, ou off marchera aussi.)


timeCopy (défaut: on)
---------------------

Sur les systèmes de type Unix, lorsque la commande *ls* ou un navigateur de fichiers affiche une modification ou un
temps d’accès, il s’agit d’un affichage des éléments posix *st_atime* et *st_ctime* d’un struct renvoyé par l’appel
stat(2).  Lorsque *timeCopy* est activé, les en-têtes qui reflètent ces valeurs dans les messages d'annonce sont utilisés
pour restaurer l’accès et la modification des heures respectivement sur le système de l'abonné. Pour documenter
le retard de la réception des fichiers, cette option peut être désactivée, puis les temps du fichier sur la
source et la destination sont comparés.

Lorsqu’il est défini dans un composant de publication, les en-têtes *atime* et *mtime* des messages d'annonce sont éliminés.

timeout <intervalle> (défaut: 0)
--------------------------------

L’option **timeout** définit le nombre de secondes à attendre avant d’interrompre un
transfert de connexion ou de téléchargement (appliqué pendant le transfert).

tlsRigour (défaut: medium)
--------------------------

*tlsRigour* peut être réglé a : *lax, medium ou strict*, et donne un indice à l'application par rapport à la
configuration des connexions TLS. TLS, ou Transport Layer Security (autrefois appelée Secure Socket Layer (SSL))
est l’encapsulation de sockets TCP normales en cryptage standard. Il existe de nombreux aspects de
négociations TLS, vérification du nom d’hôte, vérification des certificats, validation, choix de
chiffrement. Ce qui est considéré comme sécuritaire évolue au fil du temps, de sorte que les paramètres
qui étaient considérés comme sécuritaire il y a quelques années, sont actuellement déconseillés.
Ceci mène naturellement à des difficultés de communication à cause de différents
niveaux de conformité par rapport à ce qui est couramment défini comme un cryptage rigoureux.

Par exemple, si on se connecte à un site et que son certificat est expiré, et
qu'il est quand même nécessaire de l’utiliser, alors définir tlsRigour a *lax* pourra
permettre la connexion de réussir.

topic <chaine> 
--------------

Définissez explicitement une chaîne de sujet d'abonnement ou de publication, en remplaçant la valeur
dériver à partir de l'habituel groupe de paramètres. Pour les pompes de données Sarracenia, cela ne 
devrait jamais être nécessaire, car l'utilisation de l'*exchange*, *topicPrefix* et *subtopic*  
construit normalement le bon valeur.

topicPrefix (défaut: v03)
-------------------------

rajouté au subtopic pour former une hiérarchie complète de thèmes (topics).
Cette option s’applique aux liaisons d’abonnement.
Indique la version des messages d'annonce reçus dans les subtopics. (V03 fait référence à `<sr3_post.7.html>`_)

users <flag> (défaut: false)
----------------------------

Utiliser comme complément lorsque l’action *declare* est utilisée, pour demander à sr3 de déclarer des utilisateurs
sur le courtier, ainsi que les files d’attente et les échanges.

v2compatRenameDoublePost <flag> ( default: false)
-------------------------------------------------

la version 3 de Sarracenia propose une logique améliorée autour du renommage des fichiers, 
en utilisant un seul message par opération de renommage. La version 2 nécessitait deux postes.
Lors de la publication, dans une situation de mise en miroir, pour la consommation par les clients 
v2, cet indicateur doit être réglé.


varTimeOffset (default: 0)
--------------------------

For example::

  varTimeOffset -7m 


modifiera des substitutions de variables qui impliquent des substitutions de date/heure.
Dans un modèle comme ${YYYY}/${MM}/${DD} sera évalué comme étant le
date, évaluée sept minutes dans le passé.

vip - OPTIONS ACTIVE/PASSIVE
----------------------------

L’option **vip** indique qu’une configuration doit être active uniquement sur
un seul nœud dans un cluster à la fois, un singleton. C’est typiquement
requis pour un composant de poll, mais cela peut être utilisé avec un sender ou avec d'autres cas.

**subscribe** peut être utilisé sur un seul nœud de serveur ou plusieurs nœuds
pourrait partager les responsabilités. Un autre logiciel de haute disponibilité et configurée séparément
présente un **vip** (ip virtuelle) sur le serveur actif. Si jamais
le serveur tombe en panne, le **vip** est déplacé sur un autre serveur et le traitement
se produit en utilisant le nouveau serveur qui a maintenant le VIP actif.
Les deux serveurs exécuteraient une instance **sr3**::

 - **vip          <string>          (None)**

Lorsqu’une seule instance **sr3** est exécutée  sur un serveur, ces options ne sont pas définies,
et l’abonnement fonctionnera en « mode autonome » (standalone mode).

Dans le cas des courtiers en cluster, les options doivent être définit en fonction du
vip qui change.

**vip 153.14.126.3**

Lorsqu’une **instance sr3** ne trouve pas l’adresse IP, elle se met en veille pendant 5 secondes et tente à nouveau.
Si c’est le cas, elle consomme et traite un message d'annonce et revérifie pour le vip.

SEE ALSO
========

`sr3(1) <sr3.1.html>`_ - Sarracenia ligne de commande principale.

`sr3_post(1) <sr3_post.1.html>`_ - émettre des messages d'annonce de fichiers (implémentation en Python.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - émettre des messages d´annonce de fichiers (implémentation en C.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - copie les messages d'annonce ( implémentation en C du composant shovel. )

**Formats:**

`sr3_post(7) <sr_post.7.html>`_ - Le formats des annonces.

**Page d'Accueil:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia : une boîte à outils de gestion du partage de données pub/sub en temps réel

