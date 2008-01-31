#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical
from tempfile import mkstemp

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call
from um_node import Node          

class Wlan_ipconfig(RPCService):
    """Class for configuring static ip addresses for VAPs"""


    #
    # Public XMLRPC Interface
    #

    @defer.inlineCallbacks
    def xmlrpc_restart(self):        

        # don't complain if stopping doesnt work
        yield self.stop()
        
        rc = yield self.reread_config()
        if rc == 0:
            rc = yield self.start()
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_start(self):
        rc = yield self.reread_config()
        if rc == 0:            
            rc = yield self.start()
        defer.returnValue(rc)

    def xmlrpc_stop(self):
        return self.stop()

    @defer.inlineCallbacks
    def xmlrpc_isAlive(self):
        """ returns always true """
        defer.returnValue(True)


    #
    # Internal stuff
    #
    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)

        # service name in the database
        self._name = "wlan_ipconfig"

        # stores a list of device configuration
        self._configs = None
        
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The wlan_Device service table has the following important columns
                 interface : interface to configure
                 prefix    : the ip prefix
                 netmask   : the netmask to set

            Will return 0 on success.
            
        """
        
        list_of_assoc = yield self._parent._dbpool.getCurrentServiceConfigMany(self._name)
        if not list_of_assoc:
            info("Found no configuration.")
            defer.returnValue(-1)

        self._configs = list_of_assoc

        defer.returnValue(0)
                                   

    @defer.inlineCallbacks
    def start(self):
        """ This function brings up the interfaces. """

        final_rc = 0
        nodenr = Node().getnumber()

        for config in self._configs:
            address = "%s%u" %(config["ipprefix"], nodenr)
            
            cmd = [ "ifconfig", config["interface"],
                     address,
                    "netmask",  config["netmask"],
                    "up" ]            

            self.info("Bringing %s up..." %config["interface"])
            (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
            if len(stdout):
                debug(stdout)

            if (rc != 0):
                self.error("start(): failed to bring %s up" %config["interface"])
                for line in stderr.splitlines():
                    error(" %s" %line)
                final_rc = rc

            yield self._parent._dbpool.startedService(config,
                                                      rc, message=stderr)
                
        defer.returnValue(final_rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function shuts the interfaces down. """

        final_rc = 0
        if not self._configs:
            self.warn("stop(): not initialized with configs")
            defer.returnValue(2)

        for config in self._configs:
            
            cmd = [ "ifconfig", config["interface"],
                    "0.0.0.0",
                    "down" ]            

            self.info("Bringing %s down..." %config["interface"])
            (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
            if len(stdout):
                debug(stdout)

            if (rc != 0):
                self.error("stop(): failed to delete %s" %config["interface"])
                for line in stderr.splitlines():
                    error(" %s" %line)
                final_rc = rc
            
            yield self._parent._dbpool.stoppedService(config,
                                                      rc, message=stderr)
        defer.returnValue(final_rc)







        
        
