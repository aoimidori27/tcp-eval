#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import subprocess, os, sys
from logging import info, debug, warn, error

# umic-mesh imports
from um_config import *

#
# generic helper functions and classes
#

class CommandFailed(Exception):
	"Convenience function to handle returncodes"
	
	def __init__(self, cmd, rc, stderr = None):
		self.cmd = cmd
		self.rc  = rc
		self.stderr = stderr
	
	def __str__(self):
		return "Command %s failed with return code %d." %(self.cmd, self.rc)


def execute(cmd, shell, raiseError=True):
	"Excecute a shell command"

	debug("Executing: %s" % cmd.__str__())
	prog = subprocess.Popen(cmd, shell = shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = prog.communicate()
	rc = prog.returncode
	if raiseError and rc != 0:
		raise CommandFailed(cmd, rc, stderr)
	
	return (stdout, stderr)


def call(cmd, shell, raiseError=True):
	"Call a shell command"

	debug("Executing: %s" % cmd.__str__())
	rc = subprocess.call(cmd, shell = shell)
	if raiseError and rc != 0:
		raise CommandFailed(cmd, rc)


#
# mesh specific helper functions and classes
#

def getnodetype():
	"Check environment variable UM_NODE_TYPE and return nodetype and nodeinfo"

	global nodetype, nodeinfo

	if not globals().has_key('nodetype'):
		if os.environ.has_key('UM_NODE_TYPE') and nodeinfos.has_key(os.environ['UM_NODE_TYPE']):
			nodetype = os.environ['UM_NODE_TYPE']
			nodeinfo = nodeinfos[nodetype]
		else:
			error("Please set environment variable UM_NODE_TYPE to one of %s." % nodeinfos.keys())
			sys.exit(1)

	return (nodetype, nodeinfo)


def getimageinfo():
	"Check environment variable UM_NODE_TYPE and return imageinfo"

	global imageinfo

	if not globals().has_key('imageinfo'):
		(nodetype, nodeinfo) = getnodetype()

		if imageinfos.has_key(nodetype):
			imageinfo = imageinfos[nodetype]
		else:
			error("No image defined for UM_NODE_TYPE=%s. Please set environment variable " \
				  "UM_NODE_TYPE to one of %s." %(nodetype, imageinfos.keys()))
			sys.exit(1)

	return imageinfo


def getimageversion():
	"Check environment variable UM_IMAGE_VERSION and return imageversion"

	global imageversion

	if not globals().has_key('imageversion'):
		imageinfo = getimageinfo()

		if os.environ.has_key('UM_IMAGE_VERSION') and os.environ['UM_IMAGE_VERSION'] in imageinfo['versions']:
			imageversion = os.environ['UM_IMAGE_VERSION']
		else:
			error("No image version defined for UM_NODE_TYPE=%s. Please set environment variable " \
				  "UM_IMAGE_VERSION to one of %s." %(nodetype, imageinfo['versions']))
			sys.exit(1)

	return imageversion


def getimagepath():
	"Derivate image path form environment variables UM_NODE_TYPE and UM_IMAGE_VERSION"

	global imagepath
	
	if not globals().has_key('imagepath'):
		imageversion = getimageversion()
		imagepath = "%s/%s.img/%s" % (imageprefix, nodetype, imageversion)
	
	return imagepath


def requireroot():
	"Check if user is root"

	if not os.getuid()==0:		
		error("You must be root to do this!")
		sys.exit(1)

