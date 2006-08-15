#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, optparse, subprocess, time
from logging import info, debug, warn, error
from mm_basic import *
from subprocess import Popen, PIPE

#
# update kernel
#

# for kernelupdate only works for meshnodes
if nodetype=='meshnode':
	kernel='linux-%s' % kernelinfos['version']
	tmp='/tmp/kernelupdate'
	dst=tmp+'/'+kernel 
	os.system("mkdir -p %s" % dst)
	
	# check out upstream files
	info("Check out kernel upstream");
	cmd=('svn','checkout',svninfos["svnrepos"]+'/boot/linux/branches/upstream',dst)
	info(cmd)
	prog = Popen(cmd,shell=False)
	sts = os.waitpid(prog.pid, 0)
	
	# download kernel image and extract
	cmd='wget %s/v2.6/%s.tar.gz -O - | tar xz -C %s' \
		 % (kernelinfos['mirror'],kernel,tmp)
	info(cmd)
	prog = Popen(cmd,shell=True)
	sts = os.waitpid(prog.pid, 0)
	
	# get revision
	cmd=("svn info %s | grep Revision | awk '{print $2;}'" % dst)
	info(cmd)
	prog = Popen(cmd,stdout=PIPE,shell=True)
	local_revision = prog.stdout.readline().splitlines()[0]
	info(local_revision)
	sts = os.waitpid(prog.pid, 0)

	# commit new versions of files to upstream repository
	cmd=('svn','commit',dst,'-m "updated kernel to %s"' % kernel)
	info(cmd)
	prog = Popen(cmd,shell=False)
	sts = os.waitpid(prog.pid, 0)
	
	# switch repository to trunk
	cmd=('svn','switch',svninfos["svnrepos"]+'/boot/linux/trunk',dst)
	info(cmd)
	prog = Popen(cmd,shell=False)
	sts = os.waitpid(prog.pid, 0)
		
	# merge upstream with trunk
	cmd=('svn','merge','-r','%s:HEAD' % local_revision,svninfos["svnrepos"]+'/boot/linux/branches/upstream',dst)
	info(cmd)
	prog = Popen(cmd,shell=False)		
	sts = os.waitpid(prog.pid, 0)


	# remove modified files and svn infos
	cmd='rm -rf `find %s -name .svn`' % dst
	info(cmd)
	prog = Popen(cmd,shell=True)
	sts = os.waitpid(prog.pid,0)
	for i in kernelinfos['modifiedfiles']:
		os.system("rm -v %s/%s" % (dst,i) )
		
	# copy other files to images
	for img in imageinfos.iterkeys():
		imgdst="%s/%s/meshnode/opt/meshnode/linux" % (imageprefix,img)
		os.system("mkdir -vp %s" % imgdst)
		cmd='cp -r %s/* %s' % (dst,imgdst)
		info(cmd)
		prog = Popen(cmd,shell=True)
		sts = os.waitpid(prog.pid,0)
		
	info("Cleaning up %s ..." % tmp)
	os.system("rm -rf %s" % tmp)
	info("done.")
