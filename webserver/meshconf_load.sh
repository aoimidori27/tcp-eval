#!/bin/sh

PROJECT=MeshConf
DEPLOYPATH=/var/lib/tomcat5/webapps/$PROJECT
WARPATH=vmeshhost1:/mnt/localscratch/eclipse-build/build/

function usage ()
{
    this=`basename $0`
    cat <<!EOF!
usage: $this [options] revision
Loads the specified revision into the tomcat server.
options:
      -h        Print this help summary and exit.
      -v        Be more verbose.

!EOF!
}


# check if root
if [ $UID -ne 0 ]; then
    echo "You are not root."
    echo "Try sudo $0 instead."
    exit 1;
fi;


#parse optional arguments
getopts vh FLAG
if [ "$?" -ne 0 ]; then
    FLAG="null"
fi

VERBOSE=n
case $FLAG in
    "v")
        VERBOSE=y; shift ;;
    "h")
        usage; exit 0;;
esac

# if there is no image argument, print usage and exit
REVISION=$1;
if [ -z $REVISION ]; then
    echo "You have to specify a revision."
    usage; exit 1;
fi

WARFILE=$PROJECT-r${REVISION}.war

su eclipse-build -c "scp $WARPATH/$WARFILE ${DEPLOYPATH}.war"
rm -rf $DEPLOYPATH
/etc/init.d/tomcat5 restart
echo "It may take the tomcat server a while to start up, please be patient."
