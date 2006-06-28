#!/bin/bash

[ "$RC_GOT_FUNCTIONS" != "yes" ] && source /usr/local/bin/functions.sh

SCRIPTNAME=$(basename $0)
SCRIPTDIR="/usr/local/bin"

# which scripts should be started
AUTOSTART="boot ifconfig iwconfig ipmonitor"
OPTS="-v --syslog"


PIDDIR="/var/run"

EXIT_SUCCESS=0
EXIT_FAILURE=1
EXIT_ERROR=2

export PGDATABASE="mcg-mesh"
export PGUSER="meshnode"
export PGHOST="meshserver"

#
# Functions
#
usage() {
	LENGTH=`echo "Usage: $SCRIPTNAME" | wc -m`
	LENGTH=$(( LENGTH - 1 ))
	INDENTATION=$(printf "%${LENGTH}s" ' ')

	echo "Usage: $SCRIPTNAME start | stop" 
	[ $# -eq 1 ]  && exit $1 || exit $EXIT_FAILURE
}


#
# The action
#
case "$1" in
	start)
		for script in $AUTOSTART; do
			ebegin Starting $script
				start-stop-daemon --start --make-pidfile --pidfile $PIDDIR/2db_$script.pid --background --startas $SCRIPTDIR/2db_$script.py -- $OPTS
			eend $?
		done
		;;

	stop)
		for script in $AUTOSTART; do
			ebegin Stopping $script
				start-stop-daemon --stop --pidfile $PIDDIR/2db_$script.pid
 			eend $?
		done
		;;
		
	*)
		usage $EXIT_ERROR;;
esac
