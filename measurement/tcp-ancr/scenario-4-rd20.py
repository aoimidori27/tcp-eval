#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):

        # Variate RTT, congestion
        for delay in [10,15,20,25,30,35,40,45,50]:
            qlen = int((2 * delay * self.bnbw)/11.44)+1

            # reorder_mode, var, reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw
            yield self.run_measurement("both", "delay", 2, 0, 20, delay, 0, qlen, self.bnbw)

if __name__ == "__main__":
    Measurement().main()
