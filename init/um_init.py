#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_config import *
from um_functions import *
from um_node import *


class Init(Application):
    "Class to start UMIC-Mesh programms"


    def __init__(self):
        "Constructor of the object"

        Application.__init__(self)


    def set_option(self):
        "Set options"

        Application.set_option(self)


    def init(self):
        node     = Node()
        hostname = node.gethostname()
        nodetype = node.gettype()
        nodeinfo = node.getinfo() 

        info("Hostname:  %s" %(hostname))
        info("Nodetype:  %s" %(nodetype))

        for line in nodeinfo['startup']:
            try:
                eval(line)
            except Exception, inst:
                error("Error while executing %s" % line)
                error(inst)

            print ("Done.")


    def main(self):
        "Main method of the Init object"

        self.parse_option()
        self.set_option()
        self.init()



if __name__ == "__main__":
    Init().main()

