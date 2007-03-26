#!/bin/sh

# script to load and initialize netconsole module

LOGSERVER=bootserver
LOGPORT=514 # syslog

# fill arp cache
ping -c 1 $LOGSERVER

SRVIP=`arp -a $LOGSERVER | awk '{ print $2; }' | tr -d '(,)'`
SRVMAC=`arp -a $LOGSERVER | awk '{ print $4; }'`

# netconsole=[src-port]@[src-ip]/[<dev>],[tgt-port]@<tgt-ip>/[tgt-macaddr]
modprobe netconsole netconsole=@/,$LOGPORT@$SRVIP/$SRVMAC
