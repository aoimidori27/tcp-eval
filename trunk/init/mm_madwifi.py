#!/usr/bin/python

# imports
import os, logging, logging.handlers, sre, socket, sys, optparse, time
from logging import info, debug, warn, error
from subprocess import Popen, PIPE


# class for the database
class Madwifi(object):
	# global variables
	address	= 'mcg-mesh'
	channel      = 'node.iwconfig'
	device       = 'meshserver'
	essid       = 'meshnode'
	mode     = 5
	hwdevice     = 2
	txpower      = 0

		
	def __init__(self, hwdevice, device, address, channel, essid, mode, address, txpower):
		self.hwdevice = hwdevice
		self.address = device
		self.channel = address
		self.device
		self.hwdevice
		self.
		

# Load module
def loadmod(options):
#	cmd = 'lsmod'
#	prog = Popen(cmd, stdout = PIPE, shell = False)
#	sts = os.wait(prog.pid, 0)
	
	if sts:
		warn('Madwifi is already loaded.')
	else:
		info('Loading madwifi...')
#		command = 'modprobe'
#		args = 'ath-pci autocreate=none'
#		prog = Popen(command + arguments, stdout = PIPE, shell = False)
#		sts = os.wait(program.pid, 0)	
#	command = 'lsmod | grep ath_pci &> /dev/null'


# Load unmodule
def unloadmod(options):
	info('Unloading madwifi...')
#	command = 'rmmod ath-pci wlan-scan-sta ath-rate-sample wlan ath-hal'
#	os.system(command)


# Create WLANDev
def createdev(options):
	info('Creating VAP in %s mode' %(options.mode))
#	command = [wlanconfig ath create wlandev $HW_WIFIDEV wlanmode, '$WLANMODE']
#	output = Popen(["mycmd", "myarg"], stdout=PIPE).communicate()[0]
#	
#	WIFIDEV = `wlanconfig ath create wlandev $HW_WIFIDEV wlanmode $WLANMODE` &>/dev/null


def killdev(options):
	print 'killdev'
#   if ip link show $WIFIDEV &>/dev/null; then
#		ebegin Destroying $WIFIDEV
#       wlanconfig $WIFIDEV destroy &>/dev/null


def ifup(options):
	print 'ifup'
#   ebegin Bringing $WIFIDEV up
#   ip link set $WIFIDEV up &>/dev/null && \
#   ip addr flush dev $WIFIDEV &>/dev/null && \
#   ip addr add $IPADDR dev $WIFIDEV &>/dev/null && \


def setessid(options):
	print 'setessid'
#	ebegin iwconfig $WIFIDEV essid $SSID
#	iwconfig $WIFIDEV essid $SSID &>/dev/null



def setchannel(options):
	print 'setchannel'
#   ebegin Setting channel on $WIFIDEV to $CHANNEL
#   iwconfig $WIFIDEV channel $CHANNEL &>/dev/null



def settxpower(options):
	print 'settxpower'
#   ebegin Setting txpower on $WIFIDEV to $TXPOWER dBm
#   iwconfig $WIFIDEV txpower $TXPOWER &>/dev/null



# main function
def main():
	# options parser
	usage = "usage: %prog [options] COMMAND \n" \
		    "where  COMMAND := { loadmod | unloadmod | createdev | killdev |" \
								"ifup |\n" \
		    "                    ifdown | setessid | setchannel | settxpower }"    
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
	parser.add_option('-a', '--addr', metavar = "IP",
					  action = 'store', dest = 'addr',
					  help = 'define the IP address [default: %default]')				  
	parser.add_option('-c', '--chan', metavar = "NUM",
					  action = 'store', dest = 'channel',
					  help = 'define the wireless channel [default: %default]')
	parser.add_option('-d', '--dev',  metavar = "DEV",
					  action = 'store', dest = 'device',
					  help = 'define the device [default: %default]')	
	parser.add_option('-e', '--essid', metavar = "ID",
					  action = 'store', dest = 'essid',
					  help = "define the essid [default: %default]")
	parser.add_option('-m', '--mode',
					  action = 'store', dest = 'mode',
					  help = "define the mode [sta|adhoc|ap|monitor|wds|"\
					         "ahdemo] \n [default: %default]")
	parser.add_option('-w', '--hwdev', metavar = "HW",
					  action = 'store', dest = 'hwdev',
					  help = 'define the device [default: %default]')
	parser.add_option('-t', '--txpower', metavar = "TX",
					  action = 'store', dest = 'txpower',
					  help = 'define the TX-Power [default: %default]')
	(options, args) = parser.parse_args()
	
	# correct numbers of arguments?
	if len(args) != 1:
		parser.error("incorrect number of arguments")
   	
	# does the command exists?
	if not args[0] in ('loadmod', 'unloadmod', 'createdev', 'killdev' \
					   'ifup', 'ifdown', 'setessid', 'setchannel', \
					   'settxpower'):
		parser.error('unkown COMMAND %s' %(args[0]))

	# being verbose?
	if options.verbose:
		log_level = logging.INFO
	else:
		log_level = logging.WARN

	# using syslog
	if options.syslog:
		syslog_facility = logging.handlers.SysLogHandler.LOG_DAEMON
		syslog_host = ('logserver', 514)
		syslog_format = parser.get_prog_name() + ' %(levelname)s: %(message)s'
		syslog_Handler = logging.handlers.SysLogHandler(address = syslog_host,
														facility = syslog_facility)
		syslog_Handler.setFormatter(logging.Formatter(syslog_format))
		logging.getLogger('').addHandler(syslog_Handler)
		logging.getLogger('').setLevel(log_level)

	# using standard logger
	else:
		log_format = '%(asctime)s %(levelname)s: %(message)s'
		log_datefmt = '%b %d %H:%M:%S'
		logging.basicConfig(level = log_level, format = log_format,
							datefmt = log_datefmt)

	print options.mode

	# call appropriate function
	eval('%s(%s)' %(args[0], options))


if __name__ == '__main__':
	main()