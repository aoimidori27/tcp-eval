#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
from logging import info, warn, error, debug

from twisted.internet import defer, error, reactor
from twisted.python import failure

# umic-mesh imports
from um_node import Node
from um_twisted_functions import twisted_call, twisted_execute

"""This module should collect standard test methods."""

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
    """This test performs a simple ping from src to dst.

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
    """This test performs a simple ping from src to dst. Drop in replacement for ping.

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

    # calculate conservative timeout with extra 10% and 5 seconds safeguard
    time_out = int(ping_interval*ping_count*1.1+5)
    rc = yield mrs.remote_execute(src.getHostname(),
                                  cmd,
                                  log_file,
                                  timeout=time_out)
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
    """This test performs a simple thrulay test with one tcp
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
def test_multiflowgrind(mrs,
                        log_file,
                        flowgrind_subflows,
                        flowgrind_bin = "flowgrind",
                        flowgrind_timeout = 10,
                        flowgrind_opts = [],
                        nodetype    = "meshrouter",
                        **kwargs ):
    """This test perfoms many flowgrind tests with one tcp flow per each flowgrind
       from a given source to a given destination

       required arguments:
            log_file            : file descriptor where the results are written to
            mrs                 : reference to parent measurement class
            flowgrind_subflows  : a dict list of flowgrind settings for each subflow

       optional arguments:
            flowgrind_bin       : flowgrind binary
            flowgrind_timeout    : additional time to wait after duration before stopping the subflow
            flowgrind_opts      : additional command line agruments for all flows
            nodetype            : the nodetype ("e.g. vmeshrouter")

        required subflow settings for each flow:
           flowgrind_src        : sender of the flow
           flowgrind_dst        : receiver of the flow
           flowgrind_iface      : iface to get ipaddress
           flowgrind_duration   : duration of the flow in seconds

        optional subflow settings for each flow
           flowgrind_opts       : additiona command line agruments
           flowgrind_cc         : congestion control method to use
           flowgrind_warmup     : warmup time for flow
    """

    # number of subflows
    num = len(flowgrind_subflows)
    max_duration = 0
    count = 0

    # path of executeable
    cmd = [ flowgrind_bin ]

    # add -p for numerical output
    cmd.extend(["-p"])

    # set number of parallel subflows
    cmd.extend(["-n", "%s" % num])

    # subflow independent options
    if flowgrind_opts:
        cmd.extend(flowgrind_opts)

    # subflows
    for subflow in flowgrind_subflows:
        # for convenience accept numbers as src and ds
        src = Node(flowgrind_subflows[subflow]['flowgrind_src'], node_type=nodetype)
        dst = Node(flowgrind_subflows[subflow]['flowgrind_dst'], node_type=nodetype)

        # ips of the measurement interfaces
        src_ip = yield mrs.getIp(src.getHostname(), flowgrind_subflows[subflow]['flowgrind_iface'])
        dst_ip = yield mrs.getIp(dst.getHostname(), flowgrind_subflows[subflow]['flowgrind_iface'])

        # classify subflow
        cmd.extend(["-F","%s" % count])
        count += 1

        # options

        # just add additional parameters
        if 'flowgrind_opts' in flowgrind_subflows[subflow]:
            cmd.extend(flowgrind_subflows[subflow]['flowgrind_opts'])

        if 'flowgrind_cc' in flowgrind_subflows[subflow]:
            cmd.extend(["-O", "s=TCP_CONG_MODULE=%s" % flowgrind_subflows[subflow]['flowgrind_cc']])

        if 'flowgrind_warmup' in flowgrind_subflows[subflow]:
                cmd.extend(["-Y", "s=%.2f" % flowgrind_subflows[subflow]['flowgrind_warmup']])
                max_duration = max(max_duration, (flowgrind_subflows[subflow]['flowgrind_duration'] + flowgrind_subflows[subflow]['flowgrind_warmup']) )
        else:
            max_duration = max(max_duration, flowgrind_subflows[subflow]['flowgrind_duration'])

        cmd.extend(["-T", "s=%f" % flowgrind_subflows[subflow]['flowgrind_duration']])

        # build host specifiers
        cmd.extend(["-H", "s=%s/%s,d=%s/%s" % (src_ip, src.getHostname(),
                    dst_ip, dst.getHostname()) ])

    result = yield mrs.local_execute(" ".join(cmd), log_file,
            timeout=(max_duration + flowgrind_timeout) )

    defer.returnValue(result)

@defer.inlineCallbacks
def test_flowgrind(mrs,
                   log_file,
                   flowgrind_src,
                   flowgrind_dst,
                   flowgrind_timeout = 10,
                   flowgrind_duration = 15,
                   flowgrind_warmup = 0,
                   flowgrind_cc     = None,
                   flowgrind_dump   = False,
                   flowgrind_iface  = "ath0",
                   flowgrind_bport  = 5999,
                   flowgrind_bin    = "flowgrind",
                   flowgrind_opts   = [],
                   gzip_dumps       = True,
                   nodetype         = "meshrouter",
                   **kwargs ):
    """This test performs a simple flowgrind (new, aka dd version) test with one tcp
       flow from src to dst.

       required arguments:
            log_file      : file descriptor where the results are written to
            mrs           : reference to parent measurement class
            flowgrind_src : sender of the flow
            flowgrind_dst : receiver of the flow

       optional arguments:
            flowgrind_duration : duration of the flow in seconds
            flowgrind_warmup   : warmup time for flow in seconds
            flowgrind_cc       : congestion control method to use
            flowgrind_dump     : turn on tcpdump on src and sender
            flowgrind_iface    : iface to get ipaddress
            flowgrind_bport    : flowgrind base port
            flowgrind_bin      : flowgrind binary
            flowgrind_opts     : additional command line arguments
            flowgrind_timeout  : additional time to wait after duration before stopping the flow
            gzip_dumps         : gzip dumps to save space
            nodetype           : the nodetype ("e.g. vmeshrouter")
    """

    # for convenience accept numbers as src and dst
    src = Node(flowgrind_src, node_type=nodetype)
    dst = Node(flowgrind_dst, node_type=nodetype)

    # ips of the measurement interfaces
    src_ip = yield mrs.getIp(src.getHostname(), flowgrind_iface)
    dst_ip = yield mrs.getIp(dst.getHostname(), flowgrind_iface)

    # path of executable
    cmd = [ flowgrind_bin ]

    # add p for numerical output
    cmd.extend(["-p"])

    # options
    cmd.extend(["-T", "s=%.2f" % flowgrind_duration])

    if flowgrind_warmup:
        cmd.extend(["-Y", "s=%.2f" % flowgrind_warmup])

    if flowgrind_cc:
        cmd.extend(["-O", "s=TCP_CONG_MODULE=%s" % flowgrind_cc])

    # build host specifiers
    cmd.extend(["-H", "s=%s/%s,d=%s/%s" % (src_ip, src.getHostname(),
                                           dst_ip, dst.getHostname()) ])

    # just add additional parameters
    if flowgrind_opts:
        cmd.extend(flowgrind_opts)

    if flowgrind_dump:
        raise NotImplementedError, "bport must be re-added to new flowgrind first"

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

    result = yield mrs.local_execute(" ".join(cmd), log_file,
            timeout=(flowgrind_duration + flowgrind_warmup + flowgrind_timeout) )

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

