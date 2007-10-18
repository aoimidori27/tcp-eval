#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call
          

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
        rc = yield twisted_call(cmd, shell=True)

        if (rc==0):
            defer.returnValue(True)
        else:
            defer.returnValue(False)

    #
    # Internal stuff
    #
    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)

        # servicename in database
        self._name = "netconsole"
        self._config = None
    
    
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

        self._config = assoc

        if not assoc.has_key("logserver") or not assoc.has_key("logport"):
            error("netconsole: Oops, configuration is broken!")
            defer.returnValue(-1)

        defer.returnValue(0)
                                   

    @defer.inlineCallbacks
    def start(self):
        """ This function loads the netconsole module. """
        
        cmd = [ "/usr/local/sbin/um_netconsole", self._config['logserver'],
                self._config['logport'].__str__() ]
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("netconsole.start(): Command failed with RC=%d", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
        yield self._parent._dbpool.startedService(self._config,
                                                  rc, message=stderr)
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
        yield self._parent._dbpool.stoppedService(self._config,
                                                  rc, message=stderr)            
        defer.returnValue(rc)






        
        
