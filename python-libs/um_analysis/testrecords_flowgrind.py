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
from um_functions import StrictStruct

########## Flowgrind Parsing #############

class FlowgrindRecord(TestRecord):


    def __init__(self, filename, regexes, whats):
        TestRecord.__init__(self, filename, regexes, whats)

    
class FlowgrindRecordFactory():

    def __init__(self):
        # phase 1 data gathering
        regexes = [
            #0: 169.254.9.1/mrouter1, MSS = 536, ws = 16384/16384 (0/0), bs = 8192/8192, delay = 0.00s/0.00s, duration = 15.00s/0.00s, thruput = 0.607300Mb/s (139 blocks), cc = cubic
            "thruput = (?P<thruput>\d+\.\d+)Mb/s",

            # ID   begin     end   c/s Mb/s   s/c Mb/s RTT, ms: min        avg        max IAT, ms: min        avg        max    cwnd  ssth #uack #sack #lost #retr #fack #reor     rtt  rttvar      rto
            " +(?P<flow_id>\d+) +(?P<begin>\d+\.\d+) +(?P<end>\d+\.\d+)"\
            " +(?P<forward_tput>\d+\.\d+) +(?P<reverse_tput>\d+\.\d+)"\
            " +(?P<rtt_min>\d+\.\d+) +(?P<rtt_avg>\d+\.\d+) +(?P<rtt_max>\d+\.\d+)"\
            " +(?P<iat_min>\d+\.\d+) +(?P<iat_avg>\d+\.\d+) +(?P<iat_max>\d+\.\d+)"\
            " +(?P<cwnd>\d+) +(?P<ssth>\d+) +(?P<uack>\d+) +(?P<sack>\d+)"\
            " +(?P<lost>\d+) +(?P<retr>\d+) +(?P<fack>\d+) +(?P<reor>\d+)"\
            " +(?P<krtt>\d+\.\d+) +(?P<krttvar>\d+\.\d+) +(?P<krto>\d+\.\d+)"
        
        ]
        # compile regexes
        self.regexes = map(re.compile, regexes)


        # convenience function to group flows
        def group_flows(self, r):
            flow_ids = map(int, set(r['flow_id']))

            flow_map = dict()

            # initialize value records
            for flow in flow_ids:
                flow_map[flow] = dict()

        # phase 2 result calculation
        self.whats = dict(
            # average thruput just take parsed value
            thruput = lambda r: float(r['thruput'][0]),

            flow_ids          = lambda r: map(int, set(r['flow_id'])),
#            flows             = self.group_flows,
            flow_id_list      = lambda r: map(int, r['flow_id']),
            forward_tput_list = lambda r: map(float, r['forward_tput_list']),
            reverse_tput_list = lambda r: map(float, r['reverse_tput_list'])                        

         )

        

    def createRecord(self, filename, test):
        return FlowgrindRecord(filename, self.regexes, self.whats)
