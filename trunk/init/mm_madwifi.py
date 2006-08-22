#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys, os, optparse
from logging import info, debug, warn, error
from subprocess import Popen, PIPE

# mcg-mesh imports
from mm_basic import *
from mm_application import Application


class Madwifi(Application):
	"Class to handle madwifi-ng"


	def __init__(self):
		"Constructor of the object"
	
		# call the super constructor
		Application.__init__(self)
	
		# object variables (set the default for the option parser)
		self.hwdevice = "wifi0"
		self.device   = "ath0"
		self.address  = "169.254.9.1"
		self.channel  = 0
		self.essid    = "mcg-mesh"
		self.wlanmode = "adhoc"
		self.txpower  = 17

		# initialization of the option parser
		usage = "usage: %prog [options] COMMAND \n" \
				"where  COMMAND := { loadmod | unloadmod | createdev | " \
				"killdev | ifup |\n" \
				"                    ifdown | setessid | setchannel | settxpower }"
		self.parser.set_usage(usage)
		self.parser.set_defaults(addr = self.hwdevice, channel = self.channel,
								 dev = self.device, essid = self.essid,
								 mode = self.wlanmode, hwdev = self.hwdevice,
								 txpower = self.txpower)
		self.parser.add_option("-a", "--addr", metavar = "IP",
						  action = "store", dest = "address",
						  help = "define the IP address [default: %default]")				  
		self.parser.add_option("-c", "--chan", metavar = "NUM",
						  action = "store", dest = "channel",
						  help = "define the wireless channel [default: %default]")
		self.parser.add_option("-d", "--dev",  metavar = "DEV",
						  action = "store", dest = "device",
						  help = "define the device [default: %default]")	
		self.parser.add_option("-e", "--essid", metavar = "ID",
						  action = "store", dest = "essid",
						  help = "define the essid [default: %default]")
		self.parser.add_option("-m", "--mode", metavar = "MODE",
						  action = "store", dest = "wlanmode",
						  help = "define the mode [sta|adhoc|ap|monitor|wds|"\
						  		 "ahdemo] \n [default: %default]")
		self.parser.add_option("-w", "--hwdev", metavar = "HW",
						  action = "store", dest = "hwdevice",
						  help = "define the device [default: %default]")
		self.parser.add_option("-t", "--txpower", metavar = "TX",
						  action = "store", dest = "txpower",
						  help = "define the TX-Power [default: %default]")


	def init(self):
		"Initialization of the object"
		
		# call the super constructor
		Application.init(self)

		self.hwdevice = self.options.hwdevice
		self.device   = self.options.device
		self.address  = self.options.address
		self.channel  = self.options.channel
		self.essid    = self.options.essid
		self.wlanmode = self.options.wlanmode
		self.txpower  = self.options.txpower

		# correct numbers of arguments?
		if len(self.args) != 1:
			self.parser.error("incorrect number of arguments")
			
		# does the command exists?
		if not self.args[0] in ("loadmod", "unloadmod", "createdev", "killdev" \
						   		"ifup", "ifdown", "setessid", "setchannel", \
						   		"settxpower"):
			parser.error("unkown COMMAND %s" %(self.args[0]))
	

	def loadmod(self):
		"Loading madwifi-ng driver"
	
#		if lsmod | grep ath_pci &>/dev/null; then
#			warnig("Madwifi-ng is already loaded")
#		else
#			info("Loading madwifi-ng driver")
#			modprobe ath-pci autocreate=none
#		fi

	
	def unloadmod(self):
		"Loading madwifi-ng driver"
		
		info("Unloading madwifi-ng")
#		rmmod ath-pci wlan-scan-sta ath-rate-sample wlan ath-hal

		
	def createdev(self):
		"Creating VAP in the desired mode"
	
		info("Creating VAP in %s mode" %(self.wlanmode))
#		WIFIDEV=`wlanconfig ath create wlandev $HW_WIFIDEV wlanmode $WLANMODE` &>/dev/null



	def killdev(self):
		"Destroying VAP"
	
#		if ip link show $WIFIDEV &>/dev/null; then
#			info("Destroying VAP %s" %(self.device))
#			wlanconfig $WIFIDEV destroy &>/dev/null
#		else
#			warnig("VAP %s does not exist" %(self.device))
#		fi


	def ifup(self):
		"Bring the network interface up"
		
		info("Bring %s up" %(self.device))
#		ip link set $WIFIDEV up &>/dev/null && \
#		ip addr flush dev $WIFIDEV &>/dev/null && \
#		ip addr add $IPADDR dev $WIFIDEV &>/dev/null && \


	def ifdown(self):
		"Take a network interface down"
		
		info("Take %s down" %(self.device))

	
	def setessid(self):
		"Set the ESSID of desired device"
	
		info("Setting essid on %s to %s" %(self.device, self.essid))
#		iwconfig $WIFIDEV essid $SSID &>/dev/null

		
	def setchannel(self):
		"Set the WLAN channel of desired device"
		
		info("Setting channel on %s to %s" %(self.device, self.channel))
#		iwconfig $WIFIDEV channel $CHANNEL &>/dev/null


	def settxpower(self):
		"Set the TX-Power of desired device"
		
		info("Setting txpower on %s to %s dBm" %(self.device, self.txpower))
#		iwconfig $WIFIDEV txpower $TXPOWER &>/dev/null


	def run(self):
		"Main method of the madwifi object"
	
		eval("self.%s()" %(self.args[0])) 



# main function
def main():
	madwifi = Madwifi()
	madwifi.init()
	madwifi.run()
	

	
if __name__ == "__main__":
 	main()
