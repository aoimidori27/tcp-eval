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

class RateRecord(TestRecord):
    def __init__(self, filename, regexes, whats):
        TestRecord.__init__(self, filename, regexes, whats)


class RateRecordFactory():
    def __init__(self):
        # helper functions
        def createRateDict(r):
            res = dict()
            keys = [ "1", "2", "5_5", "11", "6", "9", "12", "18", "24", "36", "48", "54" ]

            for key in keys:

                # ignore empty rates because some may not be present (for instance in 802.11a mode)
                try:
                    rate_list = r['rate_%s_pkts' %key]
                except KeyError:
                    continue

                # raise a KeyError because this is what the calling class expects
                if len(r['rate_%s_pkts' %key])<2:
                    raise KeyError("len(rate_%s_pkts)<2" %key)
                res[key] = int(r['rate_%s_pkts' %key][1])-int(r['rate_%s_pkts' %key][0])

            return res

        def calcAverageRate(r):
            """Calculates the average rate."""

            rates = createRateDict(r)
            nominator = 0
            denom     = 0

            for (key, val) in rates.iteritems():
                if key == "5_5":
                    fac = 5.5
                else:
                    fac = float(key)

                nominator += fac*val
                denom     += val

            # if there weren't any packets return 0 as average rate
            if denom==0:
                warn("No packets")
                return 0
            return (nominator/denom)

        # phase 1 data gathering
        regexes = [
            # rate    tt  perfect failed  pkts    avg_tries   last_tx
            #    1    14206   14016    0  32095   1.05    1.222
            "(?P<rate_1_current>.)  1  \t *(?P<rate_1_tt>\d+) *\t *(?P<rate_1_perfect>\d+) *\t *(?P<rate_1_failed>\d+) *\t *(?P<rate_1_pkts>\d+) *\t *(?P<rate_1_avg_tries>\d+\.\d+) *\t *(?P<rate_1_last_tx>[\-\d-]+)",
            "(?P<rate_2_current>.)  2  \t *(?P<rate_2_tt>\d+) *\t *(?P<rate_2_perfect>\d+) *\t *(?P<rate_2_failed>\d+) *\t *(?P<rate_2_pkts>\d+) *\t *(?P<rate_2_avg_tries>\d+\.\d+) *\t *(?P<rate_2_last_tx>[\-\d-]+)",
            "(?P<rate_5_5_current>.)  5\.5\t *(?P<rate_5_5_tt>\d+) *\t *(?P<rate_5_5_perfect>\d+) *\t *(?P<rate_5_5_failed>\d+) *\t *(?P<rate_5_5_pkts>\d+) *\t *(?P<rate_5_5_avg_tries>\d+\.\d+) *\t *(?P<rate_5_5_last_tx>[\.\d-]+)",
            "(?P<rate_11_current>.) 11  \t *(?P<rate_11_tt>\d+) *\t *(?P<rate_11_perfect>\d+) *\t *(?P<rate_11_failed>\d+) *\t *(?P<rate_11_pkts>\d+) *\t *(?P<rate_11_avg_tries>\d+\.\d+) *\t *(?P<rate_11_last_tx>[\.\d-]+)",
            "(?P<rate_6_current>.)  6  \t *(?P<rate_6_tt>\d+) *\t *(?P<rate_6_perfect>\d+) *\t *(?P<rate_6_failed>\d+) *\t *(?P<rate_6_pkts>\d+) *\t *(?P<rate_6_avg_tries>\d+\.\d+) *\t *(?P<rate_6_last_tx>[\.\d-]+)",
            "(?P<rate_9_current>.)  9  \t *(?P<rate_9_tt>\d+) *\t *(?P<rate_9_perfect>\d+) *\t *(?P<rate_9_failed>\d+) *\t *(?P<rate_9_pkts>\d+) *\t *(?P<rate_9_avg_tries>\d+\.\d+) *\t *(?P<rate_9_last_tx>[\.\d-]+)",
            "(?P<rate_12_current>.) 12  \t *(?P<rate_12_tt>\d+) *\t *(?P<rate_12_perfect>\d+) *\t *(?P<rate_12_failed>\d+) *\t *(?P<rate_12_pkts>\d+) *\t *(?P<rate_12_avg_tries>\d+\.\d+) *\t *(?P<rate_12_last_tx>[\.\d-]+)",
            "(?P<rate_18_current>.) 18  \t *(?P<rate_18_tt>\d+) *\t *(?P<rate_18_perfect>\d+) *\t *(?P<rate_18_failed>\d+) *\t *(?P<rate_18_pkts>\d+) *\t *(?P<rate_18_avg_tries>\d+\.\d+) *\t *(?P<rate_18_last_tx>[\.\d-]+)",
            "(?P<rate_24_current>.) 24  \t *(?P<rate_24_tt>\d+) *\t *(?P<rate_24_perfect>\d+) *\t *(?P<rate_24_failed>\d+) *\t *(?P<rate_24_pkts>\d+) *\t *(?P<rate_24_avg_tries>\d+\.\d+) *\t *(?P<rate_24_last_tx>[\.\d-]+)",
            "(?P<rate_36_current>.) 36  \t *(?P<rate_36_tt>\d+) *\t *(?P<rate_36_perfect>\d+) *\t *(?P<rate_36_failed>\d+) *\t *(?P<rate_36_pkts>\d+) *\t *(?P<rate_36_avg_tries>\d+\.\d+) *\t *(?P<rate_36_last_tx>[\.\d-]+)",
            "(?P<rate_48_current>.) 48  \t *(?P<rate_48_tt>\d+) *\t *(?P<rate_48_perfect>\d+) *\t *(?P<rate_48_failed>\d+) *\t *(?P<rate_48_pkts>\d+) *\t *(?P<rate_48_avg_tries>\d+\.\d+) *\t *(?P<rate_48_last_tx>[\.\d-]+)",
            "(?P<rate_54_current>.) 54  \t *(?P<rate_54_tt>\d+) *\t *(?P<rate_54_perfect>\d+) *\t *(?P<rate_54_failed>\d+) *\t *(?P<rate_54_pkts>\d+) *\t *(?P<rate_54_avg_tries>\d+\.\d+) *\t *(?P<rate_54_last_tx>[\.\d-]+)"
        ]

        # compile regexes
        self.regexes = map(re.compile, regexes)

        # phase 2 result calculation
        # these functions get a dict of lists as an argument which
        # holds the result of the parsing process
        self.whats = dict(
            # rate dict
            pkt_rates_tx   = createRateDict,

            # average rage
            average_rate = calcAverageRate
        )

    def createRecord(self, filename, test):
        return RateRecord(filename, self.regexes, self.whats)

