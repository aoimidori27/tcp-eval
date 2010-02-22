#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# python imports
import os
import os.path
from logging import info, debug, warn, error
from sqlite3 import dbapi2 as sqlite
import numpy
import scipy.stats
import sys

# umic-mesh imports
from um_functions import call
from um_analysis.analysis import Analysis
from um_gnuplot import UmHistogram, UmGnuplot, UmLinePlot, UmBoxPlot

class ReorderingAnalysis(Analysis):
    """Application for analysis of flowgrind results.
       It needs flowlogs produced by the -tcp-more-info branch to fully work.
       Usually, you won't call this app directly, but use
       vmesh_dumbbell_flowgrind_complete_test.pl instead."""

    def __init__(self):
        Analysis.__init__(self)
        self.parser.add_option('-V', '--variable', metavar="Variable",
                         action = 'store', type = 'string', dest = 'variable',
                         help = 'The variable of the measurement [qlimit|rrate|rdelay].')
        self.parser.add_option('-T', '--type', metavar="Type",
                         action = 'store', type = 'string', dest = 'rotype',
                         help = 'The type of the measurement [reordering|congestion|both].')

        self.plotlabels = dict()
        self.plotlabels["qlimit"]  = r"bottleneck queue length [packets]";
        self.plotlabels["rrate"]   = r"reordering rate [$\\si{\\percent}$]";
        self.plotlabels["rdelay"]  = r"reordering delay [$\\si{\\milli\\second}$]";
        self.plotlabels["rtos"]    = r"RTO retransmissions [$\\#$]";
        self.plotlabels["frs"]     = r"fast retransmissions [$\\#$]";
        self.plotlabels["thruput"] = r"throughput [$\\si[per=frac,fraction=nice]{\\Mbps}$]";


    def set_option(self):
        "Set options"
        Analysis.set_option(self)

        if not self.options.variable:
            error("Please provide me with the variable and type of the measurement!")
            sys.exit(1)
        if self.options.variable != "rrate" and self.options.variable != "rdelay" and self.options.variable != "qlimit":
            error("I did not recognize the variable you gave me!")
            sys.exit(1)
        if self.options.rotype != "reordering" and self.options.rotype != "congestion" and self.options.rotype != "both":
            error("I did not recognize the type you gave me!")
            sys.exit(1)


    def onLoad(self, record, iterationNo, scenarioNo, runNo, test):
        dbcur = self.dbcon.cursor()

        recordHeader = record.getHeader()
        src            = recordHeader["flowgrind_src"]
        dst            = recordHeader["flowgrind_dst"]
        run_label      = recordHeader["run_label"]
        scenario_label = recordHeader["scenario_label"]
        variable       = recordHeader["testbed_param_variable"]
        reordering     = recordHeader["testbed_param_reordering"]
        qlimit         = int(recordHeader["testbed_param_qlimit"])
        rrate          = int(recordHeader["testbed_param_rrate"])
        rdelay         = int(recordHeader["testbed_param_rdelay"])

        # test_start_time was introduced later in the header, so its not in old test logs
        try:
            start_time = int(float(recordHeader["test_start_time"]))
        except KeyError:
            start_time = 0

        rtos           = int(record.calculate("total_rto_retransmits"))
        frs            = int(record.calculate("total_fast_retransmits"))
        thruput        = record.calculate("thruput")
        if not thruput:
            if not self.failed.has_key(run_label):
                self.failed[run_label] = 1
            else:
                self.failed[run_label] = self.failed[run_label]+1
            return

        dbcur.execute("""
                      INSERT INTO tests VALUES ("%s", "%s", %u, %u, %u, %u, %u, %u, %u, %u, "%s", "%s", %f, %u, "$%s$", "%s", "%s")
                      """ % (variable, reordering, qlimit, rrate, rdelay, rtos, frs, iterationNo, scenarioNo, runNo, src, dst, thruput,
                             start_time, run_label, scenario_label, test))


    def generateYOverXLinePlot(self, y):
        """Generates a line plot of the DB column y over the DB column x
           reordering rate. One line for each scenario.
        """

        x      = self.options.variable
        rotype = self.options.rotype

        dbcur = self.dbcon.cursor()

        # get all scenario labels
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests ORDER BY scenarioNo'''
        )
        scenarios = dict()
        for row in dbcur:
            (key,val) = row
            scenarios[key] = val

        dbcur = self.dbcon.cursor()

        outdir = self.options.outdir
        p = UmLinePlot("%s_over_%s" % (y, x))
        p.setXLabel(self.plotlabels[x])
        p.setYLabel(self.plotlabels[y])

        for scenarioNo in scenarios.keys():
            # first, aggregate the parallel runs by sum() to get the total y of a single iteration
            # second, aggregate the iterations by avg() to get the average total y of one test
            dbcur.execute('''
            SELECT %s, avg(total_y) AS avg_total_y
            FROM
            (
                SELECT %s, iterationNo, sum(%s) AS total_y
                FROM tests
                WHERE scenarioNo=%u AND variable='%s' AND reordering='%s'
                GROUP BY iterationNo
            )
            GROUP BY %s
            ORDER BY %s
            ''' % (x, x, y, scenarioNo, x, rotype, x, x))

            plotname = "%s_over_%s_s%u" % (y, x, scenarioNo)
            valfilename = os.path.join(outdir, plotname+".values")

            info("Generating %s..." % valfilename)
            fhv = file(valfilename, "w")

            # header
            fhv.write("# %s %s\n" % (x, y))

            # data
            for row in dbcur:
                (x_value, y_value) = row
                fhv.write("%u %f\n" %(x_value, y_value))
            fhv.close()

            p.plot(valfilename, scenarios[scenarioNo], linestyle=scenarioNo + 1, using="1:2")

        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)


    def run(self):
        """Main Method"""

        # bring up database
        dbexists = False
        if os.path.exists('data.sqlite'):
            dbexists = True
        self.dbcon = sqlite.connect('data.sqlite')

        if not dbexists:
            dbcur = self.dbcon.cursor()
            dbcur.execute("""
            CREATE TABLE tests (variable    VARCHAR(15),
                                reordering  VARCHAR(15),
                                qlimit      INTEGER,
                                rrate       INTEGER,
                                rdelay      INTEGER,
                                rtos        INTEGER,
                                frs         INTEGER,
                                iterationNo INTEGER,
                                scenarioNo  INTEGER,
                                runNo       INTEGER,
                                src         INTEGER,
                                dst         INTEGER,
                                thruput     DOUBLE,
                                start_time  INTEGER,
                                run_label   VARCHAR(70),
                                scenario_label VARCHAR(70),
                                test        VARCHAR(50))
            """)
            # store failed test as a mapping from run_label to number
            self.failed = dict()
            # only load flowgrind test records
            self.loadRecords(tests=["flowgrind"])
            self.dbcon.commit()

        # Do Plots
        for y in ("thruput", "frs", "rtos"):
            self.generateYOverXLinePlot(y)


    def main(self):
        """Main method of the ping stats object"""

        self.parse_option()
        self.set_option()
        ReorderingAnalysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    ReorderingAnalysis().main()
