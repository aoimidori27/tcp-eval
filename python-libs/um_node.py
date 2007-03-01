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
                raise NodeTypeException('Invalid value for \"NODETYPE\"'
                        'Please set it to one of %s.'% nodeinfos.keys())
        
        else:
            # Compute list of nodetypes which match for hostname
            f = lambda x: re.match(um_config.nodeinfos[f]['hostnameprefix'])
            type_list = filter(f, hostname)

            if len(type_list) == 1:
                self.type = type_list[0]
            else:
                raise NodeTypeException('\"NODETYPE\" cannot be derived from'
                        'hostname, as there are multiple types with fitting'
                        'hostnameprefix" entries: %s' % cannodetype)


    def gettype(self):
        "Returns the nodetype of the node"

        return self.type
    

    def hostname(self):
        "Returns the hostname of the node"

        return self.hostname


    def info(self):
        "Returns the nodeinfos of the node"

        return nodeinfos[self.type]


    def hostnameprefix(self):
        "Derives the hostnameprefix from the hostname"

        return self.info()['hostnameprefix']


    def number(self):
        "Derives the nodenumber from the hostname"

        return re.sub(self.hostnameprefix(), '', self.hostname)


    def ipaddress(self, device = 'ath0'):
        "Get the IP of a specific device of the node"

        # get ip of target
        meshdevs   = self.info()['meshdevices']
        devicecfg  = meshdevs[device]
        activecfg  = deviceconfig[devicecfg]
        address    = re.sub('@NODENR', self.number(), activecfg['address'])
        
        return adress


    def ipconfig(self, device = 'ath0'):
        "Get the IP of a specific device of the node"
        
        meshdevs  = self.info()['meshdevices']
        devicecfg = meshdevs[device]
        activecfg = deviceconfig[devicecfg]       
        netmask   = activecfg['netmask']
        address   = "%s/%s" %(self.deviceIP(), netmask)

        return address


    def imageinfo(self):
        "Return the imageinfos for the node"

        return imageinfos[self.info()['imagetype']]


    def imagepath(self):
        "Return the imagepath for the node"

        nodeinfo = self.info()
        return "%s/%s.img/%s" % (imageprefix, nodeinfo['imagetype'], nodeinfo['imageversion'])



class NodeTypeException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
