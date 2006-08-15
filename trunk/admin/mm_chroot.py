#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, optparse, subprocess, time
from logging import info, debug, warn, error
from pyPgSQL import PgSQL
from mm_basic import *
from subprocess import Popen, PIPE


#
# Chroot and execute a command
#

def chroot_exec(cmd):

	# must be root
	requireroot();
	
	# for chroot, imagetype and nodetype are required
	requirenodetype();
	requireimagetype();
	print imagetype;
	
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
	print os_cmd
	os.system(os_cmd)

	# umount
	for dst in mounts.itervalues():
		os.system("umount %s/%s" % (imagepath,dst))
				  

chroot('bash')
