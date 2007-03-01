#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, re
from socket import gethostname

# umic-mesh imports
from um_config import *


class Node(object):
    "Provides access to configuration infos about a certain host (or a node type)"

    def __init__(self, hostname = None, type = None):
        """ Creates a new Node object.

        If hostname is None, gethostname() is used. The \"NODETYPE\" will
        derived from the hostname and can be overriden by setting the
        parameter nodetype.

        If no nodetype can be derived, a NodeTypeException is raised.
        """

        # object variables
        self.hostname = ''
        self.type = ''

        if not hostname == None:
            self.hostname = hostname
        else:
            self.hostname = gethostname()


        if not type == None:
        
            if type in nodeinfos:
                self.type = type
            else:
                raise NodeTypeException('Invalid value for NODETYPE'
                        'Please set it to one of %s.'% nodeinfos.keys())
        
        else:
            # Compute list of nodetypes which match for hostname
            type_list = []
            for (nodetype, nodeinfo) in nodeinfos.iteritems():
                if re.match(nodeinfo['hostnameprefix'], self.hostname):
                    type_list.append(nodetype)

            if len(type_list) == 1:
                self.type = type_list[0]
            elif len(type_list) == 0:
                raise NodeTypeException('Cannot derived NODETYPE from'
                        'hostname, as there no types with fitting'
                        'hostnameprefix" entries: %s' % type_list)
            else:
                raise NodeTypeException('Cannot derived NODETYPE from'
                        'hostname, as there multiple types with fitting'
                        'hostnameprefix" entries: %s' % type_list)


    def gettype(self):
        "Returns the nodetype of the node"

        return self.type
    

    def gethostname(self):
        "Returns the hostname of the node"

        return self.hostname


    def getinfo(self):
        "Returns the nodeinfos of the node"

        return nodeinfos[self.type]


    def gethostnameprefix(self):
        "Derives the hostnameprefix from the hostname"

        return self.getinfo()['hostnameprefix']


    def getnumber(self):
        "Derives the nodenumber from the hostname"

        return re.sub(self.gethostnameprefix(), '', self.hostname)


    def getipaddress(self, device = 'ath0'):
        "Get the IP of a specific device of the node"

        # get ip of target
        meshdevs   = self.info()['meshdevices']
        devicecfg  = meshdevs[device]
        activecfg  = deviceconfig[devicecfg]
        address    = re.sub('@NODENR', self.number(), activecfg['address'])
        
        return adress


    def getipconfig(self, device = 'ath0'):
        "Get the IP of a specific device of the node"
        
        meshdevs  = self.info()['meshdevices']
        devicecfg = meshdevs[device]
        activecfg = deviceconfig[devicecfg]       
        netmask   = activecfg['netmask']
        address   = "%s/%s" %(self.getipconfig(), netmask)

        return address


    def getimageinfo(self):
        "Return the imageinfos for the node"

        return imageinfos[self.getinfo()['imagetype']]


    def getimagepath(self):
        "Return the imagepath for the node"

        nodeinfo = self.getinfo()
        return "%s/%s.img/%s" % (imageprefix, nodeinfo['imagetype'], nodeinfo['imageversion'])



class NodeTypeException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
