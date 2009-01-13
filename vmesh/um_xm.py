#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
import sys
import tempfile
from logging import info, debug, warn, error
from optparse import OptionValueError

# umic-mesh imports
from um_application import Application
from um_image import Image, ImageValidityException
from um_node import Node, VMeshHost, NodeValidityException
from um_functions import requireroot, call, execute, CommandFailed


class Xen(Application):
    """Class to start virtual nodes on the basis of Xen"""

    def __init__(self):
        """Creates a new Xen object"""

        Application.__init__(self)

        # object variables
        self._range = []

        # initialization of the option parser
        usage = "usage: %prog [options] ID | FROM TO \n" \
                "where ID, FROM, TO are node IDs (integers) greater than zero"
        self.parser.set_usage(usage)
        self.parser.set_defaults(console = False, dry_run = False,
                image_type = "vmeshnode", kernel = "default/vmeshnode-vmlinuz",
                memory = 50, node_type = "vmeshrouter",
                ramdisk = "vmeshnode-initrd", image_version = "default")

        self.parser.add_option("-c", "--console",
                action = "store_true", dest = "console",
                help = "attaches to domU console (xm -c)")
        self.parser.add_option("-d", "--dry-run",
                action = "store_true", dest = "dry_run",
                help = "do not start the domain automatically; create only the "\
                       "start file (XEN config file) for domain")
        self.parser.add_option("-I", "--image_type", metavar = "TYPE",
                action = "store", dest = "image_type", choices = Image.types(),
                help = "the image type for the domain [default: %default]")               
        self.parser.add_option("-k", "--kernel", metavar = "FILE",
                action = "store", dest = "kernel", type="string",
                help = "kernel image for the domain [default: %default]")            
        self.parser.add_option("-m", "--memory", metavar = "MEMORY",
                action = "store", dest = "memory", type = "int",
                help = "amount of RAM in MB to allocate to the "\
                       "domain when it starts [default: %default]")
        self.parser.add_option("-N", "--node_type", metavar = "TYPE",
                action = "store", dest = "node_type", choices = Node.vtypes(),
                help = "the node type for the domain [default: %default]")               
        self.parser.add_option("-r", "--ramdisk", metavar = "DISK",
                action = "store", dest = "ramdisk", type="string",
                help = "initial ramdisk for the domain [default: %default]")
        self.parser.add_option("-V", "--image_version", metavar = "VERSION",
                action = "store", dest = "image_version", type="string",
                help = 'the image version for the domain [default: %default]')


    def set_option(self):
        """Set the options for the Xen object"""

        Application.set_option(self)

        try:
            # check if imagetype fit to nodetype
            Node.isValidImage(self.options.image_type, self.options.node_type)
        
            # correct numbers of arguments?
            begin = int(self.args[0])
            
            if len(self.args) == 1:
                end = begin + 1
            elif len(self.args) == 2:     
                end = int(self.args[1]) + 1
            else:
                raise IndexError
            
            # Integers greater than zero?
            if begin > 0 and end > 0:
                self._range = range(begin, end)
            else:
                raise ValueError
            
            # everthing is OK, we can leave the method
            return
                  
        except NodeValidityException, exception:
            error("Invalid combination of node type and image type")
            error(exception)
        except IndexError:
            error("Incorrect number of arguments")
        except ValueError:
            error("Arguments are not integers greater than zero")
       
        # if we come to this point we got an exception and we want to terminate
        # the program
        sys.exit(1)


    def run(self):
        """Start the desired number of vmeshnodes"""

        # must be root
        requireroot()

        # gather information form localhost (e.g. hostname)
        vmeshhost = VMeshHost()

        # create an Image object
        try:
            image = Image(self.options.image_type, self.options.image_version)        
        
        except ImageValidityException, exception:
            error(exception)
            sys.exit(1)
        
        # some temp variables
        ramdisk = os.path.join(Image.initrdPrefix(), self.options.ramdisk)
        kernel = os.path.join(Image.kernelPrefix(), self.options.kernel)

        # create the desired number of vmeshnodes    
        for number in self._range:
        
            # create a vmeshnode object
            try:       
                vmeshnode = Node(number, self.options.node_type)        
            
            except ImageValidityException, exception:
                error(exception)
                sys.exit(1)             

            # Test if vmeshnode is already running
            try:
                cmd = ["ping", "-c1", vmeshnode.getHostname()]
                execute(cmd, shell = False)
                warn("%s seems to be already running." % vmeshnode.getHostname())
                continue
            
            except CommandFailed:
                pass

            # create XEN config file
            cfg_fd, cfg_file = tempfile.mkstemp(suffix = "-%s.cfg"
                                                % vmeshnode.getHostname())
            
            info("Creating Domain config file %s" % cfg_file)

            vmnode_number = vmeshhost.getNumber()
            first_byte = vmnode_number/256
            rest_2bytes = vmnode_number%256

            f = os.fdopen(cfg_fd, "w+b")            
            f.write("name = '%s' \n"\
                    "ramdisk = '%s' \n"\
                    "kernel = '%s' \n"\
                    "memory = %s \n"\
                    "root = '/dev/ram0 console=hvc0' \n"\
                    "vif = ['mac=00:16:3E:00:%02x:%02x', 'bridge=br0'] \n"\
                    "extra = 'id=default image=%s nodetype=%s hostname=%s "\
                             "init=/linuxrc'\n"
                    %(vmeshnode.getHostname(), ramdisk, kernel,
                      self.options.memory, first_byte, rest_2bytes, 
                      image.getImagePath(canonical_path = False),                     
                      vmeshnode.getType(), vmeshnode.getHostname()))
            f.flush()

            # if this is only a dry run, we do not have to start the XENs
            if self.options.dry_run:
                f.seek(0)
                print f.read()

            else:
                # create XEN command
                if self.options.console:
                    cmd = "xm create -c %s" % cfg_file
                else:
                    cmd = "xm create %s" % cfg_file
    
                # start vmeshnode
                try:                           
                    info("Starting %s" % vmeshnode.getHostname())
                    call(cmd, shell = True)
               
                except CommandFailed, exception:
                    error("Error while starting %s" % vmeshnode.getHostname())
                    error(exception)
    
    
            # close and remove config file
            f.close()
            os.remove(cfg_file)



if __name__ == "__main__":
    inst = Xen()
    inst.parse_option()
    inst.set_option()
    inst.run()
    
