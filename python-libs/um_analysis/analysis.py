#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys
import os
import os.path
import subprocess
import re
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_config import *
from um_functions import call
from testrecordfactory import TestRecordFactory

class Analysis(Application):
    """Framework for UMIC-Mesh analysis"""

    def __init__(self):
        Application.__init__(self)

        # object variables
        self.action = ''
        self.analysis = 'none'
        self.factory = TestRecordFactory()

        # initialization of the option parser
        usage = "usage: %prog [options]"

        self.parser.set_usage(usage)
        self.parser.set_defaults(outdir = "./", indir = "./");

        self.parser.add_option('-N', '--nodes', metavar="Nodes",
                        action = 'store', type = 'int', dest = 'nodes',
                        help = 'Limit range of mrouters covered [default: unset]')
        self.parser.add_option('-I', '--iterations', metavar="n",
                        action = 'store', type = 'int', dest = 'iterations',
                        help = 'Limit to the first n iterations that were run in a row [default: unset]')
        self.parser.add_option('-R', '--runs', metavar="r",
                        action = 'store', type = 'int', dest = 'runs',
                        help = 'Limit to the first r of test runs that were performed in a row [default: unset]')
        self.parser.add_option('-D', '--input-directory', metavar="InDir",
                        action = 'store', type = 'string', dest = 'indir',
                        help = 'Set directory which contains the measurement results [default: %default]')
        self.parser.add_option('-O', '--output', metavar="OutDir",
                        action = 'store', type = 'string', dest = 'outdir',
                        help = 'Set outputdirectory [default: %default]')

        self.parser.add_option("-c", "--cfg", metavar = "FILE",
                        action = "store", dest = "cfgfile",
                        help = "use the file as config file for LaTeX. "\
                               "No default packages will be loaded.")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        if not os.path.exists(self.options.indir):
            error("%s does not exist, stop." %self.options.indir)
            sys.exit(1)

        if not os.path.exists(self.options.outdir):
            info("%s does not exist, creating. " % self.options.outdir)
            os.mkdir(self.options.outdir)

    def process(self):
        """Processing of the gathered data"""
        pass

    def onLoad(self, record, iterationNo, scenarioNo, runNo, test):
        pass

    def loadRecords(self, onLoad = None, tests = None):
        """ This function creates testrecords from test log files
            the onLoad function is called with, TestRecord, testname
            iterationNo and scenarioNo.
            If tests is set only records for these tests are created.
        """

        if not onLoad:
            onLoad = self.onLoad

        info("Loading records...")

        # testnames are only valid with plain text and numbers
	    regex = re.compile("^i(\d+)_s(\d+)_r(\d+)_(\w+)$")
        count = 0
        failed = []

        for entry in os.listdir(self.options.indir):
            match = regex.match(entry)
            if match:
                groups = match.groups()
                iterationNo = int(groups[0])
                scenarioNo  = int(groups[1])
                runNo       = int(groups[2])
                test	    = groups[3]

                # filter tests
                if tests and not test in tests:
                    continue

                count += 1
                debug("Processing %s" %entry)
                entry = "%s/%s" %(self.options.indir, entry)
                record = self.factory.createRecord(entry,test)

                # call hook
                onLoad(record, iterationNo, scenarioNo, runNo, test)

        if (count == 0):
            warn('Found no log records in "%s" Stop.' %self.options.indir)
            sys.exit(0)
        else:
            info('Found %d test records.' %count)
            if failed:
                warn('some files failed: %s' %failed)

    def run(self):
        """Main Method"""
        raise NotImplementedError

    def main(self):
        """Main method of the ping stats object"""

        self.parse_option()
        self.set_option()
        Analysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    Analysis().main()

