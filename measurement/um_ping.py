#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports 
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_measurement import *


class Ping(Measurement):
    "Class for ping measurements"
    
    
    def __init__(self):
        "Constructor of the object"
       
        Measurement.__init__(self)

        # initialization of the option parser
        self.parser.set_defaults(packet_size = 82, count = 4, interval = 1.2)

        self.parser.add_option("-p" , "--packet-size", metavar = "bytes", type = int, 
                               action = "store", dest = "packet_size", 
                               help = "Set size of ping packets [default: %default]")
        self.parser.add_option("-c" , "--counts", metavar = "#", type = int,
                               action = "store", dest = "count", 
                               help = "Set number of ping packets [default: %default]")
        self.parser.add_option("-i" , "--interval", metavar = "secs", type = float,
                               action = "store", dest = "interval", 
                               help = "Set (fraction of) number of seconds between "\
                                      "pings [default: %default]")


    def set_option(self):
        "Set options"
        
        Measurement.set_option(self)


    def test(self, iteration, run, source, target):
        "Run the ping measurement"

        targetip = getwlanip(target, self.options.device)
    
        rc = self.ssh_node(source, "ping -s %i -c %i -i %i %s"
                           % (self.options.packet_size, self.options.count,
                              self.options.interval, targetip),
                           self.options.count * self.options.interval + 4)
        if (rc != 0):
            error("ping invocation on %s failed: rc=%i" % (source, rc))
            return False
        else:
            return True


    def main(self):
        "Main method of the ping object"

        self.parse_option()
        self.set_option()
        Measurement.run(self)



if __name__ == "__main__":
    Ping().main()
