#!/usr/bin/envpython
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# python imports
import re
import time
from logging import info, debug, warn, error

# um imports
from testrecord import TestRecord
from um_functions import StrictStruct

class FlowgrindRecord(TestRecord):
    def __init__(self, filename, regexes, whats):
        TestRecord.__init__(self, filename, regexes, whats)


class FlowgrindRecordFactory():
    def __init__(self):
        # keys
         # raw_values and there convert function
        keys = { 'begin' : float,
                 'end'   : float,
                 'tput' : float,
                 'transac' : float,
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
                 'tret'    : int,
                 'fack'    : int,
                 'reor'    : int,
                 'krtt'    : float,
                 'krttvar' : float,
                 'krto'    : float,
                 'castate' : lambda x:x,
                 'mss'     : int,
                 'mtu'     : int,
                 # optional values
                 'dupthresh':int,
                 }

        def removeInf(val):
            return str(val) != 'inf'


        # convenience function to group flows
        def group_flows(r):

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
                    except TypeError, inst:
                        # ignore optional dupthresh
                        if not (key == 'dupthresh'):
                            warn('Failed to get r["%s"][%u]' %(key,i))
                            raise inst
                flow['size'] += 1

            return flow_map.values()

        # combine all flows of a given directory to one list for each key
        def filter_direction(r, direction):
            flow_ids = map(int, set(r['flow_id']))
            flow_map = dict()

            flows = group_flows(r)

            # get keys and initializa map
            for key in keys.iterkeys():
                flow_map[key] = list()

            for flow_id in flow_ids:
                for key in flow_map.iterkeys():
                    flow_map[key].extend(flows[flow_id][direction][key])

            return flow_map


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

        # phase 1 data gathering
        regexes = [
            #   0 S: mrouter4/169.254.9.4, MSS = 1448, MTU = 1500 (Ethernet/PPP), sbuf = 16384/0, rbuf = 87380/0 (real/req), delay = 5.00s/0.00s, duration = 60.00s/0.00s, through = 0.645530/0.000000Mb/s, 591/0 request blocks, 0/0 response blocks (out/in)
            "S: .* through = (?P<thruput>\d+\.\d+)(\/(?P<thruput_back>\d+\.\d+))?Mb/s",

            # receiver calculated thruput
            "R: .* through = (?P<thruput_recv>\d+\.\d+)(\/(?P<thruput_back_recv>\d+\.\d+))?Mb/s",

            # blocks
            "(?P<requ_in_sum>\d+)/(?P<requ_out_sum>\d+) request blocks, "\
            "(?P<resp_in_sum>\d+)/(?P<resp_out_sum>\d+) response blocks",
            # "listen port =\s*(?P<lport>\d+)",

            # # ID begin   end  through transac min RTT avg RTT max RTT min IAT avg IAT max IAT cwnd ssth uack sack lost retr tret fack reor rtt rttvar rto ca state mss mtu
            "(?P<direction>[S,R])\s+"\
            "(?P<flow_id>\d+)\s+"\
            "(?P<begin>\d+\.\d+)\s+(?P<end>\d+\.\d+)\s+"\
            "(?P<tput>\d+\.\d+)\s+"\
            "(?P<transac>\d+\.\d+)\s+"\
            "(?P<rtt_min>\d+\.\d+|inf)\s+(?P<rtt_avg>\d+\.\d+|inf)\s+(?P<rtt_max>\d+\.\d+|inf)\s+"\
            "(?P<iat_min>\d+\.\d+|inf)\s+(?P<iat_avg>\d+\.\d+|inf)\s+(?P<iat_max>\d+\.\d+|inf)\s+"\
            "(?P<cwnd>\d+)\s+(?P<ssth>\d+|INT_MAX|SHRT_MAX)\s+(?P<uack>\d+)\s+(?P<sack>\d+)\s+"\
            "(?P<lost>\d+)\s+(?P<retr>\d+)\s+(?P<tret>\d+)\s+(?P<fack>\d+)\s+(?P<reor>\d+)\s+"\
            "(?P<krtt>\d+\.\d+)\s+(?P<krttvar>\d+\.\d+)\s+(?P<krto>\d+\.\d+)\s+"\
            "(?P<castate>loss|open|disrdr|rcvry)\s+"\
            "(?P<mss>\d+)\s+(?P<mtu>\d+)\s+"\
            # optional extension -wolff
            "((?P<cret>\d+)\s+(?P<cfret>\d+)\s+(?P<ctret>\d+)\s+(?P<dupthresh>\d+)\s+)?"\
            # sporious retransmissions
            "(?P<srx>\d+)?",
            # Fri Oct  8 16:50:11 2010: controlling host = vmhost2, number of flows = 1, reporting interval = 0.05s, [tput] = 10**6 bit/second (SVN Rev 6595)
            "^# (?P<test_start_time>(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (?:|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) +\d{1,2} \d{2}:\d{2}:\d{2} \d{4}): .* reporting interval = (?P<reporting_interval>\d+\.\d+)"
        ]

        # compile regexes
        self.regexes = map(re.compile, regexes)

        def extInt(a):
            try:
                ret = int(a)
            except TypeError, inst:
                ret = None
            return ret

        def average(val):
            return sum(val) / len(val)

        # phase 2 result calculation
        self.whats = dict(
            # average thruput: just sum up all summary lines (calculated from sender estimate)
            thruput           = lambda r: sum(map(float, r['thruput'])),
            # average thruput: just sum up all summary lines (calculated from receiver estimate)
            thruput_recv      = lambda r: sum(map(float, r['thruput_back_recv'])),
            rtt_min           = lambda r: min(map(float, filter(removeInf,  filter_direction(r, 'S')['rtt_min']))),
            rtt_max           = lambda r: max(map(float, filter(removeInf, filter_direction(r, 'S')['rtt_max']))),
            rtt_avg           = lambda r: average(map(float, filter(removeInf, filter_direction(r, 'S')['rtt_avg']))),
            total_retransmits      = lambda r: max(map(extInt, r['cret'])),
            total_fast_retransmits = lambda r: max(map(extInt, r['cfret'])),
            total_rto_retransmits  = lambda r: max(map(extInt, r['ctret'])),
            # list of summary lines
            thruput_list      = lambda r: map(float, r['thruput']),
            lport_list        = lambda r: map(int, r['lport']),
            flow_ids          = lambda r: map(int, set(r['flow_id'])),
            flows             = group_flows,
            flow_id_list      = lambda r: map(int, r['flow_id']),
            forward_tput_list = lambda r: map(float, r['forward_tput_list']),
            reverse_tput_list = lambda r: map(float, r['reverse_tput_list']),
            test_start_time   = lambda r: time.mktime(time.strptime(r['test_start_time'][0])),
            outages           = outages
        )

    def createRecord(self, filename, test):
        return FlowgrindRecord(filename, self.regexes, self.whats)

