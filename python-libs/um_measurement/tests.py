#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pwd

from twisted.internet import defer, error, reactor
from twisted.python import failure

from um_node import Node

"""

This module should collect standard test methods.

"""

def test_ping(mrs,
              log_file,
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
        mrs        : reference to parent measurement class
        log_file   : file descriptor where the results are written to
        ping_src   : sender of the pings
        ping_dst   : receiver of the pings

    optional arguments:
        ping_size    : size in bytes of the packets send out
        ping_count   : how many packets should be send out
        ping_interval: time between to pings in seconds
        ping_opts    : additional ping options
        
    """
    # for convenience accept numbers as src and dst
    src = Node(ping_src, type_="meshrouter")
    dst = Node(ping_dst, type_="meshrouter")

    cmd = "ping -i %.3f -c %u -s %u %s %s" % (ping_interval, ping_count,
                                              ping_size, ping_opts,
                                              dst.ipaddress())
    return mrs.remote_execute(src.hostname(),
                              cmd,
                              log_file,
                              timeout=(ping_interval*ping_count)+5)


def test_fping(mrs,
              log_file,
              ping_src,
              ping_dst,
              ping_size     = 56,
              ping_interval = 1,
              ping_count    = 10,
              fping_opts     = "",
              **kwargs ):
    """

    This test performs a simple ping from src to dst. Drop in replacement for ping.
        
    required arguments:
        mrs        : reference to parent measurement class
        log_file   : file descriptor where the results are written to
        ping_src   : sender of the pings
        ping_dst   : receiver of the pings

    optional arguments:
        ping_size    : size in bytes of the packets send out
        ping_count   : how many packets should be send out
        ping_interval: time between to pings in seconds
        fping_opts   : additional fping options
        
    """
    # for convenience accept numbers as src and dst
    src = Node(ping_src, type_="meshrouter")
    dst = Node(ping_dst, type_="meshrouter")

    cmd = "fping -A -p %u -c %u -b %u %s %s 2>&1" % ((ping_interval*100), ping_count,
                                             ping_size, fping_opts,
                                             dst.ipaddress())
    return mrs.remote_execute(src.hostname(),
                              cmd,
                              log_file,
                              timeout=(ping_interval*ping_count)+5)


def test_thrulay(mrs,
                 log_file, 
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
         mrs        : reference to parent measurement class
         thrulay_src: sender of the flow
         thrulay_dst: receiver of the flow

    optional arguments:
         thrulay_duration: duration of the flow in seconds
         thrulay_cc      : congestion control method to use
         thrulay_opts    : additional command line arguments

    """

    # for convenience accept numbers as src and dst
    src = Node(thrulay_src, type_="meshrouter")
    dst = Node(thrulay_dst, type_="meshrouter")

    cmd = "thrulay -Q -c %s -t %.3f -H %s/%s" % (thrulay_cc,
                                               thrulay_duration,
                                               dst.ipaddress(),
                                               dst.hostname())

    return mrs.remote_execute(src.hostname(),
                             cmd,
                             log_file,
                             timeout=thrulay_duration+5)



def test_flowgrind(mrs,
                 log_file, 
                 flowgrind_src,
                 flowgrind_dst,
                 flowgrind_duration = 15,
                 flowgrind_cc     = "reno",
                 flowgrind_opts   = "",
                 **kwargs ):
    """

    This test performs a simple flowgrind test with one tcp
    flow from src to dst.

    required arguments:
         log_file   : file descriptor where the results are written to
         mrs        : reference to parent measurement class
         flowgrind_src: sender of the flow
         flowgrind_dst: receiver of the flow

    optional arguments:
         flowgrind_duration: duration of the flow in seconds
         flowgrind_cc      : congestion control method to use
         flowgrind_opts    : additional command line arguments

    """

    # for convenience accept numbers as src and dst
    src = Node(flowgrind_src, type_="meshrouter")
    dst = Node(flowgrind_dst, type_="meshrouter")

    cmd = "flowgrind -Q -c %s -t %.3f -H %s/%s" % (flowgrind_cc,
                                               flowgrind_duration,
                                               dst.ipaddress(),
                                               dst.hostname())

    return mrs.remote_execute(src.hostname(),
                             cmd,
                             log_file,
                             timeout=flowgrind_duration+5)


