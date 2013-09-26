#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):

        # Variate Bandwidth, reordering
        for bnbw in [1,2,5,10,20,30,40,50,60,70,80]:
            qlen = int((2 * self.delay * bnbw)/11.44)+1

            # reorder_mode, var, reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw
            yield self.run_measurement("both", "bnbw", 2, 0, self.delay, self.delay, 0, qlen, bnbw)

if __name__ == "__main__":
    Measurement().main()
