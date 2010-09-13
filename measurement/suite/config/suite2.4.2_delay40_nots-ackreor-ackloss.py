#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):
                                       #reorder_mode,  var    , reorder    , ackreor,   rdelay    , delay, ackloss, limit, bottleneckbw
        # 4.1 Constant Reordering Delay without Congestion
        for rdelay in [10,20,30,40,50,60,70,80,90,100,110,120,130,140,160,180,200]:
            #self.later_args_list = [[2, rdelay, None, None, None, "change"]]
            #self.later_args_time = 1
            yield self.run_measurement("reordering" , "rdelay",    0       , 2      ,   rdelay,    self.delay,  5      , 140 ,    20)

if __name__ == "__main__":
    Measurement().main()
