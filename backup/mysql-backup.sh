#!/bin/bash

umask 027
BACKUP_DIR=${1:-/dumps/mysql}
BACKUP_FILE="mysql_dumpall"

if [ ! -d $BACKUP_DIR ]; then mkdir -p $BACKUP_DIR; fi
/usr/bin/mysqldump --all-databases | gzip --rsyncable > $BACKUP_DIR/$BACKUP_FILE.gz
