# Sarracenia Jupyter Notebooks

Une collection de démonstrations des différentes API pour s’abonner à des flux de données continus
à partir d’une pompe de données Sarracenia.

Configuration d’un environnement local :

    python3 -m venv sarracenia
    cd sarracenia
    . bin/activate  # yes, that is a period
    git clone https://github.com/MetPX/sarracenia.git
    cd sarracenia
    git checkout v03_wip
    cd jupyter
    pip install -r requirements.txt
    jupyter notebook --ip=0.0.0.0 --port=8040

Une autre option:

    establish a virtual machine running ubuntu 20.04 or later.
    sudo apt update ; sudo apt upgrade
    sudo apt install git python3-pip
    export PATH="${HOME}/.local/bin:${PATH}"
    git clone -b v03_wip https://github.com/MetPX/sarracenia.git sr3
    cd sr3
    pip3 install -e .
    pip3 install -r requirements-dev.txt 
    cd docs/source/jupyter
    ip addr show # to know the ip to point your browser at.
    jupyter notebook --ip=0.0.0.0 --port=8040
    # open broser on ip:8040
    #look for the certificate to post as credential for browser. 
    # in the startup text.

## Interface de ligne de commande

Introduction à l’interface de ligne de commande, utilisée pour gérer les flottes d’instances et de configurations.
L’arborescence et la langue du fichier de configuration sr3 placent les journaux dans un emplacement standard,
et où le démarrage, la surveillance et l’arrêt des instances sont effectués à l’aide de SR3.

Démonstration : [CLI_introduction.ipynb](CLI_introduction.ipynb)


## Personnalisation avec rappels (callbacks)

Qu’est-ce qu’un flux ? Il s’agit des étapes suivantes :

* gather (obtenir de nouveaux messages à partir d’une pompe de données, d’une source 
  d’interrogation distante ou d’un répertoire local.)
* filter (appliquer les masques accept/reject, puis le traitement on_filter.)
* work (faire un téléchargement (la plupart des flux) ou envoyer, ou quoi que ce soit)
* post ( poster un message sur une nouvelle pompe pour que d’autres flux puissent 
  l’utiliser, ou l’écrire dans un fichier, ou rien.)

FIXME : notebook manquant. Planifié.
La classe Sarracenia flowCallback (sarracenia.flowcb.FlowCB) permet aux développeurs
d’implémenter des processus personnalisés.

## Exemple de Polling avec un Callback.

Il existe de nombreuses sources de données qui ne produisent pas de messages Sarracenia en mode natif.
Pour travailler avec eux, il faut les interroger pour les ingérer dans un réseau de pompage de données.

FIXME : notebook manquant. Planifié.

## Pure Python Sarracenia.Flow.Subscribe

Avec cette API, on peut exécuter un composant complet de téléchargement et de republication, p
articipant pleinement à une pompe de données Sarracenia.
Il exécute l’algorithme de flux, y compris la collecte d’informations à partir d’une source 
en amont (une pompe ou une arborescence de répertoires).
Le traite et permet de l’afficher par la suite. Toute la configuration en configurant des 
structures de données dans des appels d’API n’utilise pas le langage de configuration.

Démonstration : [Sarracenia_flow_demo](Sarracenia_flow_demo.ipynb)


## Pure Python Sarracenia.Moth

Le poids le plus léger / le moins d’intrusion dans une base de code existante serait d’utiliser
l’API sarracenia.moth, et demander à l’application de demander des messages chaque fois qu’elle est prête
pour les digérer. Moth gère uniquement l’interaction avec un agent de messages, de sorte que l’application
est responsable des téléchargements de données réels, de la récupération des erreurs, de la gestion des processus, etc.

Démonstration: [Sarracenia_moth_demo.ipynb](Sarracenia_flow_demo.ipynb)
[mybinder.org](https://mybinder.org/v2/gh/MetPX/sarracenia/v03_wip?filepath=jupyter%2FSarracenia_moth_demo.ipynb)
