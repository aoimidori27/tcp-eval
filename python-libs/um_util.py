#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import subprocess, os, os.path, sys, sre
from logging import info, debug, warn, error
from socket import gethostname

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


def requireroot():
    "Check if user is root"

    if not os.getuid()==0:
        error("You must be root. Operation not permitted.")
        sys.exit(1)


#
# mesh specific helper functions and classes
#

def getnodetype():
    "Check environment variable UM_NODE_TYPE and return nodetype"

    global nodetype

    if not globals().has_key('nodetype'):
        if os.environ.has_key('UM_NODE_TYPE') and nodeinfos.has_key(os.environ['UM_NODE_TYPE']):
            nodetype = os.environ['UM_NODE_TYPE']
        else:
            error("Please set environment variable UM_NODE_TYPE to one of %s." % nodeinfos.keys())
            sys.exit(1)

    return nodetype


def getnodeinfo():
    "Get the node infos for the desired note type"

    global nodeinfo

    if not globals().has_key('nodeinfo'):
        nodetype = getnodetype()
        nodeinfo = nodeinfos[nodetype]

    return nodeinfo


def getimageinfo():
    "Get the image infos for the desired note type"

    global imageinfo

    if not globals().has_key('imageinfo'):
        nodeinfo  = getnodeinfo()
        imageinfo = imageinfos[nodeinfo['imagetype']]

    return imageinfo


def getimagepath():
    "Get the image path for the desired note type"

    global imagepath

    if not globals().has_key('imagepath'):
        nodeinfo = getnodeinfo()
        imagepath = "%s/%s.img/%s" % (imageprefix, nodeinfo['imagetype'], nodeinfo['imageversion'])

    return imagepath


def getnodenr():
    "Get node number from hostname"

    hostname = gethostname()

    for nodeinfo in nodeinfos.itervalues():
        if sre.match(nodeinfo['hostnameprefix'], hostname):
            return sre.sub(nodeinfo['hostnameprefix'],"",hostname)
