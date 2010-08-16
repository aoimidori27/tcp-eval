#!/bin/bash

# Script to perform an automated build of MeshConf. 
#
# Copyright (C) 2008 - 2010 Arnd Hannemann <arnd@arndnet.de>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

## settings
WORKDIR=/home/eclipse-build/workdir
PROJECT=MeshConf
WARDIR=/home/eclipse-build/build
DEPLOYFILE=webserver:/var/lib/tomcat5.5/webapps/$PROJECT.war
VERSIONFILE=$WORKDIR/src/net/umic_mesh/meshconf/common/Version.java
DOCDIR=/home/eclipse-build/public_html/
## END SETTINGS

TMPFILE=$(mktemp -p /tmp eclipse-build.XXXXXX)

echo "Reverting $VERSIONFILE..."
svn revert $VERSIONFILE 2>&1 | tee $TMPFILE

echo "Syncing with repository..."
svn up $WORKDIR

REV=$(svnversion $WORKDIR)
WARFILE=$WARDIR/$PROJECT-r$REV.war

echo "Modifying $VERSIONFILE..."
sed -i "s/@PLACEHOLDER@/r$REV/g" $VERSIONFILE

echo "Cleaning workdir..."
ant -f $WORKDIR/build.xml clean | tee $TMPFILE

echo "Invoking ant..."
cd $WORKDIR
ant -f $WORKDIR/build.xml -Dwar.destfile=$WARFILE war | tee $TMPFILE
RC=$?
if [ $RC -ne 0 ]; then
  echo "Ant exited with $RC. Not deploying.";
  rm $TMPFILE;
  exit 1;
fi;

if grep -i "error" $TMPFILE; then
  echo "Build failed with error. Not deploying.";
  rm $TMPFILE;
  exit 1;
fi;

rm $TMPFILE;
cd $WARDIR
ln -vsf $WARFILE current.war
cd -

scp $WARFILE $DEPLOYFILE
#echo "Restarting tomcat5..."
#ssh webserver "sudo /etc/init.d/tomcat5 restart </dev/null >/dev/null 2>/dev/null"
echo "Done."

echo "Generating javadoc..."
ant -f $WORKDIR/build.xml javadoc
