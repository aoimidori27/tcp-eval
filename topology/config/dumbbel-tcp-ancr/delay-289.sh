#!/bin/bash

# für vmrouter268
#------------------

#alle filter entfernen
tc filter del dev eth0 parent 1: prio 16

#richtige wieder hinzufügen
VMROUTER281=`host vmrouter281 | cut -d' ' -f4`
VMROUTER283=`host vmrouter283 | cut -d' ' -f4`
VMROUTER285=`host vmrouter285 | cut -d' ' -f4`
VMROUTER287=`host vmrouter287 | cut -d' ' -f4`

tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:1  match ip dst $VMROUTER281
tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:2  match ip dst $VMROUTER283
tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:3  match ip dst $VMROUTER285
tc filter add dev eth0 parent 1: protocol ip prio 16 u32  match ip protocol 47 0xff flowid 1:4  match ip dst $VMROUTER287

#zusätzliche queues/classes für src abhängiges delay
tc class add dev eth0 parent 1: classid 1:51 htb rate 100Mbit
tc class add dev eth0 parent 1: classid 1:52 htb rate 100Mbit
tc class add dev eth0 parent 1: classid 1:53 htb rate 100Mbit
tc class add dev eth0 parent 1: classid 1:54 htb rate 100Mbit

tc qdisc add dev eth0 parent 1:51 handle 51: netem delay 2ms 200us 20%
tc qdisc add dev eth0 parent 1:52 handle 52: netem delay 5ms 500us 20%
tc qdisc add dev eth0 parent 1:53 handle 53: netem delay 20ms 2ms 20%
tc qdisc add dev eth0 parent 1:54 handle 54: netem delay 50ms 5ms 20%

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

iptables -A PREROUTING -t mangle -s vmrouter281 -j MARK --set-mark 1
iptables -A PREROUTING -t mangle -s vmrouter283 -j MARK --set-mark 3
iptables -A PREROUTING -t mangle -s vmrouter285 -j MARK --set-mark 5
iptables -A PREROUTING -t mangle -s vmrouter287 -j MARK --set-mark 7
