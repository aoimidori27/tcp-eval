#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pwd

from twisted.internet import defer, error, reactor
from twisted.python import failure


"""

This module should collect standard test methods.

"""

@defer.inlineCallbacks
def test_ping(log_file,
              ping_src,
              ping_dst,
              ping_size     = 56,
              ping_interval = 1,
              ping_count    = 10,
              ping_opts     = "",
              **kwargs ):
    """

    This test performs a simple ping from src to dst.
        
    required arguments:
        log_file   : file descriptor where the results are written to
        ping_src: sender of the pings
        ping_dst: receiver of the pings

    optional arguments:
        ping_size    : size in bytes of the packets send out
        ping_count   : how many packets should be send out
        ping_interval: time between to pings in seconds
        
    """
        
    # for convenience accept numbers as src and dst
    src = Node(src, type="meshrouter")
    dst = Node(dst, type="meshrouter")
    
    cmd = "ping -i %.3f -c %u -s %u %s %s" % (ping_interval, ping_count,
                                              ping_size, ping_opts,
                                              dst.ipaddress())
    yield self.remote_execute(src.hostname(),
                              cmd,
                              log_file,
                              timeout=(ping_interval*ping_count)+5)


@defer.inlineCallbacks
def test_thrulay(log_file,
                 thrulay_src,
                 thrulay_dst,
                 thrulay_duration = 15,
                 thrulay_cc     = "reno",
                 thrulay_opts   = "",
                 **kwargs ):
    """

    This test performs a simple thrulay test with one tcp
    flow from src to dst.

    required arguments:
         log_file   : file descriptor where the results are written to
         thrulay_src: sender of the flow
         thrulay_dst: receiver of the flow

    optional arguments:
         thrulay_duration: duration of the flow in seconds
         thrulay_cc      : congestion control method to use
         thrulay_opts    : additional command line arguments

    """

    # for convenience accept numbers as src and dst
    src = Node(thrulay_src, type="meshrouter")
    dst = Node(thrulay_dst, type="meshrouter")

    cmd = "thrulay -Q -c %s -t %.3f -H %s/%s" % (thrulay_cc,
                                               thrulay_duration,
                                               dst.ipaddress(),
                                               dst.hostname())

    yield self.remote_execute(src.hostname(),
                              cmd,
                              log_file,
                              timeout=thrulay_duration+5)


