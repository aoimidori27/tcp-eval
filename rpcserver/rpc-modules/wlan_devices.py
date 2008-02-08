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
          

class Wlan_devices(RPCService):
    """Class for loading wifi drivers and create VAPs"""


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
        self._name = "wlan_devices"

        # stores a list of device configuration
        self._configs = None
        
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The wlan_Device service table has the following important columns
                 wlandev   : native base device (eg. wifi0)
                 vap       : the virtual device to create (eg. ath0)
                 wlanmode  : the mode of the device to create (eg. adhoc)
                 bssid     : a flag to override the bssid
                 nosbeacon : a flag to override sending of hardware beacons

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
        """ This function creates the vaps. """

        final_rc = 0

        for config in self._configs:
            
            cmd = [ "wlanconfig", config["vap"], "create",
                    "wlandev",  config["wlandev"],
                    "wlanmode", config["wlanmode"] ]
            
            if config["bssid"]:
                cmd.append("bssid")
            else:
                cmd.append("-bssid")            

            if config["nosbeacon"]:
                cmd.append("nosbeacon")
                
            (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
            if len(stdout):
                debug(stdout)

            if (rc != 0):
                error("wlan_devices.start(): failed to create %s" %config["vap"])
                for line in stderr.splitlines():
                    error(" %s" %line)
                final_rc = rc
            else:
                cmd = [ "ip", "link", "set", config["vap"], "up" ]
                yield twisted_call(cmd, shell=False)

            yield self._parent._dbpool.startedService(config,
                                                      rc, message=stderr)
                
        defer.returnValue(final_rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function destroys the vaps. """

        final_rc = 0
        if not self._configs:
            warn("wlan_devices.stop() not initialized with configs")
            defer.returnValue(2)

        for config in self._configs:
            cmd = [ "ip", "link", "set", config["vap"], "down" ]
            yield twisted_call(cmd, shell=False)
            
            cmd = [ "wlanconfig", config["vap"], "destroy" ]            
                
            (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
            if len(stdout):
                debug(stdout)

            if (rc != 0):
                error("wlan_devices.stop(): failed to destroy %s" %config["vap"])
                for line in stderr.splitlines():
                    error(" %s" %line)
                final_rc = rc
            yield self._parent._dbpool.stoppedService(config,
                                                      rc, message=stderr)
                
        defer.returnValue(final_rc)
