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
                "RTT_var | probes | backoffs | lost_packets | ssthresh | cwnd }"

        self.parser.set_usage(usage)


    def set_option(self):
        "Option Setter"

        Analysis.set_option(self)

        if not self.action in ("tput", "RTO_count", "RTO_msec", "RTT_msec", \
                               "RTT_var", "probes", "backoffs", "lost_packets", \
                               "retransmits", "ssthresh", "cwnd"):
            self.parser.error("unknown WHAT %s" %(self.action))


    def ssthresh(self):
        "Greps ssthresh values"

        print("SS-Thresh ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("ssthresh_packets=\d+", "\d+")

        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input

    def cwnd(self):
        "Greps cwnd values"

        print("CWND ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("cwnd_packets=\d+", "\d+")

        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input

    def tput(self):
        "Greps tput values"

        print("Throughput ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("rate_Mbps=\d+\.\d+", "\d+\.\d+")

        #NaN values are 0 Tput
        stats_input = nan_to_num(stats_input)
        return stats_input


    def RTO_count(self):
        "Greps count of RTOs"

        print("#RTO ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("rto_count=\d+", "\d+")

        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def RTO_msec(self):
        "Greps RTO time"

        print("RTO msec ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("rto_msec=\d+", "\d+")

        return stats_input


    def RTT_msec(self):
        "Greps RTT value"

        print("RTT msec ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("rtt_msec=\d+", "\d+")

        return stats_input


    def RTT_var(self):
        "Greps RTT variation"

        print("RTT var msec ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("rtt_var_msec=\d+", "\d+")

        return stats_input


    def probes(self):
        "Greps count of probes"

        print("#0WProbes ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("0wprobes_count=\d+", "\d+")

        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def backoffs(self):
        "Greps count of backoffs"

        print("#Backoffs ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("backoffs_count=\d+", "\d+")

        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def lost_packets(self):
        "Greps count of lost packets"

        print("#Lost Packets ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("lost_packets=\d+", "\d+")

        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
                if source==target:
                    continue
                stats_input[source-1][target-1] = int( (stats_input[source-1][target-1] + .5) )

        return stats_input


    def retransmits(self):
        "Greps count of retransmitted packets"

        print("#Retransmits ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("retransmitted_packets=\d+", "\d+")

        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
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
    
