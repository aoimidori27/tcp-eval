#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
from logging import info, debug, warn, error

# mcg-mesh imports
from mm_application import Application
from mm_util import *


class OlsrUpdate(Application):
	"Class to handle update of olsr files in the local svn repos"

	def __init__(self):
		"Constructor of the object"

		# call the super constructor
		Application.__init__(self)
	
		# initialization of the option parser
		self.parser.set_defaults(verbose = True, syslog=False,
								 debug = False)
		
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
		local_repos    = svninfos["svnrepos"]
		local_upstream = olsrinfos["local_upstream"]
		local_trunk    = olsrinfos["local_trunk"]


		dst = tmp+"/upstream"
		# check out upstream files
		info("Checking out olsr local upstream...")
		cmd = ("svn","co","-q",
			   local_repos+local_upstream,
			   dst)
		call(cmd, shell = False)

		# get revision

		cmd = "svn info %s | grep Revision | awk '{print $2;}'" %(dst)	
		(stdout, stderr) = execute(cmd, shell = True)
		local_revision = stdout.splitlines()[0]
		info("Revision of checkout is: %s" %(local_revision))

		# clean up upstream
		info("Cleaning up upstream checkouts...")
		cmd = "find %s ! -path '*.svn*' -type f | xargs rm -f" \
			  %(dst)
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
		cmd = "find %s -name CVS | xargs rm -rf" %(dst)
		call(cmd, shell = True)

		
		info("Searching updated files...")	
		# add new files 
		cmd = "svn st %s | grep '?' | awk '{ print $2; }'" \
			  %(dst)
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
		info("Commiting changes...")
 		cmd = ("svn","ci",dst,
 			   "-m","new olsr version")
 		call(cmd, shell = False)


		# switch upstream to trunk
		info("Switching local checkout to trunk...")
		cmd = ("svn", "switch", "%s/%s" %(local_repos,
										  local_trunk),
			   dst)
		call(cmd, shell = False)
		# just for completeness rename it
		cmd = "mv %s %s/trunk" %(dst,tmp)
		call(cmd, shell = True)
		

		# merging changes from upstream local trunk
		info("Merging changes with local trunk...")
		cmd = ("svn","merge","-r","%s:HEAD" %(local_revision),
			   "%s/%s" %(local_repos, local_upstream),
			   tmp+"/trunk")
		call(cmd, shell = False)

		# commiting changes to local trunk
		info("Commiting these changes to repository...")
		cmd = ("svn","commit", tmp+"/trunk",
			   "-m","new olsr version")
		call(cmd, shell = False)	 

        # cleanup
		info("Cleaning up %s..." %(tmp))
		cmd = "rm -rf %s" %(tmp)
		call(cmd, shell = True)

		info("Done.")
		


	def main(self):
		"Main method of the OlsrUpdate object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		self.olsrupdate()	
				  


if __name__ == "__main__":
	OlsrUpdate()
