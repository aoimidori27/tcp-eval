#!/bin/bash

# für vmrouter275
#------------------

#alle filter entfernen
tc filter del dev eth0 parent 1: prio 16

#richtige wieder hinzufügen
VMROUTER262=`host vmrouter261 | cut -d' ' -f4`
VMROUTER264=`host vmrouter263 | cut -d' ' -f4`
VMROUTER266=`host vmrouter265 | cut -d' ' -f4`
VMROUTER268=`host vmrouter267 | cut -d' ' -f4`

tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:1  match ip dst $VMROUTER262
tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:2  match ip dst $VMROUTER264
tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:3  match ip dst $VMROUTER266
tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:4  match ip dst $VMROUTER268

#zusätzliche queues/classes für src abhängiges delay
tc class add dev eth0 parent 1: classid 1:51 htb rate 100Mbit
tc class add dev eth0 parent 1: classid 1:52 htb rate 100Mbit
tc class add dev eth0 parent 1: classid 1:53 htb rate 100Mbit
tc class add dev eth0 parent 1: classid 1:54 htb rate 100Mbit

tc qdisc add dev eth0 parent 1:51 handle 51: netem delay 3ms
tc qdisc add dev eth0 parent 1:52 handle 52: netem delay 10ms
tc qdisc add dev eth0 parent 1:53 handle 53: netem delay 20ms
tc qdisc add dev eth0 parent 1:54 handle 54: netem delay 100ms

tc qdisc add dev eth0 parent 51:1 pfifo limit 1000
tc qdisc add dev eth0 parent 52:1 pfifo limit 1000
tc qdisc add dev eth0 parent 53:1 pfifo limit 1000
tc qdisc add dev eth0 parent 54:1 pfifo limit 1000

#filter für die marks
tc filter add dev eth0 protocol ip parent 1: prio 1 handle 1 fw flowid 1:51
tc filter add dev eth0 protocol ip parent 1: prio 1 handle 3 fw flowid 1:52
tc filter add dev eth0 protocol ip parent 1: prio 1 handle 5 fw flowid 1:53
tc filter add dev eth0 protocol ip parent 1: prio 1 handle 7 fw flowid 1:54

#iptables netfilter MARKs
iptables -F PREROUTING -t mangle

iptables -A PREROUTING -t mangle -s vmrouter262 -j MARK --set-mark 1
iptables -A PREROUTING -t mangle -s vmrouter264 -j MARK --set-mark 3
iptables -A PREROUTING -t mangle -s vmrouter266 -j MARK --set-mark 5
iptables -A PREROUTING -t mangle -s vmrouter268 -j MARK --set-mark 7
