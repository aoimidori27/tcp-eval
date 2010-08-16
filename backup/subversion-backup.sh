#!/bin/bash

# Script to perform incremental subversion dumps.
#
# Copyright (C) 2010 Arnd Hannemann <arnd@arndnet.de>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

umask 027
BACKUP_DIR=${1:-/dumps/subversion}

# time in seconds at which a FULL dump is regenerated (30 days)
FULL_EXPIRE=$((3600*24*30))
NOW=$(/bin/date "+%s")

if [ ! -d $BACKUP_DIR ]; then mkdir -p $BACKUP_DIR; fi

for i in /srv/svn/*; do
    REV=$(svnlook youngest $i)
    BACKUP_FILE_FULL=$BACKUP_DIR/$(basename "$i")_dump_full.gz
    BACKUP_FILE_INCR=$BACKUP_DIR/$(basename "$i")_dump_incr.gz
    BACKUP_FILE_FULL_REV=$BACKUP_DIR/$(basename "$i")_FULL_REV
    LAST_FULL_CHANGE=0
    if [ -e "$BACKUP_FILE_FULL" -a -e "$BACKUP_FILE_FULL_REV" ]; then
        LAST_FULL_CHANGE=$(stat --format="%Y" $BACKUP_FILE_FULL);
        LAST_FULL_REV=$(cat $BACKUP_FILE_FULL_REV)
    fi;
    EXPIRY=$(($LAST_FULL_CHANGE+$FULL_EXPIRE))

    if [ $EXPIRY -lt $NOW ]; then
        # make full dump
        svnadmin dump "$i" -r 0:$REV -q | gzip --rsyncable > $BACKUP_FILE_FULL
        echo $REV > $BACKUP_FILE_FULL_REV
        rm -f $BACKUP_FILE_INCR
    else
        # only incremental dump 
        OLDREV=$(($LAST_FULL_REV+1))
        if [ $OLDREV -le $REV ]; then
            svnadmin dump "$i" -r $(($LAST_FULL_REV+1)):$REV --incremental -q | gzip --rsyncable > $BACKUP_FILE_INCR
        fi
    fi; 
done
