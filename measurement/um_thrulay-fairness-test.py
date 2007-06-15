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


class ThrulayTest(Measurement):
    "Class for thrulay measurements"


    def __init__(self):
        "Constructor of the object"

        Measurement.__init__(self)


    def set_option(self):
        "Set options"

        Measurement.set_option(self)


    def test_elcn(self, iteration, run, source, target):
        "Run the thrulay measurement"

        targetnode = Node(hostname = target)
        targetip = targetnode.ipaddress(self.options.device)

        route_rc = self.ssh_node(source, "ip route list %s" % targetip, 3, False)

	length = 10;
        measurement_rc = self.ssh_node(source, "thrulay -t 5 -m 8 -H %s/%s -F 1,2,3,4 -e" % (length, target, targetip), length + 5, False)

        if (measurement_rc != 0):
            error("thrulay invocation %s  failed: rc=%i" % (source, measurement_rc))
            return False

        return True


    def test_noelcn(self, iteration, run, source, target):
        "Run the thrulay measurement"

        targetnode = Node(hostname = target)
        targetip = targetnode.ipaddress(self.options.device)

        route_rc = self.ssh_node(source, "ip route list %s" % targetip, 3, False)

	length = 10;
        measurement_rc = self.ssh_node(source, "thrulay -t 5 -m 8 -H %s/%s" % (length, target, targetip), length + 5, False)

        if (measurement_rc != 0):
            error("thrulay invocation %s  failed: rc=%i" % (source, measurement_rc))
            return False

        return True


    def main(self):
        "Main method of the thrulay test object"

        self.parse_option()
        self.set_option()
        Measurement.run(self)



if __name__ == "__main__":
    thrulayTest().main()
