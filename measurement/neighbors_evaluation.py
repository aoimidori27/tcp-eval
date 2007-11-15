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
                     ping_interval    = 0.07,
                     ping_count       = 200,
                    )

        # test nodes 1-45
        testnodes = range(1,46)

        runs = self.generate_pair_permutations(testnodes)

        # repeat loop
        iterations  = range(3)

        # inner loop with different scenario settings
        scenario   =  dict( scenario_label = "Neighbor", tprofile = "minimum"  )

        yield self.switchTestbedProfile(scenario["tprofile"])

        for it in iterations:
            for run_no in range(len(runs)):
                kwargs = dict()
                kwargs.update(opts)
                kwargs.update(runs[run_no])
                kwargs['ping_src'] = kwargs['src']
                kwargs['ping_dst'] = kwargs['dst']

                kwargs.update(scenario)

                self.logprefix="i%03u_s%u_r%u" % (it, 0, run_no)
                yield self.run_test(tests.test_fping, **kwargs)

        yield self.tear_down()
        reactor.stop()



if __name__ == "__main__":
    instance = NeighborsEvaluationMeasurement()
    instance.parse_option()
    instance.set_option()
    instance.run()
    reactor.run()
