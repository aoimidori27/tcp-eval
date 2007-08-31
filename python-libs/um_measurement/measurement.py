#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import os
from logging import info, debug, warn, error, critical

from twisted.internet import defer, reactor
from twisted.python import log

from um_application import Application
from um_measurement.sshexec import SSHConnectionFactory

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
        """Executes command cmd on host(s), creating a master connection if necessary"""

        # for convenience assume that if host is not string its something to it
        # iterate over        
        if type(host) is not str:
            yield remote_execute_many(self, host, cmd, **kwargs)
        
        if not log_file:
            logfile = self._getNull()
            
        if not self._scf.isConnected(host):
            info("no master connection to %s found creating one..." % host)
            yield self._scf.connect([host])
            
        debug("%s: running %s" %(host,cmd))
        yield self._scf.remoteExecute(host, cmd,
                                      out_fd=log_file,
                                      err_fd=sys.stderr, **kwargs)

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

        # write labels into logfile
        if kwargs.has_key('run_label'):
            log_file.write("run_label:%s\n" %kwargs['run_label'])
            log_file.flush()
        if kwargs.has_key('scenario_label'):
            log_file.write("scenario_label:%s\n" %kwargs['scenario_label'])
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
