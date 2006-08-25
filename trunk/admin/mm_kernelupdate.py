#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, subprocess
from logging import info, debug, warn, error
 

# mcg-mesh imports
from mm_application import Application
from mm_basic import *


class KernelUpdate(Application):
	"Class to handle kernel source update within images"

	def __init__(self):
		"Constructor of the object"

		# call the super constructor
		Application.__init__(self)

		# no custom options yet

		# execute object
		self.main()

	def set_option(self):
		"set options"
		
		# call the super set_option method
		Application.set_option(self)


	def main(self):
		"Main method of the madwifi object"

		# parse options
		self.parse_option()
		
		# set options
		self.set_option()
		
		# call the corresponding method
		self.kernelupdate()

	def kernelupdate(self):
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
		prog = subprocess.call(cmd,shell=False)
	
		# download kernel image and extract
		cmd='wget %s/v2.6/%s.tar.gz -O - | tar xz -C %s' \
			 % (kernelinfos['mirror'],kernel,tmp)
		info(cmd)
		prog = subprocess.call(cmd,shell=True)
	
		# get revision
		cmd=("svn info %s | grep Revision | awk '{print $2;}'" % dst)
		info(cmd)
		prog = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
		local_revision = prog.stdout.readline().splitlines()[0]
		info(local_revision)
		sts = os.waitpid(prog.pid, 0)

		# commit new versions of files to upstream repository
		cmd=('svn','commit',dst,'-m "updated kernel to %s"' % kernel)
		info(cmd)
		prog = subprocess.call(cmd,shell=False)
	
		# switch repository to trunk
		cmd=('svn','switch',svninfos["svnrepos"]+'/boot/linux/trunk',dst)
		info(cmd)
		prog = subprocess.call(cmd,shell=False)
		
		# merge upstream with trunk
		cmd=('svn','merge','-r','%s:HEAD' % local_revision,svninfos["svnrepos"]+'/boot/linux/branches/upstream',dst)
		info(cmd)
		prog = subprocess.call(cmd,shell=False)


		# remove modified files and svn infos
		cmd='rm -rf `find %s -name .svn`' % dst
		info(cmd)
		prog = subprocess.call(cmd,shell=True)
		for i in kernelinfos['modifiedfiles']:
			os.system("rm -v %s/%s" % (dst,i) )
		
		# copy other files to images
		for img in imageinfos.iterkeys():
			imgdst="%s/%s/meshnode/opt/meshnode/linux" % (imageprefix,img)
			os.system("mkdir -vp %s" % imgdst)
			cmd='cp -r %s/* %s' % (dst,imgdst)
			info(cmd)
			prog = subprocess.call(cmd,shell=True)
				
		
		info("Cleaning up %s ..." % tmp)
		os.system("rm -rf %s" % tmp)
		info("done.")

if __name__ == "__main__":
	KernelUpdate()

