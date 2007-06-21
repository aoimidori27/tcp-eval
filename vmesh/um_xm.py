#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_config import *
from um_util import *


class Init(Application):
    "Class to start vmrouters."


    def __init__(self):
        "Constructor of the object"

        Application.__init__(self)

        # Object variables
        self.range = ''

        # initialization of the option parser
        usage = "usage: %prog [OPTIONS] FROM TO"
        self.parser.set_usage(usage)
        self.parser.set_defaults(
                ramdisk = None,
                kernel = None,
                memory = None,
                console = False)

        self.parser.add_option("-k", "--kernel", metavar = "KERNEL",
                action = "store", dest = "kernel",
                help = "Kernel to use instead of the default one.")
        self.parser.add_option("-m", "--memory", metavar = "MEMORY",
                action = "store", dest = "memory", type = "int",
                help = "Amount of memory to allocate to the domain (in megabytes).")
        self.parser.add_option("-r", "--ramdisk", metavar = "RAMDISK",
                action = "store", dest = "ramdisk",
                help = "Initial ramdisk to use instead of the default one.")
        self.parser.add_option("-c", "--config", metavar = "CONFIG",
                action = "store", dest = "config",
                help = "Configuration from um_config.py's xenconfig.")
        self.parser.add_option("-C", "--console",
                action = "store_true", dest = "console",
                help = "Attaches to dom-U console (xm -c)")


    def set_option(self):
        "Set options"

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) == 0:
            self.parser.error("incorrect number of arguments")
        elif len(self.args) == 1:
            self.range = range(int(self.args[0]), int(self.args[0])+1)
        else:
            self.range = range(int(self.args[0]), int(self.args[1])+1)


    def append(self, list, item):
        tmp = list[:]
        tmp.append(item)
        return tmp


    def start_xen(self):
        cmd = ['sudo', 'xm', 'create', '/etc/xen/guests/vmeshrouter']

        # These options are optional ...
        if self.options.kernel != None:
            cmd.append('kernel=%s' % self.options.kernel)
        if self.options.memory != None:
            cmd.append('memory=%s' % self.options.memory)
        if self.options.ramdisk != None:
            cmd.append('ramdisk=%s' % self.options.ramdisk)
        if self.options.config != None:
            cmd.append('config=%s' % self.options.config)
        if self.options.console:
            cmd.append('-c')

        for number in self.range:
            # Test if the hostname vmrouter%s was already requested by someone else
            try:
                execute(["ping", "-c1", "vmrouter%s" % number], shell=False, raiseError=True)
                warn("vmrouter%s seems to be already running." % number)
                continue
            except CommandFailed:
                pass

            # Try to start vmrouter%s
            try:
                info("starting vmrouter%s" % number)
                call(self.append(cmd, 'vmid=%s' % number), shell=False, raiseError=True)
            except CommandFailed, inst:
                error("Error while starting vmrouter%s" % number)
                error(inst)

        print ("Done.")


    def main(self):
        "Main method of the Init object"

        self.parse_option()
        self.set_option()
        self.start_xen()



if __name__ == "__main__":
    Init().main()
