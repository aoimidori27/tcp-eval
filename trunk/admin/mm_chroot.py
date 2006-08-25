#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
import os, subprocess
from logging import info, debug, warn, error


# mcg-mesh imports
from mm_application import Application
from mm_basic import *



class Chroot(Application):
	"Class to handle chroot into the images"

	def __init__(self):
		"Constructor of the object"

		# call the super constructor
		Application.__init__(self)

		# default command to execute
		self.command = 'bash'
		
		usage = "usage: %prog [options] [command] \n" \
				"       where  command is a command to execute within chroot"
		
		self.parser.set_usage(usage)
		self.parser.set_defaults(verbose = True)
		
		# execute object
		self.main()

	def set_option(self):
		"set options"
		
		# call the super set_option method
		Application.set_option(self)

		if len(self.args) > 0:
			self.command = self.args[0]
			for arg in self.args[1:]:
				self.command = self.command . arg


	def main(self):
		"Main method of the madwifi object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		self.chroot_exec(self.command)	

	
	# Chroot and execute a command	
	def chroot_exec(self,cmd):
		
		# must be root
		requireroot();
		
		# for chroot, imagetype and nodetype are required
		requirenodetype();
		requireimagetype();
		info("Imagetype: "+imagetype);
		
		# common mounts for all chroots
		mounts = { '/dev'  : '/dev',
				   '/proc' : '/proc' }
		
		# join with mounts of nodes
		mounts.update(imageinfo['mounts'])
		
		# mount
		for src,dst in mounts.iteritems():
			os.system("mount -o bind %s %s/%s" % (src,imagepath,dst))
			
		# exec command
		# TODO: error handling, mount only once (in case of multiple shells)
		os_cmd = " ".join(["chroot",imagepath,"/bin/bash -c 'export HOSTNAME=%s && source /etc/profile && %s'" % (nodeinfo['hostprefix'],cmd)])
		info(os_cmd)
		os.system(os_cmd)

		# umount
		for dst in mounts.itervalues():
			os.system("umount %s/%s" % (imagepath,dst))
				  

if __name__ == "__main__":
	Chroot()
