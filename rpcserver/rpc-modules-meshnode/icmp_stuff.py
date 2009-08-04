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
from subprocess import Popen,PIPE
from time import sleep

class Icmp_stuff(RPCService):
    #
    # Public XMLRPC Interface
    #

    @defer.inlineCallbacks
    def xmlrpc_restart(self):
        rc = yield self.reread_config()
        rc = yield self.stop()
        rc = yield self.start()
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_start(self):
        rc = yield self.reread_config()
        rc =  yield self.start()
        defer.returnValue(rc)

    def xmlrpc_stop(self):
        return self.stop()

    #
    # Internal stuff
    #
    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)
        self._name = "icmp_stuff"
        self._config = None

    
    @defer.inlineCallbacks
    def reread_config(self):
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        self._config = assoc
        defer.returnValue(0)                                  


    def start(self):
      
	Popen(["/sbin/route", "del", "default"], shell=False)
	Popen(["/sbin/route", "del", "-net", "192.168.9.0/24", "dev", "ath0"], shell=False)
	Popen(["/sbin/sysctl", "net.ipv4.tcp_retries2=999"], shell=False)
	Popen(["/sbin/sysctl", "net.ipv4.conf.all.accept_redirects=0"], shell=False)
	Popen(["/sbin/sysctl", "net.ipv4.conf.all.send_redirects=0"], shell=False)


    def stop(self):
    	pass


