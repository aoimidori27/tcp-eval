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

from global_vars import global_vars

class MeasurementClass(measurement.Measurement):
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
                                 offset=0)
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
        self.gvars = global_vars(self.options.offset)

    @defer.inlineCallbacks
    def run_netem(self, reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw, mode):
        fdnode="vmrouter%s" %(int(self.options.offset) + 10)    # forward path delay
        frnode="vmrouter%s" %(int(self.options.offset) + 11)    # forward path reordering
        qlnode="vmrouter%s" %(int(self.options.offset) + 12)    # queue limit
        rrnode="vmrouter%s" %(int(self.options.offset) + 13)    # reverse path reordering
        rdnode="vmrouter%s" %(int(self.options.offset) + 14)    # reverse path delay
        alnode="vmrouter%s" %(int(self.options.offset) + 15)     # ack loss

        info("Setting netem..")

        #forward path delay
        if not delay == None:
            tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:2 handle 20: netem delay %ums" %(mode, delay)
            rc = yield self.remote_execute(fdnode, tc_cmd)

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
        if not delay == None:
            tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:1 handle 10: netem delay %ums" %(mode, delay)
            rc = yield self.remote_execute(rdnode, tc_cmd, log_file=sys.stdout)

        #ack loss
        if ackloss == 0:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:5 handle 10: netem drop 0%%" %(mode)
        else:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:5 handle 10: netem drop %u%%" %(mode, ackloss)
        rc = yield self.remote_execute(alnode, tc_cmd, log_file=sys.stdout)

    def run_periodically(self, count = -1):
        """change netem settings every <later_args_time> seconds"""

        if len(self.later_args_list) == 0:
            return

        if count >= 0 and count < len(self.later_args_list):
            self.run_netem(*self.later_args_list[count])

        settings = [count+1]
        reactor.callLater(self.later_args_time, self.run_periodically, *settings)

    def run_iperf(self, bandwidth, duration):
        """start iperf udp flow in a new thread"""
        sender   = "vmrouter%s" %(int(self.options.offset) + 9)
        reveicer = "vmrouter%s" %(int(self.options.offset) + 15)
        param = [sender, 'iperf -c ath0.%s --udp -b %s -t %s' %(receiver, bandwidth, duration)]
        reactor.callLater(0, self.remote_execute, *param)

    @defer.inlineCallbacks
    def run_measurement(self, reorder_mode, var, reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw):
        for it in self.gvars.iterations:
            for scenario_no in range(len(self.gvars.scenarios)):
                tasks = list()
                logs = list()
                for run_no in range(len(self.gvars.runs)):
                    kwargs = dict()

                    kwargs.update(self.gvars.opts)
                    kwargs.update(self.gvars.runs[run_no])

                    kwargs['flowgrind_src'] = kwargs['src']
                    kwargs['flowgrind_dst'] = kwargs['dst']

                    # use a different port for every test

                    kwargs['flowgrind_bport'] = int("%u%u%02u" %(scenario_no+1,self.count, run_no))

                    # set logging prefix, tests append _testname
                    self.logprefix="i%03u_s%u_r%u" % (self.count, scenario_no, run_no)
                    logs.append(self.logprefix)

                    # merge parameter configuration for the tests
                    kwargs.update(self.gvars.scenarios[scenario_no])

                    # set source and dest for tests
                    # actually run tests
                    info("run test %s" %self.logprefix)
                    if self.gvars.parallel:
                        tasks.append(self.run_test(tests.test_flowgrind, **kwargs))
                    else:
                        yield self.run_netem(reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw, "change")
                        self.run_periodically()
                        #self.run_iperf(self.iperf_bandwidth, self.gvars.opts['flowgrind_duration'])

                        yield self.run_test(tests.test_flowgrind, **kwargs)

                if self.gvars.parallel:
                    yield self.run_netem(reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw, "change")
                    self.run_periodically()
                    #self.run_iperf(self.iperf_bandwidth, self.gvars.opts['flowgrind_duration'])

                    yield defer.DeferredList(tasks)

                # header for analyze script
                for prefix in logs:
                    logfile = open("%s/%s_test_flowgrind" %(self.options.log_dir, prefix), "r+")
                    old = logfile.read() # read everything in the file
                    logfile.seek(0) # rewind
                    logfile.write("""testbed_param_qlimit=%u\n""" \
                        """testbed_param_rdelay=%u\n"""           \
                        """testbed_param_rrate=%u\n"""            \
                        """testbed_param_delay=%u\n"""            \
                        """testbed_param_ackreor=%u\n"""          \
                        """testbed_param_ackloss=%u\n"""          \
                        """testbed_param_reordering=%s\n"""       \
                        """testbed_param_variable=%s\n"""         \
                        """testbed_param_bottleneckbw=%u\n"""       %(limit, rdelay, reorder, delay, ackreor, ackloss, reorder_mode, var, bottleneckbw))
                    logfile.write(old)
                    logfile.close()

                info("Sleeping ..")
                time.sleep(10)

            # count overall iterations
            self.count += 1

    @defer.inlineCallbacks
    def run(self):
        pass

    @defer.inlineCallbacks
    def run_all(self):
        """Main method"""

        self.count = 0
        self.delay = 40
        yield self.switchTestbedProfile(self.gvars.testbed_profile)

        #iperf settings
        #self.iperf_bandwidth = '1M'

        #initial settings for netem
        yield self.run_netem(0, 0, 0, 0, 0, 1000, 100, "add")

        yield self.run()

        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run_all()
        reactor.run()
