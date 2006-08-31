#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import subprocess,types,os,sys,re,copy
from logging import info, debug, warn, error
from socket import gethostname

# mcg-mesh imports
from mm_cfg import *


# Generic helper functions + classes

class CommandFailed(Exception):
	"Framework for MCG-Mesh applications"
	
	
	def __init__(self, cmd, rc, stderr = None):
		self.cmd = cmd
		self.rc  = rc
		self.stderr = stderr
	
		
	def __str__(self):
		return "Command %s failed with return code %d." %(self.cmd, self.rc)



def execute(cmd, shell, raiseError=True):
	"Convenience function to handle returncodes"

	debug("Executing: %s" % cmd.__str__())
	prog = subprocess.Popen(cmd,shell = shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = prog.communicate()
	rc = prog.returncode
	if raiseError and rc != 0:
		raise CommandFailed(cmd, rc, stderr)
	return (stdout, stderr)

def call(cmd, shell, raiseError=True):
	"Convenience function to handle returncodes"

	debug("Executing: %s" % cmd.__str__())
	rc = subprocess.call(cmd,shell = shell)
	if raiseError and rc != 0:
		raise CommandFailed(cmd, rc)



# Mesh specific helper functions + classes


# check environment variable MESH and return nodetype
def getnodetype():
	global nodetype,nodeinfo

	# do action only if not yet registered
	if not globals().has_key('nodetype'):
		if os.environ.has_key('MESH') and nodeinfos.has_key(os.environ['MESH']):
			nodetype = os.environ['MESH']
			nodeinfo = nodeinfos[nodetype]
		else:
			error("please set environment variable MESH to one of %s" % nodeinfos.keys())
			sys.exit(1)

	return (nodetype,nodeinfo)

# check environment variable MESH_IMAGE and return nodetype
def getimagetype():
	global imagetype,imageinfo

	if not globals().has_key('imagetype'):
#		info("registering imagetype")
		if os.environ.has_key('MESH_IMAGE') and imageinfos.has_key(os.environ['MESH_IMAGE']):
			imagetype = os.environ['MESH_IMAGE']
			imageinfo = imageinfos[imagetype]
			if globals().has_key('nodetype'):
				imagepath = "%s/%s/%s" % (imageprefix,imagetype,nodetype)
		else:
			error("please set environment variable MESH_IMAGE to one of %s" % imageinfos.keys())
			sys.exit(1)

	return (imagetype,imageinfo)

# get imagepath
def getimagepath():
	global imagepath
	
	if not globals().has_key('imagepath'):
		(nodetype,nodeinfo) = getnodetype();
		(imagetype,imageinfo) = getimagetype();
		imagepath = "%s/%s/%s" % (imageprefix,imagetype,nodetype)

	return imagepath



# check if user is root
def requireroot():
	if not os.getuid()==0:		
		error("you must be root to do this")
		sys.exit(1)
	

# get nodename from nodenumber
def nodename(nr):
	requirenodetype()
	
	if type(nr) is types.StringType: return nr
	return "%s%d" % (nodeinfo['hostprefix'],nr)

def getnodenr():
	"Get node number from hostname"
	
	hostname = gethostname()
	nr = re.sub("^mrouter","",hostname)
	return nr


