#!/bin/bash

# Firstrun.sh for new VMware guests.

FQD=emt.hobsons.local
guest_name=sjc1du-ansitest01
#guest_name={{ vmware_guest_name }}
#guest_mac={{ ansible_facts.macaddress }}
guest_ip=`/usr/bin/dig +short $guest_name.$FQD`
guest_net=`echo $guest_ip | cut -d . -f 1,2,3`

echo "guest_ip is $guest_ip"
echo "guest_net is $guest_net"

func_setnetwork() {
	echo "Gettin' funcy!"
	echo "broadcast is $guest_broadcast"
	echo "network is $guest_network"
	echo "netmask is $guest_netmask"
	echo "gateway is $guest_gateway"
	echo "IP is $guest_ip"
}

case ${guest_net} in

10.24.128)
	#SJC Dev/QA
	guest_gateway=10.24.128.1
	guest_netmask=255.255.255.0
	guest_network=10.24.128.0
	guest_broadcast=10.24.128.255
	func_setnetwork
	;;
10.24.129)
	#SJC Dev/QA
	guest_gateway=10.24.129.1
	guest_netmask=255.255.255.0
	guest_network=10.24.129.0
	guest_broadcast=10.24.129.255
	func_setnetwork
	;;
10.24.132)
	#SJC1 Prod
	guest_gateway=10.24.132.1
	guest_netmask=255.255.254.0
	guest_network=10.24.132.0
	guest_broadcast=10.24.132.255
	func_setnetwork
	;;
10.24.133)
	#SJC1 Prod
	guest_gateway=10.24.132.1
	guest_netmask=255.255.254.0
	guest_network=10.24.132.0
	guest_broadcast=10.24.133.255
	func_setnetwork
	;;
10.24.168)
	#SJC1 Internal Only
	guest_gateway=10.24.168.1
	guest_netmask=255.255.255.0
	guest_network=10.24.168.0
	guest_broadcast=10.24.168.255
	func_setnetwork
	;;
10.24.180)
	#SJC1 DMZ
	guest_gateway=10.24.180.1
	guest_netmask=255.255.255.0
	guest_network=10.24.180.0
	guest_broadcast=10.24.180.255
	func_setnetwork
	;;
10.56.152)
	#IAD1 Prod
	guest_gateway=10.56.152.1
	guest_netmask=255.255.254.0
	guest_network=10.56.152.0
	guest_broadcast=10.56.152.255
	func_setnetwork
	;;
10.56.153)
	#IAD1 Prod
	guest_gateway=10.56.152.1
	guest_netmask=255.255.254.0
	guest_network=10.56.152.0
	guest_broadcast=10.56.153.255
	func_setnetwork
	;;
10.56.148)
	#IAD1 Dev/QA
	guest_gateway=10.56.148.1
	guest_netmask=255.255.255.0
	guest_network=10.56.148.0
	guest_broadcast=10.56.148.255
	func_setnetwork
	;;
10.56.168)
	#IAD2 Internal Only
	guest_gateway=10.56.168.1
	guest_netmask=255.255.255.0
	guest_network=10.56.168.0
	guest_broadcast=10.56.168.255
	func_setnetwork
	;;
10.56.180)
	#IAD2 DMZ
	guest_gateway=10.56.180.1
	guest_netmask=255.255.255.0
	guest_network=10.56.180.0
	guest_broadcast=10.56.180.255
	func_setnetwork
	;;
10.104.128)
	#LHR1 Prod
	guest_gateway=10.56.128.1
	guest_netmask=255.255.254.0
	guest_network=10.56.128.0
	guest_broadcast=10.56.128.255
	func_setnetwork
	;;
10.104.129)
	#LHR1 Prod
	guest_gateway=10.56.128.1
	guest_netmask=255.255.254.0
	guest_network=10.56.128.0
	guest_broadcast=10.56.129.255
	func_setnetwork
	;;
*)
	echo "No matching subnet!"
	exit 0
esac
