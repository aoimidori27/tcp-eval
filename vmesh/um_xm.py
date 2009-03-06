#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
import sys
import tempfile
import xmlrpclib
import socket
import MySQLdb
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


        self.action = ''
        self.commands = ('list', 'create')

        self.dbhost = 'webserver'
        self.db = 'umic-mesh'   
        self.dbuser = 'um_xm'
        self.dbpass = 'eSWEuB7LeEss6sjF'
    
        # object variables
        self._range = []
        self.serverlist = ['vmhost1', 'vmhost2', 'vmhost11']

        # initialization of the option parser
        usage = "usage: \t%prog [options] list \n" \
                "\t%prog [options] create ID | FROM TO \n" \
                "\twhere ID, FROM, TO are node IDs (integers) greater than zero"
        self.parser.set_usage(usage)
        self.parser.set_defaults(console = False, dry_run = False,
                image_type = "vmeshnode", kernel = "default/vmeshnode-vmlinuz",
                memory = 50, node_type = "vmeshrouter", hostinfo = False,
                ramdisk = "vmeshnode-initrd", image_version = "default", force = False)

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
        self.parser.add_option("-H", "--host-info", metavar = "HOSTINFO",
                action = "store_true", dest = "hostinfo",
                help = 'WITH LIST: show information about Domain-0 of each host')
        self.parser.add_option("-f", "--force",
                action = "store_true", dest = "force",
                help = "do action, even if the database can't be reached")


    def db_connect(self):
        self.dbconn = None
        try:
            self.dbconn = MySQLdb.connect(host = self.dbhost, 
                                          db = self.db,
                                          user = self.dbuser,
                                          passwd = self.dbpass)
            self.dbconn.autocommit(True)
                                          
        except Exception, e:
            error("Could not connect to database: %s" %e)
            if not self.options.force:
                error("Use -f if you want to continue anyways")
                sys.exit(1)
                


    def set_options_create(self):
        try:
            # check if imagetype fit to nodetype
            Node.isValidImage(self.options.image_type, self.options.node_type)
        
            # correct numbers of arguments?
            begin = int(self.args[1])
            
            if len(self.args) == 2:
                end = begin + 1
            elif len(self.args) == 3:     
                end = int(self.args[2]) + 1
            else:
                raise IndexError
            
            # no vmnode-numbers greater than 4000
            if end > 4001:
                error("No numbers greater than 4000")
                sys.exit()

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

    def set_options_list(self):
        groups = os.getgroups()
        allowed = 0
        for i in [0, 2000, 2009, 2010]:  # root, um-admin, vmeshhost-admin, vmeshhost-user
            if i in groups:
                return

    def set_option(self):
        """Set the options for the Xen object"""

        Application.set_option(self)

        # correct numbers of arguments?
        if (len(self.args) == 0) or (len(self.args) > 3): 
            self.parser.error("Incorrect number of arguments")

        # set arguments
        self.action = self.args[0]

        # does the command exists?
        if not self.action in self.commands:
            self.parser.error('Unkown COMMAND %s' %(self.action))

        # additional option checking for create
        if self.action == 'create':
            self.set_options_create()
        # additional option checking for list
        if self.action == 'list':
            self.set_options_list()

    def run_create(self):
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

            vmnode_number = vmeshnode.getNumber()
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
       
            # write user to the databse
            if self.dbconn:
                if os.environ.has_key("SUDO_USER"):
                    user = os.environ["SUDO_USER"]
                else: 
                    user = os.environ["USER"]
                cursor = self.dbconn.cursor()
                query = "INSERT IGNORE INTO nodes SET "\
                        "name='%s',nodetype='vmeshrouter',hardware='XEN',nr=%u,"\
                        "room='',box='',comment='';" %(vmeshnode.getHostname(),vmeshnode.getNumber())
                cursor.execute(query)
                query = "INSERT INTO nodes_vmesh (nodeID,created_by) "\
                        "SELECT nodeID,'%s' FROM nodes WHERE nodes.name='%s' "\
                        "ON DUPLICATE KEY UPDATE created_by='%s';" %(user,vmeshnode.getHostname(),user)
                cursor.execute(query)
    def run_list(self):
       
        def vmr_compare(x, y):
            # only compare numerical part, works for our purpose
            x_nr = int(filter(lambda c: c.isdigit(), x))
            y_nr = int(filter(lambda c: c.isdigit(), y))
            return cmp(x_nr, y_nr)                  

        if self.options.hostinfo:
            info("Collecting stats ..")
            #print headline
            print "Host           #Nodes     Mem   VCPUs"
            print "-------------------------------------"
            for server in self.serverlist:
                # connect to server
                session = xmlrpclib.Server('http://%s:8006/' %server)
                try:
                    vm = session.xend.domains(True,False)
                except socket.error, err:
                    error("Server %s: %s" %(server, err))
                    continue

                # number of vmrouter running on this host
                nr_router = len(vm)-1

                # print infos
                print "%s \t %s \t %s \t %s" %(server, nr_router, vm[0][11][1], vm[0][5][1])

        else:
            info("Collecting stats ..")

            vm_all = dict() 
            for server in self.serverlist:
                # connect to server
                session = xmlrpclib.Server('http://%s:8006/' %server)
                try:
                    vm = session.xend.domains(True,False)
                except socket.error, err:
                    error("Server %s: %s" %(server, err))
                    continue
    
                # extend list of all vmrouters by new ones
                for entry in vm: 
                    d = dict()
                    # skip first elem in entry
                    for elem in entry[1:]:
                        (key, value) = elem
                        d[key] = value
                    # add server name to entry
                    d["server"] = server
                    # skip dom0
                    if d["domid"] == 0:
                        continue
                    # initialize user field
                    d["user"] = "None"
                    # use domain name as key
                    key = d["name"]
                    vm_all[key] = d
    
            #sort by vmrouter name
            sorted_keyset = vm_all.keys()
            sorted_keyset.sort(vmr_compare)

            # get vmrouter reservationss: 
            if self.dbconn:
                nodeset = ",".join(map(lambda s: "'"+s+"'", sorted_keyset))
                cursor = self.dbconn.cursor()
                cursor.execute("SELECT nodes.name,created_by FROM nodes,nodes_vmesh WHERE nodes.nodeID=nodes_vmesh.nodeID AND nodes.name IN (%s)" %nodeset)
                for row in cursor.fetchall():
                    (key, value) = row
                    vm_all[key]['user'] = value

            # print infos
            print "Name          Host      User                 Mem State  Time"
            print "------------------------------------------------------------------------------------"    
            for key in sorted_keyset:
                  entry = vm_all[key]
                  print "%s %s %s %3s %6s %s" \
                        %(entry["name"].ljust(13), entry["server"].ljust(9), entry["user"].ljust(20), entry["maxmem"], entry["state"], entry["cpu_time"])

    def run(self):
        self.db_connect()
        if self.action == 'create':
            self.run_create()
        if self.action == 'list':
            self.run_list()


if __name__ == "__main__":
    inst = Xen()
    inst.parse_option()
    inst.set_option()
    inst.run()
    
