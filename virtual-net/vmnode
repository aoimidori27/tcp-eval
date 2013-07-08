#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2007 Lars Noschinski <lars.noschinski@rwth-aachen.de>
# Copyright (C) 2009 - 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# python imports
import os
import sys
import argparse
import textwrap
import tempfile
import xmlrpclib
import socket
import MySQLdb
from logging import info, debug, warn, error

# tcp-eval imports
from application import Application
from functions import requireroot, call, execute, CommandFailed

class VMNode(Application):
    """Class to start virtual nodes on the basis of Xen"""

    def __init__(self):
        """Creates a new VMNode object"""

        # database and xend connection
        self.dbconn = None
        self.xenconn = None

        # other object variables
        self.__vm_ids = None

        # create top-level parser and subparser
        description = textwrap.dedent("""\
                This program can create/shutdown/destroy an arbitrary number of
                XEN VMs (domUs) either locally or on a remote XEN host (dom0).
                Further, it can list all current running VMs in a network
                together with their respected owner (requires a MySQL
                database connection).""")
        Application.__init__(self, description=description)
        database_group = self.parser.add_mutually_exclusive_group()
        database_group.add_argument("-d", "--database", action="store",
                metavar=("HOST", "DB", "USER", "PASSWD"), nargs=4,
                help="establish database connection to store domU ownerships")
        database_group.add_argument("-n", "--no-database", action="store_true",
                default=True, help="do action without database connection "\
                        "(default: %(default)s)")
        subparsers = self.parser.add_subparsers(title="subcommands",
                dest="action", help="additional help")

        # shared parser for "create/shutdown/destroy" command
        shared_parser = argparse.ArgumentParser(add_help=False)
        shared_parser.add_argument("vm_ids", metavar="id", type=int, nargs="+",
                help="execute command for domU with ID '%(metavar)s'. The ID "\
                        "will be used as a network-wide unique domU identifier")
        shared_parser.add_argument("-s", "--host", metavar="HOST", nargs=1,
                action="store", default="localhost", help="execute command "\
                        "on dom0 '%(metavar)s' (default: %(default)s)")
        shared_parser.add_argument("-p", "--prefix", metavar="PRE", nargs=1,
                action="store", default="vmnode", help="use '%(metavar)s' as "\
                        "prefix for domU's hostname (default: %(default)s). "\
                        "As suffix the domU ID will be used")
        shared_parser.add_argument("-r", "--range", action="store_true",
                default=False, help="interprete the given domU IDs as an 'ID "\
                        "range' from 'id1' to 'id2' (default: %(default)s)")

        # create parser for "create" command
        parser_create = subparsers.add_parser("create",
                parents=[shared_parser], help="create multiple XEN domUs "\
                        "simultaneously")
        parser_create.add_argument("-o", "--root", metavar="PATH", nargs=1,
                action="store", default="~/root", help = "root file system "\
                        "for domU (default: %(default)s)")
        parser_create.add_argument("-k", "--kernel", metavar="FILE", nargs=1,
                action="store",  default = "~/vmlinuz", help = "kernel for "\
                        "domU (default: %(default)s)")
        parser_create.add_argument("-i", "--initrd", metavar="FILE", nargs=1,
                action="store", default="~/initrd.img", help="initial "\
                        "ramdisk for domU (default: %(default)s)")
        parser_create.add_argument("-m", "--memory", metavar="#", nargs=1,
                action="store", type=int, default=128, help="amount of RAM "\
                        "in MB to allocate to domU (default: %(default)s)")
        create_group = parser_create.add_mutually_exclusive_group()
        create_group.add_argument("-c", "--console", action="store_true",
                default=False, help="attaches to domU console (xm -c)")
        create_group.add_argument("-y","--dry-run", action="store_true",
                default=False, help="do not start domUs automatically; "\
                        "create start file (XEN config file) only")

        # create parser for "shutdown" command
        parser_shutdown = subparsers.add_parser("shutdown",
                parents=[shared_parser], help="shutdown multiple XEN domUs "\
                        "simultaneously")

        # create parser for "destroy" command
        parser_destroy = subparsers.add_parser("destroy",
                parents=[shared_parser], help="destroy multiple XEN domUs "\
                        "simultaneously")

        # create parser for "list" command
        parser_list = subparsers.add_parser("list", help="list XEN domOs/domUs")
        parser_list.add_argument("-s", "--host", metavar="HOST", nargs="+",
                action="store", default="localhost", help="dom0s on which "\
                        "command will be executed (default: %(default)s)")
        parser_list.add_argument("--domUs", action="store_true",
                dest="show_domUs", default=True, help="show information "\
                        "about domUs (default: %(default)s)")
        parser_list.add_argument("--dom0s", action="store_false",
                dest="show_dom0s", default=False, help="show information "\
                        "about domOs")

    def apply_options(self):
        """Configure XEN object based on the options form the argparser.
        On the given options perform some sanity checks"""

        # for all commands
        Application.apply_options(self)

        # for all commands except "list"
        if not self.args.action == "list":
            # VM IDs are never negative
            for vm_id in self.args.vm_ids:
                if vm_id < 0:
                    error("A domU ID must be greater than zero")
                    sys.exit(1)

            # if desired build a range of domU IDs
            if self.args.range:
                # can only generate a range if exact two IDs are given
                if not len(self.args.vm_ids) == 2:
                    error("Can only generate an 'ID range' if exact two domU "\
                            "IDs are given")
                    sys.exit(1)
                else:
                    self.__vm_ids = range(self.args.vm_ids[0],
                            self.args.vm_ids[1] + 1)
            # for convinced copy domU IDs
            else:
                self.__vm_ids = self.args.vm_ids

        # for command "create" only
        if self.args.action == "create":
            # cannot attach console if we start multiple VMs
            if self.args.console and self.args.do_create > 1:
                warn("Starting more than VMs with attached console is almost "\
                        "certainly not what you want. Console option is "\
                        "deactivated")
                self.args.console = False

    def db_connect(self, host, db, user, passwd, abort_on_failure=True):
        """Establish MySQL database connection to store domU ownerships"""

        try:
            self.dbconn = MySQLdb.connect(host=host, db=db, user=user,
                    passwd=passwd)
            self.dbconn.autocommit(True)
        except Exception, exception:
            error_msg = "Could not connect to database"
            if abort_on_failure:
                error("%s: %s. Exit" %(error_msg, exception))
                sys.exit(1)
            else:
                warn("%s: %s. Continue" %(error_msg, exception))

    def db_insert(self, vm_hostname):
        """Insert domU with their respected owner into the database"""

        if os.environ.has_key("SUDO_USER"):
            user = os.environ["SUDO_USER"]
        else:
            user = os.environ["USER"]

        cursor = self.dbconn.cursor()
        query = "INSERT INTO nodes_vmesh (nodeID,created_by) "\
                "SELECT nodeID,'%s' FROM nodes WHERE nodes.name='%s' "\
                "ON DUPLICATE KEY UPDATE created_by='%s';"\
                        %(user, vm_hostname, user)
        cursor.execute(query)

    def db_delete(self, vm_hostname):
        """Delete domU from the database"""

        cursor = self.dbconn.cursor()
        query = "DELETE FROM nodes WHERE name='%s';" %(vm_hostname)
        cursor.execute(query)

    def xen_connect(self, host, abort_on_failure=True):
        """Establish connection to xen daemon"""

        try:
            self.xenconn = xmlrpclib.Server('http://%s:8006/' %(host))
        except socket.error, exception:
            error_msg = "Could not connect to XEN daemon"
            if abort_on_failure:
                error("%s: %s. Exit" %(error_msg, exception))
                sys.exit(1)
            else:
                warn("%s: %s. Continue..." %(error_msg, exception))

    def xen_getDomains(self, a, b, abort_on_failure=True):
        """Return all hostet domains"""

        try:
            return self.xenconn.domains(a, b)
        except socket.error, exception:
            error_msg = "Could not retrieve XEN domains from the XEN daemon"
            if abort_on_failure:
                error("%s: %s. Exit" %(error_msg, exception))
                sys.exit(1)
            else:
                warn("%s: %s. Continue..." %(error_msg, exception))

    def create(self):
        """Start the desired number of domUs"""

        #FIXME
        if not self.args.host == "localhost":
            raise NotImplementedError

        # only a dry run require no root privileges
        if not self.args.dry_run:
            requireroot()

        # create desired domUs
        for index, vm_id in enumerate(self.__vm_ids):
            # build hostname
            vm_hostname = "%s%i" %(self.args.prefix, vm_id)

            # test if domU is already running
            try:
                cmd = ["ping", "-c1", vm_hostname]
                execute(cmd, shell=False)
                warn("%s seems to be already running." %(vm_hostname))
                continue
            except CommandFailed:
                pass

            # create XEN config file
            info("Creating config file for domU %s" %(vm_hostname))
            first_byte = vm_id / 256
            rest_2bytes = vm_id % 256
            xen_config = textwrap.dedent("""\
                    name    = '%s'
                    ramdisk = '%s'
                    kernel  = '%s'
                    memory  = %s
                    cpus    = '2-15'
                    root    = '/dev/ram0 console=hvc0'
                    vif     = ['mac=00:16:3E:00:%02x:%02x', 'bridge=br0']
                    extra   = 'id=default image=%s"""
                    %(vm_hostname, self.args.initrd, self.args.kernel,
                        self.args.memory, first_byte, rest_2bytes,
                        self.args.root))

            # dry run - only print config file and continue
            if self.args.dry_run:
                print xen_config
                if not index == len(self.__vm_ids) - 1:
                    print ""
                continue

            # write config into a file
            cfg_fd, cfg_file = tempfile.mkstemp(suffix = "-%s.cfg"
                    %(vm_hostname))
            f = open(cfg_fd, "w")
            f.write(xen_config)
            f.flush()

            # create XEN command
            if self.args.console:
                cmd = "xm create -c -f %s" %(cfg_file)
            else:
                cmd = "xm create -f %s" %(cfg_file)

            # start VM
            try:
                info("Starting %s" %(vm_hostname))
                call(cmd, shell=True)
            except CommandFailed, exception:
                error("Error while starting %s" %(vm_hostname))
                error(exception)

            # close and remove config file
            f.close()
            os.remove(cfg_file)

            # write user to the database
            if self.args.database:
                self.db_insert(vm_hostname)

    def shutdown(self):
        """Shutdown the desired number of domUs"""

        #FIXME
        if not self.args.host == "localhost":
            raise NotImplementedError

        # must be root
        requireroot()

        # shudown the desired number of VMs
        for vm_id in self.__vm_ids:

            # build hostname
            vm_hostname = "%s%i" %(self.args.prefix, vm_id)

            # create XEN command
            cmd = "xm shutdown %s" %(vm_hostname)

            # shutdown vm
            try:
                info("Shutting down %s" %(vm_hostname))
                call(cmd, shell=True)
            except CommandFailed, exception:
                error("Error while shutting down %s" %(vm_hostname))
                error(exception)

            # delete node entry from database
            if self.args.database:
                self.db_delete(vm_hostname)

    def destroy(self):
        """Destroy the desired number of domUs"""

        #FIXME
        if not self.args.host == "localhost":
            raise NotImplementedError

        # must be root
        requireroot()

        # destroy the desired number of VMs
        for vm_id in self.__vm_ids:

            # build hostname
            vm_hostname = "%s%i" %(self.args.prefix, vm_id)

            # create XEN command
            cmd = "xm destroy %s" %(vm_hostname)

            # shutdown vm
            try:
                info("Destroying down %s" %(vm_hostname))
                call(cmd, shell=True)
            except CommandFailed, exception:
                error("Error while destroying %s" %(vm_hostname))
                error(exception)

            # delete node entry from database
            if self.args.database:
                self.db_delete(vm_hostname)

    def list(self):
        """Show information about domOs/domUs"""

        # helper function
        def vmr_compare(x, y):
            # only compare numerical part, works for our purpose
            x_nr = int(filter(lambda c: c.isdigit(), x))
            y_nr = int(filter(lambda c: c.isdigit(), y))
            return cmp(x_nr, y_nr)

        # must be root
        #requireroot()

        # show information about all dom0s
        if self.args.show_dom0s:
            print "Host           #Nodes     Mem   VCPUs"
            print "-------------------------------------"

            info("Collecting stats...")
            for host in self.args.host:
                # connect to xen on 'host' and get domains
                self.xen_connect(host, False)
                domains = self.xen_getDomains(True, False, False)

                # in case of an error, skip this host
                if not domains: continue

                # print dom0 informations
                print "%s \t %s \t %s \t %s" %(host, len(domains) - 1, \
                        domains[0][11][1], domains[0][5][1])

        # show information about all domUs
        if self.args.show_domUs:
            vm_all = dict()

            info("Collecting stats...")
            for host in self.args.host:
                # connect to xen on 'host' and get domains
                self.xen_connect(host, False)
                domains = self.xen_getDomains(True, False, False)

                # in case of an error, skip this host
                if not domains: continue

                # extend list of all vmrouters by new ones
                for entry in domains:
                    d = dict()
                    # skip first elem in entry
                    for elem in entry[1:]:
                        (key, value) = elem
                        d[key] = value
                    # add server name to entry
                    d["host"] = host
                    # skip dom0
                    if d["domid"] == 0: continue
                    # initialize user field
                    d["user"] = "None"
                    # use domain name as key
                    key = d["name"]
                    vm_all[key] = d

            #sort by hostname
            sorted_keyset = vm_all.keys()
            sorted_keyset.sort(vmr_compare)

            # get domU ownerships:
            if self.args.database:
                nodeset = ",".join(map(lambda s: "'"+s+"'", sorted_keyset))
                if nodeset != "":
                    cursor = self.dbconn.cursor()
                    cursor.execute("SELECT nodes.name,created_by "\
                            "FROM nodes,nodes_vmesh "\
                            "WHERE nodes.nodeID=nodes_vmesh.nodeID "\
                                "AND nodes.name IN (%s)" %(nodeset))
                    for row in cursor.fetchall():
                        (key, value) = row
                        vm_all[key]["user"] = value

            # print domU informations
            print "Name          Host      User                 Mem State  Time"
            print "------------------------------------------------------------------------------------"
            for key in sorted_keyset:
                entry = vm_all[key]
                print "%s %s %s %3s %6s %s" %(entry["name"].ljust(13),\
                        entry["host"].ljust(9), entry["user"].ljust(20),\
                        entry["maxmem"], entry["state"], entry["cpu_time"])

    def run(self):
        # establish database connection
        if self.args.database:
            dbconn = self.args.database
            self.db_connect(host=dbconn[0], db=dbconn[1], user=dbconn[2],
                    passwd=dbconn[3])

        # run command (create,shutdown,destroy,list)
        eval("self.%s()" %(self.args.action))

    def main(self):
        self.parse_options()
        self.apply_options()
        self.run()

if __name__ == "__main__":
    VMNode().main()

