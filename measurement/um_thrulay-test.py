#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_measurement import *
from um_config import *
from um_functions import *
from um_node import *


class thrulayTest(Measurement):
    "Class for thrulay measurements"


    def __init__(self):
        "Constructor of the object"

        Measurement.__init__(self)

        # initialization of the option parser
        self.parser.set_defaults(length = 10)

        self.parser.add_option("-l" , "--length", metavar = "SEC", type = int,
                               action = "store", dest = "length",
                               help = "Set length of thrulay test [default: %default]")

    def set_option(self):
        "Set options"

        Measurement.set_option(self)


    def test_throughput(self, iteration, run, source, target):
        "Run the thrulay measurement"

        targetnode = Node(hostname = target)
        targetip = targetnode.ipaddress(self.options.device)

        route_rc = self.remote_execute(source, "ip route list %s" % targetip, 3, False)

        measurement_rc = self.remote_execute(source, "thrulay -t %i -H %s/%s" % (self.options.length, targetip, target), self.options.length + 5, False)

        if (measurement_rc != 0):
            error("thrulay invocation %s  failed: rc=%i" % (source, measurement_rc))


        if (measurement_rc != 0):
            return False
        else:
            return True


    def main(self):
        "Main method of the thrulay test object"

        self.parse_option()
        self.set_option()
        Measurement.run(self)



if __name__ == "__main__":
    thrulayTest().main()
