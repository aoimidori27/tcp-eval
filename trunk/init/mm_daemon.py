#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess
from logging import info, debug, warn, error

# mcg-mesh imports
from mm_application import Application


class Daemon(Application):
	"Class to start MCG-Mesh programms as daemons"


	def __init__(self):
		"Constructor of the object"
	
		# call the super constructor
		super(Daemon, self).__init__()
	
		# object variables (set the defaults for the option parser)
		self.daemon_opts = "-v -s"
		self.piddir      = "/usr/local/bin"

		# initialization of the option parser
		usage = "usage: %prog [options] COMMAND \n" \
				"where  COMMAND := { start | stop | restart  }"
		self.parser.set_usage(usage)
		self.parser.set_defaults(daemon_opts = self.daemon_opts, \
								 piddir = self.piddir)
		self.parser.add_option("-o", "--opts", metavar = "OPTS",
						  action = "store", dest = "daemon_opts",
						  help = "define the PID directory [default: %default]")
		self.parser.add_option("-p", "--pid", metavar = "PID",
						  action = "store", dest = "piddir",
						  help = "define the PID directory [default: %default]")
		
		# execute object
		self.main()


	def set_option(self):
		"set options"
		
		# call the super set_option method
		super(Madwifi, self).set_option()
		
		# correct numbers of arguments?
		if len(self.args) != 1:
			self.parser.error("incorrect number of arguments")

		self.piddir      = self.options.piddir
		self.daemon_opts = self.options.daemon_opts
		self.action      = self.args[0]

		# does the command exists?
		if not self.action in ("start", "stop", "restart"):
			self.parser.error("unkown COMMAND %s" %(self.action))


	def start(self):
		"Set the ESSID of desired device"

#		for program in $AUTOSTART:
			info("Starting %s " %(program))
			pidfile = "%s/%s.pid" %(self.piddir, program)
			retcode = subprocess.call(["start-stop-daemon", \
									   "--start --make-pidfile --pidfile ", \
									   pidfile, "--background --startas ", \
									   program, "--", self.daemon_opts], \
								  shell = True)
		if retcode < 0:
			error("Unloading madwifi-ng driver was unsuccessful")

#		for script in $AUTOSTART; do
#			ebegin Starting $script
#				start-stop-daemon --start --make-pidfile --pidfile $PIDDIR/2db_$script.pid --background --startas $SCRIPTDIR/2db_$script.py -- $OPTS
#			eend $?
#		done
	
		
	def stop(self):
		"Set the WLAN channel of desired device"

		prog = subprocess.Popen(["ip", "link show", self.device], stdout = subprocess.PIPE)
		(stdout, stderr) = prog.communicate()

		if not stdout == "":
			info("Setting channel on %s to %s" %(self.device, self.channel))
			retcode = subprocess.call(["iwconfig", self.device, "channel", self.channel], shell = True)
			if retcode < 0:
				error("Setting channel on %s to %s was unsuccessful" %(self.device, self.channel))
		else:
			warn("VAP %s does not exist" %(self.device))

#		for script in $AUTOSTART; do
#			ebegin Stopping $script
#				start-stop-daemon --stop --pidfile $PIDDIR/2db_$script.pid
# 			eend $?
#		done		

	def restart(self):
		"Set the TX-Power of desired device"

		prog = subprocess.Popen(["ip", "link show", self.device], stdout = subprocess.PIPE)
		(stdout, stderr) = prog.communicate()

		if not stdout == "":
			info("Setting txpower on %s to %s dBm" %(self.device, self.txpower))
			retcode = subprocess.call(["iwconfig", self.device, "txpower", self.txpower], shell = True)
			if retcode < 0:
				error("Setting txpower on %s to %s dBm was unsuccessful" %(self.device, self.txpower))
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
	madwifi = Daemon()




# which scripts should be started
AUTOSTART="ifconfig iwconfig ipmonitor"
OPTS="-v --syslog"