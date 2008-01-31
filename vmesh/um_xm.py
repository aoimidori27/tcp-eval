#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
import tempfile
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_node import VMeshHost, VMeshRouter
from um_image import Image
from um_functions import requireroot, execute, CommandFailed


class Xen(Application):
    """Class to start vmrouters on the basis of Xen"""

    def __init__(self):
        """Creates a new Xen object"""

        Application.__init__(self)

        # object variables
        self.range = []

        # initialization of the option parser
        usage = "usage: %prog [options] ID | FROM TO \n" \
                "where ID, FROM, TO are node IDs (integers) greater than zero"
        self.parser.set_usage(usage)
        self.parser.set_defaults(kernel = "default/vmeshnode-vmlinuz",
                                 ramdisk = "vmeshnode-initrd",
                                 memory = 40, console = False)

        self.parser.add_option("-c", "--console",
                action = "store_true", dest = "console",
                help = "attaches to domU console (xm -c)")
        self.parser.add_option("-k", "--kernel", metavar = "KERNEL",
                action = "store", dest = "kernel", type="string",
                help = "kernel image for the domain [default: %default]")            
        self.parser.add_option("-m", "--memory", metavar = "MEMORY",
                action = "store", dest = "memory", type = "int",
                help = "amount of RAM, in megabytes, to allocate to the "\
                       "domain when it starts [default: %default]")
        self.parser.add_option("-r", "--ramdisk", metavar = "RAMDISK",
                action = "store", dest = "ramdisk", type="string",
                help = "initial ramdisk for the domain [default: %default]")


    def set_option(self):
        """Set the options for the Xen object"""

        Application.set_option(self)

        # correct numbers of arguments? Integers greater than zero?
        try:
            begin = int(self.args[0])
            
            if len(self.args) == 1:
                end = begin + 1
            elif len(self.args) == 2:     
                end = int(self.args[1]) + 1
            else:
                raise IndexError
            
            if begin > 0 and end > 0:
                self.range = range(begin, end)
            else:
                raise ValueError
        
        except IndexError:
            error("Incorrect number of arguments")                
        except ValueError:
            error("Arguments are not integers greater than zero")


    def run(self):
        """Start the desired number of vmrouters"""

        # must be root
        requireroot()

        # gather information form localhost (e.g. hostname)
        vmeshhost = VMeshHost()
        
        # some temp variables
        ramdisk = os.path.join(Image.getinitrdprefix(), self.options.ramdisk)
        kernel = os.path.join(Image.getkernelprefix(), self.options.kernel)

        # create the desired number of vmrouters    
        for number in self.range:
        
             # create a vmeshrouter object
            vmeshrouter = VMeshRouter(number)

            # Test if vmeshrouter is already running
            try:
                cmd = ["ping", "-c1", vmeshrouter.gethostname()]
                execute(cmd, shell = False)
                warn("%s seems to be already running." % vmeshrouter.gethostname())
                continue
            except CommandFailed:
                pass

            # create XEN config file
            fd, cfgfile = tempfile.mkstemp()
            os.write(fd,
                     "name = '%s' \n"\
                     "ramdisk = '%s' \n"\
                     "kernel = '%s' \n"\
                     "memory = %s \n"\
                     "root = '/dev/ram0' \n"\
                     "vif = ['mac=00:16:3E:00:%d:%d', 'bridge=br0'] \n"\
                     "extra = 'id=default image=vmeshnode.img/um_edgy " \
                     "nodetype=%s hostname=%s init=/linuxrc' \n"
                     %(vmeshrouter.gethostname(), ramdisk, kernel,
                       self.options.memory, vmeshhost.getnumber(),
                       vmeshrouter.getnumber(), vmeshrouter.gettype(),
                       vmeshrouter.gethostname()))

            # create XEN command
            if self.options.console:
                cmd = "xm create -c %s" % cfgfile
            else:
                cmd = "xm create %s" % cfgfile

            # start vmrouter
            try:
                info("Starting %s" % vmeshrouter.gethostname())
                execute(cmd, shell = True)
            except CommandFailed, exception:
                error("Error while starting vmrouter%s" % number)
                error(exception)

            # remove config file
            os.remove(cfgfile)



if __name__ == "__main__":
    inst = Xen()
    inst.parse_option()
    inst.set_option()
    inst.run()
    