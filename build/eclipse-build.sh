#!/bin/bash

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
