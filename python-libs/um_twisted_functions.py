#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-


import os
from logging import info, debug, warn, error, critical

from twisted.internet import defer, utils


"""

This module contains useful functions to use within the twisted framework.


"""

            

@defer.inlineCallbacks
def twisted_execute(cmd, shell=True):
    """
    Executes the given command and
    returns a sequence (stdout, stderr, returncode)
    
    Function which mimics um_functions.execute()
    but without exceptions.
    
    for use in twisted (the subprocess module won't work!!!)

    """
    debug("Executing: %s" % cmd.__str__())
    if not shell:
        (stdout, stderr, rc) = yield _ExecuteHelper(cmd[0],
                                                    cmd[1:],
                                                    env=os.environ,
                                                    path='.')
    else:
        (stdout, stderr, rc) = yield _ExecuteHelper("/bin/sh",
                                                    ('-c', cmd),
                                                    env=os.environ,
                                                    path='.')
        
    defer.returnValue((stdout, stderr, rc))

@defer.inlineCallbacks
def twisted_call(cmd, shell=True):
    """
    Executes the given command and
    returns a returncode suppressing output.

    Warning: is inefficient for commands with large stdoutput!
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
