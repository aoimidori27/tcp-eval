#!/bin/bash

[ "$RC_GOT_FUNCTIONS" != "yes" ] && source /usr/local/bin/functions.sh

SCRIPTNAME=$(basename $0)

EXIT_SUCCESS=0
EXIT_FAILURE=1
EXIT_ERROR=2

HW_WIFIDEV=wifi0
WIFIDEV=ath0
WLANMODE=adhoc
SSID=mcg-mesh
CHANNEL=1
TXPOWER=20
IPADDR=169.254.9.${HOSTNAME/mrouter/}/16


#
# Functions
#
loadmod() {
	if lsmod | grep ath_pci &>/dev/null; then
		einfo Madwifi is already loaded
	else
		ebegin Loading madwifi
		modprobe ath-pci autocreate=none
		eend $?
	fi
}

unloadmod() {
        ebegin Unloading madwifi
        rmmod ath-pci wlan-scan-sta ath-rate-sample wlan ath-hal
        eend $?
}

createdev() {
	ebegin Creating VAP in $WLANMODE mode
	WIFIDEV=`wlanconfig ath create wlandev $HW_WIFIDEV wlanmode $WLANMODE` &>/dev/null
	eend $?
}

killdev() {
        if ip link show $WIFIDEV &>/dev/null; then
                ebegin Destroying $WIFIDEV
                wlanconfig $WIFIDEV destroy &>/dev/null
                eend $?
        fi
}

ifup() {
        ebegin Bringing $WIFIDEV up
        ip link set $WIFIDEV up &>/dev/null && \
        ip addr flush dev $WIFIDEV &>/dev/null && \
        ip addr add $IPADDR dev $WIFIDEV &>/dev/null && \
        eend $?
}

setessid() {
	ebegin iwconfig $WIFIDEV essid $SSID
	iwconfig $WIFIDEV essid $SSID &>/dev/null
	eend $?
}

setchannel() {
        ebegin Setting channel on $WIFIDEV to $CHANNEL
        iwconfig $WIFIDEV channel $CHANNEL &>/dev/null
        eend $?
}

settxpower() {
        ebegin Setting txpower on $WIFIDEV to $TXPOWER dBm
        iwconfig $WIFIDEV txpower $TXPOWER &>/dev/null
        eend $?
}

usage() {
	LENGTH=`echo "Usage: $SCRIPTNAME" | wc -m`
	LENGTH=$(( LENGTH - 1 ))
	INDENTATION=$(printf "%${LENGTH}s" ' ')

	echo "Usage: $SCRIPTNAME loadmod | unloadmod | createdev [-w hwdev] [-m mode] | killdev [-d dev] |"
	echo "$INDENTATION ifup [-d dev] [-a addr] | setessid [-d dev] [-e essid] | setchannel [-d dev] [-c channel] |"
	echo "$INDENTATION settxpower [-d dev] [-x txpower] | autocreate"
	[ $# -eq 1 ]  && exit $1 || exit $EXIT_FAILURE
}

get_opt() {
	VALIDOPTS=$1 && shift
	while getopts "$VALIDOPTS" options
	do
		case $options in
			w) HW_WIFIDEV=$OPTARG;;
			d) WIFIDEV=$OPTARG;;
			e) WLANMODE=$OPTARG;;
			s) SSID=$OPTARG;;
			c) CHANNEL=$OPTARG;;
			x) TXPOWER=$OPTARG;;
			a) IPADDR=$OPTARG;;
			\?) echo "Unkown option \"-$OPTARG\"" && usage $EXIT_ERROR;;
			*)  echo "Option \"-$OPTARG\" requires an argument" && usage $EXIT_ERROR;;
		esac
	done
	shift $(( OPTIND - 1 ))
}


#
# The action
#
case "$1" in
	--help)		shift && get_opt "" "$@" && usage $EXIT_SUCCESS;;
	-h)		shift && get_opt "" "$@" && usage $EXIT_SUCCESS;;
        loadmod)	shift && get_opt "" "$@" && loadmod;;
        unloadmod)	shift && get_opt "" "$@" && unloadmod;;
        createdev)	shift && get_opt ":w:m:" "$@" && createdev;;
        killdev)	shift && get_opt ":d:"   "$@" && killdev;;
	ifup)		shift && get_opt ":d:a:" "$@" && ifup;;
	setessid)	shift && get_opt ":d:e:" "$@" && setessid;;
	setchannel)	shift && get_opt ":d:c:" "$@" && setchannel;;
	settxpower)	shift && get_opt ":d:x:" "$@" && settxpower;;
	autocreate)	shift && get_opt ":a:"   "$@" && loadmod && createdev && ifup && \
				setessid && setchannel && sleep 5 && settxpower;;
	*)		echo "Unkown function \"$*\"" && usage $EXIT_ERROR;;
esac
