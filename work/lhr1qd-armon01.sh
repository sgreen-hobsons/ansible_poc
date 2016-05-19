#!/bin/bash

ANSIHOST=lhr1qd-armon01

/usr/bin/ansible-playbook lhr1qd-armon01.yml --extra-vars "vmware_guest_name=$ANSIHOST"
/usr/bin/ansible-playbook /etc/ansible/playbooks/bootstrap.yml -l $ANSIHOST
/usr/bin/ansible-playbook /etc/ansible/playbooks/mongodb.yml -l $ANSIHOST
