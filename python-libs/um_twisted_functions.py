#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import os
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, utils, reactor


def twisted_sleep(timeout):
    """
    Returns a deferred, which is fired after timeout seconds. The deferred gets
    an additional "callLater" property, which contains a reference to an
    IDelayedCall instance.
    """

    d = defer.Deferred()
    # FIXME!!!
    d.callLater = reactor.callLater(timeout, d.callback, None)
    return d



@defer.inlineCallbacks
def twisted_execute(cmd, shell = True):
    """
    Executes the given command and returns a sequence (stdout, stderr,
    returncode). The function mimics um_functions.execute() but without
    exceptions. (Remember: the subprocess module won't work in twisted!!!)
    """
    
    debug("Executing: %s" % cmd.__str__())
    if not shell:
        (stdout, stderr, rc) = yield _ExecuteHelper(cmd[0], cmd[1:],
                                                    env = os.environ,
                                                    path = '.')
    else:
        (stdout, stderr, rc) = yield _ExecuteHelper("/bin/sh", ('-c', cmd),
                                                    env = os.environ,
                                                    path = '.')

    defer.returnValue((stdout, stderr, rc))



@defer.inlineCallbacks
def twisted_call(cmd, shell=True):
    """
    Executes the given command and returns a returncode suppressing output.
    Warning: is inefficient for commands with large std output!
    """
    
    (stdout, stderr, rc) = yield twisted_execute(cmd, shell)

    defer.returnValue(rc)



class _ExecuteHelper(defer.Deferred):
    """
    This a wrapper around utils.getProcessOutputAndValue, which returns the
    signal number as negative returncode in case of errback()
    """

    def __init__(self, *args, **kwargs):
        defer.Deferred.__init__(self)
        d = utils.getProcessOutputAndValue(*args, **kwargs)
        d.addCallbacks(self.callback, self._internal_errback)


    def _internal_errback(self, failure):
        (stdout, stderr, signum) = failure.value
        self.callback((stdout, stderr, -signum))
