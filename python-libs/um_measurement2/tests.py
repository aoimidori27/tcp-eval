import sys

import sshexec
import os, pwd

from twisted.internet import defer, error, reactor
from twisted.python import failure

from measurement import TestFailed

# FIXME: Document test interface!!1elf

def timeoutDeferred(timeout):
    """
    Returns a deferred, which is fired after timeout seconds.
    """

    d = defer.Deferred()
    cl = reactor.callLater(timeout, d.callback, None)
    return d

class SSHTest:

    # FIXME: Each instance may be used only once!
    # FIXME: subclassing?
    # FIXME: Does not implement the MeasurementTest interface

    def __init__(self, factory, node_info, log_fd, timeout = None):
        self._factory = factory
        # src, dst nodes
        self._src, self._dst = node_info
        # FIXME
        self._log_fd = log_fd

        # FIXME: This is interface part.
        self.timeout = timeout

        # Is the process still running?
        self._stopped = False
        # Remote process (SSHProc)
        self._proc = None
        # User-visible callback. Called by terminated_*.
        self._d = defer.Deferred()
        # Time to wait between sending a signal and expecting the result.
        self._sig_timeout = 3

    def __str__(self):
        return "%s for (%s -> %s)" % (self._factory, self._src, self._dst)

    @defer.inlineCallbacks
    def start(self):
        """
        Starts the test. Returns a deferred which fires on test termination.

        May only be called once.
        """
        if self._src in self._factory._connections:
            conn = self._factory._connections[self._src]
        else:
            raise TestFailed("Could not open channel - connection already closed")

        print self._factory._command.__class__

        if self._factory._command is str:
            command = self._factory._command
        else:
            command = self._factory._command(self._src, self._dst)

        self._proc = conn.executeChan(command, self._log_fd, self._log_fd)

        # Still necessary?
        if self._proc is None:
            raise TestFailed("Could not open channel - connection already closed")

        try:
            # FIXME: We should wrap the results?
            result = yield self._proc.deferred()
            self._stopped = True
            if result.type == "exit-status":
                defer.returnValue(result)
            else:
                raise TestFailed(result)
        except IOError, inst: #Catch which errors?
            self._stopped = True
            raise TestFailed(str(inst))
        except Exception, inst:
            self._stopped = True
            raise TestFailed(str(inst))

    @defer.inlineCallbacks
    def stop(self, proc = None):
        """
        Stops the test by trying SIGTERM, SIGKILL and disconnecting in that order.
        """
        if proc == None:
            proc = self._proc

        proc.kill("TERM")

        yield timeoutDeferred(self._sig_timeout)

        if self._stopped:
            return
        proc.kill("KILL")

        yield timeoutDeferred(self._sig_timeout)

        if self._stopped:
            return
        proc.disconnect()

class SSHTestComplex(SSHTest):

    def cancelTimeout(result):
        if cl.active():
            cl.cancel()
        return result

    @defer.inlineCallbacks()
    def remoteExecute(self, host, command, timeout=None):
        if self._src in self._factory._connections:
            conn = self._factory._connections[self._src]
        else:
            raise TestFailed("Could not open channel - connection already closed")
        proc = conn.executeChan(command, self._log_fd, self._log_fd)

        if timeout is not None:
            cl = reactor.callLater(timeout, self.cancelProc, proc)
            proc.deferred().addBoth(self.cancelTimeout)

        try:
            result = yield proc.deferred()
        except Exception, inst: # FIXME: Catch which exceptions?
            result = inst

        # FIXME: extract exit code

        return result

    # FIXME: Do a clean refactoring.


    @defer.inlineCallbacks
    def start(self):
        """
        Starts the test. Returns a deferred which fires on test termination.

        May only be called once.
        """
        if self._src in self._factory._connections:
            conn = self._factory._connections[self._src]
        else:
            raise TestFailed("Could not open channel - connection already closed")

        if self._factory._command is str:
            command = self._factory._command
        else:
            command = self._factory._command(self._src, self._dst)

        self._proc = conn.executeChan(command, self._log_fd, self._log_fd)

        # Still necessary?
        if self._proc is None:
            raise TestFailed("Could not open channel - connection already closed")

        try:
            # FIXME: We should wrap the results?
            result = yield self._proc.deferred()
            self._stopped = True
            if result.type == "exit-status":
                defer.returnValue(result)
            else:
                raise TestFailed(result)
        except IOError, inst: #Catch which errors?
            self._stopped = True
            raise TestFailed(str(inst))
        except Exception, inst:
            self._stopped = True
            raise TestFailed(str(inst))

class SSHTestFactory:

    def __init__(self, command, name = None, timeout = None):
        """
        FIXME.

        command is either a string or a callable which takes src, dst as parameters.
        """
        self._command = command
        # FIXME: user, port
        self._user = pwd.getpwuid(os.getuid())[0]
        self._timeout = timeout

        if name is None:
            self._name = self.__class__
        else:
            self._name = name

        self._connections = {}

        self._lost_ds = []
        self._cleaningUp = False

    def __call__(self, node_info, log_fd):
        """ Using this, a SSHTestFactory instance emulates a class. """
        return SSHTest(self, node_info, log_fd, timeout = self._timeout)

    def __str__(self):
        return self._name

    def _lostHandler(self, reason, host):
        # FIXME: documentation
        if self._cleaningUp:
            return reason
        else:
            # FIXME: signal error?
            print "CONNECTION TO %s LOST: %s" % (host, reason)
            del self._connections[host]

    def _connect(self, user, host, port = 22):
        """
        Creates a connection and returns a deferred.

        The deferred is callback()'ed, if the connection was established and
        errbacked if the connection attempt failed.
        """
        conn = sshexec._Connection()
        connect_d = defer.Deferred()
        lost_d = defer.Deferred()

        fact = sshexec._TransportFactory(user, conn, connectDeferred = connect_d, lostDeferred = lost_d)
        reactor.connectTCP(host, port, fact)

        return (connect_d, lost_d)

    @defer.inlineCallbacks
    def cleanup(self):
        self._cleaningUp = True
        for c in self._connections.itervalues():
            c.transport.loseConnection()
        for ld in self._lost_ds:
            try:
                yield ld
            except error.ConnectionDone:
                pass
            except:
                import traceback
                traceback.print_exc()

    def init_nodes(self, nodes):
        """
        Creates master connections.

        Returns a deferred. callback(None) if all connections could be
        successfully established, errback(reason), if at least one connection
        fails. reason is then the errback value from the first failed
        connection.
        """

        ds = []
        for n in nodes:
            if n in self._connections:
                continue
            connect_d, lost_d = self._connect(user = self._user, host = n)
            ds.append(connect_d)
            lost_d.addErrback(self._lostHandler, n)
            self._lost_ds.append(lost_d)

        dl = defer.DeferredList(ds, fireOnOneErrback = True)

        def addConnections(resList):
            for res in resList:
                conn = res[1]
                host = conn.transport.transport.getPeer().host
                self._connections[host] = conn
            return None

        # On success, store all created connections
        dl.addCallback(addConnections)
        # On error, pass it through.
        dl.addErrback(lambda reason: reason)

        return dl
