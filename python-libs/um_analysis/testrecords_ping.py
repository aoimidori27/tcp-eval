#!/usr/bin/envpython
# -*- coding: utf-8 -*-

# python imports
import sys
import os
import os.path
import subprocess
import re
import time
import signal
import socket
from logging import info, debug, warn, error
from numpy import array
import traceback

# um imports
from testrecord import TestRecord

class PingRecord(TestRecord):
    def __init__(self, filename, regexes, whats):
        TestRecord.__init__(self, filename, regexes, whats)


class PingRecordFactory():
    def __init__(self):
        # helper functions for "whats" calulation
        def compute_hop_avg(results):
            "Computes the average hopcount per test record"

            # convert array to float
            fhops = map(float, results['ppt_ttl'])
            # initial TTL is 65 so hop count is 65 - ttl
            hops = map(lambda x: 65-x, fhops)
            return array(hops).mean()

        def compute_hop_std(results):
            "Computes the hopcount deviation per test record"

            # convert array to float
            fhops = map(float, results['ppt_ttl'])
            # initial TTL is 65 so hop count is 65 - ttl
            hops = map(lambda x: 65-x, fhops)
            return array(hops).std()

        # phase 1 data gathering
        regexes = [
            # 50 packets transmitted, 47 received, 6% packet loss, time 10112ms
            # pkt_tx = packets transmitted, pkt_rx =  packets received
            "(?P<pkt_tx>\d+) packets transmitted, (?P<pkt_rx>\d+) received",

            # rtt min/avg/max/mdev = 8.216/25.760/102.090/21.884 ms
            # rtt_min, rtt_avg, rtt_max, rtt_mdev
            "rtt min/avg/max/mdev = (?P<rtt_min>\d+\.\d+)/(?P<rtt_avg>\d+\.\d+)/(?P<rtt_max>\d+\.\d+)/(?P<rtt_mdev>\d+\.\d+) ms",

            # per packet ttl (ppt_ttl), time (ppt_rtt) and seq (ppt_seq)
            "icmp_seq=(?P<ppt_seq>\d+) ttl=(?P<ppt_ttl>\d+) time=(?P<ppt_rtt>\d+\.\d+)"
        ]

        # compile regexes
        self.regexes = map(re.compile, regexes)

        # phase 2 result calculation
        # these functions get a dict of lists as an argument which
        # holds the result of the parsing process
        self.whats = dict(
            # average RTT just take parsed value
            rtt_avg  = lambda r: float(r['rtt_avg'][0]),

            # min RTT just take parsed value
            rtt_min  = lambda r: float(r['rtt_min'][0]),

            # list of rtts
            rtt_list = lambda r: map(float, r['ppt_rtt']),

            # list of seqs
            seq_list = lambda r: map(int, r['ppt_seq']),

            # pkt_tx = packets transmitted, take parsed value
            pkt_tx   = lambda r: int(r['pkt_tx'][0]),

            # pkt_rx = packets received, take parsed value
            pkt_rx   = lambda r: int(r['pkt_rx'][0]),

            # compute average hopcount
            hop_avg  = compute_hop_avg,

            # compute hopcount deviation
            hop_std  = compute_hop_std,

            # list of hop counts,
            hop      = lambda r: map(lambda x: 65-int(x), r['ppt_ttl']),

            # compute packet loss
            packet_loss = lambda r: 1-float(r['pkt_rx'][0])/float(r['pkt_tx'][0])
        )

    def createRecord(self, filename, test):
        return PingRecord(filename, self.regexes, self.whats)

