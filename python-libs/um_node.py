#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, re
from socket import gethostname, gethostbyname

# umic-mesh imports
from um_config import *

class Node(object):
    "Provides access to configuration infos about a certain host (or a node type)"

    def __init__(self, hostname = None, type_ = None):
        """ Creates a new Node object.

        If hostname is None, gethostname() is used. The "NODETYPE" will
        derived from the hostname and can be overriden by setting the
        parameter nodetype.

        If hostname is an int the nodetype will be used to determine the
        correct hostname. 

        If no nodetype can be derived, a NodeTypeException is raised.
        """

        # object variables
        self._hostname = ''
        self._type = ''
        self.msg = ''

        # if type is given check for validity
        if type_:
            if type_ in nodeinfos:
                self._type = type_
            else:
                raise NodeTypeException('Invalid value for NODETYPE'
                        'Please set it to one of %s.'% nodeinfos.keys())

        # if hostname is a number and type is set, generate hostname
        if type(hostname) is int and type_:
            hostname = nodeinfos[type_]['hostnameprefix']+str(hostname)            
        
        if hostname:                
            self._hostname = hostname
        else:
            self._hostname = gethostname()

        if not type_:
            # Compute list of nodetypes which match for hostname
            type_list = []
            for (nodetype, nodeinfo) in nodeinfos.iteritems():
                if re.match(nodeinfo['hostnameprefix'], self._hostname):
                    type_list.append(nodetype)

            if len(type_list) == 1:
                self._type = type_list[0]
            elif len(type_list) == 0:
                raise NodeTypeException('Cannot derive NODETYPE from'
                        ' hostname, as there are no types with fitting'
                        ' "hostnameprefix" entries.')
            else:
                raise NodeTypeException('Cannot derive NODETYPE from'
                        ' hostname, as there are multiple types with fitting'
                        ' hostnameprefix" entries: %s' % type_list)


    def type(self):
        "Returns the nodetype of the node"

        return self._type


    def hostname(self):
        "Returns the hostname of the node"

        return self._hostname


    def info(self):
        "Returns the nodeinfos of the node"

        return nodeinfos[self._type]


    def hostnameprefix(self):
        "Derives the hostnameprefix from the hostname"

        return self.info()['hostnameprefix']


    def number(self):
        "Derives the nodenumber from the hostname"

        return int(re.sub(self.hostnameprefix(), '', self.hostname()))


    def ipaddress(self, device = 'ath0'):
        "Get the IP of a specific device without the netmask of the node"

        raw_address = socket.gethostbyname(self._hostname)

        return raw_address


    def imageinfo(self):
        "Returns the imageinfos for the node"

        return imageinfos[self.info()['imagetype']]


    def imagepath(self):
        "Returns the imagepath for the node"

        nodeinfo = self.info()
        return "%s/%s" % (imageprefix, nodeinfo['imagetype'])



class NodeTypeException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
