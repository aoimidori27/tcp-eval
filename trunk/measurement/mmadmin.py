#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, optparse, subprocess, time
from logging import info, debug, warn, error
from pyPgSQL import PgSQL
from mmbasic import *
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
	# TODO: error handling, mount only once (in case of multiple shells)
	os.system("mount -o bind /usr/portage "+nodeinfo['imagepath']+"/usr/portage");
	os.system("mount -o bind /dev "+nodeinfo['imagepath']+"/dev");
	os.system(" ".join(["chroot",nodeinfo['imagepath'],"/bin/bash -c 'HOSTNAME=%s && source /etc/profile && %s'" % (nodeinfo['hostprefix'],cmd)]))
	os.system("umount "+nodeinfo['imagepath']+"/usr/portage");
	os.system("umount "+nodeinfo['imagepath']+"/dev");

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
