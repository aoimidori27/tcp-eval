#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, optparse, subprocess, time
from logging import info, debug, warn, error
from pyPgSQL import PgSQL
from mm_basic import *
from subprocess import *

#
# Parse args
#

#parser = optparse.OptionParser("%prog [options] program cmd")
# parser.add_option("-n", "--nodes", dest="nodes")
#options, args = parser.parse_args()
args = sys.argv[1:]

#
# Chroot
#

def chroot_exec(cmd):
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
				  

def chroot():
	chroot_exec("bash")

def emerge(args):
	chroot_exec("emerge "+args)
		

#
# Main
#

if len(args)>1: action = '"'+" ".join(args[1:])+'"'
else: action = ""

eval("%s(%s)" %(args[0],action))
