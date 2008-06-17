#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# python imports
import re
import socket
import sys
import subprocess

# umic-mesh imports
from um_application import Application
from um_functions import *
from um_node import Node, NodeException


class BuildVmesh(Application):
    """
    Setup GRE tunnels and iptables rules to simulate a mesh network with
    vmeshrouters. This script has to be executed on each vmeshrouter, which
    shall be part of the simulated network.
    """

    def __init__(self):
        """Creates a new BuildVmesh object"""

        Application.__init__(self)

        # object variables
        self.node = None
        self.conf = None
        self.confstr = None
        self.linkinfo = dict()
        self.shapecmd = """\
tc class  add dev %(iface)s parent 1: classid 1:%(nr)d cbq rate %(rate)smbit allot 1500 prio 5 bounded isolated && \
tc filter add dev %(iface)s parent 1: protocol ip prio 16 u32 \
    match ip protocol 47 0xff flowid 1:%(nr)d \
    match ip dst %(dst)s"""

        
        # initialization of the option parser
        usage = "usage: %prog [options] [CONFIGFILE] \n" \
                "where the CONFIGFILE systax looks like the following \n" \
                "   1: 2 3 5-6 \n" \
                "   2: ... \n\n" \
                "vmrouter1 reaches all vmrouters listed after the colon, every \n "\
                "vmrouter listed after the colon reaches vmrouter1. Empty lines \n "\
                "and lines starting with # are ignored."
        self.parser.set_usage(usage)
        self.parser.set_defaults(remote = True, interface = "ath0",
                                 multicast = "224.66.66.66", offset = 0, staticroutes=False)

        self.parser.add_option("-r", "--remote",
                               action = "store_true", dest = "remote",
                               help = "Apply settings for all hosts in config")
        self.parser.add_option("-l", "--local",
                               action = "store_false", dest = "remote",
                               help = "Apply just the settings for the local host")
        self.parser.add_option("-i", "--interface",
                               action = "store", dest = "interface", metavar="IFACE",
                               help = "Interface to use for the GRE tunnel "\
                                      "(default: %default)")
        self.parser.add_option("-m", "--multicast",
                               action = "store", dest = "multicast", metavar="IP",
                               help = "Multicast IP to use for GRE tunnel "\
                                      "(default: %default)")
        self.parser.add_option("-o", "--offset",
                               action = "store", dest = "offset", metavar="OFFSET",
                               type = int,
                               help = "Add this offset to all hosts in the config "\
                                      "(default: %default)")
        self.parser.add_option("-s", "--staticroutes",
                               action = "store_true", dest = "staticroutes",
                               help = "Setup static routing according to topology"\
                                      "(default: %default)")
        self.parser.add_option("-R", "--rate",
                               action = "store", dest = "rate", metavar="RATE",
                               help = "Rate limit in mbps")



    def set_option(self):
        """Set the options for the BuildVmesh object"""

        Application.set_option(self)

        if len(self.args) == 0:
            error("Config file must be given!")
            sys.exit(1)
        else:
            self.conf = self.parse_config(self.args[0])


    def parse_config(self, file):
        """
        Returns an hash which maps host number -> set of reachable host numbers

        Config file syntax: Each line either begins with a # (comment)
        or has a form like

             host1: host2 host3 host5-host6

        where host* are numbers.

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

        # mach comments
        comment_re = re.compile('^\s*#')
        
        # line syntax:
        # LINE = HOST ":" REACHES
        # HOST = DIGITS
        # REACHES = DIGITS REACHES | DIGITS "-" DIGITS " " REACHES
        # additional spaces are allowed everywhere, except around the "-"
        line_str = r"""
                ^([0-9]+)\ *:                   # HOST ":"
                \ *                             # optional spaces
                ( ( %s )+ )                     # REACHES
                $"""
        reaches_str = r"""
                ([0-9]+)(?:-([0-9]+))?          # DIGITS | DIGITS "-" DIGITS
                (?:\[([0-9.]+)\])?               # [ "[" FLOAT "]" ]
                (?:\ +|$)                       # optional spaces
                """
        line_re    = re.compile(line_str % reaches_str, re.VERBOSE)
        reaches_re = re.compile(reaches_str, re.VERBOSE)
        # read (asymmetric) reachability information from the config file
        asym_map = {}
        if file == "-":
            fd = sys.stdin
        else:
            fd = open(file, 'r')

        self.confstr = list()
        for line in fd:
            self.confstr.append(line)
            
            # strip trailing spaces
            line = line.strip()

            # ignore comments
            if comment_re.match(line):
                continue

            # parse line, skip on syntax error
            lm = line_re.match(line)
            if not lm:
                warn("Syntax error in line %s. Skipping." %line)
                continue

            host = lm.group(1)
            reaches = set()
            for m in reaches_re.findall(lm.group(2)):
                first = int(m[0])
                if m[1]: last = int(m[1])
                else: last = first
                info = m[2]
                if last:
                    reaches.update(range(first, last+1))
                else:
                    reaches.add(first)

                if info:
                    if not self.linkinfo.has_key(int(host)):
                        self.linkinfo[int(host)] = dict()
                    for i in range(first, last+1):
                        self.linkinfo[int(host)][i] = info

            asym_map[int(host)] = reaches

        # Add offset
        asym_map2 = {}
        offset = self.options.offset
        for (host, reaches) in asym_map.iteritems():
            asym_map2[host+offset] = map(lambda x: x+offset, reaches)
        asym_map = asym_map2

        # Compute symmetric hull
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


    def setup_gre(self):
        hostnum = self.node.getNumber()
        public_ip = self.node.getIPaddress(device = None)
        gre_ip = self.gre_ip(hostnum, mask=True)

        try:
            iface = self.options.interface
            info("setting up GRE Broadcast tunnel for %s" % hostnum)
            execute('ip tunnel del %s' % iface, True, False)
            execute('ip tunnel add %(iface)s mode gre local %(public)s remote %(mcast)s ttl 1 \
                     && ip addr add %(gre)s broadcast 255.255.255.255 dev %(iface)s \
                     && ip link set %(iface)s up' %
                     {"public": public_ip, "gre": gre_ip, "iface": iface, "mcast": self.options.multicast},
                     True)
        except CommandFailed, inst:
            error("Setting up GRE tunnel %s (%s, %s) failed." % (hostnum, public_ip, gre_ip))
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))

    def setup_trafficcontrol(self):
        iface = "eth0"
        hostnum = self.node.getNumber()
        peers = self.conf.get(hostnum, set())
        prefix = self.node.getHostnamePrefix()

        # Add qdisc
        try:
            execute("tc qdisc del dev %s root &&" % iface +
                    "tc qdisc add dev %s root handle 1: cbq avpkt 1000 bandwidth 100mbit" % iface
                    ,True)
        except CommandFailed, inst:
            error('Couldnt install queuing discipline')
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            raise

        # Add class and filter for each peer
        i = 0
        for p in peers:
            try:
                if self.linkinfo.has_key(hostnum) and self.linkinfo[hostnum].has_key(p):
                    rate = self.linkinfo[hostnum][p]
                elif self.options.rate:
                    rate = self.options.rate
                else:
                    continue

                i+=1

                info("Limiting rate of link %s -> %s to %s mbit" % (hostnum,p,rate))

                execute(self.shapecmd % { 
                        'iface' : iface, 
                        'nr' : i, 
                        'dst' : socket.gethostbyname('%s%s' % (prefix,p)),
                        'rate' : rate}, 
                        True)

            except CommandFailed, inst:
                error('Failed to add tc classes and filters for link %s -> %s' % (hostnum, p))
                error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
                raise

    def setup_iptables(self):
        hostnum = self.node.getNumber()
        peers = self.conf.get(hostnum, set())
        prefix = self.node.getHostnamePrefix()
        mcast = self.options.multicast

        try:
            execute('iptables -D INPUT -j mesh_gre_in -d %s;' % mcast
                    + 'iptables -F mesh_gre_in;'
                    + 'iptables -X mesh_gre_in;'
                    + 'iptables -N mesh_gre_in', True)
        except CommandFailed, inst:
            error('Could not create iptables chain "mesh_gre_in"')
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            raise

        for p in peers:
            try:
                info("Add iptables entry: %s reaches %s" % (p, hostnum))
                execute('iptables -A mesh_gre_in -s %s%s -j ACCEPT' %(prefix,p), True)
            except CommandFailed, inst:
                error('Adding iptables entry "%s reaches %s" failed.' % (p, hostnum))
                error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
                raise

        try:
            execute('iptables -A mesh_gre_in -j DROP &&'
                    'iptables -A INPUT -d %s -j mesh_gre_in' % mcast, True)
        except CommandFailed, inst:
            error("Inserting iptables chain into INPUT failed.")
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            raise

    @staticmethod
    def find_shortest_path(graph, start, end, path=[]):
        path = path + [start]
        if start == end:
            return path
        if not graph.has_key(start):
            return None
        shortest = None
        for node in graph[start]:
            if node not in path:
                newpath = BuildVmesh.find_shortest_path(graph, node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    def set_sysctl(self, key, val):
        arg = "%s=%s" %(key,val)
        cmd = ["sysctl","-w",arg]
        try:
            execute(cmd, shell=False)
        except CommandFailed, inst:
            error('Failed sysctl %s failed.' %arg)
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            raise

    def setup_routing(self):
        iface   = self.options.interface            
        hostnum = self.node.getNumber()

        # disable send_redirects and accept redirects
        self.set_sysctl("net.ipv4.conf.all.send_redirects",0)
        self.set_sysctl("net.ipv4.conf.all.accept_redirects",0)
        self.set_sysctl("net.ipv4.conf.%s.send_redirects" %iface,0)
        self.set_sysctl("net.ipv4.conf.%s.accept_redirects" %iface,0)
        self.set_sysctl("net.ipv4.conf.%s.forwarding" %iface, 1)

        for host in self.conf.keys():
            if host==hostnum:
                continue        
            shortest = BuildVmesh.find_shortest_path(self.conf, hostnum, host)
            # not all hosts may be reachable from this hosts ignore them
            if not shortest:
                continue

            # calculate distance
            dist = len(shortest)-1

            # ignore direct neighbors for now as network mask should cover them
            if dist==1:
                continue
            
            debug(shortest)
            host_ip = self.gre_ip(host, mask=False)
            gw_ip   = self.gre_ip(shortest[1], mask=False)

            cmd = ["ip", "route", "replace", host_ip, "dev", iface, "via", gw_ip, "metric", str(dist)]
            try:
                execute(cmd, shell=False)
            except CommandFailed, inst:
                error('Adding routing entry for host %s failed.' % host_ip)
                error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
                raise

    def run(self):
        """Main method of the Buildmesh object"""

        # Apply settings on remote hosts
        if self.options.remote:
            for host in self.conf.keys():
                h = "vmrouter%s" % host
                info("Configuring host %s" % h)
                cmd = ["ssh", h, "sudo", "./um_vmesh", "-i",
                                        self.options.interface, "-l", "-"]
                if self.options.debug:
                    cmd.append("--debug")

                if self.options.staticroutes:
                    cmd.append("--staticroutes")
    
                if self.options.rate:
                    cmd.append("-R")
                    cmd.append(self.options.rate)

                proc =subprocess.Popen(cmd, stdin=subprocess.PIPE)
                rc = proc.communicate("".join(self.confstr))
                if proc.returncode != 0:
                    error("Configuring host %s FAILED (%s)" % (h, proc.returncode))
        
        # Apply settings on local host
        else:
            self.node = Node()

            info("Setting up GRE tunnel ...")
            self.setup_gre()
            
            info("Setting up iptables rules ... ")
            self.setup_iptables()

            info("Setting up traffic shaping ... ")
            self.setup_trafficcontrol()

            if self.options.staticroutes:
                info("Setting up static routing...")
                self.setup_routing()



if __name__ == "__main__":
    inst = BuildVmesh()
    inst.parse_option()
    inst.set_option()
    inst.run()
