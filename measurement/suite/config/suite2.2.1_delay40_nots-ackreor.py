#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):
                                      #reorder_mode,  var    , reorder    , ackreor,    rdelay   , delay, ackloss, limit, bottleneckbw
        # 3.1 Constant Reordering Rate without Congestion
        for delay in [5,10,20,30,40,50,60,70,80,90,100]:
            yield self.run_measurement("reordering" , "delay", 0          , 2          , delay   , delay , 0    , 1000 , 100)

if __name__ == "__main__":
    Measurement().main()
