#!/bin/bash

BACKUPDIR=${1:-/backup/subversion}
BACKUPFILE="pg_dumpall.dump"

if [ ! -d $BACKUPDIR ]; then mkdir -p $BACKUPDIR; fi

for i in /srv/svn/*; do
	BACKUPFILE=`basename "$i"`
	svnadmin dump "$i" -q | gzip > $BACKUPDIR/$BACKUPFILE.gz
done
