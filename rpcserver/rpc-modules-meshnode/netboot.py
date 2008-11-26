#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call
          

class Netboot(RPCService):
    """Class for managing the netboot module"""


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
        """ Check if kernel is loaded ;-) """
        defer.returnValue(True)
    
    #
    # Internal stuff
    #
    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)

        # servicename in database
        self._name = "netboot"
        self._config = None
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The netboot service table has the following important columns
                   logserver : the server to log to
                   logport   : the server port to use

            Will return 0 on success.
            
        """
        
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        self._config = assoc

        if not assoc.has_key("version") or not assoc.has_key("flavorName"):
            error("netboot: Oops, configuration is broken!")
            defer.returnValue(-1)

        defer.returnValue(0)
                                   

    @defer.inlineCallbacks
    def start(self):
        """ This function just checks if the node has booted the correct profile. If not in initiates a reboot. """
        rc = 0

        # parse kernel cmdline
        fh = file("/proc/cmdline")
        cmdline = fh.readline()
        fh.close()
        assoc = dict()
        for pair in cmdline.split():
            tmpary = pair.split('=', 1)
            key = tmpary[0]
            if len(tmpary) == 2:
                value = tmpary[1]
            else:
                value = None
            assoc[key] = value
		
        # compare with current config (version and name should match)
        restart = False
        if not assoc.has_key("id"):
            error("netboot: Oops, failed to extract pxe flavor from kernel cmdline")
            defer.returnValue(-1)
        else:
            restart = restart or (assoc["id"] != self._config["flavorName"])

        if not assoc.has_key("version"):
            warn("netboot: Failed to extract version from kernel cmdline, ignoring...")
        else:
            restart = restart or (assoc["version"] != str(self._config["version"]))
        
        if restart:
            info("I have to start another pxe configuration: flavor=%s id=%s" %(self._config["flavorName"], self._config["version"]))
            yield twisted_execute(["/sbin/shutdown", "-r","now"], shell=False)
        else:
            info("Config and /proc/cmdline match, doing nothing.")
            yield self._parent._dbpool.startedService(self._config,
                                                      rc, message="")
 
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function does nothing,  as it is not possible to "unload" a kernel """
        rc = 0
        yield self._parent._dbpool.stoppedService(self._config,
                                                  rc, message="")
        defer.returnValue(rc)
