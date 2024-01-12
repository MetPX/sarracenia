=======================
Normes de documentation
=======================


Structure des dossiers
~~~~~~~~~~~~~~~~~~~~~~

Avant de commencer à travailler avec la documentation, lire `l’intégralité de l’article de documentation Divo
<https://documentation.divio.com/>`_ (et les liens sur la barre latérale gauche).
Cela ne prendra pas plus de 30 minutes et vous obtiendrez une compréhension complète de
la structure, du style et du contenu attendus de la documentation ici.


.. Lien divo de sauvegarde en cas de décès du site : https://github.com/divio/diataxis-documentation-framework/
.. image:: https://documentation.divio.com/_images/overview.png
  :target: https://documentation.divio.com/

Nous regardons la directive unix dans notre documentation, chaque fichier de documentation fait une chose
et le fait bien en ce qui concerne les 4 quadrants.


.. note:: TODO:Ajoutez des exemples de liens vers chacune des sections ci-dessous:

Traitement
----------

Toute la documentation se trouve sous l’arborescence docs/source. Il est traité à l’aide de sphinx,
invoqué à l’aide du Makefil dans docs/.  On peut installer sphinx localement, et exécuter make pour
construire localement et déboguer. Le résultat est produit dans docs/build/html::

    pip install -f requirements-dev.txt
    cd docs
    make html
 
Pointez ensuite un navigateur sur docs/Build/HTML.

Il existe un travail Github Actions qui effectue cette opération à chaque push vers les branches
appropriées pour mettre à jour la documentation principale. L’URL principale du site Web résultant est:

  https://metpx.github.io/sarracenia/

Le processus de publication est automatisé par deux actions github CI/CD :

  * exécutez sphinx et validez les résultats dans une branche gh-pages: https://github.com/MetPX/sarracenia/actions/workflows/docs.yml
  * mettre à jour le site web de la branche: https://github.com/MetPX/sarracenia/actions/workflows/pages/pages-build-deployment

C´est une bonne pratique de jeter un coup d´œil aux messages d'erreur sphinx générés par le premier action. Il y a typiquement
des centaines de petits problèmes à corriger (liens qui ne sont pas tout à fait corrects, formatage de tableau cassé, etc...)



Tutoriels
---------

- Orienté vers l’apprentissage, en particulier apprendre comment plutôt que d’apprendre *cela*.
- Permettez à l’utilisateur d’apprendre en faisant pour le faire démarrer, assurez-vous que votre
  tutoriel fonctionne et que les utilisateurs peuvent voir les résultats immédiatement.
- Les tutoriels doivent être reproductibles de manière fiable et axés sur des étapes concrètes
  (et non sur des concepts abstraits) avec le minimum d’explications nécessaires.

De nombreux didacticiels sont créés à l’aide de jupyter notebooks. Voir docs/source/fr/Tutoriels/README.md pour
apprendre comment travailler avec eux.

How2Guides (Comment Faire)
--------------------------

- Axé sur le problème et l’objectif : "**Je veux... Comment puis-je...**" Différent des tutoriels parce que
  les tutoriels sont pour les débutants, et how2guides (comment faire) suppose une certaine connaissance
  et compréhension avec une configuration et des outils de base.
- Fournir une série d’étapes axées sur les résultats d’un problème particulier.
- N’expliquez pas les concepts, s’ils sont importants, ils peuvent être liés à `.. /Explication/`
- Il existe plusieurs façons d’écorcher un chat, restez flexible dans votre guide afin que les utilisateurs
  puissent voir *comment* les choses sont faites.
- **NOMMEZ BIEN LES GUIDES** assez pour dire à l’utilisateur *exactement* ce qu’il fait en un coup d’œil.

Explication
-----------

- Axé sur la compréhension: peut également être considéré comme des discussions. Version beaucoup
  plus détendue de la documentation où les concepts sont explorés à partir d’un niveau supérieur
  ou de perspectives différentes.
- Fournir un contexte, discuter des alternatives et des opinions tout en fournissant une référence
  technique (pour les autres sections).

Référence
---------

- Style dictionnaire.
- Orienté vers l’information: descriptions des fonctionnalités déterminées par le code.
- Strictement pour les pages de manuel et la référence directe des différents programmes, protocoles et fonctions.


Contribution
------------

- Informations essentielles à l’amélioration et à la progression du projet Sarracenia, c’est-à-dire: pour
  ceux qui cherchent à développer Sarracenia.
- Guide(s) de style
- Modèle(s)

Processus
~~~~~~~~~

Le processus de développement consiste à écrire ce que l’on a l’intention de faire ou ce que l’on a fait dans
un fichier `reStructuredText <https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html>`_
dans `/docs/Explanation/Design/`. Idéalement, la discussion de l’information y agit
comme point de départ qui peut être édité dans la documentation pour la ou les fonctionnalités au fur et à
mesure qu’elles sont mises en œuvre. Chaque nouveau composant sr_<whatever>, doit avoir des pages de manuel
pertinentes implémentées. Les how2guides et tutoriels devraient également être révisés pour tenir compte des
ajouts ou des modifications apportés au nouveau composant.


.. error::
    Besoin de Peter pour identifier les informations importantes dans doc/design pour tirer sur le
    /docs/Explanation/Design/


Guide de Style
~~~~~~~~~~~~~~

L’exécution sur la ligne de commande doit être écrite dans le style suivant.
Un commentaire initial décrivant les étapes ou processus suivants::

    $ command 1
      relevant output
    $command 2
      .
      .
      relevant output
      newline relevant output

Remarques importantes:

- Le commentaire initial se termine par `::` suivi d’une nouvelle ligne vide
- Ensuite, se trouve le bloc de code indenté (deux espaces)
- Syntaxe des commandes: '`$ <cmd>`'

- Vous pouvez également indiquer les commandes de niveau root avec '`# <cmd>`'
- La sortie de la commande est (deux espaces) en retrait de la commande principale.

  - Les lignes de sortie non pertinentes peuvent être remplacées par des points ou carrément omises.

Choisissez et respectez une hiérarchie d’en-tête par défaut (ie : = > ~ > - > ... pour un titre > h1 > h2 > h3... etc)

Style de Code
-------------

Nous suivons généralement les standards `PEP 8 <https://peps.python.org/pep-0008/>`_ pour la mise en forme du code,
et on utilise `YAPF <https://github.com/google/yapf>`_ pour reformater automatiquement le code.
Une exception au PEP 8 est que nous utilisons une longueur de ligne de 119 caractères.

Pour les docstrings dans le code, nous suivons le Guide de style Google.
Ces docstrings seront analysés dans une documentation formatée par Sphinx.


Des exemples détaillés peuvent être trouvés dans le
`Documents du plugin Napoleon Sphinx <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_
et les `Guide Google de Style Python <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_.

Exemples choisis de ``credentials.py``:

.. code-block:: python

    class Credential:
        """Objet qui contient des informations sur les informations d’identification, lues à partir d’un fichier
         credentials, qui a une information d’identification par ligne, en format::
            url option1=value1, option2=value2
            
        Exemples::
            sftp://alice@herhost/ ssh_keyfile=/home/myself/mykeys/.ssh.id_dsa
            ftp://georges:Gpass@hishost/  passive = True, binary = True
            
        `Format de la Documentation. <https://metpx.github.io/sarracenia/Reference/sr3_credentials.7.html>`_

        Attributs:
            url (urllib.parse.ParseResult): object with URL, password, etc.
            ssh_keyfile (str): path to SSH key file for SFTP
            passive (bool): use passive FTP mode, defaults to ``True``
            binary (bool): use binary FTP mode, defaults to ``True``
            tls (bool): use FTPS with TLS, defaults to ``False``
            prot_p (bool): use a secure data connection for TLS
            bearer_token (str): bearer token for HTTP authentication
            login_method (str): force a specific login method for AMQP (PLAIN,
                AMQPLAIN, EXTERNAL or GSSAPI)
        """

        def __init__(self, urlstr=None):
            """Créer un objet Credential.

                Args:
                    urlstr (str): a URL in string form to be parsed.
            """


.. code-block:: python
    
    def isValid(self, url, details=None):
        """Valide un objet URL et Credential. Vérifie les mots de passe vides, les schémas, etc.
            
        Args:
            url (urllib.parse.ParseResult): ParseResult objet pour un URL.
            details (sarracenia.credentials.Credential): objet Crednetial sarra qui contient des details additionels
            à propos de l'URL.
        Returns:
            bool: ``True`` si un URL est valide, ``False`` sinon.
        """

Why rST?
--------

`reStructuredText`_ a été choisi principalement parce qu’il prend en charge la création automatique d’une
table des matières avec la directive '``.. Table des matières::``'.
Comme beaucoup d’autres langages de Markup, il prend également en charge le style en ligne,
les tableaux, les en-têtes et les blocs littéraux.

Dans Jupyter Notebooks, malheureusement, seul Markdown est pris en charge, sinon RST est génial.

Localisation
~~~~~~~~~~~~

Ce projet est destiné à être traduit en Français et en anglais à un minimum tel qu’il est
utilisé dans l’ensemble du gouvernement du Canada, qui possède ces deux langues officielles.

La documentation Française a la même structure de fichiers et les mêmes noms que la documentation anglaise, mais
est placé dans le sous-répertoire fr/.  C’est plus facile si la documentation est produite
dans les deux langues à la fois. Utilisez au moins un outil de traduction automatique (tel que
`deepl <https://deepl.com>`_) pour fournir un point de départ. Même procédure pour les francophones.
