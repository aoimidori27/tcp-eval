#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import os
import errno
import re
import signal
import subprocess

from logging import info, debug, warn, error, critical
from tempfile import mkstemp

# twisted imports
from twisted.internet import defer, protocol, reactor, threads
from twisted.internet import error as twisted_error
from twisted.web import xmlrpc

from um_rpcservice import RPCService
from um_functions import execute, CommandFailed
from um_node import Node


class Tcpdump(xmlrpc.XMLRPC):
    """Class for managing the packet capturin"""

    NOT_RUNNING = 1
    STOPPING_FAILED = 2
    STOPPED = 3

    def __init__(self, parent = None):

        # Call super constructor
        xmlrpc.XMLRPC.__init__(self)

        if os.path.exists("/usr/local/sbin/tcpdump"):
            self._daemon = "/usr/local/sbin/tcpdump"
        else:
            self._daemon = "/usr/sbin/tcpdump"

        self._name = "tcpdump"
        self._proc = None


    @defer.inlineCallbacks
    def xmlrpc_start(self, iface, expr):
        if self._proc is not None and self._proc.active():
            error("Tcpdump already started!")
            defer.returnValue((False, ""))

        # -Z?
        cmd = [self._daemon, "-i", iface, "-w", "-", expr]

#        dir = "/mnt/scratch/%s/tcpdump" % Node().hostname()
        dir = "/tmp"

        try:
            os.mkdir(dir)
            os.chmod(dir, 0777)
        except OSError, inst:
            if inst.errno == errno.EEXIST:
                pass
            else:
                error(inst)
                defer.returnValue((False, ""))

        try:
            temp_fd, temp_file = mkstemp(suffix=".pcap", dir=dir)
        except OSError, inst:
            error(inst)
            defer.returnValue((False, ""))

        self._proc = _ProcessProtocol()
        reactor.spawnProcess(self._proc, self._daemon, args = cmd, path='/',
                childFDs = {1: temp_fd, 2: "r"})
        os.close(temp_fd)

        success, status, stderr = yield self._proc.deferred()

        if not success:
            error("Tcpdump failed (exit status: %s):" % status)
            error(stderr)
            os.unlink(temp_file)
            defer.returnValue((False, ""))
        else:
            defer.returnValue((True, temp_file))

    @defer.inlineCallbacks
    def xmlrpc_stop(self):
        if self._proc is None:
            defer.returnValue(Tcpdump.NOT_RUNNING)
        rc =  yield self._proc.kill()
        self._proc = None
        if rc:
            defer.returnValue(Tcpdump.STOPPED)
        else:
            defer.returnValue(Tcpdump.STOPPING_FAILED)


class _ProcessProtocol(protocol.ProcessProtocol):

    def __init__(self):
        self._stderr = []
        self._ended = False
        self._fired = False
        self._timeout = None
        self._deferred = defer.Deferred()

    def active(self):
        return not self._ended

    def deferred(self):
        return self._deferred

    def connectionMade(self):
        self.transport.closeStdin()

    def errConnectionLost(self):
        if not self._fired:
            self._checkStderr()

    def errReceived(self, data):
        if self._fired:
            return
        self._stderr.append(data)
        if data.find('\n') == -1:
            return
        # This expects tcpdump to output an line like
        #   tcpdump: listening on eth1, link-type EN10MB (Ethernet), capture size 96 bytes
        # as first output on stderr ...
        stderr = "".join(self._stderr)
        self._fired = True
        if re.search("listening on.*link-type", stderr):
            self._deferred.callback((True, None, stderr))
        else:
            self._deferred.callback((False, None, stderr))

    @defer.inlineCallbacks
    def kill(self):
        try:
            self.transport.signalProcess('TERM')
            self._timeout = twisted_sleep(2)
            if (yield self._timeout):
                defer.returnValue(True)

            self.transport.loseConnection()
            self.transport.signalProcess('KILL')
        except twisted_error.ProcessExitedAlready:
            defer.returnValue(True)

        self._timeout = twisted_sleep(2)
        if (yield self._timeout):
            defer.returnValue(True)
        else:
            defer.returnValue(False)

    def processEnded(self, status):
        self._ended = True
        if self._timeout is not None and self._timeout.active():
            self._timeout.callLater.cancel()
            self._timeout.callback(True)
        if not self._fired:
            self._deferred.callback((False, status, "".join(self._stderr)))
