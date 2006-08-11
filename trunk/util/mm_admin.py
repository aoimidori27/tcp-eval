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
				  

def chroot():
	chroot_exec("bash")

def emerge(args):
	chroot_exec("emerge "+args)

# svn update
def svnupdate():
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

# update kernel
def kernelupdate():
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
		
			

#
# Main
#

if len(args)>1: action = '"'+" ".join(args[1:])+'"'
else: action = ""

eval("%s(%s)" %(args[0],action))
