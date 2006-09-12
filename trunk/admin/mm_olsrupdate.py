#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
from logging import info, debug, warn, error

# mcg-mesh imports
from mm_application import Application
from mm_util import *


class OlsrUpdate(Application):
	"Class to handle chroot into the images"

	def __init__(self):
		"Constructor of the object"

		# call the super constructor
		Application.__init__(self)

		# object variables (set the defaults for the option parser)
		self.command = 'bash'
		
		# initialization of the option parser
		usage = "usage: %prog [options] [command] \n" \
				"where  command is a command to execute within chroot"
		self.parser.set_usage(usage)
		self.parser.set_defaults(verbose = True, syslog=False)
		
		# execute object
		self.main()


	def set_option(self):
		"Set options"
		
		# call the super set_option method
		Application.set_option(self)

		if len(self.args) > 0:
			self.command = self.args[0]
			for arg in self.args[1:]:
				self.command = self.command + arg



	def olsrupdate(self):
		# create temporary directory
		tmp = "/tmp/olsrupdate"
		cmd = "mkdir -p %s" %(tmp)
		call(cmd, shell = True)

		remote_repos   = olsrinfos["remote_repos"]
		remote_module  = olsrinfos["remote_module"]
		local_repos    = olsrinfos["local_repos"]
		local_upstream = olsrinfos["local_upstream"]
		local_trunk    = olsrinfos["local_trunk"]

		# check out upstream files
		info("Checking out olsr local upstream...")
		cmd = ("svn","co","-q",
			   local_repos+local_upstream,
			   tmp+"/upstream")
		call(cmd, shell = False)

		# clean up upstream
		info("Cleaning up upstream checkouts...")
		cmd = "find %s ! -path '*.svn*' -type f | xargs rm -f" \
			  %(tmp+"/upstream")
		call(cmd, shell = True)

		# check out trunk from remote repos
		info("Checking out olsr trunk from remote...")
		save_path = os.getcwd()
		os.chdir(tmp)
		cmd = ["cvs","-Q",
			   "-d%s" %(remote_repos),
			   "co","-d","upstream", remote_module]
		call(cmd, shell = False)
		os.chdir(save_path)

		# clean up trunk from remote repos
		info("Removing CVS folders...")
		cmd = "find %s -name CVS | xargs rm -rf" %(tmp+"/upstream")
		call(cmd, shell = True)

		
		info("Searching updated files...")	
		# add new files 
		cmd = "svn st %s | grep '?' | awk '{ print $2; }'" \
			  %(tmp+"/upstream")
		(stdout,stderr) = execute(cmd, shell = True)
		debug("Stdout: %s" %stdout)
		if (stdout != ""):
			info("Found new files. Adding them...")						
			cmd = "svn add %s" %(stdout)
			call(cmd, shell = True)

		# remove files, which were removed in upstream
		cmd = "svn st %s | grep '!' | awk '{ print $2; }'" \
			  %(tmp+"/upstream")
		(stdout,stderr) = execute(cmd, shell = True)
		debug("Stdout: %s" %stdout)
		if (stdout != ""):
			info("Found removed files. Deleting them...")						
			cmd = "svn rm %s" %(stdout)
			call(cmd, shell = True)


		# commit changes
		info("Commiting Changes...")
 		cmd = ("svn","ci",tmp+"/upstream",
 			   "-m","new olsr version")
 		call(cmd, shell = False)

		# merging changes to local trunk
		info("Merging changes with local trunk...")
#		cmd = ("svn","merge","-r",

        # cleanup
		info("Cleaning up %s..." %(tmp))
		cmd = "rm -rf %s" %(tmp)
		call(cmd, shell = True)

		info("Done.")
		


	def main(self):
		"Main method of the chroot object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		self.olsrupdate()	
				  


if __name__ == "__main__":
	OlsrUpdate()
