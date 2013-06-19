#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import re
import socket
from logging import info, debug, warn, error

# umic-mesh imports
import um_config as config

class Node(object):
    """Provides access to information about a certain UMIC-Mesh.net node."""

    def __init__(self, hostname = None, node_type = None):
        """Creates a new Node object with two following parameters: hostname and
           node_type.

           1. If the hostname is None, socket.gethostname() will be used to determine
           the hostname. The node type will be derived from the hostname and can be
           overriden by setting the parameter node_type.

           2. If the hostname is a string, the string will be used to set the hostname.
           The node type will be derived from the hostname and can be overriden by
           setting the parameter node_type.

           3. If the hostname is an integer, the node type is mandatory. Both parameter
           will be used used to determine the correct hostname.
        """

        # object variables
        self._hostname = None
        self._type = None
        self._info = None

        # if the node_type is set, we need validity check
        if node_type is not None and Node.isValidType(node_type):
            self._type = node_type
            self._info = config.node_info[self._type]

        # first case
        if hostname is None:
            self._hostname = self.getHostname()

        # third case
        elif type(hostname) is int:
            if node_type is not None:
                self._hostname = "%s%s" %(Node.hostnamePrefix(node_type),
                                          str(hostname))
            else:
                raise NodeException("If the hostname is an integer, the "\
                                    "parameter node_type is mandatory.")
        # second case
        else:
            self._hostname = hostname

        # if the node_type is not set, we can now derive the node_type from the hostname
        if node_type is None:
            node_type_list = []
            for node_type in Node.types():
                if re.match(Node.hostnamePrefix(node_type), self._hostname):
                    node_type_list.append(node_type)

            if len(node_type_list) == 1:
                self._type = node_type_list[0]
                self._info = config.node_info[self._type]
            elif len(node_type_list) == 0:
                raise NodeException("Cannot derive node_type from "\
                        "hostname, as there are no types with fitting "
                        "hostname_prefix entries.")
            else:
                raise NodeException("Cannot derive node_type from "
                        "hostname, as there are multiple types with fitting "
                        "hostname_prefix entries: %s" % node_type_list)

    @staticmethod
    def types():
        """Return the names of all possible node types"""
        return config.node_info.keys()

    @staticmethod
    def isValidType(node_type, raiseError = True):
        """Return true if the node type is valid"""

        contained = node_type in Node.types()
        if not contained and raiseError:
            raise NodeValidityException("node_type", Node.types())
        return contained

    @staticmethod
    def vtypes():
        """Return the names of all node types that are virtualizable"""
        return filter(lambda key: config.node_info[key]["virtual"],
                      config.node_info.keys())

    @staticmethod
    def isValidVtype(node_type, raiseError = True):
        """Return true if the node type is valid and virtualizable"""

        contained = node_type in Node.vtypes()
        if not contained and raiseError:
            raise NodeValidityException("node_type", Node.vtypes())
        return contained

    @staticmethod
    def hostnamePrefix(node_type):
        """Return the hostname prefix of the node type"""

        Node.isValidType(node_type)
        return config.node_info[node_type]["hostname_prefix"]

    @staticmethod
    def images(node_type):
        """Return a list of all possible images names for the node type"""

        Node.isValidType(node_type)
        return config.node_info[node_type]["image_names"]

    @staticmethod
    def isValidImage(image_name, node_type, raiseError = True):
        """Return true if the image name is valid for the node type"""

        contained = image_name in Node.images(node_type)
        if not contained and raiseError:
            raise NodeValidityException("image_name", Node.images(node_type))
        return contained

    @staticmethod
    def virtualizable(node_type):
        """Return true if the node type virtualizable"""

        Node.isValidType(node_type)
        return config.node_info[node_type]["virtual"]

    def getHostname(self):
        """Return the hostname of the node"""

        if not self._hostname:
            self._hostname = socket.gethostname()
        return self._hostname

    def getType(self):
        """Return the node type of the node"""
        return self._type

    def getHostnamePrefix(self):
        """Return the hostname prefix of the node"""
        return self._info["hostname_prefix"]

    def getImages(self):
        """Return the list of all possible images names for the node"""
        return self._info["image_names"]

    def isVirtual(self):
        """Return true if the node is virtualizable"""
        return self._info["virtual"]

    def getNumber(self):
        """Derives the node number from the hostname"""
        return int(re.sub(self.getHostnamePrefix(), "", self._hostname))

    def getIPaddress(self, device = "ath0"):
        """Get the IP address of a specific device without the netmask. If device
           is None only the hostname will be looked up.
        """

        if device is None:
            name = self._hostname
        else:
            name = "%s.%s" %(device, self._hostname)

        try:
            address = socket.gethostbyname(name)
        except socket.gaierror, inst:
            raise NodeException("Failed to lookup %s:%s "% (name, inst.args[0]))

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
    def __init__(self, value):
        Exception.__init__(self)
        self._value = value

    def __str__(self):
        return repr(self._value)


class NodeValidityException(NodeException):
    def __init__(self, value, choices):
        NodeException.__init__(self, value)
        self._choices = choices

    def __str__(self):
        return 'Invalid "%s". Please set it to one of the following: %s' \
                % (self._value, self._choices)

