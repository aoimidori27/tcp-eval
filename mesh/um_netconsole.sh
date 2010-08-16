#!/bin/bash

# Script to load and initialize netconsole module.
#
# Copyright (C) 2007 Arnd Hannemann <arnd@arndnet.de>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

LOGSERVER=bootserver
LOGPORT=515 # syslog

if [ "$1" = "-h" -o "$1" = "--help" ]; then
    echo "Usage: `basename $0` [LOGSERVER LOGPORT]"
    exit 1
fi

if [ -n "$1" ]; then
    LOGSERVER=$1
fi;

if [ -n "$2" ]; then
    LOGPORT=$2
fi;

# fill arp cache
ping -c 1 $LOGSERVER

SRVIP=`arp -a $LOGSERVER | awk '{ print $2; }' | tr -d '(,)'`
SRVMAC=`arp -a $LOGSERVER | awk '{ print $4; }'`

# netconsole=[src-port]@[src-ip]/[<dev>],[tgt-port]@<tgt-ip>/[tgt-macaddr]
modprobe netconsole netconsole=@/,$LOGPORT@$SRVIP/$SRVMAC
