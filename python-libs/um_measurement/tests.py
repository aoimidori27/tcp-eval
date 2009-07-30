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

@defer.inlineCallbacks
def test_rate(mrs,
              log_file,
              rate_src,
              rate_dst,
              rate_iface = "ath0",
              rate_size  = 1600,
              **kwargs ):

    # for convenience accept numbers as src and dst
    src = Node(rate_src, node_type="meshrouter")
    dst = Node(rate_dst, node_type="meshrouter")

    dst_ip = yield mrs.getIp(dst.getHostname(), rate_iface)

    nexthop = yield mrs.get_next_hop(src.getHostname(), dst_ip)
    debug("nexthop: %s" %nexthop)
    mac = yield mrs.get_mac(src.getHostname(), nexthop, rate_iface)
    if not mac:
        error("Failed to get mac for: %s" %nexthop)
        defer.returnValue("-1")
    debug("mac    : "+mac)

    cmd = 'grep -A 13 "%s" /proc/net/madwifi/%s/ratestats_%u' %(mac, rate_iface, rate_size)
    
    result = yield mrs.remote_execute(src.getHostname(),
                                      cmd,
                                      log_file,
                                      timeout=2)
              
@defer.inlineCallbacks
def test_ping(mrs,
              log_file,
              ping_src,
              ping_dst,
              ping_size     = 56,
              ping_interval = 1,
              ping_count    = 10,
              ping_opts     = "",
              ping_iface    = "ath0",
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
    src = Node(ping_src, node_type="meshrouter")
    dst = Node(ping_dst, node_type="meshrouter")

    dst_ip = yield mrs.getIp(dst.getHostname(), ping_iface)

    cmd = "ping -i %.3f -c %u -s %u %s %s" % (ping_interval, ping_count,
                                              ping_size, ping_opts,
                                              dst_ip)

    
    rc = yield mrs.remote_execute(src.getHostname(),
              	                  cmd,
                                  log_file,
                                  timeout=int((ping_interval*ping_count)+5))

    defer.returnValue(rc)

@defer.inlineCallbacks
def test_fping(mrs,
              log_file,
              ping_src,
              ping_dst,
              ping_size     = 56,
              ping_interval = 1,
              ping_count    = 10,
              ping_iface    = "ath0",
              fping_opts    = "",
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
    src = Node(ping_src, node_type="meshrouter")
    dst = Node(ping_dst, node_type="meshrouter")

    dst_ip = yield mrs.getIp(dst.getHostname(), ping_iface)

    cmd = "fping -A -p %u -c %u -b %u %s %s 2>&1" % ((ping_interval*1000), ping_count,
                                             ping_size, fping_opts,
                                             dst_ip)
    rc = yield mrs.remote_execute(src.getHostname(),
                                  cmd,
                                  log_file,
                                  timeout=int((ping_interval*ping_count)+5))

    defer.returnValue(rc)


@defer.inlineCallbacks
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
    src = Node(thrulay_src, node_type="meshrouter")
    dst = Node(thrulay_dst, node_type="meshrouter")

    dst_ip = yield mrs.getIp(dst.getHostname(), "ath0")

    cmd = "thrulay -Q -c %s -t %.3f -H %s/%s" % (thrulay_cc,
                                               thrulay_duration,
                                               dst_ip,
                                               dst.getHostname())

    rc = mrs.remote_execute(src.getHostname(),
                            cmd,
                            log_file,
                            timeout=thrulay_duration+5)

    defer.returnValue(rc)


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

    This test performs a simple flowgrind (new, aka dd version) test with one tcp
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
    src = Node(flowgrind_src, node_type="meshrouter")
    dst = Node(flowgrind_dst, node_type="meshrouter")

    dst_ip = yield mrs.getIp(dst.getHostname(), flowgrind_iface)

    cmd = "flowgrind -O s=TCP_CONG_MODULE=%s -T s=%.3f -p %u -H %s" % (flowgrind_cc,
                                                         flowgrind_duration,
                                                         flowgrind_bport,
                                                         dst_ip)
    if flowgrind_opts:
        cmd = " ".join([cmd, flowgrind_opts])

    if flowgrind_dump:
        dumpfile_src = None
        dumpfile_dst = None
        results = yield mrs.xmlrpc_many([src.getHostname(),dst.getHostname()],
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
            warn("Failed to start tcpdump on %s: %s" %(src.getHostname(),
                                                       sres[1].getErrorMessage()))
        if dres[0]:
            dumpfile_dst = dres[1]
        else:
            warn("Failed to start tcpdump on %s: %s" %(dst.getHostname(),
                                                       dres[1].getErrorMessage()))


    result = yield  mrs.remote_execute(src.getHostname(),
                                       cmd,
                                       log_file,
                                       timeout=flowgrind_duration+5)
    if flowgrind_dump:
        yield mrs.xmlrpc_many([src.getHostname(),dst.getHostname()],
                              "tcpdump.stop")

        # just schedule moving and compressing for later execution
        if dumpfile_src:
            # just append .hostname.pcap to logfilename
            sfile = "%s.%s.pcap" %(log_file.name, src.getHostname())
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
            dfile = "%s.%s.pcap" %(log_file.name, dst.getHostname())
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
