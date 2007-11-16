#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pwd
from logging import info, warn, error, debug

from twisted.internet import defer, error, reactor
from twisted.python import failure

from um_node import Node
from um_twisted_functions import twisted_call

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

    cmd = "fping -A -p %u -c %u -b %u %s %s 2>&1" % ((ping_interval*1000), ping_count,
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


@defer.inlineCallbacks
def test_flowgrind(mrs,
                   log_file, 
                   flowgrind_src,
                   flowgrind_dst,
                   flowgrind_duration = 15,
                   flowgrind_cc     = "reno",
                   flowgrind_dump   = False,
                   flowgrind_iface  = "ath0",
                   flowgrind_bport  = 20000,
                   flowgrind_opts   = "",
                   gzip_dumps       = True,
                   **kwargs ):
    """

    This test performs a simple flowgrind test with one tcp
    flow from src to dst.

    required arguments:
         log_file      : file descriptor where the results are written to
         mrs           : reference to parent measurement class
         flowgrind_src : sender of the flow
         flowgrind_dst : receiver of the flow

    optional arguments:
         flowgrind_duration : duration of the flow in seconds
         flowgrind_cc       : congestion control method to use
         flowgrind_dump     : turn on tcpdump on src and sender
         flowgrind_iface    : iface to get ipaddress
         flowgrind_bport    : flowgrind base port
         flowgrind_opts     : additional command line arguments
         gzip_dumps         : gzip dumps to save space

    """

    # for convenience accept numbers as src and dst
    src = Node(flowgrind_src, type_="meshrouter")
    dst = Node(flowgrind_dst, type_="meshrouter")

    cmd = "flowgrind -Q -c %s -t %.3f -O %u -H %s/%s" % (flowgrind_cc,
                                                         flowgrind_duration,
                                                         flowgrind_bport,
                                                         dst.ipaddress(flowgrind_iface),
                                                         dst.hostname())

    if flowgrind_dump:
        dumpfile_src = None
        dumpfile_dst = None
        results = yield mrs.xmlrpc_many([src.hostname(),dst.hostname()],
                                       "tcpdump.start",
                                       flowgrind_iface,
                                       "port %u" %flowgrind_bport )
        debug(results)
        # shortcuts
        sres = results[0]
        dres = results[1]
        if sres[0]:
            dumpfile_src = sres[1]
        else:
            warn("Failed to start tcpdump on %s: %s" %(src.hostname(),
                                                       sres[1].getErrorMessage()))
        if dres[0]:
            dumpfile_dst = dres[1]
        else:
            warn("Failed to start tcpdump on %s: %s" %(dst.hostname(),
                                                       dres[1].getErrorMessage()))
                                                       

    result = yield  mrs.remote_execute(src.hostname(),
                                       cmd,
                                       log_file,
                                       timeout=flowgrind_duration+5)
    if flowgrind_dump:
        yield mrs.xmlrpc_many([src.hostname(),dst.hostname()],
                              "tcpdump.stop")

        if dumpfile_src:
            # just append .hostname.pcap to logfilename
            sfile = "%s.%s.pcap" %(log_file.name, src.hostname())
            cmd = ["mv",dumpfile_src, sfile]
            d=twisted_call(cmd, shell=False)
            if gzip_dumps:
                def callback(rc):
                    if rc != 0:
                        return
                    cmd = ["gzip", sfile]
                    twisted_call(cmd, shell=False)
                    
                d.addCallback(callback)
        if dumpfile_dst:
            # just append .hostname.pcap to logfilename
            dfile = "%s.%s.pcap" %(log_file.name, dst.hostname())
            cmd = ["mv",dumpfile_dst, dfile]            
            d=twisted_call(cmd, shell=False)
            if gzip_dumps:
                def callback(rc):
                    if rc != 0:
                        return
                    cmd = ["gzip", dfile]
                    twisted_call(cmd, shell=False)
                    
                d.addCallback(callback)                                         

    defer.returnValue(result)
    


