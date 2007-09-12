#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_twisted import twisted_execute, twisted_call
          

class Netconsole(RPCService):
    """Class for managing the netconsole module"""


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
        """ Check if netconsole module is loaded. """
        cmd = "/sbin/lsmod | grep netconsole"
        rc = call(cmd, shell=True, raiseError=False)

        if (rc==0):
            return True
        else:
            return False


    #
    # Internal stuff
    #
    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)

        self._name = "olsr"
        self._flavor = None
        self._logserver = None
        self._logport   = None
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The netconsole service table has the following important columns
                   logserver : the server to log to
                   logport   : the server port to use

            Will return 0 on success.
            
        """
        
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        if assoc.has_key("flavor"):
            self._flavor = assoc["flavor"]

        if not assoc.has_key("logserver") or not assoc_has_key("logport"):
            error("netconsole: Oops, configuration is broken!")
            defer.returnValue(-1)

        self._logserver = assoc["logserver"]
        self._logport   = assoc["logport"]

        defer.returnValue(0)
                                   

    @defer.inlineCallbacks
    def start(self):
        """ This function loads the netconsole module. """
        
        cmd = [ "/usr/local/sbin/um_netconsole", self._logserver,
                self._logport ]
        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("netconsole.start(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
                
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function unloads the netconsole module """

        cmd = [ "/sbin/rmmod", "netconsole" ]               
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("netconsole.stop(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
            
        defer.returnValue(rc)






        
        
