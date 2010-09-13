#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):
                                       #reorder_mode,  var    , reorder    , ackreor,   rdelay    , delay, ackloss, limit, bottleneckbw
        # 1.1 Constant Bandwidth without Reordering
        for bnbw in [1,2,5,10,20,30,40,50,60,70,80]: #100Mbit keine gute idee.. quasi local congestion
            yield self.run_measurement("congestion" , "bnbw"  ,    0       , 0         , 0       , self.delay , 0     , 7*bnbw, bnbw)

if __name__ == "__main__":
    Measurement().main()
