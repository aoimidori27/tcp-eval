#!/usr/bin/env python
# -*- coding: utf-8 -*-

import errno
import os.path
import random
import sys
from logging import info, debug, warn, error, critical

from twisted.internet import defer, reactor
from twisted.python import log

from um_application import Application
from um_measurement2.sshexec import SSHConnectionFactory


def combine(*args):
    print "LEN: %s; %s; %s" % (len(args), args, args[0])
    def join_args(*args):
        return args
    for i in args[0]:
        if len(args)==1:
            yield (i,)
        else:
            for t in combine(*args[1:]):
                yield join_args(i, *t)

class Measurement2App(Application):
    """
    Framework for UMIC-Mesh measurement applications.

    Provides an Application wrapper around the Measurement2 class. Must be
    subclassed to be used.

    As usual for Application subclassses, the subclass may add own parameters to self.parser.
    It must call parse_option() and Measurement2App.set_option afterwards.
    Before starting the measurement by calling run(), add_test must be used to
    add test classes.
    """

    def __init__(self):
        Application.__init__(self)

        self.node_list = None
        self.node_pairs = None
        self._scf = SSHConnectionFactory()
        self._null = None

        p = self.parser

        usage = "usage: %prog [options] -L outputdir\n" 
        p.set_usage(usage)


        p.set_defaults(
                log_dir = None,
                )

        # FIXME: Ignore critical; Abort run
        p.add_option("-L", "--log-dir", metavar="NAME",
                action = "store", dest = "log_dir",
                help = "Where to store the log files.")


    def set_option(self):
        Application.set_option(self)

        if not self.options.log_dir:
            self.parser.error("An output directory must be specified.")


    def _getNull(self):
        if not self._null:
            self._null = open('/dev/null','w')
        return self._null


    @defer.inlineCallbacks
    def remote_execute_many(self, hosts, cmd, **kwargs):
        """Executes command cmd on hosts"""
        deferedList = []

        for host in hosts:            
            deferedList.append(self.remote_execute(host, cmd,
                                                   **kwargs))
        yield defer.DeferredList(deferedList)
        
        

    @defer.inlineCallbacks
    def remote_execute(self, host, cmd, log_file=None, **kwargs):
        """Executes command cmd on host, creating a master connection if necessary"""
        if not log_file:
            logfile = self._getNull()
        if not self._scf.isConnected(host):
            info("no master connection to %s found creating one..." % host)
            yield self._scf.connect([host])
        debug("%s: running %s" %(host,cmd))
        yield self._scf.remoteExecute(host, cmd,
                                      out_fd=log_file,
                                      err_fd=sys.stderr, **kwargs)


    @defer.inlineCallbacks
    def run_test(self, test, **kwargs):
        "Runs a test method with arguments self, logfile, args"
        if not os.path.exists(self.options.log_dir):
            info("%s does not exist, creating. " % self.options.log_dir)
            os.mkdir(self.options.log_dir)
        log_name = "%s_%s" %(self.logprefix, test.func_name)
        log_path = os.path.join(self.options.log_dir, log_name)
        log_file = file(log_path, 'w')
        if kwargs.has_key('run_label'):
            log_file.write("run_label:%s\n" %kwargs['run_label'])
            log_file.flush()
        if kwargs.has_key('scenario_label'):
            log_file.write("scenario_label:%s\n" %kwargs['scenario_label'])
            log_file.flush()            

        # actually run test
        info("Starting test %s with: %s", test.func_name, kwargs)
        rc = yield test(log_file, **kwargs)
        info("Finished test.")
        
        log_file.close()

    @defer.inlineCallbacks
    def tear_down(self):
        yield self._scf.disconnect()


    def generate_pair_permutations(self, nodelist,
                                   symmetric=True,
                                   label_= lambda src, dst: r"%s\\sra%s" %(src,dst),
                                   **kwargs):
        """returns a list of dicts
        Generates all 2-tuple permutations of the given nodelist
        """
        res = list()
        for target in nodelist:
            for source in nodelist:
                if source == target:
                    continue
                if not symmetric and source > target:
                    continue
                else:
                    res.append(dict( run_label=label_(source,target), src=source, dst=target, **kwargs))
        return res
    

#    def run(self):
#m = Measurement2(
#                node_list = self.node_list,
#                node_pairs = self.node_pairs,
#                symmetric = not self.options.asymmetric,
#                outer_repeats = self.options.outer_loops,
#                inner_repeats = self.options.inner_loops,
#                log_dir = self.options.log_dir
#                )
#        for test in self.tests:
#            info("Adding test %s" % test)
#            m.add_test(test)
#
#        # Create log directory, if necessary
#        log_dir = self.options.log_dir
#        if log_dir is not None:
#            try:
#                info("Creating log_dir.")
#                os.makedirs(log_dir)
#            except os.error, inst:
#                if not (inst.errno == errno.EEXIST and os.path.isdir(log_dir)):
#                    error("Failed to creat log_dir!")
#                    sys.exit(1)
#
#        m.start()
#        reactor.run()



class Measurement2():
    """ FIXME """

    def __init__(self, node_list = None, node_pairs = None, symmetric = False,
            outer_repeats = 1, inner_repeats = 1, log_dir = None):
        """
        Initializes the class.

         * node_list: A list of nodes to run the tests on
         * node_pairs: A list of node pairs to run the tests on.
                Exactly one of node_list and node_pairs must be given!
         * symmetric: If we've tested (node1, node2), shall we test
                (node2, node1) too?
         * def_timeout: Default time limit for each test run.
         * inner_repeats, outer_repeats: How often shall the tests be repeated?
                inner: Execute a test for a node_pair multiple times in a row
                outer: Repeat the whole measurement.
        """

        self._node_pairs = node_pairs
        if node_pairs is not None:
            # Generate list of nodes in node_pairs
            nodeset = set()
            for np in node_pairs:
                nodeset.add(np[0])
                nodeset.add(np[1])
            node_list = list(nodeset)
        self._node_list = node_list

        self._symmetric = symmetric
        # FIXME: Add an option to override this setting on a per-test basis
        self._inner_repeats = inner_repeats
        self._outer_repeats = outer_repeats
        self._log_dir = log_dir

        # A list of tests to execute
        self._tests = []
        # Generator for tuples of test and nodes
        self._generator = None
        # FIXME
        if self._log_dir is None:
            self._log_fd = sys.stdout
        else:
            self._log_fd = None

    def add_test(self, test):
        """
        Adds a test. Interface of a test is defined as follows:

        __init__(self, node_info):
            Creates a new test instance to test node_info=(src,dst) pair

        start(self):
            Runs test for (src,dst) pair. May only be called once. Returns an deferred.
            A test is considered to be successful, if callback() is called and failed,
            if an TestFailed instance is errbacked. Other exceptions are considered to be
            a programming error (and passed through).

        stop(self):
            Cancels a test run. This is called if the timeout elapsed.
        """
        self._tests.append(test)

    def host_pairs(self):
        """
        Generator. Generates all host/target pairs depending on the
        self._symmetric and self._nodes settings.

        FIXME!
        """
        if self._node_pairs is not None:
            for p in self._node_pairs:
                yield p
        else:
            for target in self._node_list:
                for source in self._node_list:
                    if source == target:
                        continue
                    if not self._symmetric and source > target:
                        continue
                    else:
                        yield (source, target)

    def test_sequence(self):
        for o in range(self._outer_repeats):
            for node_info in self.host_pairs():
                for test in self._tests:
                    for i in range(self._inner_repeats):
                        if self._log_dir is not None:
                            logname = "o%03d_%s_%s_%s_i%03d.log" % \
                                    (o, node_info[0], node_info[1], test, i)
                            self._log_fd = open(os.path.join(self._log_dir, logname), "w")
                        yield (o, node_info, test, i)
        if self._log_dir is not None:
            self._log_fd.close()

    def run_test(self, test_inst):
        info("Running test: %s." % test_inst)
        d = test_inst.start()
        if test_inst.timeout is not None:
            cl = reactor.callLater(test_inst.timeout, test_inst.stop)
            def cancelTimeout(result):
                if cl.active():
                    cl.cancel()
                return result
            # Ensure that cl is not called if test terminated by itself.
            d.addBoth(cancelTimeout)
        return d



        
        
    @defer.inlineCallbacks
    def start(self):
        """
        Runs all tests as generated by test_sequence().
        """
        info("Initializing Nodes ...")
        try:
            for test in self._tests:
                yield test.init_nodes(self._node_list)
        except Exception, inst:
            # FIXME: Get better error reporting: I'd would be nice to know
            # which node failed.
            error("ERROR: Initialising one node failed! Terminating.")
            error(repr(inst))
            reactor.stop()
            defer.returnValue(False)
        info("All nodes initialized. Starting measurements.")
        for o, node_info, test, i in self.test_sequence():
            test_inst = test(node_info, self._log_fd)
            try:
                result = yield self.run_test(test_inst)
                info("Test (%s) successful: %s" % (test_inst, result))
            except TestFailed, inst:
                info("Test (%s) failed: %s" % (test_inst, inst))
        info("Measurements finished.")
        yield test.cleanup()
        reactor.stop()


class TestFailed(Exception):
    """Test failed"""

    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '%s: %s' % (s, ' '.join(map(lambda x: str(x), self.args)))
        s = '%s.' % s
        return s
