
Changements de conception depuis l’original (2015)
==================================================

Depuis 2022/03, la conception n’a pas beaucoup changé, mais la mise en œuvre de SR3
est totalement différent de la v2. Modifications de conception :

* La prise en charge explicite des applications de base pour les rapports a été supprimée
  comme ils n’ont jamais été utilisés, peuvent facilement être réinsérés en tant que rappels
  et conventions.
* personne n’utilisait de fichiers segmentés, et ils étaient très compliqués,
  mais tout le monde les trouve fantastiques en théorie. Nécessité de ré-implémenter
  après la refactorisation SR3.
* la mise en miroir était un cas d’utilisation que nous devions aborder, nous devions ajouter des métadonnées,
  et évoluer un peu.
* les concepts de routage de cluster ont été supprimés (cluster_from, cluster_to, etc...)
  Cela a gêné les analystes plus qu’il ne les a aidé. Super facile à
  implémenter en utilisant des rappels de flux, si jamais nous voulons les récupérer.
* l’algorithme `Flow <.. /Explication/Concepts.html#the-flow-algorithm>`_ est apparu comme un concept
  fédérateur pour toutes les différentes composantes initialement envisagées. Dans les premiers travaux
  sur la v2, nous ne savions pas si tous les composants fonctionneraient de la même manière, ils ont donc
  été écrits séparément de zéro. Beaucoup de copier/coller de code parmi les points d’entrée.

