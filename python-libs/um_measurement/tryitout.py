#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from twisted.internet import defer, reactor

from sshexec import SSHConnectionFactory

@defer.inlineCallbacks
def main():
    scf = SSHConnectionFactory()
    yield scf.connect(["localhost","127.0.0.1"])
    result = yield scf.remoteExecute("localhost", "ls", out_fd=sys.stdout, err_fd=sys.stderr)
    print "RESULT: %s" % result
    result = yield scf.remoteExecute("localhost", "echo ----------------------; whoami", out_fd=sys.stdout, err_fd=sys.stderr)
    print "RESULT: %s" % result
    yield scf.disconnect()
    reactor.stop()


main()
reactor.run()
