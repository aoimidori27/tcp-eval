#!/bin/bash

## settings
ECLIPSE=/opt/eclipse/eclipse
WORKSPACE=/home/eclipse-build/workspace
PROJECT=MeshConf
WARDIR=/home/eclipse-build/build
VMARGS="-Xmx512M -XX:MaxPermSize=128M -Djava.library.path=/usr/lib/jni"

DEPLOYFILE=webserver:/var/lib/tomcat5.5/webapps/$PROJECT.war
VERSIONFILE=$WORKSPACE/$PROJECT/src/net/umic_mesh/meshconf/common/Version.java

## END SETTIGNS

TMPFILE=$(mktemp -p /tmp eclipse-build.XXXXXX)

echo "Reverting $VERSIONFILE..."
svn revert $VERSIONFILE 2>&1 | tee $TMPFILE

echo "Syncing with repository..."
svn up $WORKSPACE/$PROJECT

REV=$(svnversion $WORKSPACE/$PROJECT)
WARFILE=$WARDIR/$PROJECT-r$REV.war

echo "Modifying $VERSIONFILE..."
sed -i "s/@PLACEHOLDER@/r$REV/g" $VERSIONFILE

echo "Cleaning and building workspace..."
$ECLIPSE --launcher.suppressErrors -nosplash -application org.eclipse.jdt.apt.core.aptBuild -data $WORKSPACE -vmargs $VMARGS 2>&1 | tee $TMPFILE

echo "Exporting $PROJECT to $WARFILE..."
$ECLIPSE --launcher.suppressErrors -nosplash -application in.cypal.studio.gwt.core.ExportWar -data $WORKSPACE -dest $WARFILE -project $PROJECT -vmargs $VMARGS 2>&1 | tee -a $TMPFILE

if grep "error" $TMPFILE; then
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
