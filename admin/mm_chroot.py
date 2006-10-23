#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
from logging import info, debug, warn, error

# mcg-mesh imports
from mm_application import Application
from mm_util import *


class Chroot(Application):
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


	def chroot_exec(self,command):
		"Chroot and execute a command"
		
		# must be root
		requireroot()
		
		# for chroot, imagetype and nodetype are required
		(nodetype,nodeinfo) = getnodetype()
		(imagetype,imageinfo) = getimagetype()
		imagepath = getimagepath()
		
		info("Imagetype: %s" %(imagetype))
		info("Nodetype:  %s" %(nodetype))
		
		# common mounts for all chroots
		mounts = { '/dev'  : '/dev',
				   '/proc' : '/proc' }
		
		# join with mounts of nodes
		mounts.update(imageinfo['mounts'])
		
		# mount
		for (src, dst) in mounts.iteritems():
			# check if directory is already mounted
			cmd= ('grep','%s%s'  % (imagepath,dst), '/etc/mtab')
			rc = subprocess.call(cmd)
			if rc != 0:
				cmd = "mount -o bind %s %s%s" % (src, imagepath, dst)
				execute(cmd, shell = True)
				
		# exec command	
		cmd = "/usr/sbin/chroot %s /bin/bash -c " \
			  "'export HOSTNAME=%s && export CHROOT=true && export HOME=/root && source /etc/profile && %s'" \
			  % (imagepath,nodeinfo['hostprefix'], command)
		call(cmd, shell = True)

		# umount
		for dst in mounts.itervalues():
			cmd = "umount %s/%s" %(imagepath,dst)
			call(cmd, shell = True, raiseError = True)


	def main(self):
		"Main method of the chroot object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		self.chroot_exec(self.command)	
				  


if __name__ == "__main__":
	Chroot()
