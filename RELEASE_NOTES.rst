
Le français suit (recherchez FRANCAIS)

-----------------------
Data Mart Client README
-----------------------

English
-------

1. dd.weather.gc.ca (the MSC Datamart) is Environment Canada's public
   meteorological data access repository.

2. For each product posted on the Datamart, an AMQP message is
   immediately transmitted. This message contains :
   "timestamp http://servername/basedir relative_file_path".
   The product's URL is described by the last two fields.
   Any application which can subscribe to an AMQP service can
   receive notification of products being published and then retrieve
   them in real time via http. Message format is fully described here:
   ( https://github.com/MetPX/sarracenia/blob/master/doc/sr_post.1.rst )

3. Datamart clients.

   * Sarracenia ( http://github.com/MetPX/sarracenia ) a complete reference implementation in Python >= 3.4. 
     It runs on Linux, Mac, and Windows. This is the best choice to use, if you can.
   * Sarrac ( https://github.com/MetPX/sarrac ) is a C implementation of data insertion (post & watch.) 
     It is Linux only. There is also a libcshim to be able to tranparently implement data insertion with 
     this tool, and libsarra allows C programs to post directly. There is consumer code as well 
     (to read queues) so messages can be passed to the downloader of your choice, but no built-in 
     downloading so far. This subset is meant to be used where python3 environments are 
     impractical (example: high performance computing environments.), or where memory & cpu is usage
     is particularly important such as in embedded systems.
   * node-sarra ( https://github.com/darkskyapp/node-sarra ) An embryonic implementation for node.js.
   * dd_subscribe is a python2 program that uses python-amqplib to receive these amqp notification 
     messages, retrieve the products from the datamart via HTTP and place them in a 
     chosen local directory. More info: ( https://github.com/MetPX/sarracenia/blob/master/doc/dd_subscribe.rst , 
     https://github.com/MetPX/sarracenia/blob/master/doc/dd_subscribe.1.rst )

6. Under samples/config you will find working configuration files for sarracenia, provided as is,
   without warranty. Under samples/program you will find other programs we played with.


_____________________________________________________________________________________


FRANCAIS
--------


1. dd.weather.gc.ca (le datamart du SMC) est le dépôt public de
   données météorologiques d'Environnement Canada

2. Chaque fois qu'un produit arrive dans le datamart, un message AMQP
   est immédiatement transmis. Ce message a la forme :
   "horodatage http://servername/racine chemin_relative_du_fichier".
   Le URL du produit est décrit par les deux derniers chanps.
   Toute application capable de s'abonner à un service AMQP
   peut recevoir les notifications des produits en qui sont publiés et
   les récupérer en temps réel par HTTP. plus d´information sur le format
   (pour l´instant en anglais seulement):
   ( https://github.com/MetPX/sarracenia/blob/master/doc/sr_post.1.rst )


3. Clients de téléchargement.

  * Sarracenia ( http://github.com/MetPX/sarracenia ) un client en Python >= 3.4. 
    Peut opérer sur Linux, Mac, et Windows. Meilleur choix d´habitude.
  * Sarrac ( https://github.com/MetPX/sarrac ), un client en C pour Linux seulement. Il permet 
    l´insertion de données et l´abonnement, mais ne contient rien pour télécharger. Il faut le combiner 
    avec un téléchargeur externe. Sa vocation est de servir dans les environnment ou python 3 n´est pas 
    facilement disponible (exemple: environnement de haute performance, tel Cray), ou bien ou on veut 
    minimiser la consommation de ressources (systèmes embarqué.) 
  * node-sarra ( https://github.com/darkskyapp/node-sarra ) client en javascript pour node.js.
  * dd_subscribe un client en python2, ancêtre de Sarracenia, une autre option quand python 3 n´est 
    pas utilisable. 
    plus d´infos (anglais): ( https://github.com/MetPX/sarracenia/blob/master/doc/dd_subscribe.rst )

6. Dans le répertoire samples/config vous trouverez des fichiers de
   configuration pour Sarracenia qui devraient fonctionner tels quels (sans
   garantie). Sous samples/program vous trouverez d'autres programmes
   avec lesquels nous avons expérimenté.

