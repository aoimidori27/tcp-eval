#!/bin/bash

umask 027
BACKUP_DIR=${1:-/backup/mysql}
BACKUP_FILE="mysql_dumpall"

if [ ! -d $BACKUP_DIR ]; then mkdir -p $BACKUP_DIR; fi
/usr/bin/mysqldump --all-databases | gzip > $BACKUP_DIR/$BACKUP_FILE.gz
