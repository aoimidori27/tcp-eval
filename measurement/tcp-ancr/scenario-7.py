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

        # Variate RDelay, no congestion
        for rdelay in [5,10,15,20,25,30,35,40,45,50,60,70,80]:

            # reorder_mode, var, reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckb
            yield self.run_measurement("reordering", "rdelay", 2, 0, rdelay, self.delay, 0, 1000, 100)

if __name__ == "__main__":
    Measurement().main()
