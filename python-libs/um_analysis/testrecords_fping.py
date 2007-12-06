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

class FpingRecord(TestRecord):

    def __init__(self, filename, regexes, whats):
        TestRecord.__init__(self, filename, regexes, whats)


class FpingRecordFactory():

    def __init__(self):
        # phase 1 data gathering
        regexes = [
            # 169.254.9.1 : xmt/rcv/%loss = 30/22/26%, min/avg/max = 0.82/3.71/12.7
            # pkt_tx = packets transmitted, pkt_rx =  packets received        
            "xmt/rcv/%loss = (?P<pkt_tx>\d+)/(?P<pkt_rx>\d+)",
                
            # rtt_min, rtt_avg, rtt_max
            "min/avg/max = (?P<rtt_min>\d+\.\d+)/(?P<rtt_avg>\d+\.\d+)/(?P<rtt_max>\d+\.\d+)",

            # 169.254.9.1 : [8], 128 bytes, 3.98 ms (3.98 avg, 88% loss)
            "\[(?P<ppt_seq>\d+)\], .+, (?P<ppt_rtt>\d+\.\d+) ms"            
        
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

            # compute packet loss
            packet_loss = lambda r: 1-float(r['pkt_rx'][0])/float(r['pkt_tx'][0])
        )

        
    

    def createRecord(self, filename, test):
        return FpingRecord(filename, self.regexes, self.whats)


