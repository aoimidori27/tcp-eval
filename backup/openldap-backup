#!/bin/bash

umask 027
BACKUP_DIR=${1:-/backup/openldap}
BACKUP_FILE="ldap_dump.ldif"

if [ ! -d $BACKUP_DIR ]; then mkdir -p $BACKUP_DIR; fi
slapcat | gzip > $BACKUP_DIR/$BACKUP_FILE.gz
