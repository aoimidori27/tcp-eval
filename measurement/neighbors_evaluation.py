#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import sys

from twisted.internet import defer, reactor

from um_measurement import measurement, tests
from um_node import Node


class NeighborsEvaluationMeasurement(measurement.Measurement):
    """
        This Measurement tests connectivity via ping.:
    """


    def __init__(self):
        """Constructor of the object"""    
        self.logprefix=""
        measurement.Measurement.__init__(self)

    def set_option(self):
        """Set options"""
        measurement.Measurement.set_option(self)
        
                                  
    @defer.inlineCallbacks
    def run(self):
        "Main method"

        # common options used for all tests
        opts = dict( ping_size        = 100,
                     ping_interval    = 0.2,
                     ping_count       = 30
                    )

        # test nodes 30-39
        runs = self.generate_pair_permutations(range(1,40))

        # repeat loop
        iterations  = range(1,10)

        # inner loop with different scenario settings
        scenarios   = [ dict( scenario_label = "Neighbor", tprofile = "minimum"  )
                        ]

        yield self.switchTestbedProfile("minimum")

        for it in iterations:
            for run_no in range(len(runs)):
                kwargs = dict()
                kwargs.update(opts)
                kwargs.update(runs[run_no])
                kwargs['ping_src'] = kwargs['src']
                kwargs['ping_dst'] = kwargs['dst']

                for scenario_no in range(len(scenarios)):
                    kwargs.update(scenarios[scenario_no])

                    self.logprefix="i%03u_s%u_r%u" % (it, scenario_no, run_no)
                    yield self.run_test(tests.test_ping, **kwargs)

        yield self.tear_down()
        reactor.stop()



if __name__ == "__main__":
    instance = NeighborsEvaluationMeasurement()
    instance.parse_option()
    instance.set_option()
    instance.run()
    reactor.run()
