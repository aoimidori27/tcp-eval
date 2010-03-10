#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
from logging import info, warn, debug
from twisted.internet import defer, reactor

#umic-mesh imports
from um_twisted_functions import twisted_sleep
from um_measurement import measurement, tests
from um_node import Node

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
                     flowgrind_opts = "-n 2 -F 1 -H s=ath0.mrouter17/mrouter17,d=ath0.mrouter9/mrouter9 -T b=200 -Y b=300".split() )

        # meshrouters to test (1-10)
        all = map(lambda x: "mrouter%s" %x, [8,9,14,15,16,17])

        # inner loop configurations
        runs = [ dict( run_label = r"16\\sra8", src=16, dst=8 )]

        # repeat loop
        iterations  = range(1,20)

        # outer loop with different scenario settings
        scenarios   = [ dict( scenario_label = "Flowgrind Example Measurement") ]

        # configure testbed
        yield self.switchTestbedProfile("flowgrind_test_globecom")

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

        yield self.switchTestbedProfile("minimum")

        yield self.tear_down()
        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()


if __name__ == "__main__":
    TcpMeasurement().main()

