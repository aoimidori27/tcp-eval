#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

# Copyright (C) 2007 - 2011 Arnd Hannemann <arnd@arndnet.de>
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
from logging import info, warn, debug
from twisted.internet import defer, reactor

# tcp-eval imports
from network.functions import twisted_sleep
from measurement import measurement, tests

class TcpMeasurement(measurement.Measurement):
    """This Measurement script resembles measurement for flowgrind globecom paper"""

    def __init__(self):
        """Constructor of the object"""
        self.logprefix=""
        measurement.Measurement.__init__(self)

    def set_option(self):
        """Set options"""
        measurement.Measurement.set_option(self)

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        # common options used for all tests
        opts = dict( flowgrind_cc = "reno",
                     flowgrind_duration = 900,
                     # flowgrind_opts = "-n 2 -T b=200 -Y b=300 -F 1 -D b=0x04".split(), moved to scenarios
                     nodetype = "vmeshrouter" )

        # vmeshrouters to test (601-608)
        all = map(lambda x: "vmrouter%s" %x, [601,602,603,604,605,606,607,608])

        # inner loop configurations
        runs = [ dict( run_label = r"601\\sra608", src=601, dst=608 )]

        # repeat loop
        iterations  = range(1,10)

        # outer loop with different scenario settings
        scenarios   = [ dict(   scenario_label = "Single Flow", 
                                flowgrind_opts = "-n 1 -T b=200 -Y b=300".split()) ,
                        dict(   scenario_label = "Two flows, default and secondary",
                                flowgrind_opts = "-n 2 -T b=200 -Y b=300 -F 1 -D b=0x04".split()),
                        dict(   scenario_label = "Two flows, default and tertiary",
                                flowgrind_opts = "-n 2 -T b=200 -Y b=300 -F 1 -D b=0x08".split()),
                        dict(   scenario_label = "Three flows",
                                flowgrind_opts = "-n 3 -T b=200 -Y b=300 -F 1 -D b=0x04 -F 2 -D b=0x08".split())
                      ]

        # configure testbed
#        yield self.switchTestbedProfile("flowgrind_test_globecom")

        # wait a few minutes to let olsr converge
        yield twisted_sleep(3)

        # make sure there are no flows active
        yield self.remote_execute_many(all,"flowgrind-stop")

        for scenario_no, scenario in enumerate(scenarios):
            kwargs = dict()
            kwargs.update(scenario)
            for it in iterations:
                for run_no in range(len(runs)):
                    # set logging prefix, tests append _testname
                    self.logprefix="i%03u_s%u_r%u" % (it, scenario_no, run_no)

                    # merge parameter configuration for the tests
                    kwargs.update(runs[run_no])
                    kwargs.update(opts)

                    # set source and dest for tests
                    kwargs['flowgrind_src'] = kwargs['src']
                    kwargs['flowgrind_dst'] = kwargs['dst']

                    # actually run tests
                    yield self.run_test(tests.test_flowgrind, **kwargs)

#        yield self.switchTestbedProfile("minimum")

        yield self.tear_down()
        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()


if __name__ == "__main__":
    TcpMeasurement().main()

