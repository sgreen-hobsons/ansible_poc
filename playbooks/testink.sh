#!/bin/bash

ANSIHOST=$1

/usr/bin/ansible-playbook blah-deploy.yml --extra-vars "vmware_guest_name=$ANSIHOST"
/usr/bin/ansible-playbook blah-bootstrap.yml -l $ANSIHOST
