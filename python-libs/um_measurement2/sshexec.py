from twisted.internet import reactor

import getpass
import os
import struct

from twisted.conch.ssh import channel, common, connection, keys, transport, userauth
from twisted.conch.error import ConchError
from twisted.conch.client import agent
from twisted.internet import defer, error, protocol
from twisted.python import log, failure

from um_functions import StrictStruct

class _Transport(transport.SSHClientTransport):

    def __init__(self, factory):
        self.factory = factory

    def _isInKnownHosts(self, host, pubKey):
        # FIXME
        return 1

        # copied from twisted.conch.client.default - but does not work with hashed known_hosts ...
        """checks to see if host is in the known_hosts file for the user.
        returns 0 if it isn't, 1 if it is and is the same, 2 if it's changed.
        """
        keyType = common.getNS(pubKey)[0]
        retVal = 0

        kh_file = '~/.ssh/known_hosts'
        try:
            known_hosts = open(os.path.expanduser(kh_file))
        except IOError:
            return 3
        for line in known_hosts.xreadlines():
            split = line.split()
            if len(split) < 3:
                continue
            hosts, hostKeyType, encodedKey = split[:3]
            if host not in hosts.split(','): # incorrect host
                continue
            if hostKeyType != keyType: # incorrect type of key
                continue
            try:
                decodedKey = base64.decodestring(encodedKey)
            except:
                continue
            if decodedKey == pubKey:
                return 1
            else:
                retVal = 2
        return retVal

    def verifyHostKey(self, hostKey, fingerprint):
        host = self.transport.getPeer().host
        rv = self._isInKnownHosts(host, hostKey)
        if rv == 1:     # valid key
            return defer.succeed(1)
        elif rv == 2:   # key changed
            return defer.fail(ConchError("WARNING: %s' host key changed! Aborting!" % host))
        elif rv == 3:
            return defer.fail(ConchError("Oppening ~/.ssh/known_hosts failed." % host))
        else:
            return defer.fail(ConchError("WARNING: %s's host key unknown. Aborting!" % host))

    def connectionSecure(self):
        self.requestService(_Auth(self.factory.user, self.factory.conn))

class _TransportFactory(protocol.ClientFactory):
    # This factory exists just for passing additional parameters on reactor.connectTCP:
    #
    #       fact = _TransportFactory(...)
    #       reactor.connectTCP(host, port, fact)
    #
    # It is not intended to be used more than once; doing so will cause breakage.
    #
    # FIXME: Untwingle all these classes ...
    #
    # FIXME: It would be nice to have a reconnecting factory. This would require:
    #   - Working support for key authentication
    #   - ...

    def __init__(self, user, conn, connectDeferred = None, lostDeferred = None):
        """
        Takes two deferreds:

         * connectDeferred is always called: Either when the connection was
           established or when establishing the connection failed
         * lostDeferred is called (as errback), if the connection was lost in
           an unclean fashion.
           FIXME: The connection is also lost, if I close the connection ...
        """
        self.user = user
        self.conn = conn
        self._connectDeferred = connectDeferred
        self._lostDeferred = lostDeferred

    def buildProtocol(self, addr):
        return _Transport(self)

    def clientConnectionEstablished(self, conn):
        """
        Called by _Connection, if the connection was established. conn is a
        _Connection instance.

        Note: Despite its naming similarity to clientConnectionFailed/Lost, it
        is not a standard method of the ClientFactory class.
        """
        # FIXME: Untwingle classes?
        if self._connectDeferred is not None:
            self._connectDeferred.callback(conn)


    def clientConnectionFailed(self, connector, reason):
        if self._connectDeferred is not None:
            self._connectDeferred.errback(reason)

    def clientConnectionLost(self, connector, reason):
        if self._lostDeferred is not None:
            self._lostDeferred.errback(reason)


class _Auth(userauth.SSHUserAuthClient):
    """
    SSH authentication class.

    Uses public key authentication if ssh-agent is available, else password authentication.

    Magic stuff copied from twisted.conch.client.default.
    """

    def __init__(self, user, *args):
        userauth.SSHUserAuthClient.__init__(self, user, *args)
        self._agent = None

    def serviceStarted(self):
        # Use SSH agent if available
        if 'SSH_AUTH_SOCK' in os.environ:
            cc = protocol.ClientCreator(reactor, agent.SSHAgentClient)
            d = cc.connectUNIX(os.environ['SSH_AUTH_SOCK'])
            d.addCallback(self._setAgent)
            d.addErrback(self._ebSetAgent)
        else:
            userauth.SSHUserAuthClient.serviceStarted(self)

    def serviceStopped(self):
        if self._agent:
            self._agent.transport.loseConnection()
            self._agent = None

    def _setAgent(self, agent):
        self._agent = agent
        d = self._agent.getPublicKeys()
        d.addBoth(self._ebSetAgent)
        return d

    def _ebSetAgent(self, f):
        userauth.SSHUserAuthClient.serviceStarted(self)

    def getPassword(self):
        return defer.succeed(getpass.getpass("password: "))

    def signData(self, publicKey, signData):
        return self._agent.signData(publicKey, signData)

    def getPrivateKey(self):
        return None

    def getPublicKey(self):
        if self._agent:
            blob = self._agent.getPublicKey()
            if blob:
                return blob


class _Connection(connection.SSHConnection):
    """
    SSH connection class. With openChannel(), multiple programs can be executed
    using one instance of this class.

    """

    def __init__(self):
        self._established = False
        connection.SSHConnection.__init__(self)

    def channelClosed(self, channel):
        # Work around a bug in Conch 0.8 - channelClosed tries to close
        # channels which are not really open yet. This is fixed since twisted's
        # SVN revision 20700.
        # FIXME: Remove after upgrade to newer twisted.
        if channel in self.channelsToRemoteChannel:
            connection.SSHConnection.channelClosed(self, channel)
        else:
            # See http://twistedmatrix.com/trac/ticket/2782.
            # FIXME: A more useful error?
            channel.openFailed(ConchError("Service stopped"))

    def executeChan(self, command, fd_out, fd_err):
        """
        returns an SSHProc instance (or None, if the connection was already closed before ...)
        FIXME
        """

        if not self._established:
            return None

        # Open a channel
        ch = CommandChannel(command, conn=self, fd_out=fd_out, fd_err=fd_err)
        self.openChannel(ch)

        proc = SSHProc(ch)
        return proc

    def serviceStarted(self):
        self._established = True
        self.transport.factory.clientConnectionEstablished(self)

    def serviceStopped(self):
        self._established = False
        # FIXME: Message SSHExec?
        connection.SSHConnection.serviceStopped(self)


class SSHProc:
    """
    Remote process object.
    """

    def __init__(self, chan):
        self._chan = chan
        self._d = defer.Deferred()
        self._chan.d.chainDeferred(self._d)

    def deferred(self):
        """
        Returns a deferred. This deferred is called when the Channel terminates.
        """
        return self._d

    def disconnect(self):
        """
        See _Channel.disconnect
        """
        self._chan.forceDisconnect()

    def kill(self, signal):
        """
        Sends a signal to the remote process. See _Channel.kill
        """
        self._chan.kill(signal)


class ChanExitStruct(StrictStruct):
    """ CommandChannel exit status struct """

    def __init__(self, **kwargs):
        StrictStruct.__init__(self, ['type', 'status'], **kwargs)


class CommandChannelDisconnect(Exception):
    """Command channel was closed, but no result was set"""
    # FIXME: Better description

    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(self.args))
        s = '%s.' % s
        return s


class CommandChannel(channel.SSHChannel):
    # sets the channel type (see ssh rfc)
    name = 'session'

    def __init__(self, command, fd_out, fd_err, *args, **kwargs):
        """
        command is a string, which will be executed on the other connection endpoint.

        d is an callback, which will be called, when the channel exits. The
        result will be a ChanExitStruct with:

        * exit type: one of "exit-status", "exit-signal" or "disconnect".
            exit-status: Remote program terminated by itself and returned status code
            exit-signal: Remote program was terminated by signal status code
            disconnect: Channel was closed by a call to disconnect or forceDisconnect
        * status code: exit status or name of killing signal. None in case of disconnect.
        """
        channel.SSHChannel.__init__(self, *args, **kwargs)
        self._command = command
        self.d = defer.Deferred()
        self._stdout = fd_out
        self._stderr = fd_err

        self._result = None

    def closed(self):
        if self.d is not None:
            if self._result is None:
                self.d.errback(failure.Failure(CommandChannelDisconnect()))
            else:
                self.d.callback(self._result)
        channel.SSHChannel.closed(self)

    def disconnect(self):
        """
        Disconnects the channel.

        If the remote end does not react with an exit-{signal,status} request,
        self.d will be called with ChanExitStruct and type="disconnect".
        """
        self._result = ChanExitStruct(type="disconnect")
        self.loseConnection()

    def forceDisconnect(self):
        """
        Disconnects the channel and fires the callback immediately.

        Channel is disconnected like with disconnect(), but forceDisconnect
        does not wait till the other end closes the channel, before firing the
        "channel terminated" callback.

        Rationale: OpenSSH server does not immediately react on a "channel close"
        request, but only terminates, if the program tries to write something
        on stdout or stderr.
        """
        self.disconnect()
        self.d.callback(self._result)
        self.d = None

    def kill(self, sig):
        """
        Sends signal sig to the remote process, where sig is the name of a
        signal without the leading SIG. For valid values of sig, see RFC 4254.

        Note: The OpenSSH daemon does not support this but dropbear does.
        """
        self.conn.sendRequest(self, 'signal', common.NS(sig))

    def openFailed(self, reason):
        self.d.errback(reason)

    def channelOpen(self, ignoredData):
        self.conn.sendRequest(self, 'exec', common.NS(self._command))

    def dataReceived(self, data):
        self._stdout.write(data)

    def extReceived(self, type, data):
        self._stderr.write(data)

    def request_exit_status(self, data):
        """
        Called, when an exit-status request was sent by the remote connection end.
        """
        status = parseSSHAnswer('u', data)
        self._result = ChanExitStruct(type='exit-status', status=status)
        self.loseConnection()

    def request_exit_signal(self, data):
        """
        Called, when an exit-signal request was sent by the remote connection end.
        """
        status = parseSSHAnswer('sbss', data)
        self._result = ChanExitStruct(type='exit-signal', status=status)
        self.loseConnection()


def parseSSHAnswer(format, data):
    pos = 0
    parsed = []
    for fmt in format:
        if fmt == 's':      # String
            len = struct.unpack(">L", data[pos:pos+4])[0]
            parsed.append(data[pos+4:pos+4+len])
            pos += 4 + len
        elif fmt == 'b':    # Boolean
            parsed.append(struct.unpack('>B', data[pos])[0])
            pos += 1
        elif fmt == 'u':    # uint32
            parsed.append(struct.unpack('>L', data[pos:pos+4])[0])
            pos += 4
        elif fmt == 'U':    # uint64
            parsed.append(struct.unpack('>Q', data[pos:pos+8])[0])
            pos += 8
        else:
            raise NotImplementedError("Format char '%s' is not implemented" % fmt)
    return parsed
