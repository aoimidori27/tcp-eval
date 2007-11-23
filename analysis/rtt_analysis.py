#!/usr/bin/env python
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
import optparse
import time
import gc
from logging import info, debug, warn, error
from datetime import timedelta, datetime

import numpy

# umic-mesh imports
from um_application import Application
from um_config import *
from um_functions import call
from um_analysis.testrecords import TestRecordFactory
from um_analysis.analysis import Analysis

from um_gnuplot import UmPointPlot

class RttAnalysis(Analysis):
    "Application for rtt analysis"

    def __init__(self):

        Analysis.__init__(self)
        self.parser.set_defaults(indir = "./",
                                 outdir = "./rtt");


        self.nodepairs = dict()


    def set_option(self):
        "Set options"
        Analysis.set_option(self)


    def onLoad(self, record, iterationNo, scenarioNo, test):
    
        recordHeader = record.getHeader()
        src = recordHeader["ping_src"]
        dst = recordHeader["ping_dst"]
        count = int(recordHeader["ping_count"])

        # get per packet statistics
        rtts = record.calculate("rtt_list") 
        seqs = record.calculate("seq_list")

        # ignore results with no packets received
        if not rtts:
            return

        key = (src, dst)

        if not self.nodepairs.has_key(key):
            assoc = dict()
            self.nodepairs[key] = assoc
        else:
            assoc = self.nodepairs[key]

        # only map rtts of packets available
        for i in range(len(seqs)):
            # add for every iteration ping_count
            seq = seqs[i]+(iterationNo)*count
            rtt = rtts[i]
            assoc[seq] = rtt
        

    def generateRttGraph(self, pair, data):
        """
        This function expects a node pair, and a dict
        which maps sequence numbers to rtt
        """

        prefix = self.options.outdir+"/rtt_%s_%s" %pair
        valfilename = prefix+".values"

        info("Generating %s" %valfilename)
        fh = file(valfilename, "w")

        # header
        fh.write("# RTT graph for ping measurement from %s to %s\n"% pair)
        fh.write("# seq,  rtt\n")

        # sort by sequence number
        skeys = data.keys()
        skeys.sort()

        for key in skeys:
            fh.write("%u %f\n" %(key,data[key]))

        fh.close()

        info("Generating %s" %valfilename)

        p = UmPointPlot()
        p.setYLabel("RTT in ms")
        p.setXLabel("ICMP sequence number")
        p.setOutput(prefix+".tex")

        p.plot(valfilename, "RTT")
        # workaround to flush plot to disk
        p = None
        gc.collect()


        # workaround for bug in gnuplot2pdf
        # os.chdir(self.options.outdir)
        info("Generating %s.pdf" % prefix)
        cmd = ["gnuplot2pdf.py", "-f", "-p","pdf"]
        if self.options.cfgfile:
            cmd.extend(["-c", self.options.cfgfile])
        if self.options.debug:
            cmd.append("--debug")
        cmd.append(prefix)
        call(cmd, shell=False)
        


    def run(self):
        "Main Method"

        # only load ping test records
        self.loadRecords(tests=["ping","fping"])

        # for each pair generate an graph
        for pair in self.nodepairs:
            self.generateRttGraph(pair, self.nodepairs[pair])
        
            
    def main(self):
        "Main method of the ping stats object"

        self.parse_option()
        self.set_option()
        RttAnalysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    RttAnalysis().main()

