#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):

        # App limit 20 Mbit/s
        for scenario in self.gvars.scenarios:
            scenario['flowgrind_opts'].extend(['-R', 's=20M'])

        # Variate RRate, no congestion
        for reorder in [0,1,2,3,5,7,10,15,20,25,30,35,40]:
            yield self.run_measurement("reordering", "rrate", reorder, 0, self.delay, self.delay, 0, 1000, 100)

if __name__ == "__main__":
    Measurement().main()
