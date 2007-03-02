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

class Nuttcp(Measurement):
    "Class for nuttcp measurements"


    def __init__(self):
        "Constructor of the object"

        Measurement.__init__(self)

        # object variables
        self._reverse = ''

        # initialization of the option parser
        self.parser.set_defaults(length = 10, reverse = False,
                                 start_server = False)

        self.parser.add_option("-l" , "--length", metavar = "SEC", type = int,
                               action = "store", dest = "length",
                               help = "Set length of nuttcp test [default: %default]")
        self.parser.add_option("-r" , "--reverse",
                               action = "store_true", dest = "reverse",
                               help = "Receive from server instead to transmit "\
                                      "to [default: %default]")
        self.parser.add_option("-y" , "--start-server",
                               action = "store_true", dest = "start_server",
                               help = "Start nuttcp on target router [default: %default]")


    def set_option(self):
        "Set options"

        Measurement.set_option(self)

        # being reverse?
        if self.options.reverse:
            self._reverse = "-r"


    def test(self, iteration, run, source, target):
        "Run the nuttcp measurement"

        # if desired start the nuttcp server here
        if self.options.start_server:
            rc = self.ssh_node(target, "pidof nuttcp", 3, True)
            if (rc == 0):
                warn("%s already runs nuttcp server albeit --start-server." % (target))

            rc = self.ssh_node(target, "nuttcp -1 </dev/null 2>&0 1>&0", 3)
            if (rc != 0):
                error("%s failed to start nuttcp server. rc=%d" % (target, rc))
                return False

        # we might accidently hit a non server mode nuttcp here.
        rc = self.ssh_node(target, "pidof nuttcp", 3, True)
        if (rc != 0):
            error("%s is not running a nuttcp server. pidof rc=%d" % (target, rc))
            return False

        targetnode = Node(hostname = target)
        targetip = targetnode.ipaddress(self.options.device)

        rc = self.ssh_node(source, "nuttcp -T  %i %s -v -fparse %s"
                           % (self.options.length, self.reverse, targetip),
                           self.options.length + 5, False)

        if (rc != 0):
            error("nuttcp invocation %s  failed: rc=%i" % (source, rc))
            return False
        else:
            return True


    def main(self):
        "Main method of the nuttcp object"

        self.parse_option()
        self.set_option()
        Measurement.run(self)



if __name__ == "__main__":
    Nuttcp().main()
