#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, optparse, subprocess, time
from logging import info, debug, warn, error
from mm_basic import *
from subprocess import Popen, PIPE

#
# svn update
#

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
			prog = Popen(cmd,shell=False)
			sts = os.waitpid(prog.pid, 0)
