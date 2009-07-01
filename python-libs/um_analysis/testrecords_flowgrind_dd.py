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

class FlowgrindddRecord(TestRecord):


    def __init__(self, filename, regexes, whats):
        TestRecord.__init__(self, filename, regexes, whats)

    
class FlowgrindddRecordFactory():

    def __init__(self):
        # phase 1 data gathering
        regexes = [
            #0: 169.254.9.1/mrouter1, MSS = 536, ws = 16384/16384 (0/0), bs = 8192/8192, delay = 0.00s/0.00s, duration = 15.00s/0.00s, thruput = 0.607300Mb/s (139 blocks), cc = cubic
            "thruput = (?P<thruput>\d+\.\d+)(\/(?P<thruput_back>\d+\.\d+))?Mb/s",

            # S ID   begin     end   tput Mb/s RTT, ms: min        avg        max IAT, ms: min        avg        max    cwnd  ssth #uack #sack #lost #retr #fack #reor     rtt  rttvar      rto    mss     mtu
	    " +(?P<direction>[S,R])"\
            " +(?P<flow_id>\d+) +(?P<begin>\d+\.\d+) +(?P<end>\d+\.\d+)"\
            " +(?P<tput>\d+\.\d+)"\
            " +(?P<rtt_min>\d+\.\d+|inf) +(?P<rtt_avg>\d+\.\d+|inf) +(?P<rtt_max>\d+\.\d+|inf)"\
            " +(?P<iat_min>\d+\.\d+|inf) +(?P<iat_avg>\d+\.\d+|inf) +(?P<iat_max>\d+\.\d+|inf)"\
            " +(?P<cwnd>\d+\.\d+) +(?P<ssth>\d+) +(?P<uack>\d+) +(?P<sack>\d+)"\
            " +(?P<lost>\d+) +(?P<retr>\d+) +(?P<fack>\d+) +(?P<reor>\d+)"\
            " +(?P<krtt>\d+\.\d+) +(?P<krttvar>\d+\.\d+) +(?P<krto>\d+\.\d+)"\
	    " +(?P<castate>loss|open|disorder|recovery) +(?P<mss>\d+) +(?P<mtu>\d+)",
	    "^# (?P<test_start_time>(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (?:|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} \d{2}:\d{2}:\d{2} \d{4}): controlling host"
        ]

        # compile regexes
        self.regexes = map(re.compile, regexes)

        # convenience function to group flows
        def group_flows(r):

            # raw_values and there convert function
            keys = { 'begin' : float,
                     'end'   : float,
                     'tput' : float,
                     'rtt_min' : float,
                     'rtt_avg' : float,
                     'rtt_max' : float,
                     'iat_min' : float,
                     'iat_avg' : float,
                     'iat_max' : float,
                     'cwnd'    : float,
                     'ssth'    : int,
                     'uack'    : int,
                     'sack'    : int,
                     'lost'    : int,
                     'retr'    : int,
                     'fack'    : int,
                     'reor'    : int,
                     'krtt'    : float,
                     'krttvar' : float,
                     'krto'    : float,
                     'castate' : lambda x:x,
		     'mss'     : int,
		     'mtu'     : int }
            
            flow_ids = map(int, set(r['flow_id']))
            flow_map = dict()

            # initialize value records
            for flow_id in flow_ids:
                flow_map[flow_id] = dict()
                flow_map[flow_id]['S'] = StrictStruct(direction='S', size=0, **keys)
                flow_map[flow_id]['R'] = StrictStruct(direction='R', size=0, **keys)
                for key in keys.iterkeys():
                    flow_map[flow_id]['S'][key] = list()
                    flow_map[flow_id]['R'][key] = list()

            # iterate over all entries, shuffle and convert
            for i in range(len(r['flow_id'])):
                    if r['direction'][i] == 'S':
                        dir = 'S'
                    else:
                        dir = 'R'

                    flow = flow_map[int(r['flow_id'][i])][dir]
                    for (key, convert) in keys.iteritems():
                            try:
                                flow[key].append(convert(r[key][i]))
                            except KeyError, inst:
                                warn('Failed to get r["%s"][%u]' %(key,i))
                                raise inst
                    flow['size'] += 1

            return flow_map.values()

        def outages(r, min_retr=0, min_time=0, time_abs=1):
		flow_map = dict()
		outages = dict()
		if time_abs: time_abs = time.mktime(time.strptime(r['test_start_time'][0]))
		for i in range(len(r['begin'])):
			flow_id, retr, dir = int(r['flow_id'][i]), int(r['retr'][i]), r['direction'][i]

			if flow_id not in flow_map: flow_map[flow_id] = dict()
			if dir not in flow_map[flow_id]: flow_map[flow_id][dir] = None

			if flow_map[flow_id][dir] is None and retr > 0:
				flow_map[flow_id][dir] = dict(begin=i, retr=retr)
			if flow_map[flow_id][dir] is not None:
				tmp = flow_map[flow_id][dir]
				if retr > 0:
					tmp['retr'] = retr
				else:
					b, e, re = float(r['begin'][tmp['begin']]), float(r['begin'][i]), int(tmp['retr'])
					if re >= min_retr and e - b >= min_time:
						if flow_id not in outages: outages[flow_id] = dict()
						if dir not in outages[flow_id]: outages[flow_id][dir] = []
						outages[flow_id][dir].append(dict(begin=b+time_abs,end=e+time_abs,retr=re))
					flow_map[flow_id][dir] = None
		return outages



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
            reverse_tput_list = lambda r: map(float, r['reverse_tput_list']),
            test_start_time   = lambda r: time.mktime(time.strptime(r['test_start_time'][0])),
            outages	      = outages
         )

    def createRecord(self, filename, test):
        return FlowgrindddRecord(filename, self.regexes, self.whats)

