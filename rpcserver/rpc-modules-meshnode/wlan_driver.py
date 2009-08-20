#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call
          

class Wlan_driver(RPCService):
    """Class for managing the wlan driver module"""

    #
    # Public XMLRPC Interface
    #

    @defer.inlineCallbacks
    def xmlrpc_restart(self):
        rc = yield self.reread_config()
        
        if rc == 0:
            # don't complain if stopping doesnt work
            yield self.stop()
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
        """ Check if driver module is loaded. """
        defer.returnValue(True)

    #
    # Internal stuff
    #
    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)

        # servicename in database
        self._name = "wlan_driver"
        self._config = None
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The wlan_driver service table has the following important columns
                   driver   : the driver to load (madwifi or ath5k)
                   opt_args : optional module parameters

            Will return 0 on success.
            
        """
        
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        self._config = assoc

        if not assoc.has_key("driver"):
            error("wlan_driver: Oops, configuration is broken!")
            defer.returnValue(-1)

        defer.returnValue(0)

    def getModuleName(self, driver):
        if (driver == "madwifi"):
            return "ath_pci"
        else:
            return driver

    @defer.inlineCallbacks
    def ath5k_hack(self):
        """ Workaround to delete autocreated interfaces """
        created_interfaces  = [ "wlan0", "wlan1" ]
        for interface in created_interfaces:
            cmd = [ "iw", "dev", interface, "del" ]
            (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
            if (rc != 0):
                error("ath5k_hack(): Command failed with RC=%d", rc)

    @defer.inlineCallbacks
    def start(self):
        """ This function loads the driver module. """
        modulename = self.getModuleName(self._config['driver'])       

        cmd = [ "/sbin/modprobe", modulename ]
        if self._config['opt_args']:
            cmd.append(self._config['opt_args'])
            
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("wlan_device.start(): Command failed with RC=%d", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
        else:
            if modulename == "ath5k":
                yield self.ath5k_hack()
        yield self._parent._dbpool.startedService(self._config,
                                                  rc, message=stderr)
              
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function unloads the driver module """
        modulename = self.getModuleName(self._config['driver'])       

        cmd = [ "/sbin/rmmod", modulename ]               
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("wlan_device.stop(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
        yield self._parent._dbpool.stoppedService(self._config,
                                                  rc, message=stderr)            
        defer.returnValue(rc)
