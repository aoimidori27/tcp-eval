#!/bin/bash

BACKUPDIR=${1:-/mnt/backup/postgresql}
BACKUPFILE="pg_dumpall.dump"

if [ ! -d $BACKUPDIR ]; then mkdir -p $BACKUPDIR; fi

su postgres pg_dumpall | gzip > $BACKUPDIR/$BACKUPFILE.gz
