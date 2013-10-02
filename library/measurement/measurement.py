#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2007 - 2011 Arnd Hannemann <arnd@arndnet.de>
# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
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
import os.path
import os
import sys
import time
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.web.xmlrpc import Proxy
from twisted.internet import defer, reactor
from twisted.python import log
import twisted.names.client

# tcp-eval imports
from common.application import Application
from sshexec import SSHConnectionFactory
from network.meshdb import MeshDbPool
from network.xmlrpc import xmlrpc_many, xmlrpc
from network.functions import twisted_sleep

class Measurement(Application):
    """Provides an Application wrapper for Measurement classes. Must be
    subclassed to be used.

    As usual for Application subclassses, the subclass may add own parameters
    to self.parser. It must call apply_optiosn() and Measurement2App.set_options
    afterwards."""

    def __init__(self, prog=None, usage=None, description=None, epilog=None):

        # object variables
        self.node_list = None
        self.node_pairs = None
        self._scf = SSHConnectionFactory()
        self._null = None
        self._dbpool = MeshDbPool(username="measurement",
                password="XaNU7X84BQJveYQX")
        self._maccache = dict()     # caches mac addresses
        self._stats = dict()

        # create top-level parser and subparser
        Application.__init__(self, prog=prog, usage=usage,
                description=description, epilog=epilog)
        self.parser.add_argument("-l", "--log-dir", metavar="DIR", default="./",
                action="store", dest="log_dir", help="Where to store the log "\
                        "files (default: %(default)s)")

    def apply_options(self):
        """Configure object based on the options form the argparser"""

        Application.apply_options(self)

    def _getNull(self):
        """Provides a null file descriptor"""

        if not self._null:
            self._null = open('/dev/null','w')

        return self._null

    def xmlrpc_many(self, hosts, cmd, *args):
        """Calls a remote procedure on hosts"""

        # for convenience only
        return xmlrpc_many(hosts, cmd, *args)

    def xmlrpc(self, host, cmd, *args):
        """Calls a remote procedure on a host"""

        # for convenience only
        return xmlrpc(host, cmd, *args)

    def _pollNodeCallback(self, clean, d, hostname):
        """Callback for a isNodeClean call"""

        # polling stopped?
        if not d.polling:
            return

        if clean:
            # node is ready now, cancel timer and fire d
            d.timer.cancel()
            d.polling = False
            d.callback(True)
        else:
            # schedule next poll in 5 seconds
            reactor.callLater(5, self._pollNode, d, hostname)


    def _pollNode(self, d, hostname):
        """Performs a db query"""

        # polling stopped?
        if not d.polling:
            return

        # start a new poll
        debug("Check if %s is ready now..." %hostname)
        poll = self._dbpool.isNodeClean(hostname)
        poll.addCallback(self._pollNodeCallback, d, hostname)

    def _pollNodeTimeout(self, d, hostname):
        """If a waitForNode call times out this is called"""

        # stop new polls
        d.polling = False

        debug("waitForNode(%s) timed out" %hostname)

        # return false
        d.callback(False)

    def waitForNode(self, hostname, timeout=300):
        """Waits until the specified node has started all services
           or returns False when timeout is hit"""

        d = defer.Deferred()

        # return false if timeout is hit, and store timer in deferred
        d.timer = reactor.callLater(timeout, self._pollNodeTimeout, d, hostname)

        # store boolean in deferred
        d.polling = True

        # start polling
        self._pollNode(d, hostname)

        return d

    def waitForNodes(self, hostnames, *args):
        deferredList = []

        for hostname in hostnames:
            deferredList.append(self.waitForNode(hostname, *args))

        # if a defered returns a failure, the failure instance is
        # in the result set returnend by DeferredList
        # so prevent "Unhandled error in Deferred" warnings by
        # setting consumeErrors=True
        return defer.DeferredList(deferredList, consumeErrors=True)

    @defer.inlineCallbacks
    def switchTestbedProfile(self, name):
        """Switches the current testbed profile
           and applies configuration changes to all nodes.
        """

        dirty_nodes = yield self._dbpool.switchTestbedProfile(name)
        reboot_nodes = list()

        current = yield self._dbpool.getCurrentTestbedProfiles()
        if name not in current:
            error("Switch to testbed profile %s failed. Current: %s"
                  %(name,current))
            defer.returnValue(-1)

        info("Applying configuration changes...")
        results = yield self.xmlrpc_many(dirty_nodes,"apply")

        i = 0
        succeeded = 0
        failed = 0
        reboot = 0

        for i,result in enumerate(results):
            if result[0] == defer.FAILURE:
                warn("Failed to setup %s: %s" %(dirty_nodes[i], result[1].getErrorMessage()))
                failed = failed+1
            else:
                rc = result[1]
                if (rc == 0):
                    succeeded = succeeded+1
                elif (rc == "reboot"):
                    warn("Node %s will reboot to apply config" %dirty_nodes[i])
                    reboot_nodes.append(dirty_nodes[i])
                    reboot = reboot + 1
                else:
                    warn("Failed to setup %s: apply() returned: %s" %(dirty_nodes[i], rc))
                    failed = failed + 1

        info("Succeeded: %d, Failed: %d, Reboot: %d" %(succeeded, failed, reboot))

        if reboot != 0:
            info("Waiting for booting nodes to become ready...")
            results = yield self.waitForNodes(reboot_nodes)

            for i,result in results:
                if not result:
                    warn("Node %s did not become ready after reboot (timeout)" %reboot_nodes[i])

        info("Activated testbed profiles are now: %s" %current)


    def remote_execute_many(self, hosts, cmd, **kwargs):
        """Executes command cmd on hosts, returns a DeferredList"""

        deferredList = []

        for host in hosts:
            deferredList.append(self.remote_execute(host, cmd,
                                                   **kwargs))
        # if a defered returns a failure, the failure instance is
        # in the result set returnend by DeferredList
        # so prevent "Unhandled error in Deferred" warnings by
        # setting consumeErrors=True
        return defer.DeferredList(deferredList, consumeErrors=True)


    def local_execute(self, cmd, log_file, *args, **kwargs):
        """Execute command locally"""
        return self.remote_execute("localhost", cmd, log_file, *args, **kwargs)


    @defer.inlineCallbacks
    def remote_execute(self, host, cmd, log_file=None, **kwargs):
        """Executes command cmd on host(s), creating a master connection if necessary"""

        # for convenience assume that if host is not string its something to it
        # iterate over
        if type(host) is not str:
            yield remote_execute_many(self, host, cmd, **kwargs)

        if not log_file:
            logfile = self._getNull()

        if not self._scf.isConnected(host):
            info("no master connection to %s found creating one..." % host)
            rc = yield self._scf.connect([host])
            if len(rc) !=0:
                error("failed to connect to %s: %s" %(host, rc[-1].getErrorMessage()))
                defer.returnValue(-1)

        debug("%s: running %s" %(host,cmd))
        res = yield self._scf.remoteExecute(host, cmd,
                                            out_fd=log_file,
                                            err_fd=sys.stderr, **kwargs)
        defer.returnValue(res)

    def _update_stats(self, test, rc):
        """ This function updates internal statistics """

        test_name = test.func_name

        if not self._stats.has_key(test_name):
            self._stats[test_name] = dict()

        test_stats = self._stats[test_name]

        if not test_stats.has_key(rc):
            test_stats[rc] = 1
        else:
            test_stats[rc] += 1

    @defer.inlineCallbacks
    def run_test(self, test, append=False, **kwargs):
        """Runs a test method with arguments self, logfile, args"""

        if not os.path.exists(self.args.log_dir):
            info("%s does not exist, creating. " % self.args.log_dir)
            os.mkdir(self.args.log_dir)

        log_name = "%s_%s" %(self.logprefix, test.func_name)
        log_path = os.path.join(self.args.log_dir, log_name)

        if append:
            log_file = open(log_path, 'a')
        else:
            log_file = open(log_path, 'w')

            # write config into logfile
            for item in kwargs.iteritems():
                log_file.write("%s=%s\n" %item)
            log_file.write("test_start_time=%s\n" %time.time())
            log_file.write("BEGIN_TEST_OUTPUT\n")
            log_file.flush()

        # actually run test
        info("Starting test %s with: %s", test.func_name, kwargs)
        rc = yield test(self, log_file, **kwargs)
        if (rc == 0):
            info("Finished test.")
        else:
            warn("Test returned with RC=%s" %rc)

        self._update_stats(test,rc)

        log_file.close()

    @defer.inlineCallbacks
    def tear_down(self):
        yield self._scf.disconnect()

    def sleep(self, seconds):
        """ This function returns a deferred which will fire seconds later """

        d = defer.Deferred()
        reactor.callLater(seconds, d.callback, 0)
        return d

    def generate_pair_permutations(self, nodelist,
                                   symmetric=True,
                                   label_= lambda src, dst: r"%s\\sra%s" %(src,dst),
                                   **kwargs):
        """returns a list of dicts

           Generates all 2-tuple permutations of the given nodelist. The dicts
           generated have the keys src, dst, run_label and all keys out of kwargs.
        """

        res = list()
        for target in nodelist:
            for source in nodelist:
                if source == target:
                    continue
                if not symmetric and source > target:
                    continue
                else:
                    res.append(dict( run_label=label_(source,target),
                                     src=source,
                                     dst=target, **kwargs))
        return res

    def load_pairs_from_file(self, filename,
                                   label_= lambda src, dst: r"%s\\sra%s" %(src,dst),
                                   **kwargs):
        """returns a list of dicts

           Loads pairs from the given filename. The dicts
           generated have the keys src, dst, run_label and all keys out of kwargs.
        """

        fh = file(filename)

        res = list()
        for line in fh.readlines():
            (source, target) = line.split()
            res.append(dict( run_label=label_(source,target),
                             src=int(source),
                             dst=int(target), **kwargs))
        return res

    @defer.inlineCallbacks
    def get_next_hop(self, src, dst):
        """Get the next hop for the given destination.
           Destination must be an ip address or prefix
        """

        cmd = "ip route get %s" %dst
        stdout = os.tmpfile()
        result = yield self.remote_execute(src,
                                           cmd,
                                           stdout,
                                           timeout=3)

        stdout.seek(0)
        # get first word of the first line
        lines = stdout.readlines()
        debug(lines)
        if len(lines)>0:
            firstline = lines[0]
            # direct neihbor
            if firstline.find("via") == -1:
                nexthop = lines[0].split(" ",1)[0]
                nexthop = nexthop.strip()
            # there is an explict gateway
            else:
                nexthop = lines[0].split(" ",3)[2]
                nexthop = nexthop.strip()
        else:
            nexthop = None

        stdout.close()

        defer.returnValue(nexthop)

    @defer.inlineCallbacks
    def get_mac(self, src, dst, interface):
        """Returns the mac address for the destination address"""

        try:
            mac = self._maccache[dst]
            defer.returnValue(mac)
        except KeyError:
            debug("Trying to determine mac of %s..." %dst)

        cmd = "sudo arping -c 1 -i %s -r %s " %(interface,dst)
        stdout = os.tmpfile()
        result = yield self.remote_execute(src,
                                           cmd,
                                           stdout,
                                           timeout=2)

        stdout.seek(0)
        # get first word of the first line
        lines = stdout.readlines()
        debug(lines)
        if len(lines)>0:
            mac = lines[0].split(" ",1)[0]
            mac = mac.strip()
            self._maccache[dst] = mac
        else:
            mac = None
        stdout.close()

        defer.returnValue(mac)

    @defer.inlineCallbacks
    def preInit(self, nodes, ssh_master=True):
        """ Does some pre init of the nodes (creating ssh master connection etc... """

        if ssh_master:
            rc = yield self._scf.connect(nodes)

        defer.returnValue(rc)

    def getIp(self, hostname, interface = None):
        if interface:
            name = "%s.%s" %(interface, hostname)
        else:
            name = hostname
        deferred = reactor.resolve(name)

        def errorHandler(inst):
            error("Failed to resolve %s: %s"%(name, inst.getErrorMessage()))
            # re-raise error
            return inst

        deferred.addErrback(errorHandler)

        return deferred

