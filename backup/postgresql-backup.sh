#!/bin/bash

umask 027
BACKUP_DIR=${1:-/backup/postgresql}
BACKUP_FILE="pg_dumpall"

if [ ! -d $BACKUP_DIR ]; then mkdir -p $BACKUP_DIR; fi
su postgres pg_dumpall | gzip > $BACKUP_DIR/$BACKUP_FILE.gz
