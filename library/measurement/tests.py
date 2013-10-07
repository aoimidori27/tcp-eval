#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2007 - 2011 Arnd Hannemann <arnd@arndnet.de>
# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# python imports
from logging import info, warn, error, debug

# twisted imports
from twisted.internet import defer, error, reactor
from twisted.python import failure

# tcp-eval imports
from network.functions import twisted_call, twisted_execute

"""This module should collect standard test methods."""

@defer.inlineCallbacks
def test_ping(mrs, log_file, src, dst, size=56, interval=1, count=10, opts="",
        **kwargs):
    """This test performs a simple ping from src to dst.

       required arguments:
           mrs     : reference to parent measurement class
           log_file: file descriptor where the results are written to
           src     : sender of the pings
           dst     : receiver of the pings

       optional arguments:
           size    : size in bytes of the packets send out
           count   : how many packets should be send out
           interval: time between to pings in seconds
           opts    : additional ping options
    """

    cmd = "ping -i %.3f -c %u -s %u %s %s" % (interval, count, size, opts, ip)
    rc = yield mrs.remote_execute(src, cmd, log_file,
                                  timeout=int((interval * count) + 5))
    defer.returnValue(rc)

@defer.inlineCallbacks
def test_fping(mrs, log_file, src, dst, size=56, interval=1, count=10, opts="",
        **kwargs):
    """This test performs a simple ping from src to dst. Drop in replacement for ping.

       required arguments:
           mrs     : reference to parent measurement class
           log_file: file descriptor where the results are written to
           src     : sender of the pings
           dst    : receiver of the pings

       optional arguments:
           size    : size in bytes of the packets send out
           count   : how many packets should be send out
           interval: time between to pings in seconds
           opts    : additional fping options
    """

    cmd = "fping -A -p %u -c %u -b %u %s %s 2>&1" % ((interval * 1000), count,
            size, opts, dst)

    # calculate conservative timeout with extra 10% and 5 seconds safeguard
    time_out = int(interval * count * 1.1 + 5)

    rc = yield mrs.remote_execute(src, cmd, log_file, timeout=time_out)
    defer.returnValue(rc)

@defer.inlineCallbacks
def test_thrulay(mrs, log_file, src, dst, dst_ctrl=None, duration=15,
        cc="reno", opts="", **kwargs):
    """This test performs a simple thrulay test with one tcp
       flow from src to dst.

       required arguments:
            mrs     : reference to parent measurement class
            log_file: file descriptor where the results are written to
            src     : sender of the flow
            dst     : receiver of the flow

       optional arguments:
            dst_ctrl: control connection to the receiver
            duration: duration of the flow in seconds
            cc      : congestion control method to use
            opts    : additional command line arguments
    """

    if dst_ctrl:
        cmd = "thrulay -Q -c %s -t %.3f -H %s/%s" % (cc, duration, dst,
                dst_ctrl)
    else:
        cmd = "thrulay -Q -c %s -t %.3f -H %s" % (cc, duration, dst)
    rc = mrs.remote_execute(src, cmd, log_file, timeout=duration + 5)
    defer.returnValue(rc)

@defer.inlineCallbacks
def test_flowgrind(mrs, log_file, src, dst, src_ctrl=None, dst_ctrl=None,
                   timeout=10, duration=15, warmup=0, cc=None, dump=None,
                   bport=5999, opts=[], fg_bin="flowgrind", gzip_dumps=True,
                   **kwargs ):
    """This test performs a simple flowgrind (new, aka dd version) test with
    one tcp flow from src to dst.

       required arguments:
            mrs     : reference to parent measurement class
            log_file: file descriptor where the results are written to
            src     : sender of the flow
            dst     : receiver of the flow

       optional arguments:
            src_ctrl : control connection to the sender
            dst_ctrl : control connection to the receiver
            duration : duration of the flow in seconds
            cc       : congestion control method to use
            warmup   : warmup time for flow in seconds
            dump     : turn tcpdump on src and dst on iface 'dump' on
            bport    : flowgrind base port
            opts     : additional command line arguments
            fg_bin   : flowgrind binary
            gzip_pcap: gzip dumps to save space
    """

    # path of executable
    cmd = [ fg_bin ]

    # add -p for numerical output
    cmd.extend(["-p"])

    # test duration
    cmd.extend(["-T", "s=%.2f" % duration])

    # inital delay
    if warmup:
        cmd.extend(["-Y", "s=%.2f" % warmup])

    # which tcp congestion control module
    if cc:
        cmd.extend(["-O", "s=TCP_CONG_MODULE=%s" % cc])

    # control connections in place?
    if not src_ctrl:
        src_ctrl = src
    if not dst_ctrl:
        dst_ctrl = dst

    # build host specifiers
    cmd.extend(["-H", "s=%s/%s,d=%s/%s" %(src, src_ctrl, dst, dst_ctrl)])

    # just add additional parameters
    if opts:
        cmd.extend(opts)

    # start tcpdump
    if dump:
        raise NotImplementedError, "bport must be re-added to new flowgrind first"

        dumpfile_src = None
        dumpfile_dst = None
        results = yield mrs.xmlrpc_many([src_ctrl, dst_ctrl], "tcpdump.start",
            dump, "port %u" %bport )
        debug(results)

        # shortcuts
        sres = results[0]
        dres = results[1]
        if sres[0]:
            dumpfile_src = sres[1]
        else:
            warn("Failed to start tcpdump on %s: %s" %(src_ctrl,
                sres[1].getErrorMessage()))
        if dres[0]:
            dumpfile_dst = dres[1]
        else:
            warn("Failed to start tcpdump on %s: %s" %(dst_ctrl,
                dres[1].getErrorMessage()))

    # run flowgrind
    result = yield mrs.local_execute(" ".join(cmd), log_file, timeout=(duration
        + warmup + timeout))

    # stop tcpdump
    if dump:
        yield mrs.xmlrpc_many([src_ctrl, dst_ctrl], "tcpdump.stop")

        # just schedule moving and compressing for later execution
        if dumpfile_src:
            # just append .hostname.pcap to logfilename
            sfile = "%s.%s.pcap" %(log_file.name, src_ctrl)
            cmd = ["mv", dumpfile_src, sfile]
            d = twisted_call(cmd, shell=False)
            if gzip_pcap:
                def callback(rc):
                    if rc != 0:
                        return
                    cmd = ["gzip", sfile]
                    twisted_call(cmd, shell=False)

                d.addCallback(callback)
        if dumpfile_dst:
            # just append .hostname.pcap to logfilename
            dfile = "%s.%s.pcap" %(log_file.name, dst_ctrl)
            cmd = ["mv", dumpfile_dst, dfile]
            d=twisted_call(cmd, shell=False)
            if gzip_dumps:
                def callback(rc):
                    if rc != 0:
                        return
                    cmd = ["gzip", dfile]
                    twisted_call(cmd, shell=False)

                d.addCallback(callback)

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

