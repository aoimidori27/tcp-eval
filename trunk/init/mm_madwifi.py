#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess
from logging import info, debug, warn, error
 
# mcg-mesh imports
from mm_application import Application


class Madwifi(Application):
	"Class to handle madwifi-ng"


	def __init__(self):
		"Constructor of the object"
	
		# call the super constructor
		super(Madwifi, self).__init__()
	
		# object variables (set the defaults for the option parser)
		self.hwdevice = "wifi0"
		self.device   = "ath0"
		self.address  = "169.254.9.1"
		self.channel  = 0
		self.essid    = "mcg-mesh"
		self.wlanmode = "ahdemo"
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
		
		# execute object
		self.main()


	def set_option(self):
		"Set options"
		
		# call the super set_option method
		super(Madwifi, self).set_option()
		
		# correct numbers of arguments?
		if len(self.args) != 1:
			self.parser.error("incorrect number of arguments")

		self.hwdevice = self.options.hwdevice
		self.device   = self.options.device
		self.address  = self.options.address
		self.channel  = self.options.channel
		self.essid    = self.options.essid
		self.wlanmode = self.options.wlanmode
		self.txpower  = self.options.txpower
		self.action   = self.args[0]

		# does the command exists?
		if not self.action in ("loadmod", "unloadmod", "createdev", "killdev" \
						   	   "ifup", "ifdown", "setessid", "setchannel", \
						   	   "settxpower"):
			self.parser.error("unkown COMMAND %s" %(self.action))
	

	def loadmod(self):
		"Loading madwifi-ng driver"

		prog1 = subprocess.Popen(["lsmod"], stdout = subprocess.PIPE)
		prog2 = subprocess.Popen(["grep", "ath-pci"],
								 stdin = prog1.stdout, stdout = subprocess.PIPE)
		(stdout, stderr) = prog2.communicate()
	
		if stdout == "":
			info("Loading madwifi-ng driver...")
			retcode = subprocess.call(["modprobe", "ath-pci", \
									   "autocreate=none"], shell = True)
			if retcode < 0:
				error("Loading madwifi-ng driver was unsuccessful")
		else:
			warn("Madwifi-ng is already loaded")

	
	def unloadmod(self):
		"Loading madwifi-ng driver"

		prog1 = subprocess.Popen(["lsmod"], stdout = subprocess.PIPE)
		prog2 = subprocess.Popen(["grep", "ath-pci"], 
								 stdin = prog1.stdout, stdout = subprocess.PIPE)
		(stdout, stderr) = prog2.communicate()

		if not stdout == "":
			info("Unloading madwifi-ng")
			retcode = subprocess.call(["rmmod", "ath-pci wlan-scan-sta " \
									   "ath-rate-sample wlan ath-hal"], \
									  shell = True)
			if retcode < 0:
				error("Unloading madwifi-ng driver was unsuccessful")
		else:
			warn("Madwifi-ng is not loaded")

		
	def createdev(self):
		"Creating VAP in the desired mode"
	
		info("Creating VAP in %s mode" %(self.wlanmode))
		retcode = subprocess.call(["wlanconfig", self.device, "create wlandev", \
								   self.hwdevice, "wlanmode", self.wlanmode], \
								  shell = True)
		if retcode < 0:
			error("Unloading madwifi-ng driver was unsuccessful")


	def killdev(self):
		"Destroying VAP"

		prog = subprocess.Popen(["ip", "link show", self.device], \
								stdout = subprocess.PIPE)
		(stdout, stderr) = prog.communicate()

		if not stdout == "":
			info("Destroying VAP %s" %(self.device))
			retcode = subprocess.call(["wlanconfig", self.device, "destroy"], \
									  shell = True)
			if retcode < 0:
				error("Destroying VAP %s was unsuccessful" %(self.device))
		else:
			warn("VAP %s does not exist" %(self.device))


	def ifup(self):
		"Bring the network interface up"

		prog = subprocess.Popen(["ip", "link show", self.device], \
								stdout = subprocess.PIPE)
		(stdout, stderr) = prog.communicate()

		if not stdout == "":
			info("Bring VAP %s up" %(self.device))
			retcode1 = subprocess.call(["ip", "link set", self.device, "up"], \
									   shell = True)
			retcode2 = subprocess.call(["ip", "addr flush dev", self.device],
									   shell = True)
			retcode3 = subprocess.call(["ip", "addr add", self.address, "dev",
										"self.device"], shell = True)
			if retcode1 < 0 or retcode2 < 0 or retcode3 < 0:
				error("Bring VAP %s up was unsuccessful" %(self.device))
		else:
			warn("VAP %s does not exist" %(self.device))


	def ifdown(self):
		"Take a network interface down"
		
		info("Take %s down" %(self.device))

	
	def setessid(self):
		"Set the ESSID of desired device"

		prog = subprocess.Popen(["ip", "link show", self.device], \
								stdout = subprocess.PIPE)
		(stdout, stderr) = prog.communicate()

		if not stdout == "":
			info("Setting essid on %s to %s" %(self.device, self.essid))
			retcode = subprocess.call(["iwconfig", self.device, "essid", \
									  self.essid], shell = True)
			if retcode < 0:
				error("Setting essid on %s to %s was unsuccessful" \
					  %(self.device, self.essid))
		else:
			warn("VAP %s does not exist" %(self.device))
	
		
	def setchannel(self):
		"Set the WLAN channel of desired device"

		prog = subprocess.Popen(["ip", "link show", self.device], \
								stdout = subprocess.PIPE)
		(stdout, stderr) = prog.communicate()

		if not stdout == "":
			info("Setting channel on %s to %s" %(self.device, self.channel))
			retcode = subprocess.call(["iwconfig", self.device, "channel", \
									  self.channel], shell = True)
			if retcode < 0:
				error("Setting channel on %s to %s was unsuccessful" \
					  %(self.device, self.channel))
		else:
			warn("VAP %s does not exist" %(self.device))
		

	def settxpower(self):
		"Set the TX-Power of desired device"

		prog = subprocess.Popen(["ip", "link show", self.device], \
								stdout = subprocess.PIPE)
		(stdout, stderr) = prog.communicate()

		if not stdout == "":
			info("Setting txpower on %s to %s dBm" %(self.device, self.txpower))
			retcode = subprocess.call(["iwconfig", self.device, "txpower", \
									  self.txpower], shell = True)
			if retcode < 0:
				error("Setting txpower on %s to %s dBm was unsuccessful"
					  %(self.device, self.txpower))
		else:
			warn("VAP %s does not exist" %(self.device))

		
	def main(self):
		"Main method of the madwifi object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		eval("self.%s()" %(self.action)) 



if __name__ == "__main__":
	Madwifi()