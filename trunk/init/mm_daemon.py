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
		self.piddir      = "/var/run"

		# initialization of the option parser
		usage = "usage: %prog [options] PROGRAM COMMAND \n" \
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
		"Set options"
		
		# call the super set_option method
		super(Daemon, self).set_option()
		
		# correct numbers of arguments?
		if len(self.args) != 2:
			self.parser.error("incorrect number of arguments")

		self.piddir      = self.options.piddir
		self.daemon_opts = self.options.daemon_opts
		self.program     = self.args[0]
		self.action      = self.args[1]

		# does the command exists?
		if not self.action in ("start", "stop", "restart"):
			self.parser.error("unkown COMMAND %s" %(self.action))


	def start(self):
		"Starting the program as a daemon"

		info("Starting %s " %(self.program))
		pidfile = "%s/%s.pid" %(self.piddir, self.program)
		retcode = subprocess.call(["start-stop-daemon", \
								   "--start --make-pidfile --pidfile ", \
								   pidfile, "--background --startas ", \
								   self.program, "--", self.daemon_opts], \
								  shell = True)
		if retcode < 0:
			error("Starting %s as a daemon was unsuccessful" %(self.program))

		
	def stop(self):
		"Stopping the daemon"

		info("Stopping %s " %(self.program))
		pidfile = "%s/%s.pid" %(self.piddir, self.program)
		retcode = subprocess.call(["start-stop-daemon", \
								   "--stop --pidfile ", pidfile], \
								  shell = True)
		if retcode < 0:
			error("Stopping the daemon %s was unsuccessful" %(self.program))
		

	def restart(self):
		"Restarting the daemon"

		self.stop()
		self.start()


	def main(self):
		"Main method of the madwifi object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		eval("self.%s()" %(self.action)) 



if __name__ == "__main__":
	Daemon()