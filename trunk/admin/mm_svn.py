#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, subprocess, time, optparse
from mm_application import Application
from logging import info, debug, warn, error
from mm_basic import *
from subprocess import Popen, PIPE


class Subversion(Application):
	"Class to manage Subvserions repositories within those images"


	def __init__(self):
		Application.__init__(self);
		usage = "usage: %prog [options] COMMAND \n\n" \
				"COMMAND:= { status | update }\n"
		self.parser.set_usage(usage)
		self.parser.add_option('-b','--bla');

	def commit():
		pass

	def init(self,options,args):
		pass

	def run(self,options,args):
		if args[0] == 'update':
			self.update()

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
					print cmd
					prog = subprocess.call(cmd,shell=False)

def main():
	myClass = Subversion()
	myClass.start()
	
#	(options,args) = myObject.parse()
	
if __name__ == '__main__':
 	main()



