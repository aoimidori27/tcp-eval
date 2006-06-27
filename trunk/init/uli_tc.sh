#!/bin/bash

DEV=ath0

# Adding a priority queue with two bands.
# The priomap directs all traffic to band 1 by default
tc qdisc add dev eth0 root handle 1: prio bands 2 priomap  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
tc qdisc add dev $DEV root handle 1: prio bands 2 priomap  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1

# Setting the default band to a sfq qdisc (distributes evenly)
tc qdisc add dev eth0 parent 1:2 handle 20: sfq
tc qdisc add dev $DEV parent 1:2 handle 20: sfq

# Setting our gatewayed band to a tocken bucket filter
#tc qdisc add dev eth0 parent 1:1 handle 10: tbf rate 1mbit burst 10000 limit 30000
#tc qdisc add dev $DEV parent 1:1 handle 10: tbf rate 1mbit burst 10000 limit 30000

tc qdisc add dev $DEV parent 1:1 handle 10: tbf rate 1mbit burst 128k latency 10ms
tc qdisc add dev eth0 parent 1:1 handle 10: tbf rate 1mbit burst 128k latency 10ms

# Classification
#tc filter add dev eth0 protocol ip parent 1: prio 1 u32 match ip dport 22 0xffff flowid 1:1

tc filter add dev eth0 protocol ip parent 1: prio 1 handle 6 fw flowid 1:1
tc filter add dev $DEV protocol ip parent 1: prio 1 handle 7 fw flowid 1:1

iptables -A PREROUTING -t mangle -i $DEV -j MARK --set-mark 6
iptables -A PREROUTING -t mangle -i eth0 -j MARK --set-mark 7

