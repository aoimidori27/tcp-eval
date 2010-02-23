#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# python imports
from logging import info, debug, warn, error
from twisted.internet import defer, reactor

# umic-mesh imports
from um_measurement import measurement, tests
from um_node import Node

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

        self.parser.set_defaults(pairfile = "vmesh_dumbbell_flowgrind_measurement_pairs.lst")
        self.parser.add_option('-f', '--pairfile', metavar="PAIRFILE",
                               action = 'store', type = 'string', dest = 'pairfile',
                               help = 'Set file to load node pairs from [default: %default]')

    def set_option(self):
        """Set options"""
        measurement.Measurement.set_option(self)

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        # this must be adjusted for the specific measurement
        testbed_profile = "vmesh_flowgrind"
        node_type = "vmeshrouter"

        # common options used for all tests
        opts = dict( flowgrind_duration = 60,
                     flowgrind_dump   = False,
					 flowgrind_bin = "/home/wolff/svn/flowgrind/branches/flowgrind-wolff/src/flowgrind",
                     tprofile = testbed_profile,
                     nodetype = node_type )

        # test nodes load from file
        runs = self.load_pairs_from_file(self.options.pairfile)

        # repeat loop
        iterations  = range(2)

        # parallel or consecutive flows?
        parallel = True

        # inner loop with different scenario settings
        scenarios   = [ dict( scenario_label = "Linux Native", flowgrind_cc="reno", flowgrind_opts=["-O", "s=TCP_REORDER_MODULE=native"] ),
                        dict( scenario_label = "TCP-NCR CF",   flowgrind_cc="reno", flowgrind_opts=["-O", "s=TCP_REORDER_MODULE=ncr",  "-O", "s=TCP_REORDER_MODE=1"] ),
                        dict( scenario_label = "TCP-NCR AG",   flowgrind_cc="reno", flowgrind_opts=["-O", "s=TCP_REORDER_MODULE=ncr",  "-O", "s=TCP_REORDER_MODE=2"] ),
                        dict( scenario_label = "TCP-aNCR CF",  flowgrind_cc="reno", flowgrind_opts=["-O", "s=TCP_REORDER_MODULE=ancr", "-O", "s=TCP_REORDER_MODE=1"] ),
                        dict( scenario_label = "TCP-aNCR AG",  flowgrind_cc="reno", flowgrind_opts=["-O", "s=TCP_REORDER_MODULE=ancr", "-O", "s=TCP_REORDER_MODE=2"] ) ]

        yield self.switchTestbedProfile(testbed_profile)

        for it in iterations:
            tasks = list()
            for scenario_no in range(len(scenarios)):
                for run_no in range(len(runs)):
                    kwargs = dict()

                    kwargs.update(opts)
                    kwargs.update(runs[run_no])

                    kwargs['flowgrind_src'] = kwargs['src']
                    kwargs['flowgrind_dst'] = kwargs['dst']

                    # use a different port for every test

                    kwargs['flowgrind_bport'] = int("%u%u%02u" %(scenario_no+1,it, run_no))

                    # set logging prefix, tests append _testname
                    self.logprefix="i%03u_s%u_r%u" % (it, scenario_no, run_no)

                    # merge parameter configuration for the tests
                    kwargs.update(scenarios[scenario_no])

                    # set source and dest for tests
                    # actually run tests
                    if parallel:
                        tasks.append(self.run_test(tests.test_flowgrind, **kwargs))
                    else:
                        yield self.run_test(tests.test_flowgrind, **kwargs)
                if parallel:
                    yield defer.DeferredList(tasks)

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
