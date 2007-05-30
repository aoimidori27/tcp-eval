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


class PingTest(Measurement):
    "Class for ping measurements"


    def __init__(self):
        "Constructor of the object"

        Measurement.__init__(self)

        # initialization of the option parser
        self.parser.set_defaults(packet_size = 82, count = 4, interval = 1.2)

        self.parser.add_option("-p" , "--psize", metavar = "byte", type = int,
                               action = "store", dest = "packet_size",
                               help = "set size of ping packets [default: %default]")
        self.parser.add_option("-c" , "--counts", metavar = "#", type = int,
                               action = "store", dest = "count",
                               help = "set number of ping packets [default: %default]")
        self.parser.add_option("-i" , "--interval", metavar = "SEC", type = float,
                               action = "store", dest = "interval",
                               help = "set (fraction of) number of seconds between "\
                                      "pings [default: %default]")


    def set_option(self):
        "Set options"

        Measurement.set_option(self)


    def test_ping(self, iteration, run, source, target):
        "Run the ping measurement"

        targetnode = Node(hostname = target)
        targetip = targetnode.ipaddress(self.options.device)

        rc = self.remote_execute (source, "ping -s %i -c %i -i %s %s"
                           % (self.options.packet_size, self.options.count,
                              self.options.interval, targetip),
                           self.options.count * self.options.interval + 4)
        if (rc != 0):
            error("ping invocation on %s failed: rc=%i" % (source, rc))
            return False
        else:
            return True


    def main(self):
        "Main method of the ping test object"

        self.parse_option()
        self.set_option()
        Measurement.run(self)



if __name__ == "__main__":
    PingTest().main()
