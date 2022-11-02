

Status: Approved-Draft2-20150825

================================================
Description du protocole / format du message v02
================================================

Ce fichier a été utilisé lors de la phase de conception, mais après la mise en œuvre,
elle est remplacée par la page de manuel sr_post(7).

Ce dossier documente les conclusions/propositions finales, les raisonnements/débats
va ailleurs.

Les messages affichés comprennent quatre parties :
Sujet: .<version><type>. <src>(.<dir>.) *. <nom de fichier>
en-têtes : série de paires clé-valeur, selon les spécifications AMQP.
1ère ligne (champs séparés par des espaces) : <horodatage> <srcURL> <relURL><newline>
Reste du corps:

La sujet du message se décompose comme suit ::

	<version>.<type>.[Varie selon la version].<dir>.<dir>.<dir>...

	<version>:
		exp -- Version initiale, obsolète (non traitée dans ce document)
		v00 -- utilisé pour NURP & PAN-AM en 2013-2014. (non couvert dans le présent document)
		v01 -- version 2015.
		v02 -- 2015 est passé aux embases AMQP pour les composants non obligatoires

	<type>:
		adm  - Modifier les paramètres
			´admin´, ´config´, etc...

		log  - rendre compte de l’état des opérations.

		notify - ´post´ mais dans les versions exp et v00. (Non couvert ici.)

		post - annoncer ou notifier qu’un nouveau bloc de produits est disponible.
	       		Chaînes possibles : post,ann(ounce), not(ify)

	<source>:

Le reste de ce document suppose la version 2 (sujet v02) :

se décompose en:

  <horodatage>: date
	YYYYMMDDHHMMSS.<decimal> 

<srcURL> -- URL de base utilisée pour récupérer les données.

	options: URL Complet:

	sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_000.gif

	dans le cas où l’URL ne se termine pas par un séparateur de chemin ('/'),
        le chemin src est considéré comme la source complète du fichier à récupérer.


	URL Statique:

	sftp://afsiext@cmcdataserver/

	Si l’URL se termine par un séparateur de chemin ('/'), alors l’URL src est
        considéré comme un préfixe pour la partie variable de l’URL de récupération.


<relURL> -- Chemin d’accès relatif du répertoire actif dans lequel placer le fichier.
	
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


AMQP fournit des EN-TÊTES qui sont des paires clé/valeur.

Décrivez quelle partie de l’URL est annoncée :

parts=1,sz  
	-- Extraction dans une seule pièce, de la taille donnée en octets
	
parts=<i|p>,<bsz>,<fzb>,<bno>,<remainder>
	-- Récupération en plusieurs parties.

        -- File Segment strategy::
		i - inplace (ne pas créer de fichiers temporaires, juste lseek
			dans le fichier.)
		    peut entraîner la création d’un fichier .srsig?
		p - part files.  Utilisez .part fichiers, suffixe fixe.
		    Je ne sais pas lequel sera par défaut.

    -- La stratégie de segment de fichier peut être remplacée par le client. Juste une suggestion.
    -- analogues aux options rsync : --inplace, --partial,

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


sum=<algorithm>,<value>

	<algorithm>

        d - Additionner l’intégralité des données
        n - somme de contrôle sur le nom du fichier
        <script> - omme de contrôle avec un script, nommée <script>

        <script> doit être "enregistré" dans le réseau de commutateurs.
       			enregistré signifie que tous les abonnés en aval
			peuvent obtenir le script pour valider la somme de contrôle.
			Il faut un mécanisme de récupération.

	<value> est la valeur de la somme de contrôle

flow=<flowid>
	Une balise arbitraire utilisée pour le suivi des données via le réseau.

  Les deux voies sont subtilement liées.  Ni l’un ni l’autre ne peuvent être interprétés seuls.
  Il faut considérer les deux composantes du chemin.


FIXME : vérifiez les points suivants :
	fsz = Taille d’un fichier en octets = ( bsz * (fsb-1) ) + brem ?


exemple 1:

v02.post.ec_cmc.NRDPS.GIF.NRDPS_HiRes_000.gif
201506011357.345 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif 
EN-TÊTES:
parts=1,457
rename=NRDPS/GIF/ 
sum=d,<md5sum>
flow=exp13

	v01 - version du protocol
	post - indique le type de message

	La version et le type déterminent ensemble le format des sujets suivantes et le corps du message.

	ec_cmc - le compte utilisé pour émettre le post (unique dans un réseau).
  
	  -- taille du fichier est de 457  (== taille du fichier)
	  -- d - La somme de contrôle a été calculée sur le corps.
	  -- flow est appelé ´exp13´ par le poster...
	  -- URL source complète spécifiée (ne se termine pas par '/')
	  -- chemin relatif spécifié pour

	pull de:
		sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif

	Chemin de téléchargement relatif complet :
		NRDPS/GIF/NRDPS_HiRes_000.gif

		-- Prend le nom de fichier de srcpath.
		-- peut être modifié par un processus de validation.


exemple 2:

v02.post.ec_cmc.NRDPS.GIF.NRDPS_HiRes_000.gif
201506011357.345 http://afsiext@cmcdataserver/data/  
HEADERS:
rename=NRDPS/GIF/NRDPS_HiRes_000.gif
parts=1,457
sum=d,<md5sum>
flow=exp13

Dans ce cas,
	pull de:
		http://afsiext@cmcdataserver/data/NRPDS/GIF/NRDPS_HiRes_000.gif

		-- srcpath se termine par '/', donc concaténé, prend le fichier de l’URL relative.
		-- véritable 'miroir'


	Chemin de téléchargement relatif complet :
		NRDPS/GIF/NRDPS_HiRes_000.gif

    -- peut être modifié par un processus de validation.

exemple 3:

v02.post.ec_cmc.NRDPS.GIF.NRDPS_HiRes_000.gif
201506011357.345 http://afsiext@cmcdataserver/data/ 
HEADERS:
rename=NRDPS/GIF/NRDPS_HiRes_000.gif
parts=i,457,0,0,1,0
sum=d,<md5sum>
flow=exp13

Cas d’attente.

wait=on/off


