#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import os
from logging import info, debug, warn, error, critical

from twisted.web.xmlrpc import Proxy
from twisted.internet import defer, reactor
from twisted.python import log

from um_application import Application
from um_measurement.sshexec import SSHConnectionFactory
from um_twisted_meshdb import MeshDbPool


class Measurement(Application):
    """

    Framework for UMIC-Mesh measurement applications.

    Provides an Application wrapper for Measurement classes. Must be
    subclassed to be used.

    As usual for Application subclassses, the subclass may add own parameters
    to self.parser.
    It must call parse_option() and Measurement2App.set_option afterwards.

    """

    def __init__(self):
        Application.__init__(self)

        self.node_list = None
        self.node_pairs = None
        self._scf = SSHConnectionFactory()
        self._null = None
        self._dbpool = MeshDbPool(username = "measurement",
                                  password = "XaNU7X84BQJveYQX")

        self.xmlrpc_port = 7080

        self._stats = dict()

        p = self.parser

        usage = "usage: %prog [options] -L outputdir\n"
        p.set_usage(usage)


        p.set_defaults(
                log_dir = None,
                )

        p.add_option("-L", "--log-dir", metavar="NAME",
                action = "store", dest = "log_dir",
                help = "Where to store the log files.")


    def set_option(self):
        Application.set_option(self)

        if not self.options.log_dir:
            self.parser.error("An output directory must be specified.")



    def _getNull(self):
        """ Provides a null file descriptor. """
        if not self._null:
            self._null = open('/dev/null','w')
        return self._null


    def xmlrpc_many(self, hosts, cmd, *args):
        """Calls a remote procedure on hosts"""

        deferredList = []

        for host in hosts:
            deferredList.append(self.xmlrpc(host, cmd,
                                           *args))
        return defer.DeferredList(deferredList, consumeErrors=True)                
            


    def xmlrpc(self, host, cmd, *args):
        """Calls a remote procedure on a host"""

        proxy = Proxy('http://%s:%u' %(host, self.xmlrpc_port))
        debug("Calling %s on %s with args %s" %(cmd,host,args))
        return proxy.callRemote(cmd, *args)

    @defer.inlineCallbacks
    def switchTestbedProfile(self, name):
        """
        
        Switches the current testbed profile
        and applies configuration changes to all nodes.
        
        """

        yield self._dbpool.switchTestbedProfile(name)

        current = yield self._dbpool.getCurrentTestbedProfile()
        if not current==name:
            error("Switch to testbed profile %s failed. Current: %s"
                  %(name,current))
            defer.returnValue(-1)

        info("Applying configuration changes...")
        nodes = yield self._dbpool.getTestbedNodes()
        results = yield self.xmlrpc_many(nodes,"apply")

        i = 0
        succeeded = 0
        failed = 0
        for result in results:
            if result[0] == defer.FAILURE:
                warn("Failed to setup %s: %s" %(nodes[i], result[1].getErrorMessage()))
                failed = failed+1
            else:
                rc = result[1]
                if (rc != 0):
                    warn("Failed to setup %s: apply() returned: %d" &(nodes[i], rc))
                    failed = failed+1
                else:
                    succeeded = succeeded+1
            i=i+1
        info("Succeeded: %d, Failed: %d" %(succeeded, failed))
        info("Testbed profile is now: %s" %current)
        

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
    def run_test(self, test, **kwargs):
        """Runs a test method with arguments self, logfile, args"""

        if not os.path.exists(self.options.log_dir):
            info("%s does not exist, creating. " % self.options.log_dir)
            os.mkdir(self.options.log_dir)

        log_name = "%s_%s" %(self.logprefix, test.func_name)
        log_path = os.path.join(self.options.log_dir, log_name)
        log_file = file(log_path, 'w')

        # write config into logfile
        for item in kwargs.iteritems():
            log_file.write("%s=%s\n" %item)
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
        """ Get the next hop for the given destination.
            Destination must be an ip adress or prefix """

        cmd = "ip route get %s" %dst
        stdout = os.tmpfile()
        result = yield self.mrs.remote_execute(src,
                                               cmd,
                                               stdout,
                                               timeout=flowgrind_duration+5)
        
        stdout.seek(0)
        # get first word of the first line
        nexthop = stdout.readlines()[0].split(" ",1)[0]

        stdout.close()

        defer.returnValue(nexthop)

    @defer.inlineCallbacks
    def get_mac(self, dst, interface):
        """ Returns the mac address for the destination address"

        cmd = "sudo arping -c 1 -r %s" %dst
                stdout = os.tmpfile()
        result = yield self.mrs.remote_execute(src,
                                               cmd,
                                               stdout,
                                               timeout=flowgrind_duration+5)
        
        stdout.seek(0)
        # get first word of the first line
        mac = stdout.readlines()[0].split(" ",1)[0]

        stdout.close()

        defer.returnValue(mac)
