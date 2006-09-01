#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess, dircache, re
from logging import info, debug, warn, error

# mcg-mesh imports
from mm_application import Application
from mm_util import *


class Subversion(Application):
	"Class to manage Subvserions repositories within those images"


	def __init__(self):
		Application.__init__(self);

		# object variables (set the defaults for the option parser)
		self.updatelinks = True

		usage = "usage: %prog [options] COMMAND \n\n" \
				"COMMAND:= { status | update }\n"
		self.parser.set_usage(usage)


		self.parser.add_option("-n", "--nolinks", 
							   action = "store_false", dest = "updatelinks",
							   help = "don't update symlinks in /usr/local/bin")	

		self.parser.set_defaults(syslog=False,verbose=True,
								 updatelinks=self.updatelinks)

		self.main()

	def set_option(self):
		# super method
		Application.set_option(self);
		
		# correct numbers of arguments?
		if len(self.args) != 1:
			self.parser.error("incorrect number of arguments")

		
		# does the command exists?
		if not self.args[0] in ('update', 'status'):
			self.parser.error('unkown COMMAND %s' %(args[0]))
		else:
			self.action = self.args[0]

		# get options
		self.updatelinks = self.options.updatelinks

	
	def main(self):
		"main method of Subversion object"
		
		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		eval("self.%s()" %(self.action)) 

	# svn update
	def update(self):
		# allow group mates to write and exec files
		os.umask(0007)
		for image in imageinfos.iterkeys():
			for node in nodeinfos.iterkeys():

				# iterate through svn mappings
				for src,dst in svninfos['svnmappings'].iteritems():	
					dst= imageprefix +"/"+ image +"/"+ node + svnprefix + dst
					src= svninfos["svnrepos"] + src
					if not os.path.exists(dst):
						warn("%s got lost! doing a new checkout" % dst)
						call("mkdir -p %s" % dst, shell = True)
						cmd = ('svn','checkout',src,dst)
					else:
						cmd = ('svn','update',dst)
					info(cmd)
					prog = call(cmd,shell=False)
					
				# update links
				if self.updatelinks:
					# scripts in this folders are copied to /usr/local/bin
					folders = ("/opt/meshnode/scripts/init",
							   "/opt/meshnode/scripts/monitor",
							   "/opt/meshnode/scripts/measurement")
					info("Updating symlinks in /usr/local/bin...")
					dst = imageprefix + "/" + image + "/" +node +\
						  "/usr/local/bin"
				
					# just remove every link with mm_ in it
					cmd = "rm -v `find %s -type l -name 'mm_*'`" %(dst)
					try:
						call(cmd,shell=True)
					except CommandFailed:
						warn("Removing of links in %s failed" %(dst))

					# recreate those links
					for d in folders:
						src = imageprefix + "/" + image + "/" +node + d
						for f in dircache.listdir(src):
							if re.match("mm_",f):
								cmd = "ln -vsf %s/%s %s/%s" %(d,f,dst,f)
								# use os.system() here because call()
								# is too slow
								os.system(cmd) 

			


	# svn status
	def status(self):
		for image in imageinfos.iterkeys():
			for node in nodeinfos.iterkeys():
				for src,dst in svninfos['svnmappings'].iteritems():	
					dst= imageprefix +"/"+ image +"/"+ node + svnprefix + dst
					cmd=('svn','status',dst)
					info(cmd)
					prog = call(cmd,shell=False)

	
if __name__ == '__main__':
	Subversion()




