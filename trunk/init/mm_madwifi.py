#!/usr/bin/python

#
# Imports
#
import os, logging, logging.handlers, sre, socket, sys, optparse, time
from logging import info, debug, warn, error
#from subprocess import Popen, PIPE


#
# Load module
#
#def loadmod():
#	cmd = 'lsmod'
#	prog = Popen(cmd, stdout = PIPE, shell = False)
#	sts = os.wait(prog.pid, 0)
#	
#	if sts:
#		warn('Madwifi is already loaded.')
#	else
#		info('Loading madwifi...')
#		command = 'modprobe'
#		args = 'ath-pci autocreate=none'
#		prog = Popen(command + arguments, stdout = PIPE, shell = False)
#		sts = os.wait(program.pid, 0)
#		
#		
#	command = 'lsmod | grep ath_pci &> /dev/null'
#
#
##
## Load unmodule
##
#def unloadmod():
#	info('Unloading madwifi...')
#	command = 'rmmod ath-pci wlan-scan-sta ath-rate-sample wlan ath-hal'
#	os.system(command)
#
#
##
## Create WLANDev
##
#def createdev():
#	info('Unloading madwifi...')
#	command = [wlanconfig ath create wlandev $HW_WIFIDEV wlanmode, '$WLANMODE']
#	output = Popen(["mycmd", "myarg"], stdout=PIPE).communicate()[0]
#	
#	WIFIDEV = `wlanconfig ath create wlandev $HW_WIFIDEV wlanmode $WLANMODE` &>/dev/null
#
#
#
#
#def killdev():
#	      if ip link show $WIFIDEV &>/dev/null; then
#                ebegin Destroying $WIFIDEV
#                wlanconfig $WIFIDEV destroy &>/dev/null
#                eend $?
#
#
#
#def ifup():
#        ebegin Bringing $WIFIDEV up
#        ip link set $WIFIDEV up &>/dev/null && \
#        ip addr flush dev $WIFIDEV &>/dev/null && \
#        ip addr add $IPADDR dev $WIFIDEV &>/dev/null && \
#        eend $?
#
#
#def setessid():
#	ebegin iwconfig $WIFIDEV essid $SSID
#	iwconfig $WIFIDEV essid $SSID &>/dev/null
#	eend $?
#
#
#def setchannel()
#        ebegin Setting channel on $WIFIDEV to $CHANNEL
#        iwconfig $WIFIDEV channel $CHANNEL &>/dev/null
#        eend $?
#
#
#def settxpower()
#        ebegin Setting txpower on $WIFIDEV to $TXPOWER dBm
#        iwconfig $WIFIDEV txpower $TXPOWER &>/dev/null
#        eend $?
#
#
#
#	echo "Usage: $SCRIPTNAME loadmod | unloadmod | createdev [-w hwdev] [-m mode] | killdev [-d dev] |"
#	echo "$INDENTATION ifup [-d dev] [-a addr] | setessid [-d dev] [-e essid] | setchannel [-d dev] [-c channel] |"
#	echo "$INDENTATION settxpower [-d dev] [-x txpower] | autocreate"


# main function
def main():
	# options parser
	usage = "usage: %prog [options] COMMAND \n\n" \
		    "COMMAND:= { loadmod | unloadmod | createdev | killdev | ifup |\n" \
		    "            ifdown | setessid | setchannel | settxpower }"    
	parser = optparse.OptionParser(usage)
	parser.set_defaults(addr = '169.254.9.1', channel = '1', dev = 'ath0',
						essid = 'mcg-mesh', mode = 'adhoc', hwdev = 'wifi0',
						txpower = '17')
	parser.add_option('-s', '--syslog',
					  action = 'store_true', dest = 'syslog',
					  help = 'log to syslog instead of stdout')
	parser.add_option('-v', '--verbose',
					  action = 'store_true', dest = 'verbose',
					  help = 'being more verbose')	
	parser.add_option('-a', '--addr', metavar="IP",
					  action = 'store', dest = 'addr',
					  help = 'define the IP address [default: %default]')				  
	parser.add_option('-c', '--chan', metavar="NUM",
					  action = 'store', dest = 'channel',
					  help = 'define the wireless channel [default: %default]')
	parser.add_option('-d', '--dev',  metavar="DEV",
					  action = 'store', dest = 'device',
					  help = 'define the device [default: %default]')	
	parser.add_option('-e', '--essid', metavar="ID",
					  action = 'store', dest = 'essid',
					  help = "define the essid [default: %default]")
	parser.add_option('-m', '--mode',
					  action = 'store', dest = 'mode',
					  help = "define the mode [sta|adhoc|ap|monitor|wds|"\
					         "ahdemo] \n [default: %default]")
	parser.add_option('-w', '--hwdev', metavar="HW",
					  action = 'store', dest = 'hwdev',
					  help = 'define the device [default: %default]')
	parser.add_option('-t', '--txpower', metavar="TX",
					  action = 'store', dest = 'txpower',
					  help = 'define the TX-Power [default: %default]')
	(options, args) = parser.parse_args()
	
	# correct numbers of arguments?
	if len(args) != 1:
		parser.error("incorrect number of arguments")

	# being verbose?
	if options.verbose:
		log_level = logging.INFO
	else:
		log_level = logging.WARN
#
#	# using syslog
#	if options.syslog:
#		syslog_facility = logging.handlers.SysLogHandler.LOG_DAEMON
#		syslog_host = ('logserver', 514)
#		syslog_format = parser.get_prog_name() + ' %(levelname)s: %(message)s'
#		syslog_Handler = logging.handlers.SysLogHandler(address = syslog_host,
#														facility = syslog_facility)
#		syslog_Handler.setFormatter(logging.Formatter(syslog_format))
#		logging.getLogger('').addHandler(syslog_Handler)
#		logging.getLogger('').setLevel(log_level)
#
#	# using standard logger
#	else:
#		log_format = '%(asctime)s %(levelname)s: %(message)s'
#		log_datefmt = '%b %d %H:%M:%S'
#		logging.basicConfig(level = log_level, format = log_format,
#							datefmt = log_datefmt)
#
#	# create database object
#	info('Create database object...')
#	database = Database()
#
#	# create interface list object and send the results to the database
#	info('Create interface list object...')
#	ifaces = InterfaceList.get_ifconfig()
#	database.send(ifaces, InterfaceList(), InterfaceList())
#
#	info('Entering endless loop...')
#	try:
#		while True:
#			# get new ifconfig's output and compare it with the old one
#			new_ifaces = InterfaceList.get_ifconfig()
#			(removed_ifaces, changed_ifaces) = ifaces.compare(new_ifaces)
#			(added_ifaces, changed_ifaces) = new_ifaces.compare(ifaces)
#
#			# something change?
#			if not added_ifaces.empty() or not removed_ifaces.empty() \
#			   or not changed_ifaces.empty():
#
#				# send changes to database
#				if not added_ifaces.empty():
#					info('Ifconfig changed. Added ifaces: %s' %(added_ifaces))
#				if not removed_ifaces.empty():
#					info('Ifcondig changed. Removed ifaces: %s' %(removed_ifaces))
#				if not changed_ifaces.empty():
#					info('Ifconfig changed. Changed ifaces: %s' %(changed_ifaces))
#				database.send(added_ifaces, removed_ifaces, changed_ifaces)
#
#			# update interface list
#			ifaces = new_ifaces
#
#			# sleep for a while
#			time.sleep(options.time)
#
#	except KeyboardInterrupt:
#		info('Aborted...')
#


if __name__ == '__main__':
	main()