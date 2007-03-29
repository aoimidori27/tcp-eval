#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import re
import socket

# umic-mesh imports
from um_application import Application
from um_functions import *
from um_node import Node, NodeTypeException

class Buildmesh(Application):
    """ Setup GRE tunnels and iptables rules to simulate a mesh network with vmeshrouters.

     This script has to be executed on each vmeshrouter, which shall be part of the simulated network.
    """

    def __init__(self):

        Application.__init__(self)

        self.node = None

        self.config = None

        usage = """usage: %prog [options] [CONFIGFILE]

CONFIGFILE syntax: A line looks like the following:
    host1: host2 host3 host5-host6

host1 reaches all hosts listed after the colon, every host listed after the
colon reaches host1. Empty lines and lines starting with # are ignored.
"""

        self.parser.set_usage(usage)

    def parse_config(self, file):
        """ returns an hash which maps
                host number -> set of reachable host numbers

            Config file syntax: Each line either begins with a # (comment)
            or has a form like:

                host1: host2 host3 host5-host6

            Where host* are numbers.

                host1: host2

            means, that host1 reaches host2 and vice versa.

                host1: host2 host3

            is equivalent to

                host1: host2
                host1: host3

            and

                host1: host2-host4

            is equivalent to

                host1: host2, host3, host4

            Note that the reachability relation defined by the config file is
            always symmetric.
        """

        # comment
        comment_re = re.compile('^\s*#')
        # line syntax:
        # LINE = HOST ":" REACHES
        # HOST = DIGITS
        # REACHES = DIGITS REACHES "|" DIGITS "-" DIGITS " " REACHES
        # additional spaces are allowed everywhere, except around the "-"
        line_re = re.compile(r"""
                ^([0-9]+)\ *:                   # HOST ":"
                \ *                             # optional spaces
                (
                    ([0-9]+(-[0-9]+)?           # DIGITS | DIGITS "-" DIGITS
                    \ *)                        # optional spaces
                +)$
                """, re.VERBOSE)
        split_re = re.compile(' +')
        range_re = re.compile('([0-9]+)-([0-9]+)')

        ## read (asymmetric) reachability information from the config file
        asym_map = {}
        for line in open(file, 'r'):

            # ignore comments
            if comment_re.match(line):
                continue

            # parse line, skip on syntax error
            lm = line_re.match(line)
            if not lm:
                warn("Syntax error in line %s. Skipping.")
                continue

            host = lm.group(1)
            reaches = set()
            for r in split_re.split(lm.group(2)):
                # expand ranges if necessary
                rm = range_re.match(r)
                if rm:
                    reaches.update(range(int(rm.group(1)), int(rm.group(2))+1))
                else:
                    reaches.add(int(r))

            asym_map[int(host)] = reaches

        ## Compute symmetric hull
        hosts = set(asym_map.keys()).union(reduce(lambda u,v: u.union(v), asym_map.values(), set()))
        reachability_map = dict(map(lambda x: (x, set()), hosts))
        for (host, reaches) in asym_map.iteritems():
            for r in reaches:
                reachability_map[host].add(r)
                reachability_map[r].add(host)

        return reachability_map

    def gre_ip(self, hostnum, mask=False):
        """ Gets the gre ip for host with number "hostnum" """

        if mask:
            return "192.168.0.%s/24" % hostnum # FIXME - do not hardcode this.
        else:
            return "192.168.0.%s" % hostnum

    def gre_net(self, mask = True):
        """ Gets the gre network address """

        if mask:
            return "192.168.0.0/24"
        else:
            return "192.168.0.0"


    def public_ip(self):
        """ Gets the local public ip """
        return socket.gethostbyname(gethostname))

    def setup_gre(self):
        hostnum = self.node.number()
        public_ip = self.public_ip()
        gre_ip = self.gre_ip(hostnum, mask=True)

        try:
            info("setting up GRE Broadcast tunnel for %s" % hostnum)
            execute('ip tunnel del wldev', True, False)
            execute('ip tunnel add wldev mode gre local %s remote 224.66.66.66 ttl 1 \
                     && ip addr add %s broadcast 255.255.255.255 dev wldev \
                     && ip link set wldev up' % (public_ip, gre_ip), True)
        except CommandFailed, inst:
            error("Setting up GRE tunnel %s (%s, %s) failed." % (hostnum, public_ip, gre_ip))
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))

    def setup_iptables(self):
        hostnum = self.node.number()
        peers = self.conf.get(hostnum, set())

        try:
            execute('iptables -D INPUT -j mesh_gre_in;'
                    'iptables -F mesh_gre_in;'
                    'iptables -X mesh_gre_in;'
                    'iptables -N mesh_gre_in', True)
        except CommandFailed, inst:
            error('Could not create iptables chain "mesh_gre_in"')
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            raise

        for p in peers:
            try:
                info("Add iptables entry: %s reaches %s" % (p, hostnum))
                execute('iptables -A mesh_gre_in -s %s -j ACCEPT' % self.gre_ip(p), True)
            except CommandFailed, inst:
                error('Adding iptables entry "%s reaches %s" failed.' % (p, hostnum))
                error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
                raise

        try:
            execute('iptables -A mesh_gre_in -s %s -j DROP &&'
                    'iptables -A INPUT -j mesh_gre_in' % self.gre_net(), True)
        except CommandFailed, inst:
            error("Inserting iptables chain into INPUT failed.")
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            raise

    def main(self):

        self.parse_option()
        self.set_option()

        if len(self.args) == 0:
            error("Config file must be given!")
            sys.exit(1)
            pass # FIXME error
        else:
            self.conf = self.parse_config(self.args[0])

        self.node = Node()
        if self.node.type() != 'vmeshrouter':
            raise NodeTypeException("Only vmeshrouters are supported")

        info("Setting up GRE tunnel ...")
        self.setup_gre()
        info("Setting up iptables rules ... ")
        self.setup_iptables()

if __name__ == "__main__":
    try:
        Buildmesh().main()
    except NodeTypeException, inst:
        error(inst)
    except CommandFailed:
        error("Applying mesh rules failed. For reason see above.")
