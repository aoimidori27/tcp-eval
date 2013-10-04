#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# python imports
from logging import info, debug, warn, error
from twisted.internet import defer, reactor
import os
import sys
import time

# umic-mesh imports
from um_measurement import measurement, tests
from um_functions import call
from measurement_class import MeasurementClass
from um_application import Application


class DumbbellEvaluationMeasurement(MeasurementClass):
    """This Measurement will run tests of several scenarios:
       - Each scenario is defined by it's flowgrind options.
       - One test of a scenario consists of parallel runs (flows)
         between all pairs defined in the pairs file.
       - One measurement-iteration will run one test of each scenario.
       - The number of iterations is determined by the "iterations" variable.
    """

    def set_option(self):
        """Set options"""
        Application.set_option(self)

        if (self.options.offset == 0):
            error("Please give an offset!")
            sys.exit(1)

    @defer.inlineCallbacks
    def run(self):
        """Main method"""

        delay  = 20
        rate   = 20
        qlen   = int((2*delay*rate)/11.44)+1

        rrate  = 2
        rdelay = 20

        ackreor = 0
        ackloss = 0

        #initial settings for netem
        yield self.run_netem(0, 0, 0, 0, 0, 1000, 100, "add")
        yield self.run_netem(rrate,ackreor, rdelay, delay, ackloss, qlen,  rate, "change")
                         #reorder, ackreor, rdelay, delay, ackloss, limit, bottleneckbw

        reactor.stop()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()
        reactor.run()


if __name__ == "__main__":
    DumbbellEvaluationMeasurement().main()
