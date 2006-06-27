#!/bin/bash
einfo "Setting up Uli's measurement stuff"

HOSTID=${HOSTNAME##mrouter}

IPADDR=169.254.9.$HOSTID

BBONEIP=`ip addr show dev eth0 | grep inet | sed -r -e 's/^.*inet ([0-9.]*).*$/\1/'`

DEV=ath0

EXTADDRS=5

einfo HOSTID $HOSTID

einfo Adding external addresses
for ((i=1;i<=EXTADDRS;i++)); do ip addr add 10.1.$((i)).$HOSTID dev $DEV; done

einfo Adding NAT rule

iptables -t nat -A POSTROUTING -j SNAT -s 10.1.$HOSTID.0/24 -o eth0 --to-source $BBONEIP

einfo Disabling reverse path filter, enabling ip forwarding

echo 0 >/proc/sys/net/ipv4/conf/$DEV/rp_filter
echo 1 >/proc/sys/net/ipv4/ip_forward

einfo Adding route for own external addresses

ip route add 10.1.$HOSTID.0/24 dev $DEV

einfo Initializing table 200 with external host stuff

ip rule add prio 50000 lookup 200

ip route del default

# ip route add table 200 default dev $DEV
ip route add table 200 192.168.10.0/24 dev $DEV

ip route add table 200 default via 192.168.9.1

if [ $HOSTID -gt 2 ]; then
	# Gateway
	einfo Gateway Node. Adding rules and routes
	ip rule add prio 39999 from 10.1.$HOSTID.0/24 lookup 99
	ip route add table 99 192.168.10.0/24 via 192.168.9.2 dev eth0
	einfo Setting up tc stuff
	/opt/meshnode/scripts/measurement/uli_tc.sh	
fi

eend
