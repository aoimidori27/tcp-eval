#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical
from tempfile import mkstemp

# twisted imports
from twisted.internet import defer, threads
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_functions import execute, CommandFailed


class Olsr(RPCService):
    """Class for managing the OLSR daemon"""

    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)

        self._name = "olsr"
        self._configfile = None
        self._daemon = "/usr/local/sbin/olsrd5"
    

    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The olsr service table has the following important columns
                 config : the config file contents
            
        """
        
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name, "mrouter1")
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-255)

        if self._configfile and os.path.exists(self._configfile):
            tempfile = file(self._configfile, 'w')
        else:
            # create new tempfile
            (temp_fd, self._configfile) = mkstemp(".conf", self._name)
            info("Created new configfile: %s", self._configfile)
            tempfile = os.fdopen(temp_fd, 'w')
        
        tempfile.write(assoc['config'])
        tempfile.close()

        defer.returnValue(0)
                                   
    
    def start(self):
        """ This function will be called within its own thread """
        
        args = ["-f", self._configfile]
        cmd = [ "start-stop-daemon", "--start",  "--quiet",
                "--exec", self._daemon,
                "--"]
        cmd.extend(args)
        rc = 0
        try:
            (stdout, stderr) = execute(cmd, shell=False)
            debug(stdout)
        except CommandFailed, inst:
            rc = inst.rc
            error(inst)
            for line in inst.stderr.splitlines():
                error(" %s" %line)
            
        return rc

    def stop(self):
        """ This function will be called within its own thread """

        cmd = [ "start-stop-daemon", "--stop",  "--quiet",
                "--exec", self._daemon,
                "--signal", "TERM",
                "--retry",  "5"]
        rc = 0
        try:
            (stdout, stderr) = execute(cmd, shell=False)
            debug(stdout)
        except CommandFailed, inst:
            rc = inst.rc
            error(inst)
            for line in inst.stderr.splitlines():
                error(" %s" %line)
            
        return rc

    @defer.inlineCallbacks
    def xmlrpc_restart(self):
        rc = yield self.reread_config()
        if rc == 0:            
            rc = yield threads.deferToThread(self.stop)
        if rc == 0:
            rc = yield threads.deferToThread(self.start)
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_start(self):
        rc = yield self.reread_config()
        if rc == 0:            
            rc = yield threads.deferToThread(self.start)
        defer.returnValue(rc)


    def xmlrpc_stop(self):
        return threads.deferToThread(self.stop)


    def xmlrpc_add(self, a, b):
        return a + b

    def xmlrpc_times(self, a, b):
        return a * b
