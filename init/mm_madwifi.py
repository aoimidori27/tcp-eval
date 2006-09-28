#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess, re
from logging import info, debug, warn, error
 
# mcg-mesh imports
from mm_application import Application
from mm_util import *
from mm_cfg  import *

class Madwifi(Application):
	"Class to handle madwifi-ng"


	def __init__(self):
		"Constructor of the object"
	
		# call the super constructor
		Application.__init__(self)
	
		# object variables (set the defaults for the option parser)
		self.hwdevice = "wifi0"
		self.device   = "ath0"
		self.address  = "169.254.9.1"
		self.channel  = 1
		self.essid    = "mcg-mesh"
		self.wlanmode = "ahdemo"
		self.txpower  = 20
		self.antenna  = 2

		# initialization of the option parser
		usage = "usage: %prog [options] COMMAND \n" \
				"where  COMMAND := { loadmod | unloadmod | createdev | " \
				"killdev | ifup |\n" \
				"                    ifdown | setessid | setchannel | " \
				"settxpower | setantenna | autocreate }"
		self.parser.set_usage(usage)
		self.parser.set_defaults(address  = self.hwdevice,
								 channel  = self.channel,
								 device   = self.device,
								 essid    = self.essid,
								 wlanmode = self.wlanmode,
								 hwdevice = self.hwdevice,
								 txpower  = self.txpower,
								 antenna  = self.antenna)
		
		
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
		self.parser.add_option("-z", "--ant", metavar = "ANT",
							   action = "store", dest = "antenna", type = int,
							   help = "define antenna for transmit and receive"\
							   "\n [default: %default]")
							   
		
		# execute object
		self.main()


	def set_option(self):
		"Set options"
		
		# call the super set_option method
		Application.set_option(self)
		
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
		if not self.action in ("loadmod", "unloadmod", "createdev", "killdev",
						   	   "ifup", "ifdown", "setessid", "setchannel", 
						   	   "settxpower","setantenna","autocreate"):
			self.parser.error("unknown COMMAND %s" %(self.action))
	

	def loadmod(self):
		"Loading madwifi-ng driver"

		prog1 = subprocess.Popen(["lsmod"], stdout = subprocess.PIPE)
		prog2 = subprocess.Popen(["grep", "ath_pci"],
								 stdin = prog1.stdout, stdout = subprocess.PIPE)
		(stdout, stderr) = prog2.communicate()
	
		if stdout == "":
			info("Loading madwifi-ng driver...")
			try:
				call(["modprobe", "ath-pci","autocreate=none"],
					 shell = False)
			except CommandFailed:
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
		cmd = ("wlanconfig",self.device, "create", "wlandev", \
			   self.hwdevice, "wlanmode", self.wlanmode)
		info(cmd)
		try:
			stderr = execute(cmd, shell = False)[1]
		except CommandFailed:
			error("Creating %s was unsuccessful" % self.device)


	def killdev(self):
		"Destroying VAP"

		if self.deviceexists():
			info("Destroying VAP %s" %(self.device))
			try:
				call(["wlanconfig", self.device, "destroy"], \
					 shell = False)
			except CommandFailed:
				error("Destroying VAP %s was unsuccessful" %(self.device))
		else:
			warn("VAP %s does not exist" %(self.device))


	def ifup(self):
		"Bring the network interface up"

		if self.deviceexists():
			info("Bring VAP %s up" %(self.device))
			try:
				call(["ip", "link","set", self.device, "up"], \
					 shell = False)
				call(["ip", "addr","flush","dev", self.device],
					 shell = False)
				call(["ip", "addr","add", self.address, "dev", self.device],
					 shell = False)
			except CommandFailed:
				error("Bring VAP %s up was unsuccessful" %(self.device))
		else:
			warn("VAP %s does not exist" %(self.device))


	def ifdown(self):
		"Take a network interface down"

		if self.deviceexists():
			info("Take VAP %s down" %(self.device))
			try:
				call(["ip", "link","set", self.device, "down"], 
					 shell = False)
				call(["ip", "addr","flush","dev", self.device],
					 shell = False)
			except CommandFailed:
				error("Take VAP %s down was unsuccessful" %(self.device))
		else:
			warn("VAP %s does not exist" %(self.device))
		
	
	def setessid(self):
		"Set the ESSID of desired device"

		if self.deviceexists():
			info("Setting essid on %s to %s" %(self.device, self.essid))
			try:
				call(["iwconfig", self.device, "essid", 
					  self.essid], shell = False)
			except CommandFailed:
				error("Setting essid on %s to %s was unsuccessful" \
					  %(self.device, self.essid))
		else:
			warn("VAP %s does not exist" %(self.device))
	
		
	def setchannel(self):
		"Set the WLAN channel of desired device"

		if self.deviceexists():
			info("Setting channel on %s to %s" %(self.device, self.channel))
			try:
				call(("iwconfig", self.device, "channel", 
					  self.channel), shell = False)
			except CommandFailed:
				error("Setting channel on %s to %s was unsuccessful" \
					  %(self.device, self.channel))
		else:
			warn("VAP %s does not exist" %(self.device))
		

	def settxpower(self):
		"Set the TX-Power of desired device"

		if self.deviceexists():
			info("Setting txpower on %s to %s dBm" %(self.device, self.txpower))
			try:
				call(["iwconfig", self.device, "txpower",
					  self.txpower.__str__()], shell = False)
			except CommandFailed:
				error("Setting txpower on %s to %s dBm was unsuccessful"
					  %(self.device, self.txpower))
		else:
			warn("VAP %s does not exist" %(self.device))


	def setantenna(self):
		"Set the antenna of desired device"

		try:
			info("Setting tx/rx-antenna to %d" % self.antenna)
			call("echo 0 > /proc/sys/dev/%s/diversity" % (self.hwdevice),
				 shell = True)
			call("echo %d > /proc/sys/dev/%s/txantenna" % (self.antenna,self.hwdevice),
				 shell = True)
			call("echo %d > /proc/sys/dev/%s/rxantenna" % (self.antenna,self.hwdevice),
				 shell = True)
		except CommandFailed:
			error("Setting tx/rx-antenna to %d was unsuccessful" % self.antenna)
	


	def deviceexists(self):
		cmd = ("ip","link","show",self.device)
		(stdout, stderr) = execute(cmd,shell=False,raiseError=False)
		return stdout != ""


	def autocreate(self):
		self.loadmod()
		for hwdevice,i in wlaninfos.iteritems():
			self.hwdevice = hwdevice
			self.device   = i["device"]
			self.channel  = i["channel"]
			self.address  = re.sub("\$NODENR",
								   getnodenr().__str__(),
								   i["address"])
			self.wlanmode = i["wlanmode"]
			self.antenna  = i["antenna"]
			self.txpower  = i["txpower"]
			self.essid    = i["essid"]
			self.createdev()
			self.setchannel()
			self.setessid()
			self.setantenna()
			self.ifup()
			self.settxpower()
		

		
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