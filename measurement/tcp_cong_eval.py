#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

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
import textwrap
from logging import info, debug, warn, error
from twisted.internet import defer, reactor

# tcp-eval imports
from measurement import measurement, tests

class TcpEvaluationMeasurement(measurement.Measurement):
    """Measurement class to test four different congestion control algorithms:
    New Reno, Highspeed TCP, Westwood+ and Cubic"""

    def __init__(self):
        """Creates a new TcpEvaluationMeasurement object"""

        # create top-level parser
        description = textwrap.dedent("""\
                Creates successively four TCP flows with four different TCP
                congestion control algorithms: New Reno, SACK TCP, Westwood+
                and Cubic. On all TCP senders all congestion control algorithms
                must be available and be allowable to be set . Run 'sudo sysctl
                -a | grep congestion_control' to check.""")
        measurement.Measurement.__init__(self, description=description)
        self.parser.add_argument("pairfile", metavar="FILE", type=str,
                help="Set file to load node pairs from")

    def apply_options(self):
        """Configure object based on the options form the argparser"""

        measurement.Measurement.apply_options(self)

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        # common options used for all ntests
        opts = dict(fg_bin="~/bin/flowgrind", duration=10, dump=None)

        # test nodes load from file
        runs = self.load_pairs_from_file(self.args.pairfile)

        # repeat loop
        iterations  = range(1)

        # inner loop with different scenario settings
        scenarios   = [ dict(scenario_label="New Reno", cc="reno"),
                        dict(scenario_label="Westwood+", cc="westwood"),
                        dict(scenario_label="Highspeed TCP", cc="highspeed"),
                        dict(scenario_label="Cubic", cc="cubic")]

        #yield self.switchTestbedProfile("vmesh_flowgrind")

        for it in iterations:
            for run_no in range(len(runs)):
                kwargs = dict()

                kwargs.update(opts)
                kwargs.update(runs[run_no])

                for scenario_no in range(len(scenarios)):
                    # use a different port for every test
                    kwargs['bport'] = int("%u%u%02u" %(scenario_no + 1, it, run_no))

                    # set logging prefix, tests append _testname
                    self.logprefix="i%03u_s%u_r%u" % (it, scenario_no, run_no)

                    # merge parameter configuration for the tests
                    kwargs.update(scenarios[scenario_no])

                    # actually run tests
                    yield self.run_test(tests.test_flowgrind, **kwargs)

        # switch back to minimum when done
        # yield self.switchTestbedProfile("minimum")

        yield self.tear_down()
        reactor.stop()

    def main(self):
        self.parse_options()
        self.apply_options()
        self.run()
        reactor.run()

if __name__ == "__main__":
    TcpEvaluationMeasurement().main()

