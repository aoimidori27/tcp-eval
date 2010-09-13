#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

from measurement_class import MeasurementClass
from twisted.internet import defer

class Measurement(MeasurementClass):
    @defer.inlineCallbacks
    def run(self):
                                       #reorder_mode,  var    , reorder    , ackreor,   rdelay    , self.delay, ackloss, limit, bottleneckbw
        for reorder in [0,1,2,3,5,7,10,15,20,25,30,35,40]:
            yield self.run_measurement("both" , "rrate" , reorder    , 0          , self.delay   , self.delay , 0     , 140 , 20)

if __name__ == "__main__":
    Measurement().main()
