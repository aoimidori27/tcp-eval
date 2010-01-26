#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

# umic-mesh imports
from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call

class Batman(RPCService):
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
        """Check if batman is alive by looking in the process table."""

        cmd = ["/bin/ps", "-C", "batmand" ]
        rc = yield twisted_call(cmd, shell=False)

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

        self._name = "batman"
        self._config = None
        self._configfile = None
        self._daemon = "/usr/local/sbin/batmand"

    @defer.inlineCallbacks
    def reread_config(self):
        """Rereads the configuration

           The batman service table has the following important columns
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
        """This function invokes start-stop daemon to bring up batmand"""

        cmd = [ "start-stop-daemon", "--start",
                "--exec", self._daemon,
                "--", self._config["interface"]]
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("batman.start(): Command failed with RC=%s", rc)
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
        """This function invokes start-stop-daemon to stop batmand"""

        cmd = [ "start-stop-daemon", "--stop",  "--quiet",
                "--exec", self._daemon,
                "--signal", "TERM",
                "--retry",  "5"]
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("batman.stop(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
        yield self._parent._dbpool.stoppedService(self._config,
                                                  rc, message=stderr)
        defer.returnValue(rc)
