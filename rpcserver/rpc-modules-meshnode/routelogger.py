#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import os
import stat
import socket
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

# umic-mesh imports
from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call

class Routelogger(RPCService):
    """Class for managing the route monitor daemon"""

    #
    # Public XMLRPC Interface
    #

    @defer.inlineCallbacks
    def xmlrpc_restart(self, logDir):
        rc = yield self.reread_config()

        rc = self.stop()
        rc = self.start(logDir) and rc
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_start(self, logdir):
        info("rpc starting routelogger")
        rc = yield self.reread_config()
        rc = yield self.start(logdir)
        defer.returnValue(rc)

    def xmlrpc_stop(self):
        return self.stop()

    @defer.inlineCallbacks
    def xmlrpc_isAlive(self):
        """Check if the routelogger is alive by looking in the process table."""

        cmd = ["/bin/ps", "-C", "routeLogger.py" ]
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

        self._name = "routelogger"
        self._config = None
        self._daemon = "/sbin/rtmon"
        self._pidfile = "/tmp/routeLogger.pid"
        self._hostname = socket.gethostname()

    @defer.inlineCallbacks
    def reread_config(self):
        assoc = yield self._parent._dbpool.getCurrentServiceConfig(self._name)
        if not assoc:
            info("Found no configuration")
            defer.returnValue(-1)
        self._config = assoc
        defer.returnValue(0)

    @defer.inlineCallbacks
    def start(self, logdir):
        """This function invokes start-stop daemon to bring up the route logger"""

        if not os.path.exists(logdir):
        info("%s does not exist. Trying to create" % logdir)
        try:
            os.mkdir(logdir)
            os.chmod(logdir, os.stat(logdir)[0] | stat.S_IWOTH)
        except OSError:
            error("Logdir creation failed")
            defer.returnValue(1)

        cmd = [ "start-stop-daemon", "--start", "--background",
                "--make-pidfile", "--pidfile", self._pidfile,
                "--chuid", "lukowski",
                "--exec", self._daemon,
                "--", "file", logdir + "/" + self._hostname + ".log"]
        yield twisted_call(cmd, shell=False)
        info("started routelogger")
        info(cmd)
        defer.returnValue(0)

    @defer.inlineCallbacks
    def stop(self):
        """This function invokes start-stop-daemon to stop routeLogger"""

        cmd = [ "start-stop-daemon", "--stop",
                "--pidfile", self._pidfile]
        rc = yield twisted_call(cmd)
        if (rc != 0):
            error("Failed to stop rtmon!!!")
        info("stopped routelogger")
        defer.returnValue(0)
