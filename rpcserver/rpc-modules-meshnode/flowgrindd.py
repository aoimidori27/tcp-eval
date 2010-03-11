#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
from logging import info, debug, warn, error, critical
import os

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

# umic-mesh imports
from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call

class Flowgrindd(RPCService):
    """Class for managing the flowgrind daemon"""

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
        """Check if flowgrinddd is alive by looking in the process table."""
        cmd = ["/bin/ps", "-C", self._daemon.split('/')[-1]]
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

        self._name = "flowgrindd"
        self._config = None
        self._daemon = None
        self._daemon_path = "/usr/local/sbin"

    @defer.inlineCallbacks
    def reread_config(self):
        """Rereads the configuration

           The flowgrindd service table has the following important columns
                port : the port on which the server should listen
           Will return 0 on success.
        """

        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        self._config = assoc
        self._daemon = os.path.join(self._daemon_path, assoc['exename'])

        if not self._config["port"]: self._config["port"] = 5999

        defer.returnValue(0)

    @defer.inlineCallbacks
    def start(self):
        """This function invokes start-stop daemon to bring up flowgrindd"""

        args = ["-p", "%u" %self._config["port"]]
        if (self._config["verbose"]):
            args.extend("-D")
        cmd = [ "start-stop-daemon", "--start",
                "--exec", self._daemon,
                "--"]
        cmd.extend(args)
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("flowgrindd.start(): Command failed with RC=%s", rc)
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
        """This function invokes start-stop-daemon to stop flowgrindd"""

        cmd = [ "start-stop-daemon", "--stop",  "--quiet",
                "--exec", self._daemon,
                "--signal", "TERM",
                "--retry",  "5"]
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("flowgrindd.stop(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)
        yield self._parent._dbpool.stoppedService(self._config,
                                                  rc, message=stderr)
        defer.returnValue(rc)
