#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
from logging import info, debug, warn, error, critical
from tempfile import mkstemp

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_twisted import twisted_execute, twisted_call
          

class Olsr(RPCService):
    """Class for managing the OLSR daemon"""


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
        """ Check if olsrd is alive by looking in the process table. """
        cmd = ["/bin/ps", "-C", "olsrd5" ]
        rc = call(cmd, shell=False, raiseError=False)

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
        self._configfile = None
        self._daemon = "/usr/local/sbin/olsrd5"
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The olsr service table has the following important columns
                 config : the config file contents

            Will return 0 on success.
            
        """
        
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        if assoc.has_key("flavor"):
            self._flavor = assoc["flavor"]            

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
                                   

    @defer.inlineCallbacks
    def start(self):
        """ This function invokes start-stop daemon to bring up olsrd """
        
        args = ["-f", self._configfile, "-d", "0"]
        cmd = [ "start-stop-daemon", "--start",  
                "--exec", self._daemon,
                "--"]
        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("olsr.start(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
                
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function invokes start-stop-daemon to stop olsrd """

        cmd = [ "start-stop-daemon", "--stop",  "--quiet",
                "--exec", self._daemon,
                "--signal", "TERM",
                "--retry",  "5"]
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("olsr.stop(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
            
        defer.returnValue(rc)






        
        
