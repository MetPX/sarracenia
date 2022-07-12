check_wsl=$(ps --no-headers -o comm 1)

if [[ $(($check_wsl == "init" )) ]]; then
	sudo service ssh start
fi

ssh localhost /bin/true
ssh_works=$?
if [ ${ssh_works} -gt 0 ]; then
    echo "no ssh to localhost... must fix..."
    # Setup autossh login
    ssh-keygen -t rsa -m PEM -N "" -f ~/.ssh/id_flow
    # https://stackoverflow.com/questions/54612609/paramiko-not-a-valid-rsa-private-key-file
    #sed -i 's/BEGIN .*PRIVATE/BEGIN RSA PRIVATE/;s/END .*PRIVATE/END RSA PRIVATE/'  ~/.ssh/id_flow
    cat ~/.ssh/id_flow.pub >> ~/.ssh/authorized_keys

    if [ ! -f ~/.ssh/id_rsa ]; then
       cp ~/.ssh/id_flow ~/.ssh/id_rsa
    else
       cat >>~/.ssh/config <<EOT
Host localhost
  IdentitiesOnly Yes
  StrictHostKeyChecking No
  IdentityFile ${HOME}/.ssh/id_flow
EOT
    fi
    ssh -o StrictHostKeyChecking=No localhost /bin/true
    ssh_works=$?
    if [ ${ssh_works} -le 0 ]; then
         echo "ssh to localhost still fails. boo!"
    else
         echo "ssh to localhost fixed by adding keys. Yay!"

    fi

else

    echo "ssh to localhost already works. yay!"

fi

