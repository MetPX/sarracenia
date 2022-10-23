

===========================
Notes de mise en œuvre MQTT
===========================



v3 vs. v5
---------

* La version 3 a des renvois envoyés sur une base chronométrée, toutes les quelques secondes
  (peut-être jusqu’à 20 secondes.)
  Si jamais vous avez un arriéré, ces retransmissions seront une tempête de trafic toujours croissant.

* La version 3 n’a pas d’abonnements partagés, ne peut utiliser qu’un seul processus par abonnement.
  L’équilibrage de charge est plus difficile.

Abonnements partagés
--------------------

* une fois que vous avez rejoint un groupe, vous y êtes jusqu’à ce que la session soit morte, même si vous vous déconnectez,
  Il empilera 1/n messages dans votre fil d’attente.

Contre-pression
---------------

1. Le client paho est asynchrone
2. La meilleure pratique consiste à avoir des handlers de on_message très légers.
3. Le client paho accuse réception dans la bibliothèque à peu près au moment où on_message est appelé.

Si vous avez une application qui prend du retard... par exemple, c'est lent à traiter,
mais comme la réception est asynchrone, tout ce que cela signifie, c’est que vous obtiendrez une
fil d’attente de messages sur l’hôte local. Idéalement, cela permettrait au courtier de savoir que
les choses vont mal et le courtier y enverra moins de données.

Méthode:

1. v5: Recevoir le maximum ... Limitez le nombre de messages en transit entre le courtier et le client.
   implémenté. Fonctionne.