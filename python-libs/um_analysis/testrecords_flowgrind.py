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
                 'bkof'    : int,
                 'krtt'    : float,
                 'krttvar' : float,
                 'krto'    : float,
                 'castate' : lambda x:x,
                 'mss'     : int,
                 'mtu'     : int,
                 # optional values
                 'dupthresh':int,
                 'revr':int
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
                flow_map[flow_id]['D'] = StrictStruct(direction='D', size=0, **keys)
                for key in keys.iterkeys():
                    flow_map[flow_id]['S'][key] = list()
                    flow_map[flow_id]['D'][key] = list()

            # iterate over all entries, rearrange and convert
            for i in range(len(r['flow_id'])):
                if r['direction'][i] == 'S':
                    d = 'S'
                else: # D,R (for compability)
                    d = 'D'

                flow = flow_map[int(r['flow_id'][i])][d]
                for (key, convert) in keys.iteritems():
                    try:
                        flow[key].append(convert(r[key][i]))
                    except KeyError, inst:
                        # ignore optional dupthresh and rvr
                        if key in ['dupthresh','revr']:
                            continue
                        warn('KeyError: Failed to get r["%s"][%u]' %(key,i))
                        raise inst
                    except TypeError, inst:
                        # ignore optional dupthresh and rvr
                        if key in ['dupthresh','revr']:
                            continue
                        warn('TypeError: Failed to get r["%s"][%u]' %(key,i))
                        raise inst
                flow.size += 1
            return flow_map.values()

        def outages(r, min_retr=1, min_time=0, time_abs=0):
            flow_map = dict()
            outages = dict()
            if time_abs: time_abs = time.mktime(time.strptime(r['test_start_time'][0]))
            if not 'begin' in r: return outages
            for i in range(len(r['begin'])):

                if r['direction'][i] == 'S':
                    dir = 'S'
                else: # D,R
                    dir = 'D'
                flow_id = int(r['flow_id'][i])
                tretr = int(r['tret'][i])
                bkof = int(r['bkof'][i])
                #revr = abs(tretr-bkof) #int(r['revr'][i])
                revr = int(r['revr'][i])
                if flow_id not in flow_map: flow_map[flow_id] = dict()
                if dir not in flow_map[flow_id]: flow_map[flow_id][dir] = None

                if flow_map[flow_id][dir] is None and tretr > 0:
                    flow_map[flow_id][dir] = dict(begin=i, tretr=tretr, revr=revr, bkof=bkof)
                if flow_map[flow_id][dir] is not None:
                    tmp = flow_map[flow_id][dir]
                    if tretr > 0:
                        tmp['tretr'] = tretr
                        tmp['revr'] = revr
                        tmp['bkof'] = bkof
                    else:
                        b = float(r['begin'][tmp['begin']])
                        e = float(r['begin'][i])
                        tre = float(tmp['tretr'])
                        rev = float(tmp['revr'])
                        bk = float(tmp['bkof'])
                        if tre >= min_retr and e - b >= min_time:
                            if flow_id not in outages: outages[flow_id] = dict()
                            if dir not in outages[flow_id]: outages[flow_id][dir] = []
                            outages[flow_id][dir].append(dict(begin=b+time_abs,end=e+time_abs,tretr=tre,revr=rev,bkof=bk))
                        flow_map[flow_id][dir] = None
            return outages


        # phase 1 data gathering
        regexes = [
            #  0 S: 10.0.1.147/vmrouter401, sbuf = 16384/0, rbuf = 87380/0 (real/req), SMSS = 1420, Path MTU = 1472, Interface MTU = 1472 (unknown), flow duration 30.004s/30.000s (real/req), through = 8.457316/0.024688Mbit/s (out/in), 128.58 transactions/s, 3872/0 request blocks (out/in), 0/3858 response blocks (out/in), 39.744/115.262/170.705 RTT (min/avg/max)

            # sender buffers and throughput
            "S: .* sbuf = (?P<s_sbuf_real>\d+)(\/(?P<s_sbuf_req>\d+)), rbuf = (?P<s_rbuf_real>\d+)(\/(?P<s_rbuf_req>\d+))",
            "S: .* through = (?P<s_thruput_out>\d+\.\d+)(\/(?P<s_thruput_in>\d+\.\d+))?Mbit\/s \(out\/in\)",

            # destination buffers and throughput
            "[R,D]: .* sbuf = (?P<d_sbuf_real>\d+)(\/(?P<d_sbuf_req>\d+)), rbuf = (?P<d_rbuf_real>\d+)(\/(?P<d_rbuf_req>\d+))",
            "[R,D]: .* through = (?P<d_thruput_out>\d+\.\d+)(\/(?P<d_thruput_in>\d+\.\d+))?Mbit\/s",

            # optional calculated source transactions
            "S: .* transactions\/s = (?P<s_transac>\d+\.\d+)",
            # source request/ response blocks
            "S: .* request blocks = (?P<s_requ_out_sum>\d+)\/(?P<s_requ_in_sum>\d+)",
            "S: .* response blocks = (?P<s_resp_out_sum>\d+)/(?P<s_resp_in_sum>\d+)",
            # reciever blocks
            "[R,D]: .* request blocks = (?P<d_requ_out_sum>\d+)\/(?P<s_requ_in_sum>\d+)",
            "[R,D]: .* response blocks = (?P<d_resp_out_sum>\d+)/(?P<s_resp_in_sum>\d+)",
            # optional icmp stats
            "# S ICMP: (?P<s_icmp_code_0>\d+) (?P<s_icmp_code_1>\d+)",
            "# D ICMP: (?P<d_icmp_code_0>\d+) (?P<d_icmp_code_1>\d+)",
            # flow duration
            # optional calculated source rtt
            "S: .* RTT = (?P<s_rtt_min>\d+\.\d+)\/(?P<s_rtt_avg>\d+\.\d+)\/(?P<s_rtt_max>\d+\.\d+)",
            # optional calculated destination iat
            "[R,D]: .* IAT = (?P<d_iat_min>\d+\.\d+)\/(?P<d_iat_avg>\d+\.\d+)\/(?P<d_iat_max>\d+\.\d+)",

            # ID begin   end  through transac min RTT avg RTT max RTT min IAT avg IAT max IAT cwnd ssth uack sack lost retr tret fack reor bkof revr  rtt rttvar    rto ca state smss pmtu
            "(?P<direction>[S,R,D])\s+"\
            "(?P<flow_id>\d+)\s+"\
            "(?P<begin>\d+\.\d+)\s+(?P<end>\d+\.\d+)\s+"\
            "(?P<tput>\d+\.\d+)\s+"\
            "(?P<transac>\d+\.\d+)\s+"\
            "(?P<rtt_min>\d+\.\d+|inf)\s+(?P<rtt_avg>\d+\.\d+|inf)\s+(?P<rtt_max>\d+\.\d+|inf)\s+"\
            "(?P<iat_min>\d+\.\d+|inf)\s+(?P<iat_avg>\d+\.\d+|inf)\s+(?P<iat_max>\d+\.\d+|inf)\s+"\
            "(?P<cwnd>\d+)\s+(?P<ssth>\d+|INT_MAX|SHRT_MAX)\s+(?P<uack>\d+)\s+(?P<sack>\d+)\s+"\
            "(?P<lost>\d+)\s+(?P<retr>\d+)\s+(?P<tret>\d+)\s+(?P<fack>\d+)\s+(?P<reor>\d+)\s+(?P<bkof>\d+)\s+"\
            # optional lcd revert count
            "(?P<revr>\d+)\s+"\
            "(?P<krtt>\d+\.\d+)\s+(?P<krttvar>\d+\.\d+)\s+(?P<krto>\d+\.\d+)\s+"\
            "(?P<castate>loss|open|disorder|recover)\s+"\
            "(?P<mss>\d+)\s+(?P<mtu>\d+)\s+",
            # optional extension -wolff
            #"((?P<cret>\d+)\s+(?P<cfret>\d+)\s+(?P<ctret>\d+)\s+(?P<dupthresh>\d+)\s+)?"
            # # Sat Dec 11 08:20:49 2010: controlling host = vmhost1, number of flows = 2, reporting interval = 0.05s, [through] = 10**6 bit/second (SVN Rev 6756)
            #
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
            thruput           = lambda r: sum(map(float, r['s_thruput_out'])),
            # average thruput: just sum up all summary lines (calculated from receiver estimate)
            thruput_recv      = lambda r: sum(map(float, r['d_thruput_out'])),
            rtt_min           = lambda r: min(map(float, r['s_rtt_min'])),
            rtt_max           = lambda r: max(map(float, r['s_rtt_max'])),
            rtt_avg           = lambda r: average(map(float, r['s_rtt_avg'])),
            total_retransmits      = lambda r: max(map(extInt, r['cret'])),
            total_fast_retransmits = lambda r: max(map(extInt, r['cfret'])),
            total_rto_retransmits  = lambda r: max(map(extInt, r['ctret'])),
            # list of summary lines
            thruput_list      = lambda r: map(float, r['s_thruput_out']),
            thruput_recv_list = lambda r: map(float, r['d_thruput_out']),
            transac_list      = lambda r: map(float, r['s_transac']),
            rtt_min_list      = lambda r: map(float, r['s_rtt_min']),
            rtt_max_list      = lambda r: map(float, r['s_rtt_max']),
            rtt_avg_list      = lambda r: map(float, r['s_rtt_avg']),
            iat_min_list      = lambda r: map(float, r['d_iat_min']),
            iat_max_list      = lambda r: map(float, r['d_iat_max']),
            iat_avg_list      = lambda r: map(float, r['d_iat_avg']),
            lport_list        = lambda r: map(int, r['lport']),
            flow_ids          = lambda r: map(int, set(r['flow_id'])),
            flows             = group_flows,
            flow_id_list      = lambda r: map(int, r['flow_id']),
            forward_tput_list = lambda r: map(float, r['forward_tput_list']),
            reverse_tput_list = lambda r: map(float, r['reverse_tput_list']),
            test_start_time   = lambda r: time.mktime(time.strptime(r['test_start_time'][0])),
            outages           = outages,
            # icmp stats
            s_icmp_code_0 = lambda r: sum(map(int, r['s_icmp_code_0'])),
            s_icmp_code_1 = lambda r: sum(map(int, r['s_icmp_code_1'])),
            d_icmp_code_0 = lambda r: sum(map(int, r['d_icmp_code_0'])),
            d_icmp_code_1 = lambda r: sum(map(int, r['d_icmp_code_1'])),
        )

    def createRecord(self, filename, test):
        return FlowgrindRecord(filename, self.regexes, self.whats)

