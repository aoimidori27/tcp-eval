#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# python imports
from logging import info, debug, warn, error
from twisted.internet import defer, reactor
import os
import sys
import time

# umic-mesh imports
from um_measurement import measurement, tests
from um_node import Node
from um_functions import call

class DumbbellEvaluationMeasurement(measurement.Measurement):
    """This Measurement will run tests of several scenarios:
       - Each scenario is defined by it's flowgrind options.
       - One test of a scenario consists of parallel runs (flows)
         between all pairs defined in the pairs file.
       - One measurement-iteration will run one test of each scenario.
       - The number of iterations is determined by the "iterations" variable.
    """

    def __init__(self):
        """Constructor of the object"""
        self.logprefix=""
        measurement.Measurement.__init__(self)

        self.parser.set_defaults(pairfile = "vmesh_dumbbell_flowgrind_measurement_pairs.lst",
                                 offset=None, log_dir="out")
        self.parser.add_option('-f', '--pairfile', metavar="PAIRFILE",
                               action = 'store', type = 'string', dest = 'pairfile',
                               help = 'Set file to load node pairs from [default: %default]')
        self.parser.add_option('-o', '--offset', metavar="OFFSET",
                               action = 'store', type = 'string', dest = 'offset',
                               help = 'Offset for routers [default: %default]')
        self.later_args_list = []

    def set_option(self):
        """Set options"""
        measurement.Measurement.set_option(self)

        if (self.options.offset == None):
            error("Please give an offset!")
            sys.exit(1)

    @defer.inlineCallbacks
    def run_netem(self, reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw, mode):
        fdnode="vmrouter%s" %(int(self.options.offset) + 9)    # forward path delay
        frnode="vmrouter%s" %(int(self.options.offset) + 11)    # forward path reordering
        qlnode="vmrouter%s" %(int(self.options.offset) + 12)    # queue limit
        rrnode="vmrouter%s" %(int(self.options.offset) + 13)    # reverse path reordering
        rdnode="vmrouter%s" %(int(self.options.offset) + 15)    # reverse path delay
        alnode="vmrouter%s" %(int(self.options.offset) + 14)     # ack loss

        info("Setting netem..")

        #forward path delay
        #if not delay == None:
        #    tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:5 handle 50: netem delay %ums %ums 20%%" %(mode, delay, (int)(delay * 0.1))
        #    rc = yield self.remote_execute(fdnode, tc_cmd)

        #forward path reordering
        if reorder == 0:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:2 handle 10: netem reorder 0%%" %(mode)
        else:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:2 handle 10: netem reorder %u%% \
                      reorderdelay %ums %ums 20%%" %(mode, reorder, rdelay, (int)(rdelay * 0.1))
        rc = yield self.remote_execute(frnode, tc_cmd, log_file=sys.stdout)

        #queue limit
        if not limit == None:
            tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:1 handle 10: netem limit %u; \
                      sudo tc qdisc %s dev eth0 parent 1:2 handle 20: netem limit %u" %(mode, limit, mode, limit)
            rc = yield self.remote_execute(qlnode, tc_cmd, log_file=sys.stdout)

        #bottleneck bandwidth
        if not bottleneckbw == None:
            tc_cmd = "sudo tc class %s dev eth0 parent 1: classid 1:1 htb rate %umbit; \
                      sudo tc class %s dev eth0 parent 1: classid 1:2 htb rate %umbit" %(mode, bottleneckbw, mode, bottleneckbw)
            rc = yield self.remote_execute(qlnode, tc_cmd, log_file=sys.stdout)

        #reverse path reordering
        if ackreor == 0:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:1 handle 10: netem reorder 0%%" %(mode)
        else:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:1 handle 10: netem reorder %u%% \
                      reorderdelay %ums %ums 20%%" %(mode, ackreor, rdelay, (int)(rdelay * 0.1))
        rc = yield self.remote_execute(rrnode, tc_cmd, log_file=sys.stdout)

        #reverse path delay
        #if not delay == None:
        #    tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:1 handle 50: netem delay %ums %ums 20%%" %(mode, delay, (int)(delay * 0.1))
        #    rc = yield self.remote_execute(rdnode, tc_cmd, log_file=sys.stdout)

        #ack loss
        if ackloss == 0:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:1 handle 10: netem drop 0%%" %(mode)
        else:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:1 handle 10: netem drop %u%%" %(mode, ackloss)
        rc = yield self.remote_execute(alnode, tc_cmd, log_file=sys.stdout)

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        delay  = 20
        rate   = 20
        qlen   = int((2*delay*rate)/11.44)+1
        rrate  = 0
        rdelay = delay

        #initial settings for netem
        yield self.run_netem(0, 0, 0, 0, 0, 1000, 100, "add")
        yield self.run_netem(rrate,   0  ,  rdelay, delay,    0,    qlen,    rate, "change")

                         #reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw
        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()

if __name__ == "__main__":
    DumbbellEvaluationMeasurement().main()
