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
          

class Autoconf(RPCService):
    """Class for managing the AUTOCONF daemon"""


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
        """ Check if autoconf is alive by looking in the process table. """
        cmd = ["/bin/ps", "-C", "autoconf" ]
        rc = yield twisted_call(cmd, shell=False)

        if (rc==0):
            defer.returnValue(True)
        else:
            defer.returnValue(False)

    @defer.inlineCallbacks
    def xmlrpc_killalldhclient(self):
        rc = yield self.killalldhclient()
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_killalldhcpd(self):
        rc = yield self.killalldhcpd()
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_killalldhcrelay(self):
        rc = yield self.killalldhcrelay()
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_deleteipv4assignment(self, interface):
        rc = yield self.deleteipv4assignment(interface)
        defer.returnValue(rc)

    #
    # Internal stuff
    #
    def __init__(self, parent = None):
        
        # Call super constructor
        RPCService.__init__(self, parent)

        self._name = "autoconf"
        self._config = None
        self._daemon = "/usr/local/sbin/autoconf"
    
    
    @defer.inlineCallbacks
    def reread_config(self):
        """ Rereads the configuration

            The autoconf service table has the following important columns
                 config : the config file contents

            Will return 0 on success.
            
        """
        
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        self._config = assoc

        defer.returnValue(0)
                                   

    @defer.inlineCallbacks
    def start(self):
        """ This function invokes start-stop daemon to bring up autoconf """
        
        args = self._config["options"].split(" ")
        cmd = [ "start-stop-daemon", "--start",  
                "--exec", self._daemon,
                "--"]
        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("autoconf.start(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
            # when an error occurs stdout is important too
            if len(stdout):
                stderr = stderr+stdout

        yield self._parent._dbpool.startedService(self._config,
                                                  rc, message=stderr)
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function invokes start-stop-daemon to stop autoconf """

        cmd = [ "start-stop-daemon", "--stop",  "--quiet",
                "--exec", self._daemon,
                "--signal", "TERM",
                "--retry",  "5"]
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("autoconf.stop(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
        yield self._parent._dbpool.stoppedService(self._config,
                                                  rc, message=stderr)            
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def killalldhclient(self):
        """ This function invokes killall to stop all running dhclients which were not shutdown correctly by autoconf """
        
        args = [ "dhclient" ]
        cmd = [ "killall" ]
        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("autoconf.killalldhclient(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
                # when an error occurs stdout is important too
                if len(stdout):
                    stderr = stderr+stdout
                    
        #yield self._parent._dbpool.startedService(self._config,rc, message=stderr)
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def killalldhcpd(self):
        """ This function invokes killall to stop all running dhcpd servers which were not shutdown correctly by autoconf """
        
        args = [ "dhcpd" ]
        cmd = [ "killall" ]
        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("autoconf.killalldhcpd(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
                # when an error occurs stdout is important too
                if len(stdout):
                    stderr = stderr+stdout
                    
        #yield self._parent._dbpool.startedService(self._config,rc, message=stderr)
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def killalldhcrelay(self):
        """ This function invokes killall to stop all running dhcrelay which were not shutdown correctly by autoconf """
        
        args = [ "dhcrelay" ]
        cmd = [ "killall" ]
        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("autoconf.killalldhcrelay(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
                # when an error occurs stdout is important too
                if len(stdout):
                    stderr = stderr+stdout
                    
        #yield self._parent._dbpool.startedService(self._config,rc, message=stderr)
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def deleteipv4assignment(self, interface):
        """ This function invokes ip to delete current ip assignment an ath0 and ath1 """

#        args = [ "addr| grep " + interface + "| grep inet| cut -d\\  -f6" ]
        cmd = [ "ip addr| grep " + interface + "| grep inet| cut -d\  -f6" ]
#        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=True)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("autoconf.killalldhcrelay(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
                # when an error occurs stdout is important too
                if len(stdout):
                    stderr = stderr+stdout

        #yield self._parent._dbpool.startedService(self._config,rc, message=stderr)
        defer.returnValue(rc)
                                                                                                                                                    







        
        
