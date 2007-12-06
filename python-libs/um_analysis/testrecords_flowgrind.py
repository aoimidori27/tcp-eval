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
            
            #after_source_TX:804
            #"after_source_TX:(?P<pkt_TX>\d+)",

            #after_target_RX:769
            #"after_target_RX:(?P<pkt_RX>\d+)"
        
        ]
        # compile regexes
        self.regexes = map(re.compile, regexes)


        # phase 2 result calculation
        self.whats = dict(
            # average thruput just take parsed value
            thruput = lambda r: float(r['thruput'][0]),

         )

        

    def createRecord(self, filename, test):
        return FlowgrindRecord(filename, self.regexes, self.whats)
