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
from logging import info, debug, warn, error

from numpy import array

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
            "thruput = (?P<thruput>\d+\.\d+)(\/(?P<thruput_back>\d+\.\d+))?Mb/s",

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
        def group_flows(r):

            # raw_values and there convert function
            keys = { 'begin' : float,
                     'end'   : float,
                     'forward_tput' : float,
                     'reverse_tput' : float,
                     'rtt_min' : float,
                     'rtt_avg' : float,
                     'rtt_max' : float,
                     'iat_min' : float,
                     'iat_avg' : float,
                     'iat_max' : float,
                     'cwnd'    : int,
                     'ssth'    : int,
                     'uack'    : int,
                     'sack'    : int,
                     'lost'    : int,
                     'retr'    : int,
                     'fack'    : int,
                     'reor'    : int,
                     'krtt'    : float,
                     'krttvar' : float,
                     'krto'    : float }
            
            flow_ids = map(int, set(r['flow_id']))
            flow_map = dict()

            debug("hmm")

            # initialize value records
            for flow_id in flow_ids:
                flow_map[flow_id] = StrictStruct(id=flow_id, size=0, **keys)
                for key in keys.iterkeys():
                    setattr(flow_map[flow_id],key,list())

            # iterate over all entries, shuffle and convert
            for i in range(len(r['flow_id'])):
                flow = flow_map[int(r['flow_id'][i])]

                for (key, convert) in keys.iteritems():
                    try:
                        getattr(flow,key).append(convert(r[key][i]))
                    except KeyError, inst:
                        warn('Failed to get r["%s"][%u]' %(key,i))
                        raise inst
                flow.size += 1

            return flow_map.values()

        # phase 2 result calculation
        self.whats = dict(
            # average thruput: just sum up all summary lines 
            thruput = lambda r: sum(map(float, r['thruput'])),
            # list of summary lines
            thruput_list = lambda r: map(float, r['thruput']),

            flow_ids          = lambda r: map(int, set(r['flow_id'])),
            flows             = group_flows,
            flow_id_list      = lambda r: map(int, r['flow_id']),
            forward_tput_list = lambda r: map(float, r['forward_tput_list']),
            reverse_tput_list = lambda r: map(float, r['reverse_tput_list'])                        

         )

        

    def createRecord(self, filename, test):
        return FlowgrindRecord(filename, self.regexes, self.whats)
