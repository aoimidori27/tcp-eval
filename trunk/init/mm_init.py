#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess, sys
from logging import info, debug, warn, error

# mcg-mesh imports
from mm_application import Application
from mm_cfg import *


# Program to start MCG-Mesh programms

def main():
	# start madwifi
	execpy('mm_madwifi.py',
		   ['--debug','autocreate'])



class SystemExitException(Exception):
	"Private exception for execpy"

	def __init__(self, args):
		self.args = args

def raiseException(status):
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

	if rc != 0:
		warn("Returncode: %s" % rc)

	# restore environment
	sys.exit = save_exit
	sys.argv = save_argv
	
	return rc
	


if __name__ == "__main__":
	main()
