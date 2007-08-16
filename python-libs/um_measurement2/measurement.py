#!/usr/bin/env python
# -*- coding: utf-8 -*-

import errno
import os.path
import random
import sys

from twisted.internet import defer, reactor
from twisted.python import log

from logging import info, debug, warn, error, critical

from um_application import Application

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
        self.tests = []

        p = self.parser

        usage = "usage: %prog [options] NODES|hostpairfilename\n" \
                "where NODES := either [v]mrouter numbers or hostnames"
        p.set_usage(usage)


        p.set_defaults(
                asymmetric = False,
                hostprefix = 'mrouter',
                outer_loops = 1,
                inner_loops = 1,
                log_dir = None,
                )

        # FIXME: this option is only relevant if we give a node list instead of a pair list.
        p.add_option("-a", "--asymmetric",
                action = "store_true", dest = "asymmetric",
                help = "consider one way tests only [default: %default]")
        p.add_option("-H", "--hostprefix", metavar="PREFIX",
                action = "store", dest = "hostprefix",
                help = "hostname prefix for node IDs [default: %default]")
        p.add_option("-o", "--outer-loops", metavar="COUNT",
                action = "store", dest = "outer_loops", type = int,
                help = "repeat the outer test loop COUNT times [default: %default]")
        p.add_option("-i", "--inner-loops", metavar="COUNT",
                action = "store", dest = "inner_loops", type = int,
                help = "repeat the inner test loop COUNT times [default: %default]")
        # FIXME: Ignore critical; Abort run
        p.add_option("-L", "--log-dir", metavar="NAME",
                action = "store", dest = "log_dir",
                help = "where to store the log files. If not given, defaults to stdout.")

        # FIXME: Add run-script facility.

    def set_option(self):

        Application.set_option(self)

        def make_hostname(node):
            """ Adds hostprefix, if necessary """
            if node.isdigit():
                return self.options.hostprefix + node
            else:
                return node

        def make_pair(line):
            """ Split the line in hosts and add hostprefix if necessary """
            s = map(make_hostname, line.split(' '))
            return (s[0], s[1])

        if len(self.args) >= 2:
            # Use command line parameters as list of hosts
            self.node_list = map(make_hostname, self.args)
        elif len(self.args) == 1:
            # Read list of node pairs from a file
            info("Parsing node pair file")
            self.node_pairs = map(make_pair, open(self.args[0]).readlines)
        else:
            self.parser.error("Incorrect number of arguments. Need either at " \
                    + "least two nodes or one filename!")

    def add_test(self, test):
        self.tests.append(test)

    def run(self):
        m = Measurement2(
                node_list = self.node_list,
                node_pairs = self.node_pairs,
                symmetric = not self.options.asymmetric,
                outer_repeats = self.options.outer_loops,
                inner_repeats = self.options.inner_loops,
                log_dir = self.options.log_dir
                )
        for test in self.tests:
            info("Adding test %s" % test)
            m.add_test(test)

        # Create log directory, if necessary
        log_dir = self.options.log_dir
        if log_dir is not None:
            try:
                info("Creating log_dir.")
                os.makedirs(log_dir)
            except os.error, inst:
                if not (inst.errno == errno.EEXIST and os.path.isdir(log_dir)):
                    error("Failed to creat log_dir!")
                    sys.exit(1)

        m.start()
        reactor.run()



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
