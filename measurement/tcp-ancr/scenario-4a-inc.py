#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):
        self.gvars.opts["flowgrind_duration"] = 45

        rdelay = 20
        delayStart = 25
        delayLater = 100

        qlen = int((2 * delayLater * self.bnbw)/11.44)+1

        # reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw, mode
        self.later_args_list = [[2, 0, rdelay, delayLater, 0, None, None, "change"]]
        self.later_args_time = 13

        qlen = int((2 * delayStart * self.bnbw)/11.44)+1

        # reorder_mode, var, reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw
        yield self.run_measurement("both", "delay", 2,  0, rdelay, delayStart, 0, qlen, self.bnbw)

if __name__ == "__main__":
    Measurement().main()
