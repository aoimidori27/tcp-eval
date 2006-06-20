#!/bin/sh

DEFAULT_GROUP=mcg-mesh

# func_usage
# outputs to stdout the --help usage message.
func_usage ()
{
  echo "\
Usage: $0 PATH [GROUP]

Change the group of all .svn directories recursivly in the given path.

Arguments:
       PATH            path to examine
       GROUP           group to change ownership to [$DEFAULT_GROUP]

Example:
 $0 /opt/mcg-mesh mcg-mesh
"
}


if [ -z $1 ]; then func_usage; exit 0; fi;
if [ -z $2 ]; then 
 NGROUP="mcg-mesh"; 
else 
 NGROUP=$2;
fi;

for i in `find $1 -name 2>/dev/null .svn`; do
  chgrp -R $NGROUP $i
  chmod -R g+w $i
done

exit 0;
