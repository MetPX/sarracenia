===========================================
Administrateur du serveur : un abonné local
===========================================
Cet exemple explique comment s'abonner aux fichiers swob du bureau météorologique d'Environnement Canada.


::

  $ sudo apt install rabbitmq-server
  $ sudo rabbitmqctl list_users
    Listing users ...
    user    tags
    guest   [administrator]

  $ sudo rabbitmqctl add_user 'bob'
    Adding user "bob" ...
    Password: robert

  $ sudo rabbitmqctl list_vhosts
    Listing vhosts ...
    name
    /

Définir les autorisations d'utilisateur pour vhost pour configurer bob:read:write::


  $ sudo rabbitmqctl set_permissions -p "/" "bob" ".*" ".*" ".*"
    Setting permissions for user "bob" in vhost "/" ...

  $ sudo rabbitmqctl set_user_tags bob management
    Setting tags for user "bob" to [management] ...

  $ sudo rabbitmq-plugins enable rabbitmq_management
  $ /etc/init.d/rabbitmq-server restart

Pour plus d’informations sur les différents types de balises d'utilisateur, voir `rabbitmq access and permissions. <https://www.rabbitmq.com/management.html#permissions>`_
Ouvrez http://localhost:15672/ dans un navigateur Web.
Connectez-vous avec le nom d’utilisateur/mot de passe créé ci-dessus.
Cliquez sur l’onglet ``Queues`` pour surveiller la progression du point de vue du courtier.
Retour dans le terminal::

  $ mkdir .config/sarra/subscribe
  $ vi .config/sarra/subscribe/test-subscribe.conf
    broker amqp://bob:robert@localhost/
    exchange xs_bob
    directory /tmp/sarra/output
    accept .*

Configurez les bits qui publient les modifications apportées à l’échange ::

  $ mkdir .config/sarra/watch
  $ vi $_/test-watch.conf
    post_broker amqp://bob:robert@localhost/
    post_exchange xs_bob
    path /tmp/sarra/input/
    events modify,create
  
  $ mkdir -p /tmp/sarra/{in,out}put
  $ sr start
  $ sr_watch log test-watch

--> Tous les rapports normaux.::

  $ sr_subscribe log test-subscribe
    .
    .
    2020-08-20 16:29:26,111 [ERROR] standard queue name based on: 
      prefix=q_bob
      component=subscribe
      exchangeSplit=False
      no=1

--> Notez la ligne avec **[ERROR]**,  elle n’a pas pu trouver la file d’attente.
c’est parce que la file d’attente doit d’abord être créée par sr_watch et puis que que nous avons commencé l'abonné et
watch en même temps avec '``sr start``' nous sommes tombés dans une petite condition de course.
Cela a été résolu peu de temps après car le sr_subscribe a un temps de nouvelle tentative de 1 seconde.
Cela peut être confirmé avec la page 'RabbitMQ Queues' affichant une ``q_bob.sr_subscribe.test_subscribe. ...`` file d’attente dans la liste.::


  $ touch /tmp/sarra/input/testfile1.txt
  $ ls /tmp/sarra/input/
    testfile1.txt
  $ ls /tmp/sarra/output/
      testfile1.txt
  $ sr_subscribe log test-subscribe
    .
    .
    2020-08-20 16:29:26,078 [INFO] file_log downloaded to: /tmp/sarra/output/testfile1.txt

  $ sr_watch log test-watch
    2020-08-20 16:29:20,612 [INFO] post_log notice=20200820212920.611807823 file:/ /tmp/sarra/input/testfile1.txt headers={'to_clusters':'localhost', 'mtime':'20200820212920.0259232521', 'atime': '20200820212920.0259232521', 'mode': '644', 'parts': '1,0,1,0,0', 'sum':'d,d41d8cd98f00b204e9800998ecf8427e'}
    
  $ touch /tmp/sarra/input/testfile{2..9}.txt
  $ for i in {001..015}; do echo "file #$i" > file$i.txt; done
  $ watch -n 1 ls /tmp/sarra/output/

Maintenant, vous pouvez regarder les fichiers ruisseler dans le dossier de sortie,
Regardez également la page 'RabbitMQ Queues' qui recoit et traite les messages AMQP.
Lorsque tout est terminé, vous pouvez arrêter à la fois l’abonné et le watcher avec::

  $ sr stop
    ...
  $ sr_subscribe cleanup test-subscribe
    ...

Maintenant, la file d’attente a été supprimée de RabbitMQ et tous les services ont été arrêtés.
