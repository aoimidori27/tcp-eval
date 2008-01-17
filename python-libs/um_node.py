#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import re
import socket
from logging import info, debug, warn, error

# umic-mesh imports
from um_config import *


class Node(object):
    """Provides access to information about a certain UMIC-Mesh.net node."""
    
    def __init__(self, hostname = None, nodetype = None):
        """
        Creates a new Node object with two following parameters: hostname and
        nodetype.
            
        1. If the hostname is None, socket.gethostname() will be used to determine
        the hostname. The nodetype will be derived from the hostname and can be
        overriden by setting the parameter nodetype.
             
        2. If the hostname is a string, the string will be used to set the hostname.
        The nodetype will be derived from the hostname and can be overriden by
        setting the parameter nodetype.
        
        3. If the hostname is an integer, the nodetype is mandatory. Both parameter
        will be used used to determine the correct hostname.
        """

        # object variables
        self._hostname = None
        self._type = None
        self._info = None
        
        # if the nodetype is set, we need validity check
        if nodetype:
            if nodetype in nodeinfos:
                self._type = nodetype
                self._info = nodeinfos[self._type]
            else:
                raise NodeException('Invalid "nodetype". Please set it to one of %s.'
                                    % Node.types())
        # first case
        if not hostname:
            self._hostname = self.gethostname()
        
        # third case
        elif type(hostname) is int:
            if not nodetype:
                raise NodeException('If the hostname is an integer, the "nodetype" '
                                    'is mandatory.')
            else:
                self._hostname = "%s%s" %(self._info["hostnameprefix"], str(hostname))

        # second case
        else:     
            self._hostname = hostname
        
        # if the nodetype is not set, we can now derive the nodetype from the hostname
        if not nodetype:           
            nodetypelist = []
            for (nodetype, nodeinfo) in nodeinfos.iteritems():
                if re.match(nodeinfo["hostnameprefix"], self._hostname):
                    nodetypelist.append(nodetype)

            if len(nodetypelist) == 1:
                self._type = nodetypelist[0]
                self._info = nodeinfos[self._type]
            elif len(nodetypelist) == 0:
                raise NodeException('Cannot derive "nodetype" from '
                        'hostname, as there are no types with fitting '
                        '"hostnameprefix" entries.')
            else:
                raise NodeException('Cannot derive "nodetype" from '
                        'hostname, as there are multiple types with fitting '
                        '"hostnameprefix" entries: %s' % nodetypelist)


    @staticmethod
    def types():
        """Return the names of the possible node types"""
        
        return imageinfos.keys() 


    def gettype(self):
        """Return the nodetype of the node"""

        return self._type


    def getinfo(self):
        """Return the nodeinfos of the node"""

        return self._info


    def gethostname(self):
        """Return the hostname of the node"""
    
        if not self._hostname:
            self._hostname = socket.gethostname()
        return self._hostname
 

    def gethostnameprefix(self):
        """Return the hostnameprefix of thee node"""

        return self._info["hostnameprefix"]


    def getnumber(self):
        """Derives the nodenumber from the hostname"""

        return int(re.sub(self.gethostnameprefix(), "", self._hostname))


    def getipaddress(self, device = "ath0"):
        """Get the IP address of a specific device without the netmask"""

        name = "%s.%s" %(device, self._hostname)
    
        try:
            address = socket.gethostbyname(name)
        except socket.gaierror, inst:
            error("Failed to lookup %s:%s "% (name, inst.args[0]))
            raise

        return address



class VMeshHost(Node):
    def __init__(self, hostname = None):
        Node.__init__(self, hostname, "vmeshhost")



class VMeshRouter(Node):
    def __init__(self, hostname = None):
        Node.__init__(self, hostname, "vmeshrouter")



class MeshRouter(Node):
    def __init__(self, hostname = None):
        Node.__init__(self, hostname, "meshrouter")



class NodeException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
