#!/bin/sh
ME=$0
if [ ! -n "$1" ]; then 
	echo "$ME runtime, e.g.: um_dump 4h"
	exit 0
fi

if [ "$(whoami)" != 'root' ]; then
        echo "Run $ME as root user."
        exit 1;
fi


DATE=`date +%x`
TIME=`date +%X`
RUNTIME=$1

# change this
CAPTURERULE="host buildserver and (tcp port 9001 or tcp port 443)"

[ -d /mnt/storage/measurement/$DATE ] || mkdir /mnt/storage/measurement/$DATE

echo "capturing packets..."
echo "capture rule is:  $CAPTURERULE"
tcpdump -i eth0 -s 0 -n -q -w /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-eth0.pcap " $CAPTURERULE " &
tcpdump -i eth1 -s 0 -n -q -w /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-eth1.pcap " $CAPTURERULE " &
sleep $RUNTIME 
killall tcpdump
echo "... completed"
sleep 2

echo "Merging capture files..."
mergecap /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-eth0.pcap /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-eth1.pcap -w /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-merged.pcap
echo "...finished"

sudo rm -f /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-eth0.pcap /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-eth1.pcap

echo "running tstat..."
mkdir /mnt/storage/measurement/$DATE/$TIME-$RUNTIME/tstat
/usr/local/bin/tstat -u -N /mnt/storage/measurement/tstat.networks -H /mnt/storage/measurement/tstat.histogramms -s /mnt/storage/measurement/$DATE/$TIME-$RUNTIME/tstat
echo "...finished"

chgrp -R users /mnt/storage/measurement/$DATE/
echo "sending result email..."

DUMPSIZE=`ls -oh /mnt/storage/measurement/$DATE/$TIME-$RUNTIME-merged.pcap`
TSTATDIR=`ls -oh /mnt/storage/measurement/$DATE/$TIME-$RUNTIME/tstat`
HOST=`/bin/hostname`
OBSERVEDHOSTS=`cat /mnt/storage/measurement/$DATE/$TIME-$RUNTIME/tstat/log_tcp_* | awk '{print $1}{print $45}' | sort -n | uniq | wc -l`

(
/bin/cat <<EOF
$ME finished capture job started at $DATE $TIME runtime: $RUNTIME on $HOST.

result is:

$DUMPSIZE

$TSTATDIR

observed $OBSERVEDHOSTS hosts.
-- 

EOF
}  2>&1 | /usr/bin/mailx -s "$ME finished capture jop started at $DATE $TIME runtime: $RUNTIME on $HOST" root
