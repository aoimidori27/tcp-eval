#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical
from tempfile import mkstemp

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call, twisted_sleep
from um_node import Node          

class Wlan_parameters(RPCService):
    """Class for configuring VAPs (ESSID, txpower etc) """


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
        """ This is not implemented """
        return self.stop();

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
        self._name = "wlan_parameters"

        # stores a list of device configuration
        self._configs = None
        
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The wlan_Device service table has the following important columns
                 interface  : interface to configure
                 essid      : the essid
                 channel    : the channel
                 txpower    : the txpower
                 mcast_rate : the baserate                 

            Will return 0 on success.
            
        """
        
        list_of_assoc = yield self._parent._dbpool.getCurrentServiceConfigMany(self._name)
        if not list_of_assoc:
            info("Found no configuration.")
            defer.returnValue(-1)

        self._configs = list_of_assoc

        defer.returnValue(0)
                                   

    @defer.inlineCallbacks
    def iwcmd(self, cmd, config, attribute):
        """ Helper function to invoke iwconfig and iwpriv """

        value = config[attribute]

        rc = 0
        if value:
            value = str(value)
            interface = config["interface"]
            self.info('Setting %s of %s to %s' %(attribute, interface, value))
            cmd = [ cmd , interface,
                    attribute, value ]
            (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
            if len(stdout):
                debug(stdout)
            if (rc != 0):
                self.error("failed to set %s of %s" %(attribute,interface))
                self.stderror(stderr)

            
        defer.returnValue(rc)
                

    @defer.inlineCallbacks
    def start(self):
        """ This function sets up vaps. """

        final_rc = 0
        nodenr = Node().getnumber()

        for config in self._configs:
            interface  = config["interface"]
            channel    = config["channel"]
            txpower    = config["txpower"]
            mcast_rate = config["mcast_rate"]

            stderr = "";

            rc = yield self.iwcmd("iwconfig", config, "essid")
            if rc != 0:
                stderr = stderr+"setting essid failed\n"
                final_rc = rc

            rc = yield self.iwcmd("iwconfig", config, "channel")
            if rc != 0:
                stderr = stderr+"setting channel failed\n"
                final_rc = rc

            # wait some time before trying to adjust txpower
            yield twisted_sleep(3)
            rc = yield self.iwcmd("iwconfig", config, "txpower")
            # give him a second chance on this, this maybe timing critical
            if rc != 0:
                info("Setting txpower failed, try another time...")
                yield twisted_sleep(5)
                rc = yield self.iwcmd("iwconfig", config, "txpower")    
            if rc != 0:
                stderr = stderr+"setting txpower failed\n"
                final_rc = rc

            rc = yield self.iwcmd("iwpriv", config, "mcast_rate")            
            if rc != 0:
                stderr = stderr+"setting mcast_rate failed\n"
                final_rc = rc
                
            yield self._parent._dbpool.startedService(config,
                                                      final_rc, message=stderr)
            
                                                        
        defer.returnValue(final_rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function resets vaps to reasonable defaults. """

        final_rc = 0
        nodenr = Node().getnumber()

        for config in self._configs:
            interface  = config["interface"]

            config["channel"] = 1;
            config["mcast_rate"] = 1000;
            config["txpower"] = 17;

            stderr = "";

            rc = yield self.iwcmd("iwconfig", config, "essid")
            if rc != 0:
                stderr = stderr+"setting essid failed\n"
                final_rc = rc

            rc = yield self.iwcmd("iwconfig", config, "channel")
            if rc != 0:
                stderr = stderr+"setting channel failed\n"
                final_rc = rc

            rc = yield self.iwcmd("iwconfig", config, "txpower")
            if rc != 0:
                stderr = stderr+"setting txpower failed\n"
                final_rc = rc

            rc = yield self.iwcmd("iwpriv", config, "mcast_rate")            
            if rc != 0:
                stderr = stderr+"setting mcast_rate failed\n"
                final_rc = rc
                
            yield self._parent._dbpool.stoppedService(config,
                                                      final_rc, message=stderr)
            
                                                        
        defer.returnValue(final_rc)







        
        
