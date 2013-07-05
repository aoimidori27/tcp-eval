#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
from twisted.internet import defer, reactor

#umic-mesh imports
from um_measurement import measurement, tests

class OlsrMeasurement(measurement.Measurement):
    """This Measurement script has serveral olsr configs to test"""

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
        opts = dict( ping_size        = 100,
                     ping_interval    = 0.2,
                     ping_count       = 30,
                     flowgrind_cc = "reno",
                     flowgrind_duration = 15 )

        # meshrouters to test (1-10)
        all = map(lambda x: "mrouter%s" %x, range(1,11))

        # inner loop configurations
        runs = []
        runs.extend(self.generate_pair_permutations(range(1,11)))

        # repeat loop
        iterations  = range(1,10)

        # outer loop with different scenario settings
        scenarios   = [ dict( scenario_label = "ETX", tprofile="OLSR evaluation ETX_FPM"),
                        dict( scenario_label = "ETT1", tprofile="OLSR evaluation TPUT_FPM") ]

        yield self.remote_execute_many(all, "iwconfig ath0")

        # BSSID merging still sucks, work around:
        yield self.remote_execute_many(all, 'sudo iw dev ath0 ibss leave')
        yield self.remote_execute_many(all, 'sudo iw ibss join "umic-mesh" 2412 E2:30:31:31:90:B3')

        for scenario_no, scenario in enumerate(scenarios):
            kwargs = dict()
            kwargs.update(scenario)
            yield self.switchTestbedProfile(scenario["tprofile"])
            for it in iterations:
                for run_no in range(len(runs)):
                    # set logging prefix, tests append _testname
                    self.logprefix="i%03u_s%u_r%u" % (it, scenario_no, run_no)

                    # merge parameter configuration for the tests
                    kwargs.update(runs[run_no])
                    kwargs.update(opts)

                    # set source and dest for tests
                    kwargs['flowgrind_src'] = kwargs['ping_src'] = kwargs['src']
                    kwargs['flowgrind_dst'] = kwargs['ping_dst'] = kwargs['dst']

                    # actually run tests
                    yield self.run_test(tests.test_fping, **kwargs)
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
    OlsrMeasurement().main()

