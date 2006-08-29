#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess
from logging import info, debug, warn, error

# mcg-mesh imports
from mm_application import Application
from mm_util import *


class Subversion(Application):
	"Class to manage Subvserions repositories within those images"


	def __init__(self):
		super(Subversion, self).__init__();

		usage = "usage: %prog [options] COMMAND \n\n" \
				"COMMAND:= { status | update }\n"
		self.parser.set_usage(usage)

		self.main()

	def set_option(self):
		# super method
		super(Subversion, self).set_option();
		
		# correct numbers of arguments?
		if len(self.args) != 1:
			self.parser.error("incorrect number of arguments")

		
		# does the command exists?
		if not self.args[0] in ('update', 'status'):
			self.parser.error('unkown COMMAND %s' %(args[0]))
		else:
			self.action = self.args[0]

	
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
				for src,dst in svninfos['svnmappings'].iteritems():	
					dst= imageprefix +"/"+ image +"/"+ node + svnprefix + dst
					src= svninfos["svnrepos"] + src
					if not os.path.exists(dst):
						warn("%s got lost! doing a new checkout" % dst)
						os.system("mkdir -p %s" % dst)
						cmd=('svn','checkout',src,dst)
					else:
						cmd=('svn','update',dst)
					info(cmd)
					prog = call(cmd,shell=False)


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




