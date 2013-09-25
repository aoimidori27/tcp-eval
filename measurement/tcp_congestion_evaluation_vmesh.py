#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2007 Arnd Hannemann <arnd@arndnet.de>
# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# python imports
from logging import info, debug, warn, error
from twisted.internet import defer, reactor

# tcp-eval imports
from measurement import measurement, tests

class TcpEvaluationMeasurement(measurement.Measurement):
    """This Measurement has serveral scenarios to test:
       one flow from each to each node with 4 different congestion
       control algorithms: New Reno, Vegas, Westwood+ and Cubic
    """

    def __init__(self):
        """Constructor of the object"""
        self.logprefix=""
        measurement.Measurement.__init__(self)

        self.parser.set_defaults(pairfile = "tcp_congestion_evaluation_vmesh_pairs.lst")
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
        opts = dict( flowgrind_duration = 20,
                     flowgrind_dump   = False,
                     tprofile = testbed_profile,
                     nodetype = node_type )

        # test nodes load from file
        runs = self.load_pairs_from_file(self.options.pairfile)

        # repeat loop
        iterations  = range(50)

        # inner loop with different scenario settings
        scenarios   = [ dict( scenario_label = "New Reno", flowgrind_cc="reno" ),
                        dict( scenario_label = "Westwood+", flowgrind_cc="westwood" ),
                        dict( scenario_label = "Vegas", flowgrind_cc="vegas" ),
                        dict( scenario_label = "Cubic", flowgrind_cc="cubic" ) ]

        yield self.switchTestbedProfile(testbed_profile)

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
        # yield self.switchTestbedProfile("minimum")
        yield self.tear_down()
        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()

if __name__ == "__main__":
    TcpEvaluationMeasurement().main()

