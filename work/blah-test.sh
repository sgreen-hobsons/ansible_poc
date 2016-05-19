#!/bin/bash

ANSIHOST=sjc1du-ansitest02

/usr/bin/ansible-playbook blah-deploy.yml --extra-vars "vmware_guest_name=$ANSIHOST"
/usr/bin/ansible-playbook blah-bootstrap.yml -l $ANSIHOST
#/usr/bin/ansible-playbook mongodb.yml -l $ANSIHOST
