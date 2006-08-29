#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import subprocess
from logging import debug


class CommandFailed(Exception):
	"Framework for MCG-Mesh applications"
	
	
	def __init__(self, cmd, rc):
		self.cmd = cmd
		self.rc  = rc
	
		
	def __str__(self):
		return "Command %s failed with return code %d." %(self.cmd, self.rc)



def execute(cmd, shell):
	"Convenience function to handle returncodes"

	debug("Execute: %s" % cmd.__str__())
	print logging.getLogger("").getEffectiveLevel()
	rc = subprocess.call(cmd, shell = shell)
	if rc != 0:
		raise CommandFailed(cmd, rc)