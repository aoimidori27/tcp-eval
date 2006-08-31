#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess, sys, re
from logging import info, debug, warn, error
from socket import gethostname

# mcg-mesh imports
import mm_util
from mm_application import Application
from mm_cfg import *


# class to start MCG-Mesh programms

class Init(Application):
	"Class to start MCG-Mesh programms as daemons"

	
	def __init__(self):
		"Constructor of the object"
	
		# call the super constructor
		Application.__init__(self)

		# object variables (set the defaults for the option parser)

		self.parser.set_defaults(verbose = True,
								 syslog  = False,
								 debug   = False)
		
		# execute object
		self.main()


	def set_option(self):
		"Set options"
		
		# call the super set_option method
		Application.set_option(self)
		

	def init(self):
		hostname = gethostname()
		
		if re.match("mrouter", hostname):
			nodetype = "meshrouter"
		elif re.match("mclient", hostname):
			nodetype = "meshclient"
		else:
			(nodetype, nodeinfo) = mm_util.getnodetype()
			
		info("Hostname: %s" % hostname)
		info("Nodetype: %s" % nodetype)
			
		if startupinfos.has_key(nodetype):
			for line in startupinfos[nodetype]:
				try:
					eval(line)
				except Exception, inst:
					error("Error while executing %s" % line)
					error(inst)
				
		if startupinfos.has_key(hostname):
			for line in startupinfos[hostname]:
				try:
					eval(line)
				except Exception, inst:
					error("Error while executing %s" % line)
					error(inst)
					
	def main(self):
		"Main method of the Init object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		self.init()



# must be in default namespace because of config file...


class SystemExitException(Exception):
	"Private exception for execpy"

	def __init__(self, args):
		self.args = args

def raiseException(status):
	"Just to raise the exception with status"
	
	raise SystemExitException(status)
	

def execpy(script, arguments = []):
	"Function to execute a python script with arguments"
	
	# save argument list
	save_argv = sys.argv

	# save function pointer for sys.exit()
	save_exit = sys.exit
	
	# flush argument list
	sys.argv = []
	
	# build new argv[0] out of script name
	sys.argv.append(script)
	# add argument list
	sys.argv.extend(arguments)

	# override sys.exit()
	sys.exit = raiseException

	rc = "0"

	try:
		info ("Now running %s " % script)
		execfile(script,globals())
	except SystemExitException:
		rc = sys.exc_info()[1]

	if rc != "0":
		warn("Returncode: %s" % rc)

	# restore environment
	sys.exit = save_exit
	sys.argv = save_argv
	
	return rc
	
def startdaemon(name):
	if daemoninfos.has_key(name):
		daemoninfo = daemoninfos[name]
		# build arguments
		args = []
		args.append(daemoninfo["path"])
		args.append("start")
		args.extend(daemoninfo["args"])
		return execpy('/usr/local/bin/mm_daemon.py',
					  args)

def stopdaemon(name):
	if daemoninfos.has_key(name):
		daemoninfo = daemoninfos[name]
		# build arguments
		args = []
		args.append(daemoninfo["path"])
		args.append("stop")
		return execpy('/usr/local/bin/mm_daemon.py',
					  args)


if __name__ == "__main__":
	Init()