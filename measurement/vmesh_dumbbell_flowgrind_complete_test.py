#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# python imports
from logging import info, debug, warn, error
from twisted.internet import defer, reactor
import os
import sys

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

       - All of this can be repeated with changing dumbbell/netem parameters
         Edit the loops in the run function for that
    """

    def __init__(self):
        """Constructor of the object"""
        self.logprefix=""
        measurement.Measurement.__init__(self)

        self.parser.set_defaults(pairfile = "vmesh_dumbbell_flowgrind_measurement_pairs.lst")
        self.parser.add_option('-f', '--pairfile', metavar="PAIRFILE",
                               action = 'store', type = 'string', dest = 'pairfile',
                               help = 'Set file to load node pairs from [default: %default]')

    def set_option(self):
        """Set options"""
        measurement.Measurement.set_option(self)

    @defer.inlineCallbacks
    def run_netem(self, reorder, rdelay, delay, limit, mode):
        fdnode="vmrouter210"    # forward path delay
        frnode="vmrouter211"    # forward path reordering
        qlnode="vmrouter212"    # queue limit
        rrnode="vmrouter213"    # reverse path reordering
        rdnode="vmrouter214"    # reverse path delay

        info("Setting netem..")

        #forward path delay
        tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:2 handle 20: netem delay %ums %ums 20%%" %(mode, delay, (int)(delay * 0.1))
        rc = yield self.remote_execute(fdnode, tc_cmd, log_file=sys.stdout)

        #forward path reordering
        if reorder == 0:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:2 handle 10: netem reorder 0%%" %(mode)
        else:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:2 handle 10: netem reorder %u%% \
                      reorderdelay %ums %ums 20%%" %(mode, reorder, rdelay, (int)(rdelay * 0.1))
        rc = yield self.remote_execute(frnode, tc_cmd, log_file=sys.stdout)

        #queue limit
        tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:1 handle 10: netem limit %u; \
                  sudo tc qdisc %s dev eth0 parent 1:2 handle 20: netem limit %u" %(mode, limit, mode, limit)
        rc = yield self.remote_execute(qlnode, tc_cmd, log_file=sys.stdout)

        #bottleneck bandwidth
        tc_cmd = "sudo tc class %s dev eth0 parent 1: classid 1:1 htb rate %umbit; \
                  sudo tc class %s dev eth0 parent 1: classid 1:2 htb rate %umbit" %(mode, bottleneckbw, mode, bottleneckbw)
        rc = yield self.remote_execute(qlnode, tc_cmd, log_file=sys.stdout)

        #reverse path reordering
        if reorder == 0:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:1 handle 10: netem reorder 0%%" %(mode)
        else:
            tc_cmd = "sudo tc-enhanced-netem qdisc %s dev eth0 parent 1:1 handle 10: netem \
                      reorder %u%% reorderdelay %ums %ums 20%%" %(mode, reorder, rdelay, (int)(rdelay * 0.1))
        rc = yield self.remote_execute(rrnode, tc_cmd, log_file=sys.stdout)

        #reverse path delay
        tc_cmd = "sudo tc qdisc %s dev eth0 parent 1:1 handle 10: netem delay %ums %ums 20%%" %(mode, delay, (int)(delay * 0.1))
        rc = yield self.remote_execute(rdnode, tc_cmd, log_file=sys.stdout)

    @defer.inlineCallbacks
    def run_measurement(self, reorder_mode, var, reorder, rdelay, delay, limit, bottleneckbw):
        # this must be adjusted for the specific measurement
        node_type = "vmeshrouter"

        # common options used for all tests
        opts = dict( flowgrind_duration = 10,
                     flowgrind_dump   = False,
					 flowgrind_bin = "flowgrind",
                     tprofile = self.testbed_profile,
                     nodetype = node_type )

        # test nodes load from file
        #runs = self.load_pairs_from_file(self.options.pairfile)
        runs = [{'src': 201, 'dst': 208, 'run_label': '201\\\\sra208'}]

        # repeat loop
        iterations  = range(1)

        # parallel or consecutive flows?
        parallel    = True

        # inner loop with different scenario settings
        scenarios   = [ dict( scenario_label = "Linux Native", flowgrind_cc="reno" ) ]

        yield self.run_netem(reorder, rdelay, delay, limit, bottleneckbw, "change")

        for it in iterations:
            for scenario_no in range(len(scenarios)):
                tasks = list()
                logs = list()
                for run_no in range(len(runs)):
                    kwargs = dict()

                    kwargs.update(opts)
                    kwargs.update(runs[run_no])

                    kwargs['flowgrind_src'] = kwargs['src']
                    kwargs['flowgrind_dst'] = kwargs['dst']

                    # use a different port for every test

                    kwargs['flowgrind_bport'] = int("%u%u%02u" %(scenario_no+1,self.count, run_no))

                    # set logging prefix, tests append _testname
                    self.logprefix="i%03u_s%u_r%u" % (self.count, scenario_no, run_no)
                    logs.append(self.logprefix)

                    # merge parameter configuration for the tests
                    kwargs.update(scenarios[scenario_no])

                    # set source and dest for tests
                    # actually run tests
                    info("run test %s" %self.logprefix)
                    if parallel:
                        tasks.append(self.run_test(tests.test_flowgrind, **kwargs))
                    else:
                        yield self.run_test(tests.test_flowgrind, **kwargs)

                if parallel:
                    yield defer.DeferredList(tasks)

                # header for analyze script
                for prefix in logs:
                    logfile = open("%s/%s_test_flowgrind" %(self.options.log_dir, prefix), "r+")
                    old = logfile.read() # read everything in the file
                    logfile.seek(0) # rewind
                    logfile.write("""testbed_param_qlimit=%u\n""" \
                        """testbed_param_rdelay=%u\n"""           \
                        """testbed_param_rrate=%u\n"""            \
                        """testbed_param_reordering=%s\n"""       \
                        """testbed_param_variable=%s\n"""         \
                        """testbed_param_bottleneckbw=%u\n"""       %(limit, rdelay, reorder, reorder_mode, var, bottleneckbw))
                    logfile.write(old)
                    logfile.close()

            # count overall iterations
            self.count += 1

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        self.count = 0
        delay = 50
        #self.testbed_profile = "profilename!"
        #yield self.switchTestbedProfile(self.testbed_profile)

        #initial settings for netem
        yield self.run_netem(0, 0, 0, 1000, 100, "add")

                                      #reorder_mode, var     , reorder    , rdelay    , delay, limit     , bottleneckbw
        for qlimit in range(15):
            yield self.run_measurement("congestion", "qlimit", 0          , 0         , delay, qlimit + 1, 100)

        for reorder in range(26):
            yield self.run_measurement("reordering", "rrate" , 2 * reorder, 30        , delay, 1000      , 100)

        for rdelay in range(16):
            yield self.run_measurement("reordering", "rdelay", 5          , 5 * rdelay, delay, 1000      , 100)

        for qlimit in range(15):
            yield self.run_measurement("both"      , "qlimit", 5          , 30        , delay, qlimit + 1, 100)

        for reorder in range(26):
            yield self.run_measurement("both"      , "rrate" , 2 * reorder, 30        , delay, 10        , 100)

        for rdelay in range(16):
            yield self.run_measurement("both"      , "rdelay", 5          , 5 * rdelay, delay, 10        , 100)

        # example using bottleneckbw to cause congestion
        for bnbw in range(10):
            yield self.run_measurement("congestion" , "bnbw" , 0          , 0         , delay, 10        , 6 * (bnbw + 1))


        # switch back to minimum when done
        # yield self.switchTestbedProfile("minimum")
        yield self.tear_down()
        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()

if __name__ == "__main__":
    DumbbellEvaluationMeasurement().main()
