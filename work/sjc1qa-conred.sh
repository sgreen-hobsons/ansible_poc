#!/bin/bash

ANSIHOST=sjc1qa-conred01

/usr/bin/ansible-playbook sjc1qa-conred.yml --extra-vars "vmware_guest_name=$ANSIHOST"
/usr/bin/ansible-playbook /etc/ansible/playbooks/bootstrap.yml -l $ANSIHOST
/usr/bin/ansible-playbook /etc/ansible/playbooks/redis.yml -l $ANSIHOST
