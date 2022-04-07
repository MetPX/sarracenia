
=========
 SR_Poll
=========

-----------------------------------
Sonder pour des fichiers à distance
-----------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite

.. contents::

SYNOPSIS
========

**sr_poll** foreground|start|stop|restart|reload|status configfile

**sr_poll** cleanup|declare|setup configfile


DESCRIPTION
===========

**sr_poll** est un composant qui se connecte à un serveur distant pour
vérifier dans différents répertoires pour certains fichiers. Lorsqu'un fichier est
présent, modifié ou créé dans le répertoire distant, le programme va
informer sur le nouveau produit.

Le protocole de notification est défini ici `sr_post(7) <sr_post.7.rst>`_

**sr_poll** se connecte à un *courtier*.  Toutes les *sleep* secondes, il se connecte à
a *destination* (sftp, ftp, ftps, ftps). Pour chacun des *directory* défini, il répertorie
le contenu. Lorsqu'un fichier correspond à un modèle donné par *accept*, **sr_poll** construit
un avis pour ce produit et l'envoie au *courtier*. Le contenu correspondant du répertoire 
est conservé dans un fichier à titre de référence. Si un fichier correspondant est modifié,
ou créé lors d'une itération ultérieure, une nouvelle notification est envoyée.

**sr_poll** peut être utilisé pour acquérir des fichiers distants en conjonction avec 
un `sr_sarra(8) <sr_sarra.8.rst>`_ qui s´abonne aux notifications postées, télécharge les
fichiers et les rediffuse.

La commande **sr_poll** prend deux arguments : un fichier de configuration décrit ci-dessous,
suivi d'une action start|stop|stop|restart|reload|reload|status.....

Les actions **cleanup**, **declare**, **setup**, **setup** peuvent être utilisées pour gérer les ressources sur
le serveur rabbitmq. Les ressources sont soit des files d'attente, soit des échanges. **declare** crée
les ressources sur le serveur (échange.)



CONFIGURATION
=============

In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.rst>`__  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.


OPTIONS DE DESTINATION
----------------------

L'option de destination spécifie ce qui est nécessaire pour se connecter au serveur distant.

**Protocole de destination://<utilisateur>@<serveur>[:port]**.

: :
      (par défaut : Aucun et il est obligatoire de le définir)

La *destination* doit être définie avec le minimum d'informations requises **sr_poll** utilise 
le paramètre *destination* non seulement lors de l'interrogation, mais aussi lors de l'interrogation
dans les messages sr_post produits.

Par exemple, l'utilisateur peut définir:

  **destination ftp://myself@myserver**

Et complétez les informations nécessaires dans le fichier d'informations d'identification avec la ligne :

**ftp://myself:mypassword@myserver:2121 passive,binaire***.


SPÉCIFICATIONS DE SONDAGE
-------------------------

Ces options définissent les fichiers pour lesquels l'utilisateur veut être 
notifié et où il doit être notifié il sera placé, et sous quel nom.
 
- **filename  <option>         (optionnel)**
- **directory <path>           (défaut: .)**
- **accept    <patron regexp> [rename=] (mandatoire)**
- **reject    <patron regexp> (optionnel)**
- **chmod     <integer>        (défaut: 0o400)**
- **poll_without_vip <on|off>  (défaut: on)**
- **file_time_limit <integer> (défaut: 60d)**
- **destination_timezone      (défaut: 'UTC')**

L'option *filename* peut être utilisée pour définir un renommage global des produits.
Ex.. :

 **filename rename=/naefs/grib2/**

Pour toutes les notifications créées, l'option *rename* serait fixée à '/naefs/grib2/filename'.
parce que j'ai spécifié un répertoire (chemin qui se termine par /)

L'option *directory* définit où obtenir les fichiers sur le serveur.
Combiné avec les options **accept** / **reject**, l'utilisateur peut sélectionner l'option
et leurs répertoires de résidence. **get** est un synonyme de
pour **accept** et est défini pour la rétrocompatibilité.

Les options **accept** et **reject** utilisent des expressions régulières 
(regexp) pour correspondre à l'URL. Ces options sont traitées séquentiellement.
L'URL d'un fichier qui correspond à un motif **reject** n'est pas publié.  Les fichiers 
correspondant à un modèle **accept** sont publiés. Un *rename* peut être ajouté à 
l'option *accept* .

**${YYYY}         années courante**
**${MM}           mois courant**
**${JJJ}          jour julien courant**
**${YYYYMMDD}     date courante**

**${YYYY-1D}      année courante - 1 jour**
**${MM-1D}        mois courant  - 1 jour**
**${JJJ-1D}       jour julien courant - 1 jour**
**${YYYYMMDD-1D}  date courante   - 1 jour**

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

        directory /mylocaldirectory/${YYYYMMDD}/mydailies
        accept    .*observations.*

L'option **chmod** permet aux utilisateurs de spécifier un masque de permission en octal numérique 
de style linux::

  chmod 040

ce qui signifie qu'un fichier ne sera pas publié à moins que le groupe n'ait l'autorisation de lecture.
(sur une sortie ls qui ressemble à : ---r-----, comme un chmod 040 <fichier <fichier>commande).
L'option **chmod** spécifie un masque, c'est à dire que les permissions doivent être
au moins ce qui est spécifié.

Comme tout les componsants, l'option **vip** signale que plusieurs noeuds
dans une grappe participent et que le composant devraient être actif uniquement
sur un noeud à la fois.  Souvent le *poll* doit se garder à jour de l´état sur
la destination qui est *pollé* (*sondé*) même quand ce n´est pas ce noeud qui
va annoncer les nouveaux arrivés.

Si les noeuds qui n´ont pas le vip peuvent être réélement entièrement passifs,
comme si les *sarra* corréspondants on *delete* actif, alors il n´ont pas besoin
de se maintenir à jour, on peut setter **poll_without_vip** à *False* (or *off*). 
Ceci peut réduire la charge sur les noeuds de facon significative (mésuré à vingt fois 
moins de charge dans un cas exemplaire.)  C´est donc utile de le choisir quand 
l´efficacité de la configuration global est une enjeu.

Par défaut, les fichiers qui sont datés d'il y a plus de deux mois ne seront pas publiés. Il est possible de modifier cette limite de temps en le spécifiant dans une configuration avec *file_date_limit <integer>*. Par défaut, ce temps sera en secondes, sauf si préciser autrement, avec 1h, 1d, ou 1w par exemple, pour heure, jour et semaine respectivement. On peut également spécifier le fuseau horaire de tels fichiers en ajoutant l'option *destination_timezone '<TIMEZONE>'* dans les configurations pour convertir le temps des fichiers au fuseau horaire 'UTC'. Par défaut, le fuseau horaire de destination_timezone est 'UTC' mais on peut spécifier un autre fuseau horaire avec le format: '<TIMEZONE>' tel que 'PST' ou 'EST'.


SPÉCIFICATIONS DE PUBLICATION
-----------------------------

Ces options définissent comment on publie les fichiers. 
**Sr_poll** interroge la disponibilité d'un fichier sur un serveur distant en créant
un avis à ce sujet.  Les abonnés utilisent `sr_subscribe <sr_subscribe.1.rst>`_
pour consommer l'annonce et télécharger le fichier (ou **sr_sarra**).
Pour mettre les fichiers à la disposition des abonnés, **sr_poll** envoie les annonces à
un serveur AMQP, aussi appelé courtier.  Format de l'argument à l'option *broker*: :

       amqp|amqps]://[user[:password]@]host[:port][/vhost][/vhost].

L'url dans l'avis sera construite à partir de l'option *destination*, avec les options suivantes
le chemin du produit (*directory*/"matched file").  Il y a un message par fichier.
La taille du fichier est tirée du répertoire "ls".... mais sa somme de contrôle ne peut pas 
être déterminé, de sorte que l'en-tête "somme" dans l'écriture est fixé à "0,0".

Par défaut, sr_poll envoie son message au courtier avec l'échange par défaut.
est le préfixe *xs_* suivi du nom d'utilisateur du courtier. Le *courtier* est obligatoire.
Elle peut être incomplète si elle est bien définie dans le fichier credentials.conf.

Référez-vous à `sr_post(1) <sr_post.1.rst>`_ - pour comprendre le processus de notification complet.
Référez-vous à `sr_post(7) <sr_post.7.rst>`_ - pour comprendre le format de notification complet.

Ici, il est important de dire que.. :

Le *sum=0,0* est utilisé parce qu'aucun calcul de la somme de contrôle n'a été effectué.....
Il est souvent souhaitable d'utiliser le *sum=z,s* pour que les téléchargeurs calculent 
une somme de contrôle utile au fur et à mesure qu'ils téléchargent pour d'autres utilisateurs.

Le *parts=1,fsiz,1,0,0,0* est utilisé et la taille du fichier est tirée du ls du fichier.
Sous **sr_sarra**, ces champs peuvent être réinitialisés.


FONCTIONNALITÉS AVANCÉES
------------------------

Il existe des moyens d'insérer des scripts dans le flux des messages et des téléchargements de fichiers :
Si vous voulez mettre en œuvre des tâches dans les différentes parties de l'exécution du programme :

- **on_line      <script>        (defaut: line_mode)**
- **do_poll      <script>        (defaut: None)**
- **on_post      <script>        (defaut: None)**
- **on_html_page <script>        (defaut: html_page)**


Le plugin **on_line** permet des scripts qui peuvent lire chaque ligne d'un 'ls' lors du sondage
pour l'interpréter plus en profondeur. Il devrait retourner True, si la ligne doit être traitée 
plus en profondeur, ou Faux pour le rejeter. Par défaut, il y a un plugin line_mode inclus avec 
le package qui implémente la comparaison des permissions de fichiers sur le serveur distant par 
rapport au serveur distant. Le masque **chmod**. Le programme suppose que le tout dernier mot de 
la ligne ls est la ligne ls nom de fichier. Cela pourrait ne pas être le cas si les noms de 
fichiers peuvent contenir des espaces. A cette fin, l'option **ls_file_index** peut être utilisée
pour définir le premier mot où commence le nom de fichier.

Si le sondage est récupéré à l'aide du protocole http, les entrées de type "ls" doivent être
dérivées des données suivantes une page html. Le plugin par défaut **html_page** fourni avec le
paquet, donne une idée de comment analyser une telle page dans un répertoire python géré par **sr_poll**.

Un script do_nothing.py pour **on_post** pourrait être ::

 class Transformer(object):
      def __init__(self):
          pass
          
      def perform(self,parent):
          logger = parent.logger
          
          logger.info("I have no effect but adding this log line")
          
          return True
          
 transformer  = Transformer()
 self.on_post = transformer.perform

Les seuls arguments que le script reçoit **parent**, qui est une instance de
la classe **sr_poll** classe

Le script **do_poll** pourrait être écrit pour prendre en charge un protocole 
autre que le protocole ftp,ftps,sftp,sftp.  Encore une fois, ce script serait 
responsable de déterminer que faire dans le cadre de son protocole avec les 
différentes options **destination**, et s'il décide d'afficher un répertoire
il aurait besoin de construire son url, partstr, sumstr, sumstr et peut se servir de:

**parent.poster.post(parent.exchange,url,parent.to_clusters, \**
**                   partstr,sumstr,rename,remote_file)**

pour poster le message, en appliquant les clauses d'acceptation/rejet et en 
déclenchant sur le traitement_post.

DEPRECATED
==========

The *get* option is a deprecated synonym for accept.  Please use *accept*.

**get    <regexp pattern> [rename=] (must be set)**


AUSSI VOIR
----------


`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Sélectionner et télécharger des fichiers publiés. (page principale de référence.)

`sr_shovel(8) <sr_shovel.8.rst>`_ - process messages (no downloading.)

`sr_winnow(8) <sr_winnow.8.rst>`_ - a shovel with cache on, to winnow wheat from chaff.

`sr_sender(1) <sr_sender.1.rst>`_ - subscribes to messages pointing at local files, and sends them to remote systems and reannounces them there.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_watch(1) <sr_watch.1.rst>`_ - post that loops, watching over directories.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_audit(8) <sr_audit.8.rst>`_ - monitoring and configuration audit.

`sr_post(7) <sr_post.7.rst>`_ - The format of announcement messages.

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_pulse(7) <sr_pulse.7.rst>`_ - The format of pulse messages.

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.


