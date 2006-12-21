#!/bin/bash

BACKUPDIR=${1:-/mnt/backup/subversion}

if [ ! -d $BACKUPDIR ]; then mkdir -p $BACKUPDIR; fi

for i in /srv/svn/*; do
	BACKUPFILE=`basename "$i"`
	svnadmin dump "$i" -q | gzip > $BACKUPDIR/$BACKUPFILE.gz
done
