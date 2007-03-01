#!/usr/bin/env python
#g -*- coding: utf-8 -*-

# python imports
import subprocess, os, sys, re
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
    "Excecute a shell command, "

    debug("Executing: %s" % cmd.__str__())
    prog = subprocess.Popen(cmd, shell = shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = prog.communicate()
    rc = prog.returncode
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc, stderr)

    return (stdout, stderr)


def call(cmd, shell, raiseError=True):
    "Call a shell command, wait for command to complete."

    debug("Executing: %s" % cmd.__str__())
    rc = subprocess.call(cmd, shell = shell)
    if raiseError and rc != 0:
        raise CommandFailed(cmd, rc)


def execpy(arguments = []):
    "Function to execute a python script with arguments"

    class SystemExitException(Exception):
        "Private exception for execpy"

        def __init__(self, status):
            self.status = status

    def raiseException(status):
        "Just to raise the exception with status"

        raise SystemExitException(status)

    global __name__;

    rc = 0

    # script is first argument
    script = arguments[0]

    # save argument list
    save_argv = sys.argv

    # save function pointer for sys.exit()
    save_exit = sys.exit

    # save __name__
    save_name = __name__;

    # override argument list
    sys.argv = arguments
    
    # override sys.exit()
    sys.exit = raiseException

    # override __name__
    __name__ = "__main__"

    try:
        info ("Now running %s " % script)
        execfile(script, globals())
        error ("One should not get here.")
    except SystemExitException, inst:
        info ("Script %s exited with sys.exit(%d)"
              % (script, inst.status))
        rc = inst.status

    if rc != 0:
        warn("Returncode: %d." % rc)

    # restore environment
    sys.exit = save_exit
    sys.argv = save_argv
    __name__ = save_name

    return rc


def requireroot():
    "Check if user is root"

    if not os.getuid() == 0:
        error("You must be root. Operation not permitted.")
        sys.exit(1)


#
# mesh specific helper functions and classes
#

def getnodetype(hostname = None):
    "Derived the nodetype either from the hostname or from environment variable UM_NODE_TYPE"

    if not hostname == None:    	
        for (can_nodetype, can_nodeinfo) in nodeinfos.iteritems():
            if re.match(can_nodeinfo['hostnameprefix'], hostname):
                nodetype = can_nodetype
        
        error("Could not derived the nodetype from the hostname %s" %(hostname))
        sys.exit(1)
        
    elif os.environ.has_key('UM_NODE_TYPE'):
        if nodeinfos.has_key(os.environ['UM_NODE_TYPE']):
            return os.environ['UM_NODE_TYPE']
        else:
            error("Please set environment variable UM_NODE_TYPE"\
                  "to one of %s." % nodeinfos.keys())
            sys.exit(1)
    
    else:
        error("Could neiher derived nodetype form the hostname "\
              "nor from the environment variable UM_NODE_TYPE.")
        sys.exit(1)

    return nodetype


def getnodeinfo(hostname = None):
    "Return the nodeinfos for the desired notetype"

    nodetype = getnodetype(hostname)
    nodeinfo = nodeinfos[nodetype]

    return nodeinfo


def gethostnameprefix(hostname = None):
    "Derived the hostnameprefix form the hostname"
        
    nodeinfo = getnodeinfo(hostname)
    hostnameprefix = nodeinfo['hostnameprefix']

    return hostnameprefix
    

def getnodenumber(hostname = None):
    "Derived the nodenumber from the hostname"
    
    hostnameprefix = gethostnameprefix(hostname)
    nodenumber = re.sub(hostnameprefix, '', hostname)

    return nodenumber

         
def getdeviceIP(hostname = None, device = 'ath0'):
    "Get the IP of a specific device of the specified node"

    # get ip of target
    nodeinfo   = getnodeinfo(hostname)
    nodenumber = getnodenumber(hostname)
    meshdevs   = nodeinfo['meshdevices']
    devicecfg  = meshdevs[device]
    activecfg  = deviceconfig[devicecfg]
    address    = re.sub('@NODENR', nodenumber, activecfg['address'])
    # strip bitmask
    address = address.split("/", 2)
    address = address[0]

    return ip_adress


def getimageinfo(hostname = None):
    "Return the imageinfos for the desired notetype"

    nodeinfo  = getnodeinfo(hostname)
    imageinfo = imageinfos[nodeinfo['imagetype']]

    return imageinfo


def getimagepath(hostname = None):
    "Return the imagepath for the desired notetype"

    nodeinfo = getnodeinfo(hostname, cache)
    imagepath = "%s/%s.img/%s" % (imageprefix, nodeinfo['imagetype'], nodeinfo['imageversion'])

    return imagepath
