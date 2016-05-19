#!/bin/bash

ANSIHOST=sjc1qd-armon04

/usr/bin/ansible-playbook armon04.yml --extra-vars "vmware_guest_name=$ANSIHOST"
/usr/bin/ansible-playbook /etc/ansible/playbooks/bootstrap.yml -l $ANSIHOST
/usr/bin/ansible-playbook /etc/ansible/playbooks/redis.yml -l $ANSIHOST
