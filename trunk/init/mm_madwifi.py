#!/usr/bin/python


# imports
import logging,sys,os,time, subprocess, time, optparse
from mm_application import Application
from logging import info, debug, warn, error
from mm_basic import *
from subprocess import Popen, PIPE



class Madwifi(Application):
	"Class to manage Subvserions repositories within those images"

	# member variables
	hwdevice = ''
	device   = ''
	address  = ''
	channel  = 0
	essid    = ''
	wlanmode = ''
	txpower  = 0
	action   = ''
	

	def __init__(self):
		super(Application, self);
		usage = "usage: %prog [options] COMMAND \n" \
				"where  COMMAND := { loadmod | unloadmod | createdev | killdev |" \
				"ifup |\n" \
				"                    ifdown | setessid | setchannel | settxpower }"
		self.parser.set_usage(usage)
		self.parser.set_defaults(addr = '169.254.9.1', channel = '1', dev = 'ath0',
								 essid = 'mcg-mesh', mode = 'adhoc', hwdev = 'wifi0',
								 txpower = '17')
		self.parser.add_option('-s', '--syslog',
						  action = 'store_true', dest = 'syslog',
						  help = 'log to syslog instead of stdout')
		self.parser.add_option('-v', '--verbose',
						  action = 'store_true', dest = 'verbose',
						  help = 'being more verbose')	
		self.parser.add_option('-a', '--addr', metavar = "IP",
						  action = 'store', dest = 'address',
						  help = 'define the IP address [default: %default]')				  
		self.parser.add_option('-c', '--chan', metavar = "NUM",
						  action = 'store', dest = 'channel',
						  help = 'define the wireless channel [default: %default]')
		self.parser.add_option('-d', '--dev',  metavar = "DEV",
						  action = 'store', dest = 'device',
						  help = 'define the device [default: %default]')	
		self.parser.add_option('-e', '--essid', metavar = "ID",
						  action = 'store', dest = 'essid',
						  help = "define the essid [default: %default]")
		self.parser.add_option('-m', '--mode', metavar = 'MODE',
						  action = 'store', dest = 'wlanmode',
						  help = "define the mode [sta|adhoc|ap|monitor|wds|"\
						  "ahdemo] \n [default: %default]")
		self.parser.add_option('-w', '--hwdev', metavar = "HW",
						  action = 'store', dest = 'hwdevice',
						  help = 'define the device [default: %default]')
		self.parser.add_option('-t', '--txpower', metavar = "TX",
						  action = 'store', dest = 'txpower',
						  help = 'define the TX-Power [default: %default]')


	def init(self,options,args):
		self.essid    = options.essid
		self.hwdevice = options.hwdevice
		self.device   = options.device
		self.address  = options.address
		self.channel  = options.channel
		self.essid    = options.essid
		self.wlanmode = options.wlanmode
		self.txpower  = options.txpower

		# correct numbers of arguments?
		if len(args) != 1:
			self.parser.error("incorrect number of arguments")
			
		# does the command exists?
		if not args[0] in ('loadmod', 'unloadmod', 'createdev', 'killdev' \
						   'ifup', 'ifdown', 'setessid', 'setchannel', \
						   'settxpower'):
			self.parser.error('unkown COMMAND %s' %(args[0]))
		else:
			self.action   = args[0]


	def setessid(self):
		print "Essid = %s" % self.essid

	# main method of application object
	def run(self):
		eval('self.%s()' %(self.action)) 


def main():
	myClass = Madwifi()
	myClass.start()
	

	
if __name__ == '__main__':
 	main()

