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


class TestRecord:
    """
    A record of a single Test.
    For performance reasons it expects already compiled regexes and
    an initialize dict with function pointers to calculate results,
    from parsed values
    """

    def __init__(self, filename, regexes, whats):
        self.results = dict()
        self.regexes = regexes
        self.filename = filename
        self.whats = whats
        self.valid = True
        self.header = dict()
        self.parse()

    def parse(self):
        """ Parses the file associated with this record """

        fh = open(self.filename, "r")

        # read header
        while 1:
            line = fh.readline()
            line = line.strip()
            if line.startswith("BEGIN_TEST_OUTPUT"):
                break
            try:
                (key, value) = line.split("=",1)
                self.header[key] = value
            except ValueError:
                warn("%s: Error parsing Header! No Header??" % self.filename)
                fh.seek(0)
                break
    

        # read the rest
        output = fh.read()

        for regex in self.regexes:
            matches = regex.finditer(output)

            for match in matches:
                for key, value in match.groupdict().iteritems():
                    if not self.results.has_key(key):
                        self.results[key] = []
                    self.results[key].append(value)

        fh.close()

    def getHeader(self):
        """ returns the header as a dictionary """
        return self.header
        
    def calculate(self, what):
        """
        
        Calculate the given value from parsed values.
        If calculation failes, this record is marked invalid, and None is returned.
        
        """
        
        if not self.valid:
            return None
           
        try:
            return self.whats[what](self.results);
        except KeyError:
            warn("Failed get %s out of %s" %(what, self.filename))
            self.valid = False
            return None

    def isValid(self):
        return self.valid 



class TestRecordFactory:
    """ A factory for test records. """

    def __init__(self):
        self.factories = dict()

    def regCompile(self, regexes):
        cregs = []
        for regex in regexes:
            cregs.append(re.compile(regex))
        return cregs

    def initFactory(self, test):
        debug("Initializing test record factory for %s..." %test)
        if test=="ping":
            factory = PingRecordFactory()
        else:
            error("No factory found for:%s" %test)
            return None
        self.factories[test] = factory
        return factory
        

    def createRecord(self, filename, test):
        
        try:
            createRecord = self.factories[test].createRecord
        except KeyError:
            createRecord = self.initFactory(test).createRecord
        return createRecord(filename, test)

########## PING Parsing #############

class PingRecord(TestRecord):

    def __init__(self, filename, regexes, whats):
        TestRecord.__init__(self, filename, regexes, whats)


class PingRecordFactory(TestRecordFactory):

    def __init__(self):
        # phase 1 data gathering
        regexes = [
            # 50 packets transmitted, 47 received, 6% packet loss, time 10112ms
            # pkt_tx = packets transmitted, pkt_rx =  packets received        
            "(?P<pkt_tx>\d+) packets transmitted, (?P<pkt_rx>\d+) received",
                
            # rtt min/avg/max/mdev = 8.216/25.760/102.090/21.884 ms
            # rtt_min, rtt_avg, rtt_max, rtt_mdev
            "rtt min/avg/max/mdev = (?P<rtt_min>\d+\.\d+)/(?P<rtt_avg>\d+\.\d+)/(?P<rtt_max>\d+\.\d+)/(?P<rtt_mdev>\d+\.\d+) ms",
            
            # per packet ttl (ppt_ttl)
            "ttl=(?P<ppt_ttl>\d+) time="
        
        ]
        # compile regexes
        self.regexes = self.regCompile(regexes)


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
                       

        # phase 2 result calculation
        # these functions get a dict of lists as an argument which
        # holds the result of the parsing process
        self.whats = dict(
            # average RTT just take parsed value
            rtt_avg = lambda r: float(r['rtt_avg'][0]),

            # min RTT just take parsed value
            rtt_min = lambda r: float(r['rtt_min'][0]),

            # pkt_tx = packets transmitted, take parsed value
            pkt_tx  = lambda r: int(r['pkt_tx'][0]),

            # pkt_rx = packets received, take parsed value
            pkt_rx  = lambda r: int(r['pkt_rx'][0]),

            # compute average hopcount
            hop_avg = compute_hop_avg,

            # compute hopcount deviation
            hop_std = compute_hop_std,

            # list of hop counts,
            hop      = lambda r: map(lambda x: 65-int(x), r['ppt_ttl']),

            # compute packet loss
            packet_loss = lambda r: 1-float(r['pkt_rx'][0])/float(r['pkt_tx'][0])
        )

        
    

    def createRecord(self, filename, test):
        return PingRecord(filename, self.regexes, self.whats)
