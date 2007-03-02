#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, sre, socket, sys, optparse, time
from logging import info, debug, warn, error
from numpy import *
from scipy import *

# umic-mesh imports
from um_application import Application
from um_analysis import *


class NuttcpStats(Analysis):

    def __init__(self):
        "Constructor of the object"
    
        Analysis.__init__(self)

        # initialization of the option parser
        usage = "usage: %prog [options] [HOW] WHAT \n" \
                "where  HOW := { min | max | mean | median | deviation } \n" \
                "and    WHAT := { tput | RTO_count | RTO_msec | RTT_msec | "\
                "RTT_var | probes | backoffs | lost_packets }"

        self.parser.set_usage(usage)


    def set_option(self):

        Analysis.set_option(self)

        if not self.action in ("tput", "RTO_count", "RTO_msec", "RTT_msec", \
                               "RTT_var", "probes", "backoffs", "lost_packets", \
                               "retransmits"):
            self.parser.error("unknown WHAT %s" %(self.action))


    def tput(self):

        print("Throughput ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("rate_Mbps=\d+\.\d+", "\d+\.\d+")

        return stats_input


    def RTO_count(self):

        print("#RTO ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("rto_count=\d+", "\d+")

        for source in range(1, self.nodes+1):
            for target in range(1, self.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def RTO_msec(self):

        print("RTO msec ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("rto_msec=\d+", "\d+")

        return stats_input


    def RTT_msec(self):

        print("RTT msec ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("rtt_msec=\d+", "\d+")

        return stats_input


    def RTT_var(self):

        print("RTT var msec ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("rtt_var_msec=\d+", "\d+")

        return stats_input


    def probes(self):

        print("#0WProbes ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("0wprobes_count=\d+", "\d+")

        for source in range(1, self.nodes+1):
            for target in range(1, self.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def backoffs(self):

        print("#Backoffs ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("backoffs_count=\d+", "\d+")

        for source in range(1, self.nodes+1):
            for target in range(1, self.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def lost_packets(self):

        print("#Lost Packets ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("lost_packets=\d+", "\d+")

        for source in range(1, self.nodes+1):
            for target in range(1, self.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def retransmits(self):

        print("#Retransmits ... \n")
        stats_input = zeros([self.nodes,self.nodes], float)
        stats_input = self.get_stats("retransmitted_packets=\d+", "\d+")

        for source in range(1, self.nodes+1):
            for target in range(1, self.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def main(self):
        "Main method of the nuttcp stats object"

        self.parse_option()
        self.set_option()
        Analysis.run(self)



if __name__ == '__main__':
    NuttcpStats().main()
    
