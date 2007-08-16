#!/usr/bin/env python
# -*- coding: utf-8 -*-

from um_measurement2 import measurement, tests

class PingTest(measurement.Measurement2App):
    "Class for ping measurements"

    def __init__(self):
        "Constructor of the object"

        measurement.Measurement2App.__init__(self)

        # initialization of the option parser
        self.parser.set_defaults(packet_size = 82, count = 4, interval = 1.2)

        self.parser.add_option("-p" , "--psize", metavar = "byte", type = int,
                               action = "store", dest = "packet_size",
                               help = "set size of ping packets [default: %default]")
        self.parser.add_option("-c" , "--counts", metavar = "#", type = int,
                               action = "store", dest = "count",
                               help = "set number of ping packets [default: %default]")
        self.parser.add_option("-I" , "--interval", metavar = "SEC", type = float,
                               action = "store", dest = "interval",
                               help = "set (fraction of) number of seconds between "\
                                      "pings [default: %default]")


    def set_option(self):
        "Set options"

        measurement.Measurement2App.set_option(self)


    def main(self):
        "Main method of the ping test object"

        self.parse_option()
        self.set_option()

        command = lambda src, dst: "ping -s %i -c %i -i %s %s" % \
            (self.options.packet_size, self.options.count,
                    self.options.interval, dst)

        self.add_test(tests.SSHTestFactory(command, name="ping",
            timeout = self.options.count * self.options.interval + 4))

        self.run()


if __name__ == "__main__":
    PingTest().main()

