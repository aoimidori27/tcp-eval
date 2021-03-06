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
import sys
import os
import os.path
import re
from logging import info, debug, warn, error

# tcp-eval imports
from common.application import Application
from common.functions import call
from testrecordfactory import TestRecordFactory
#from config import *

class Analysis(Application):
    """Framework for UMIC-Mesh analysis"""

    def __init__(self):

        # object variables
        self.action = ''
        self.analysis = 'none'
        self.factory = TestRecordFactory()

        # create top-level parser
        Application.__init__(self)
        self.parser.add_argument('-N', '--nodes', metavar="Nodes",
                        action = 'store', type=int, dest = 'nodes',
                        help = 'Limit range of mrouters covered [default: unset]')
        self.parser.add_argument('-I', '--iterations', metavar="n",
                        action = 'store', type=int, dest = 'iterations',
                        help = 'Limit to the first n iterations that were run in a row [default: unset]')
        self.parser.add_argument('-R', '--runs', metavar="r",
                        action = 'store', type=int, dest = 'runs',
                        help = 'Limit to the first r of test runs that were performed in a row [default: unset]')
        self.parser.add_argument('-D', '--input-directory', metavar="InDir", default="./",
                        action = 'store', type=str, dest = 'indir',
                        help = 'Set directory which contains the measurement results [default: %(default)s]')
        self.parser.add_argument('-O', '--output', metavar="OutDir", default="./",
                        action = 'store', type=str, dest = 'outdir',
                        help = 'Set outputdirectory [default: %(default)s]')
        self.parser.add_argument("-c", "--cfg", metavar = "FILE",
                        action = "store", dest = "cfgfile",
                        help = "use the file as config file for LaTeX. "\
                               "No default packages will be loaded.")
        self.parser.add_argument("--save", action = "store_true", dest = "save",
                        help = "save gnuplot and tex files [default: clean up]")
        self.parser.add_argument("-f", "--force",
                        action = "store_true", dest = "force",
                        help = "overwrite existing output")

    def apply_options(self):
        """Configure object based on the options form the argparser"""

        Application.apply_options(self)

        if not os.path.exists(self.args.indir):
            error("%s does not exist, stop." %self.args.indir)
            sys.exit(1)

        if not os.path.exists(self.args.outdir):
            info("%s does not exist, creating. " % self.args.outdir)
            os.mkdir(self.args.outdir)

    def process(self):
        """Processing of the gathered data"""
        pass

    def onLoad(self, record, iterationNo, scenarioNo, runNo, test):
        pass

    def loadRecords(self, onLoad = None, tests = None):
        """This function creates testrecords from test log files
           the onLoad function is called with, TestRecord, testname iterationNo
           and scenarioNo. If tests is set only records for these tests are
           created.  """

        if not onLoad:
            onLoad = self.onLoad

        info("Loading records...")

        # testnames are only valid with plain text and numbers
        regex = re.compile("^i(\d+)_s(\d+)_r(\d+)_test_(\w+)$")
        count = 0
        failed = []

        for root, dirs, files in os.walk(self.args.indir):
            debug("Processing %s" %root)
            for name in files:
                entry = os.path.join(root, name)
                match = regex.match(name)
                if match:
                    groups = match.groups()
                    iterationNo = int(groups[0])
                    scenarioNo  = int(groups[1])
                    runNo       = int(groups[2])
                    test        = groups[3]

                    # filter tests
                    if tests and not test in tests:
                        continue

                    count += 1
                    debug("Processing %s" %entry)
                    record = self.factory.createRecord(entry,test)

                    # call hook
                    onLoad(record, iterationNo, scenarioNo, runNo, test)

        if (count == 0):
            warn('Found no log records in "%s" Stop.' %self.args.indir)
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

        self.parse_options()
        self.apply_options()
        Analysis.run(self)


# this only runs if the module was *not* imported
if __name__ == '__main__':
    Analysis().main()

