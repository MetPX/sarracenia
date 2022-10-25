==================
Message v01 Format
==================

Status: Approved-Draft1-20150805

Description du protocole / format du message.

Ce dossier documente les conclusions/propositions finales, les raisonnements/débats vont ailleurs.

Les messages publiés incluent un "sujet" et un "corps".

La sujet du message se décompose comme suit ::

	<version>.<type>.[Varie selon la version].<dir>.<dir>.<dir>...

	<version>:
		exp -- Version initiale, obsolète (non traitée dans ce document)
		v00 -- utilisé pour NURP & PAN-AM en 2013-2014. (non couvert dans le présent document)
		v01 -- version 2015.

	<type>:
		adm  - Modifier les paramètres
			´admin´, ´config´, etc...

		log  - rendre compte de l’état des opérations.

		notify - ´post´ mais dans les versions exp et v00. (Non couvert ici.)

		post - annoncer ou notifier qu’un nouveau bloc de produits est disponible.
	       		Chaînes possibles : post,ann(ounce), not(ify)
		
	<source>:

Le reste de ce document suppose la version 1 (sujet v01) :

sujet: <version>.<type>.<src>(.<dir>.)*.<nom de fichier>
contenu: 1ère ligne:
<horodatage> <taille de bloc en octets> <taille du fichier en blocs> <bloc#> <reste> <flags> <md5sum> <flowid> <srcpath> <relpath>

se décompose en::

  <horodatage>: date
	YYYYMMDDHHMMSS.<decimal> 

  <taille de bloc en octets>: bsz
        Nombre d’octets dans un bloc.
	Les sommes de contrôle sont calculées par bloc, donc un post

  <taille du fichier en blocs>: fzb
	Nombre total entier de blocs dans le fichier
	FIXME: (y compris le dernier bloc ou pas?)
	si ce paramètre est défini sur 1.
	
  <block#>: bno
  	0 origine, le numéro de bloc couvert par cette publication.

  <remainder>: brem
	normalement 0, sur le dernier bloc, il reste des blocs dans le fichier
        à transférer.

	-- si (fzb=1 and brem=0)
	       alors bsz=fsz en octets.
	       -- fichiers entiers remplacés.
	       -- C’est la même chose que le mode --whole-file de rsync.

  <flags>:Une liste de lettres d’option séparées par des virgules, certaines avec des arguments après '='.

	Paramètre de somme de contrôle contenu dans le champ 'flags', mais n’est pas tout.
    D’autres lettres / chiffres pourraient être là pour désigner d’autres choses.
	'=' sépare les indicateurs des arguments.


        donne lieu à l’entrée 'flags':

        0 - Aucune somme de contrôle (copie inconditionnelle.)
        d - Additionner l’intégralité des données
        n - checksum le nom du fichier
        c=<script> - somme de contrôle avec un script, nommée <script>

        <script> doit être "enregistré" dans le réseau de commutateurs.
       			enregistré signifie que tous les abonnés en aval
			peuvent obtenir le script pour valider la somme de contrôle.
			Il faut un mécanisme de récupération.

	Autres valeurs d’indicateur possibles :

        u - unlinked... pour les fichiers qui ont été supprimés ? 'r'?

        Stratégie de segment de fichier :
		i - inplace (ne pas créer de fichiers temporaires, juste chercher
			dans le fichier.)
		    peut entraîner la création d’un fichier .ddsig?
		p - part files.  Utilisez .part fichiers, suffixe fixe.
		    Je ne sais pas lequel sera par défaut.
	   - La stratégie de segment de fichier peut être remplacée par le client. Juste une suggestion.
	   - analogues aux options rsync : --inplace, --partial,

  <flowid>
	Une balise arbitraire utilisée pour le suivi des données via le réseau.

  Les deux voies sont subtilement liées.  Ni l’un ni l’autre ne peuvent être interprétés seuls.
  Il faut considérer les deux composantes du chemin.
  ------

    Que se passe-t-il s’il y a des espaces dans le nom du fichier ?
	Il est codé en URL, donc un espace doit se transformer en : %20

------

  <srcpath> -- URL de base utilisée pour récupérer les données.

	options: URL Complet:

	sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_000.gif

	dans le cas où l’URL ne se termine pas par un séparateur de chemin ('/'),
        le chemin src est considéré comme la source complète du fichier à récupérer.


	URL Statique:

	sftp://afsiext@cmcdataserver/  

	Si l’URL se termine par un séparateur de chemin ('/'), alors l’URL src est
        considéré comme un préfixe pour la partie variable de l’URL de récupération.


  <relpath> -- Chemin d’accès relatif du répertoire actif dans lequel placer le fichier.
	
	Deux cas basés sur la fin étant un séparateur de chemin ou non.

	cas 1: NURP/GIF/

	basé sur le répertoire de travail actuel du client de téléchargement,
	créer un sous-répertoire appelé URP, et à l’intérieur de celui-ci, un sous-répertoire
	appelé GIF sera créé.  Le nom du fichier sera tiré du
	srcpath.

    Si le srcpath se termine par pathsep, alors le relpath ici sera
	concaténé au srcpath, formant l’URL de récupération complète.

	cas 2: NRP/GIF/mine.gif

	Si le srcpath se termine par pathsep, le relpath sera concaténé
	à srcpath pour former l’URL de récupération complète.

    si le chemin src ne se termine pas par pathsep, l’URL src est prise
	comme terminé, et le fichier est renommé lors du téléchargement conformément à la
	spécification (dans ce cas, la mienne.gif)




FIXME: Vérifiez les points suivants :
	fsz = taille du fichier en octeta = ( bsz * (fsb-1) ) + brem ?


exemple 1::

  v01.post.ec_cmc.NRDPS.GIF.NRDPS_HiRes_000.gif
  201506011357.345 457 1 0 0 d <md5sum> exp13 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif NRDPS/GIF/ 

	v01 - version du protocol
	post - indique le type de message

	La version et le type déterminent ensemble le format des sujets suivantes et le corps du message.

	ec_cmc - le compte utilisé pour émettre le post (unique dans un réseau).
  
	  -- blocksize est 457  (== taille du fichier)
	  -- Le nombre de blocs est de 1
	  -- le reste est égal à 0.
	  -- le numéro de bloc est 0.
	  -- d - La somme de contrôle a été calculée sur le corps.
	  -- flow est un argument après le chemin relatif.
	  -- URL source complète spécifiée (ne se termine pas par '/')
	  -- chemin relatif spécifié pour

	pull de:
		sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif

	Chemin de téléchargement relatif complet :
		NRDPS/GIF/NRDPS_HiRes_000.gif

		-- Prend le nom de fichier de srcpath.
		-- peut être modifié par un processus de validation.


exemple 2::

  v01.post.ec_cmc.NRDPS.GIF.NRDPS_HiRes_000.gif
  201506011357.345 457 1 0 0 d <md5sum> exp13 http://afsiext@cmcdataserver/data/  NRDPS/GIF/NRDPS_HiRes_000.gif

  Dana ce cas,
	pull de:
		http://afsiext@cmcdataserver/data/NRPDS/GIF/NRDPS_HiRes_000.gif
		-- srcpath se termine par '/', donc concaténé, prend le fichier de l’URL relative.
		-- véritable 'miroir'

	Chemin de téléchargement relatif complet :
		NRDPS/GIF/NRDPS_HiRes_000.gif

    -- peut être modifié par un processus de validation.


Journaux des messages
---------------------

Le message du journal contient :

n’est émis qu’une fois le traitement terminé, pour indiquer un état final.

Le sujet correspond au message de notification sauf...

v01.log. <source>. <consumer>......

version est la version du protocole, doit incrémenter en synchronisation avec notifier.

Le début est comme par post... Il suffit d’ajouter des champs après:

<date> blksz blckcnt rest blocknum flags <flow> baseurl relativeurl <status> <host> <client> <duration>

Messages du CFG
---------------

juste un espace réservé.

vraiment pas encore fini. La pensée est en configuration.txt

v01.cfg  

