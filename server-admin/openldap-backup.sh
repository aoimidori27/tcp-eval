#!/bin/bash

BACKUP_DIR=${1:-/backup/openldap}
BACKUP_FILE="ldap_dump.ldif"

if [ ! -d $BACKUP_DIR ]; then mkdir -p $BACKUP_DIR; fi
slapcat -l $BACKUP_FILE | gzip > $BACKUP_DIR/$BACKUP_FILE.gz
