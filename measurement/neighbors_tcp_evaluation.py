#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import sys
from logging import info, debug, warn, error
from twisted.internet import defer, reactor

# umic-mesh imports
from um_measurement import measurement, tests
from um_node import Node

class TcpEvaluationMeasurement(measurement.Measurement):
    """This Measurement has serveral scenarios to test:
       one flow from each to each node with 3 different congestion
       control algorithms: New Reno, Vegas and Westwood+
    """

    def __init__(self):
        """Constructor of the object"""
        self.logprefix=""
        measurement.Measurement.__init__(self)

        self.parser.set_defaults(pairfile = "pairs.lst")
        self.parser.add_option('-f', '--pairfile', metavar="PAIRFILE",
                               action = 'store', type = 'string', dest = 'pairfile',
                               help = 'Set file to load node pairs from [default: %default]')

    def set_option(self):
        """Set options"""
        measurement.Measurement.set_option(self)

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        testbed_profile = "tcp_evaluation"

        # common options used for all tests
        opts = dict( flowgrind_duration = 20,
                     flowgrind_dump   = True,
                     tprofile = testbed_profile )

        # test nodes load from file
        runs = self.load_pairs_from_file(self.options.pairfile)

        # repeat loop
        iterations  = range(50)

        # inner loop with different scenario settings
        scenarios   = [ dict( scenario_label = "New Reno 1", flowgrind_cc="reno" ),
                        dict( scenario_label = "Westwood+",  flowgrind_cc="westwood" ),
                        dict( scenario_label = "Vegas",      flowgrind_cc="vegas"),
                        dict( scenario_label = "New Reno 2", flowgrind_cc="reno") ]

        yield self.switchTestbedProfile(testbed_profile)

        # due to a flaw in flowgrindd restart it before measurement
        yield self.xmlrpc_many(range(1,46),"flowgrindd.restart")

        for it in iterations:
            for run_no in range(len(runs)):
                kwargs = dict()

                kwargs.update(opts)
                kwargs.update(runs[run_no])

                kwargs['flowgrind_src'] = kwargs['src']
                kwargs['flowgrind_dst'] = kwargs['dst']

                for scenario_no in range(len(scenarios)):
                    # use a different port for every test
                    kwargs['flowgrind_bport'] = int("%u%u%02u" %(scenario_no+1,it, run_no))


                    # set logging prefix, tests append _testname
                    self.logprefix="i%03u_s%u_r%u" % (it, scenario_no, run_no)

                    # merge parameter configuration for the tests
                    kwargs.update(scenarios[scenario_no])

                    # set source and dest for tests
                    # actually run tests
                    yield self.run_test(tests.test_flowgrind, **kwargs)

        # switch back to minimum when done
        yield self.switchTestbedProfile("minimum")
        yield self.tear_down()
        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()

if __name__ == "__main__":
    TcpEvaluationMeasurement().main()

