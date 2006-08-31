#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess, sys, re
from logging import info, debug, warn, error
from socket import gethostname

# mcg-mesh imports
from mm_util import execpy
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
		
		if re.match("mrouter",hostname):
			nodetype = "meshrouter"
		elif re.match("mclient",hostname):
			nodetype = "meshclient"
		else:
			(nodetype, nodeinfo) = mm_util.getnodetype()
			
		info ("Hostname: %s" % hostname)
		info ("Nodetype: %s" % nodetype)
			
		if startupinfos.has_key(nodetype):
			for line in startupinfos[nodetype]:
				eval(line)
				
		if startupinfos.has_key(hostname):
			for line in startupinfos[hostname]:
				eval(line)
					
	def main(self):
		"Main method of the Init object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		self.init()



if __name__ == "__main__":
	Init()
