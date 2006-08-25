# -*- coding: utf-8 -*-

# python imports
import subprocess
from logging import debug

# CommandFailed exception
class CommandFailed(Exception):
	def __init__(self, cmd, rc):
		self.cmd = cmd
		self.rc  = rc
		
	def __str__(self):
		return "Command %s failed with return code %d." % (self.cmd,self.rc)


# convenience function to handle returncodes
def execute(cmd,shell):
	debug("Execute: %s" % cmd.__str__())
	print logging.getLogger("").getEffectiveLevel()
	rc = subprocess.call(cmd,shell=shell)
	if (rc != 0):
		raise CommandFailed(cmd,rc)
	
