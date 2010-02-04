#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# python imports
import re
import socket
import sys
import subprocess
import os
from logging import info, debug, warn, error, critical

# umic-mesh imports
from um_application import Application
from um_functions import *
from um_node import Node, NodeException

class BuildVmesh(Application):
    """Setup GRE tunnels and iptables rules to simulate a mesh network with
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
tc class  add dev %(iface)s parent 1: classid 1:%(nr)d htb rate %(rate)smbit && \
tc filter add dev %(iface)s parent 1: protocol ip prio 16 u32 \
    match ip protocol 47 0xff flowid 1:%(nr)d \
    match ip dst %(dst)s"""
        self._dnsttl = 300
        self._dnskey = "o2bpYQo1BCYLVGZiafJ4ig=="
        # used routing table ids for multipath
        self._rtoffset = 300   

        # initialization of the option parser
        usage = """\
usage:  prog [options] [CONFIGFILE]
        where the CONFIGFILE syntax looks like the following
            1: 2[10,,100] 3 5-6[0.74,20,,10]
            2: ...

Explanation:
    vmrouter1 reaches all vmrouters listed after the colon,
    every vmrouter listed after the colon reaches vmrouter1.

    Link information may be given in brackets after every
    entry, and the syntax [rate, limit, delay, loss], where:
        * Rate: in mbps as float
        * Queue limit: in packets as int
        * Delay: in ms as int
        * Loss: in percent as int

Remarks:
    The link information given for an entry are just
    a limit for ONE direction, so that it is possible to
    generate asynchronous lines.

    Empty lines and lines starting with # are ignored."""

        self.parser.set_usage(usage)
        self.parser.set_defaults(remote = True, interface = "ath0",
                                 multicast = "224.66.66.66", offset = 0, staticroutes=False, multipath=False, maxpath=2)
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
        self.parser.add_option("-u", "--userscripts",
                               action = "store_true", dest = "userscripts",
                               help = "Execute user scripts for every node if available "\
                                      "(located in ~/config/vmesh_helper/vmrouter<NUMBER>)")
        self.parser.add_option("-s", "--staticroutes",
                               action = "store_true", dest = "staticroutes",
                               help = "Setup static routing according to topology "\
                                      "(default: %default)")
        self.parser.add_option("-p", "--multipath",
                               action = "store_true", dest = "multipath",
                               help = "Setup equal cost multipath routes. For use with -s"\
                                   "(default:%default)")
        self.parser.add_option("-x", "--maxpath",
                                action="store", dest="maxpath", type = int,
                                help = "Maximum number of parallel paths to set up. \
                                        Use only in connection with --multipath."\
                                        "(default:%default)")
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
        """Returns an hash which maps host number -> set of reachable host numbers

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

        # match comments
        comment_re = re.compile('^\s*#')

        # line syntax:
        # LINE = HOST ":" REACHES
        # HOST = DIGITS
        # REACHES = DIGITS REACHES | DIGITS "-" DIGITS " " REACHES
        # additional spaces are allowed everywhere, except around the "-"
        digits_str = r"""
                [0-9]+                              # INT
                """
        float_str = r"""
                %s(?:\.%s)?                         # INT "." INT
                """ % (digits_str,digits_str)
        line_str = r"""
                ^([0-9]+)\ *:                       # HOST ":"
                \ *                                 # optional spaces
                ( ( %s )+ )                         # REACHES
                $"""
        reaches_str = r"""
                (%s)(?:-(%s))?                      # DIGITS | DIGITS "-" DIGITS
                (?:\[(%s)?(?:,(%s)?)?(?:,(%s)?)?(?:,(%s)?)?\])?    # [ "[" FLOAT,INT,INT,INT "]" ]
                (?:\ +|$)                           # optional spaces
                """ % (digits_str,digits_str,float_str,digits_str,digits_str,digits_str)

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

            # ignore empty lines and comments
            if line is '' or comment_re.match(line):
                continue

            # parse line, skip on syntax error
            lm = line_re.match(line)
            if not lm:
                warn("Syntax error in line %s. Skipping." %line)
                continue

            host = lm.group(1)
            reaches = set()
            for m in reaches_re.findall(lm.group(2)):
		debug(m)
                first = int(m[0])
                if m[1]: last = int(m[1])
                else: last = first
                info_rate = m[2]
                info_limit = m[3]
                info_delay = m[4]
                info_loss = m[5]
                if last:
                    reaches.update(range(first, last+1))
                else:
                    reaches.add(first)

                if not self.linkinfo.has_key(int(host)):
                    self.linkinfo[int(host)] = dict()
                for i in range(first, last+1):
                    self.linkinfo[int(host)][i] = dict()
                    self.linkinfo[int(host)][i]['rate'] = info_rate
                    self.linkinfo[int(host)][i]['limit'] = info_limit
                    self.linkinfo[int(host)][i]['delay'] = info_delay
                    self.linkinfo[int(host)][i]['loss'] = info_loss

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

    def visualize(self, graph):
        """Visualize topology configuration"""
        info("Configured with the following topology:")
        dot_content = list()
        dot_content.append("digraph G {")
        for host in graph:
             for neigh in graph[host]:
               dot_content.append("%s -> %s" %(host, neigh))
        dot_content.append("}")
        try:
            call("graph-easy --as=ascii", input="\n".join(dot_content))
        except CommandFailed, inst:
            warn("Visualizing topology failed.")
            warn("Visualizing failed: RC=%s, Error=%s" % (inst.rc, inst.stderr))

    def gre_ip(self, hostnum, mask=False):
        """Gets the gre ip for host with number "hostnum" """

        if mask:
            return "172.16.%s.%s/16" %( (hostnum-1)/254, (hostnum-1)%254+1 ) # FIXME - do not hardcode this.
        else:
            return "172.16.%s.%s" %( (hostnum-1)/254, (hostnum-1)%254+1 )


    def gre_net(self, mask = True):
        """Gets the gre network address"""

        if mask:
            return "172.16.0.0/16"
        else:
            return "172.16.0.0"


    def setup_gre(self):
        hostnum = self.node.getNumber()
        public_ip = self.node.getIPaddress(device = None)
        gre_ip = self.gre_ip(hostnum, mask=True)

        try:
            iface = self.options.interface
            info("setting up GRE Broadcast tunnel for %s" % hostnum )
            execute('ip tunnel del %s' % iface, True, False)
            execute('ip tunnel add %(iface)s mode gre local %(public)s remote %(mcast)s ttl 1 \
                     && ip addr add %(gre)s broadcast 172.16.255.255 dev %(iface)s \
                     && ip link set %(iface)s up' %
                     {"public": public_ip, "gre": gre_ip, "iface": iface, "mcast": self.options.multicast},
                     True)
        except CommandFailed, inst:
            error("Setting up GRE tunnel %s (%s, %s) failed." % (hostnum, public_ip, gre_ip))
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))


    def chorder(self, address):
        """changes the order of an ip address"""
        sa = address.split('.')
        sa.reverse()
        return ".".join(sa)

    def setup_dns(self):
        # update dns
        iface = self.options.interface
        hostnum = self.node.getNumber()
        address = self.gre_ip(hostnum, mask=False)

        update_dns1 = "echo \"update delete %s.vmrouter%s.umic-mesh.net A\\nupdate add %s.vmrouter%s.umic-mesh.net %u A %s\\nsend\" | nsupdate -y rndc-key:%s" %(iface, hostnum, iface, hostnum, self._dnsttl, address, self._dnskey)
        try:
                (stdout, stderr) = execute(update_dns1)
        except CommandFailed, inst:
                error("Updating DNS entry for %s.vmrouter%s failed." % (iface,hostnum))
                error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))

        chaddress = self.chorder(address)
        update_dns2 = "echo \"update delete %s.in-addr.arpa PTR\\nupdate add %s.in-addr.arpa %u PTR %s.vmrouter%s\\nsend\" | nsupdate -y rndc-key:%s" %(chaddress, chaddress, self._dnsttl, iface, hostnum, self._dnskey)
        try:
                (stdout, stderr) = execute(update_dns2)
        except CommandFailed, inst:
                error("Updating DNS entry for %s.in-addr.arpa failed." % (chaddress))
                error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))

    def setup_trafficcontrol(self):
        iface = "eth0"
        hostnum = self.node.getNumber()
        peers = self.conf.get(hostnum, set())
        prefix = self.node.getHostnamePrefix()

        # Add qdisc
        try:
            execute("tc qdisc del dev %s root; " % iface +
                    "tc qdisc add dev %s root handle 1: htb default 100" % iface
                    ,True)
        except CommandFailed, inst:
            error('Could not install queuing discipline')
            error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            raise

        # Add class and filter for each peer
        i = 0
        for p in peers:
            try:
                if self.linkinfo.has_key(hostnum) and self.linkinfo[hostnum].has_key(p) and self.linkinfo[hostnum][p]['rate'] != '':
                    rate = self.linkinfo[hostnum][p]['rate']
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
                        'rate' : rate}
                        ,True)

                # netem for queue length, delay and loss
                netem_str = 'tc qdisc add dev %s parent 1:%s handle %s0: netem' % (iface, i, i)
                if self.linkinfo[hostnum][p]['limit'] != '':
                    netem_str += ' limit %s' %self.linkinfo[hostnum][p]['limit']
                if self.linkinfo[hostnum][p]['delay'] != '':
                    netem_str += ' delay %sms' %self.linkinfo[hostnum][p]['delay']
                if self.linkinfo[hostnum][p]['loss'] != '':
                    netem_str += ' drop %s' %self.linkinfo[hostnum][p]['loss']

                # create netem queue only if one of the parameter is given
                if self.linkinfo[hostnum][p]['limit'] != '' or self.linkinfo[hostnum][p]['delay'] != '' or self.linkinfo[hostnum][p]['loss'] != '':
                    info("      Adding netem queue, limit:\'%s\', delay:\'%s\', loss:\'%s\'"
                        % (self.linkinfo[hostnum][p]['limit'],self.linkinfo[hostnum][p]['delay'],self.linkinfo[hostnum][p]['loss']))
                    execute(netem_str, True)

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

    @staticmethod
    def find_k_equal_cost_paths(graph, start, end, paths=[]):
        for node in graph[start]:
            newpath = BuildVmesh.find_shortest_path(graph, node, end)
            if newpath == None:
                continue
            if len(paths)==0 or len(newpath) < len(paths[0]):
                paths = [newpath]
            if len(newpath) == len(paths[0]) and newpath not in paths:
                paths += [newpath]
        return paths

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
            # skip localhost
            if host==hostnum:
                continue

            paths = BuildVmesh.find_k_equal_cost_paths(self.conf, hostnum, host)
            # not all hosts may be reachable from this hosts ignore them
            if len(paths) == 0:
                continue

            # calculate distance unlike the single path version we don't need to subtract 1 as the node itself isn't saved in the list
            dist = len(paths[0]) #equal cost so the dist from the first path suffices

            # ignore direct neighbors for now as network mask should cover them
            if dist==1:
                continue

            host_ip = self.gre_ip(host, mask=False)

            cmd = ["ip", "route", "replace", host_ip]
            if self.options.multipath:
                for i in range(min(len(paths),self.options.maxpath)):
                    nexthop = self.gre_ip(paths[i][0], mask=False)
                    cmd += ["nexthop", "via", nexthop, "dev", iface]
            else:
                nexthop = self.gre_ip(paths[0][0], mask=False)
                cmd += ["dev", iface, "via", nexthop, "metric", str(dist)]
            try:
                execute(cmd, shell=False)
            except CommandFailed, inst:
                error('Adding routing entry for host %s failed.' % host_ip)
                error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
                raise

            # to have more control over multipath routes, add entries to distinct
            # routing tables
            if self.options.multipath:
                for i in range(min(len(paths),self.options.maxpath)):
                    nexthop = self.gre_ip(paths[i][0], mask=False)
                    table = self._rtoffset+i
                    cmd  = ["ip", "route", "replace", host_ip]
                    cmd += ["via", nexthop, "table", str(table)]
                    try:
                        execute(cmd, shell=False)
                    except CommandFailed, inst:
                        error('Failed adding entry for host %s to table %s.' % (host_ip, table))
                        error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
                        raise

    def setup_user_helper(self):
        if self.options.userscripts:
            cmd = ["%s/config/vmesh-helper/%s" %(os.environ["HOME"], self.node.getHostname())]
            if os.path.isfile(cmd[0]):
                info("Executing user-provided helper program...")
                try:
                    execute(cmd)
                except CommandFailed, inst:
                    error("Execution of %s failed." % cmd[0])
                    error("Return code %s, Error message: %s" % (inst.rc, inst.stderr))
            else:
                info("%s does not exist." % cmd[0])
                info("Skipping user-provided helper program")

    def run(self):
        """Main method of the Buildmesh object"""

        # Apply settings on remote hosts
        if self.options.remote:
            requireNOroot()
            self.visualize(self.conf)
            for host in self.conf.keys():
                h = "vmrouter%s" % host
                info("Configuring host %s" % h)
                cmd = ["ssh", h, "sudo", "/usr/local/sbin/um_vmesh",
                                                "-i", self.options.interface, "-l", "-"]
                if self.options.debug:
                    cmd.append("--debug")

                if self.options.staticroutes:
                    cmd.append("--staticroutes")

                if self.options.multipath:
                    cmd.append("--multipath")
                    cmd.append("--maxpath")
                    cmd.append(str(self.options.maxpath))

                if self.options.rate:
                    cmd.append("-R")
                    cmd.append(self.options.rate)

                if self.options.userscripts:
                    cmd.append("-u")

                debug("Executing: %s", cmd)
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                rc = proc.communicate("".join(self.confstr))
                if proc.returncode != 0:
                    error("Configuring host %s FAILED (%s)" % (h, proc.returncode))

        # Apply settings on local host
        else:
            self.node = Node()

            info("Setting up GRE tunnel ...")
            self.setup_gre()

            info("Update DNS entries ...")
            self.setup_dns()

            info("Setting up iptables rules ... ")
            self.setup_iptables()

            info("Setting up traffic shaping ... ")
            self.setup_trafficcontrol()

            if self.options.staticroutes:
                info("Setting up static routing...")
                self.setup_routing()

            self.setup_user_helper()

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__":
    BuildVmesh().main()
