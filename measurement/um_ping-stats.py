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


class PingStats(Analysis):

    def __init__(self):
        "Constructor of the object"

        Analysis.__init__(self)

        # initialization of the option parser
        usage = "usage: %prog [options] [HOW] WHAT \n" \
                "where  HOW := { min | max | mean | median | deviation } \n" \
                "and    WHAT := { hops | packet_loss | RTT_avg | RTT_mdev }"

        self.parser.set_usage(usage)


    def set_option(self):
        "Options Setter"

        Analysis.set_option(self)

        if not self.action in ("hops", "packet_loss", "RTT_avg", "RTT_mdev"):
            self.parser.error("unknown WHAT %s" %(self.action))


    def hops(self):
        "Greps the number of hops"

        print("Hop Information ... \n")
        stats_input = self.get_stats("ttl=\d+", "\d+")
        
        #Array holds summed up values for every run and iteration. 
        #Average over all of them and get an Integer out of i
        for source in range(1, self.options.nodes+1):
            for target in range(1, self.options.nodes+1):
                if source==target:
                    continue
                if stats_input[source-1][target-1] > 0:
                    stats_input[source-1][target-1] = 65 - \
                        int( (stats_input[source-1][target-1] + .5) )
                else:
                    stats_input[source-1][target-1] = 0 

        return stats_input


    def packet_loss(self):
        "Greps the packet loss"

        print("Packet Loss Information ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("\d+%", "\d+")

        return stats_input


    def RTT_avg(self):
        "Greps the average RTT"

        print("Average RoundTripTime ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("/\d+\.\d+/\d+\.\d+/", "\d+\.\d+")

        return stats_input


    def RTT_mdev(self):
        "Greps the RTT mdev"

        print("RTT medium derivation ... \n")
        stats_input = zeros([self.options.nodes,self.options.nodes], float)
        stats_input = self.get_stats("/\d+\.\d+ ms", "\d+\.\d+")

        return stats_input


    def main(self):
        "Main method of the ping stats object"

        self.parse_option()
        self.set_option()
        Analysis.run(self)



if __name__ == '__main__':
    PingStats().main()
