#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# Copyright (C) 2010 Carsten Wolff <carsten@wolffcarsten.de>
# Copyright (C) 2010 Andreas Seelinger <Andreas.Seelinger@rwth-aachen.de>
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
import os
import os.path
from logging import debug, warn, error
from sqlite3 import dbapi2 as sqlite
import numpy
import scipy.stats
import sys

# tcp-eval imports
from common.functions import call
from analysis.analysis import Analysis
from visualization.gnuplot import UmGnuplot, UmLinePointPlot, UmLinePlot

class MultipathTCPAnalysis(Analysis):
    """Application for analysis of flowgrind results for multipath tcp."""

    def __init__(self):
        Analysis.__init__(self)

        self.parser.set_usage("Usage:  %prog [options]\n"\
                              "Creates graphs showing thruput, rtt, rtt_min and rtt_max over the "\
                              "variable given by the option -V.\n"\
                              "For this all flowgrind logs out of input folder are used "\
                              "which have the type given by the parameter -T.")

        self.parser.add_option('-V', '--variable', metavar = "Variable",
                        action = 'store', type = 'string', dest = 'variable',
                        help = 'The variable of the measurement [bnbw|delay].')
        self.parser.add_option('-E', '--plot-error', metavar = "PlotError",
                        action = 'store_true', dest = 'plot_error',
                        help = "Plot error bars [default: %default]")
        self.parser.add_option('-s', '--per-subflow', metavar = "Subflows",
                        action = 'store_true', dest = 'per_subflow',
                        help = 'For senarios with mulitple subflows each subflow is '\
                                'ploted seperate instead of an aggregation of all those subflows [default: %default]'),
        self.parser.add_option('-f', '--filter', action = 'append',
                        type = 'int', dest = 'scenarios',
                        help = 'filter the scenarios to be used for a graph', default=[]),

        self.parser.add_option('-d', '--dry-run',
                        action = "store_true", dest = "dry_run",
                        help = "Test the flowlogs only")

        self.plotlabels = dict()
        self.plotlabels["bnbw"]    = r"bottleneck bandwidth [$\\si[per=frac,fraction=nice]{\\Mbps}$]";
        self.plotlabels["qlimit"]  = r"bottleneck queue length [packets]";
        self.plotlabels["rrate"]   = r"reordering rate [$\\si{\\percent}$]";
        self.plotlabels["rdelay"]  = r"reordering delay [$\\si{\\milli\\second}$]";
        self.plotlabels["rtos"]    = r"RTO retransmissions [$\\#$]";
        self.plotlabels["frs"]     = r"fast retransmissions [$\\#$]";
        self.plotlabels["thruput"] = r"throughput [$\\si[per=frac,fraction=nice]{\\Mbps}$]";

        #self.plotlabels["bnbw"]    = r"Bottleneck Bandwidth [$\\si{\\Mbps}$]";
        #self.plotlabels["qlimit"]  = r"Bottleneck Queue Length [packets]";
        #self.plotlabels["rrate"]   = r"Reordering Rate [$\\si{\\percent}$]";
        #self.plotlabels["rdelay"]  = r"Reordering Delay [$\\si{\\milli\\second}$]";
        #self.plotlabels["rtos"]    = r"RTO Retransmissions [$\\#$]";
        #self.plotlabels["frs"]     = r"Fast Retransmissions [$\\#$]";
        #self.plotlabels["thruput"] = r"Throughput [$\\si{\\Mbps}$]";
        self.plotlabels["rtt_max"] = r"Maximal Round Trip Time on Application Layer";
        self.plotlabels["rtt_min"] = r"Minimal Rount Trip Time on Application Layer";
        self.plotlabels["rtt_avg"] = r"Avarage Round Trip Time on Application Layer";
        #self.plotlabels["fairness"]= r"Fairness"
        self.plotlabels["delay"]   = r"RTT [$\\si{\\milli\\second}$]"
        #self.plotlabels["ackreor"] = r"ACK Reordering Rate [$\\si{\\percent}$]"
        #self.plotlabels["ackloss"] = r"ACK Loss Rate [$\\si{\\percent}$]"


    def set_option(self):
        "Set options"
        Analysis.set_option(self)

        if not self.options.variable and not self.options.dry_run:
            error("Please provide me with the variable")
            sys.exit(1)

    def onLoad(self, record, iterationNo, scenarioNo, runNo, test):
        dbcur = self.dbcon.cursor()

        try:
            recordHeader   = record.getHeader()
            src            = recordHeader["flowgrind_src"]
            dst            = recordHeader["flowgrind_dst"]
            scenario_label = recordHeader["scenario_label"]
            variable       = recordHeader["testbed_param_variable"]
        except:
            return

        try:
            qlimit     = int(recordHeader["testbed_param_qlimit"])
        except KeyError:
            qlimit     = "NULL"

        try:
            bnbw       = int(recordHeader["testbed_param_bottleneckbw"])
        except KeyError:
            bnbw       = "NULL"

        try:
            delay      = int(recordHeader["testbed_param_delay"])
        except KeyError:
            delay      = "NULL"

        # test_start_time was introduced later in the header, so its not in old test logs
        try:
            start_time = int(float(recordHeader["test_start_time"]))
        except KeyError:
            start_time = 0

        rtt             = record.calculate("rtt_avg")
        rtt_min         = record.calculate("rtt_min")
        rtt_max         = record.calculate("rtt_max")

        thruput         = record.calculate("thruput_recv")
        flow_ids        = record.calculate("flow_ids");

        if not thruput:
            if not self.failed.has_key(scenario_label):
                self.failed[scenario_label] = 1
            else:
                self.failed[scenario_label] = self.failed[scenario_label] + 1
            return

        if thruput == 0:
            warn("Throughput is 0 in %s!" %record.filename)

        try:
            rtt_min = float(rtt_min)
        except TypeError, inst:
            rtt_min = "NULL"

        try:
            rtt_max = float(rtt_max)
        except TypeError, inst:
            rtt_max = "NULL"

        try:
            rtt = float(rtt)
        except TypeError, inst:
            rtt = "NULL"

        dbcur.execute("""
        INSERT INTO tests VALUES ("%s", %s, %s, %s, %u, "%s", %u, %u, %u, "%s", "%s","%s", %f, %s, %s, %s, %u)
        """ % (variable,  bnbw, qlimit, delay, start_time, scenario_label, iterationNo, scenarioNo, runNo, test, src, dst, thruput, rtt_min, rtt_max, rtt, len(flow_ids)))

        # calculate per flow values
        if len(flow_ids) > 1:
            for flow_id in flow_ids:
                rtt             = record.calculate("rtt_avg_list")[flow_id]
                rtt_min         = record.calculate("rtt_min_list")[flow_id]
                rtt_max         = record.calculate("rtt_max_list")[flow_id]

                thruput         = record.calculate("thruput_recv_list")[flow_id]

                if thruput == 0:
                    warn("Throughput is 0 in %s for subflow!" %(record.filename, flow_id))
                    continue

                try:
                    rtt_min = float(rtt_min)
                except TypeError, inst:
                    rtt_min = "NULL"

                try:
                    rtt_max = float(rtt_max)
                except TypeError, inst:
                    rtt_max = "NULL"

                try:
                    rtt = float(rtt)
                except TypeError, inst:
                    rtt = "NULL"

                dbcur.execute("""
                INSERT INTO single_values VALUES (%u, %u, %u, %u,"%s", %f, %s, %s, %s)
                """ % (iterationNo, scenarioNo, runNo, flow_id, test, thruput, rtt_min, rtt_max, rtt))


    def writeValueTable(self, x, y, scenarioNo, query, filename, cur_max_y_value):
        dbcur = self.dbcon.cursor()
        max_y_value = cur_max_y_value

        debug("\n\n" + query + "\n\n")
        dbcur.execute(query)

        debug("Generating %s..." % filename)
        fhv = file(filename, "w")

        # header
        fhv.write("# %s %s\n" % (x, y))

        # data
        success = False
        for row in dbcur:
            (x_value, y_value) = row
            try:
                if self.options.plot_error:
                    stddev = self.calculateStdDev(y, x_value, scenarioNo)
                    fhv.write("%u %f %f\n" %(x_value, y_value, stddev))
                else:
                    fhv.write("%u %f\n" %(x_value, y_value))
            except TypeError:
                continue
            success = True
            if y_value > max_y_value:
                max_y_value = y_value
        fhv.close()

        return success, max_y_value

    def plotValues(self, plot, title, values, scenarioNo, style):
        debug("plot values with title %s and scenarioNo %u" % (title, scenarioNo))

        if (len(self.options.scenarios) == 0) or (scenarioNo in self.options.scenarios):
            if self.options.plot_error:
                plot.plotYerror(values, title, linestyle = style, using = "1:2:3")
                plot.plot(values, title="", linestyle = style, using = "1:2")
            else:
                plot.plot(values, title, linestyle = style, using = "1:2")

    def generateFilename(self, x, y):
        filename = "%s_over_%s" % (y, x)

        if self.options.per_subflow:
            filename += "_per_subflow"
        if len(self.options.scenarios) != 0:
            for i in self.options.scenarios:
                filename += '_%u' % i
        return filename

    def generateYOverXLinePlot(self, y):
        """Generates a line plot of the DB column y over the DB column x
           reordering rate. One line for each scenario.
        """
        debug("generateYOverXLinePlot with y = %s" % y)

        x = self.options.variable

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

        # get all subflow count
        dbcur.execute('''
            SELECT DISTINCT scenarioNo, flow_count
            FROM tests ORDER BY scenarioNo'''
        )
        count = 0
        subflow_count = dict()
        linestyle = dict()
        for row in dbcur:
            (key,val) = row
            # scenarioNo could not start at 0
            if count == 0:
                count = key + 1
            subflow_count[key] = val
            linestyle[key] = count
            count += val

        outdir = self.options.outdir
        p = UmLinePointPlot(self.generateFilename(x, y), self.options.outdir, self.options.debug)
        #p = UmLinePlot("test_%s_over_%s" % (y, x))
        p.setXLabel(self.plotlabels[x])
        p.setYLabel(self.plotlabels[y])

        max_y_value = 0
        for scenarioNo in scenarios.keys():
            # 1) aggregate the iterations of each run of one scenario under one testbed
            #    configuration by avg() to get the average total y of such flows
            # 2) sum() up these average values of each scenario under one testbed
            #    configuration to get the total average y of one scenario under one
            #    testbed configuration
            if self.options.per_subflow and (subflow_count[scenarioNo] > 1):
                for flow_id in range(subflow_count[scenarioNo]):
                    query = '''
                    SELECT %(x)s, sum(avg_y) AS total_avg_y
                    FROM
                    (
                        SELECT t.%(x)s, t.runNo, avg(s.%(y)s) AS avg_y
                        FROM tests t, single_values s
                        WHERE t.scenarioNo=%(scenarioNo)u AND t.variable='%(x)s'
                            AND t.scenarioNo=s.scenarioNo AND t.iterationNo = s.iterationNo AND t.runNo=s.runNo
                            AND s.flowNo=%(flowNo)u
                        GROUP BY t.%(x)s, t.runNo
                    )
                    GROUP BY %(x)s
                    ORDER BY %(x)s
                    ''' % {'x' : x, 'y' : y, 'scenarioNo' : scenarioNo, 'flowNo' : flow_id}

                    plotname = "%s_over_%s_s%u_f%u" % (y, x, scenarioNo, flow_id)
                    valfilename = os.path.join(outdir, plotname+".values")
                    title = '%s (flow %u)' %(scenarios[scenarioNo], flow_id)

                    success, max_y_value = self.writeValueTable(x, y, scenarioNo, query, valfilename, max_y_value)

                    if success:
                        self.plotValues(p, title, valfilename, scenarioNo, linestyle[scenarioNo] + flow_id)

            else:
                query = '''
                    SELECT %(x)s, sum(avg_y) AS total_avg_y
                    FROM
                    (
                        SELECT %(x)s, runNo, avg(%(y)s) AS avg_y
                        FROM tests
                        WHERE scenarioNo=%(scenarioNo)u AND variable='%(x)s'
                        GROUP BY %(x)s, runNo
                    )
                    GROUP BY %(x)s
                    ORDER BY %(x)s
                ''' % {'x' : x, 'y' : y, 'scenarioNo' : scenarioNo}

                plotname = "%s_over_%s_s%u" % (y, x, scenarioNo)
                valfilename = os.path.join(outdir, plotname+".values")
                title = scenarios[scenarioNo]
                if subflow_count[scenarioNo] > 1:
                    title += ' combined'

                success, max_y_value = self.writeValueTable(x, y, scenarioNo, query, valfilename, max_y_value)

                if success:
                    self.plotValues(p, scenarios[scenarioNo], valfilename, scenarioNo, linestyle[scenarioNo])

        # make room for the legend
        if max_y_value:
            p.setYRange("[*:%u]" % int(max_y_value + ((25 * max_y_value) / 100 )))

        p.save()

    def calculateStdDev(self, y, x_value, scenarioNo):
        """Calculates the standarddeviation for the values of the YoverXPlot
        """

        x = self.options.variable
        dbcur = self.dbcon.cursor()

        query = '''
            SELECT sum(%s) AS sum_y
            FROM tests
            WHERE %s=%u AND scenarioNo=%u AND variable='%s'
            GROUP BY iterationNo
        ''' % (y, x, x_value, scenarioNo, x)

        dbcur.execute(query)
        ary = numpy.array(dbcur.fetchall())
        return ary.std()

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
            CREATE TABLE tests (variable        VARCHAR(15),
                                bnbw            INTEGER,
                                qlimit          INTEGER,
                                delay           INTEGER,
                                start_time      VARCHAR(70),
                                scenario_label  VARCHAR(70),
                                iterationNo     INTEGER,
                                scenarioNo      INTEGER,
                                runNo           INTEGER,
                                test            VARCHAR(50),
                                src             VARCHAR(4),
                                dst             VARCHAR(4),
                                thruput         DOUBLE,
                                rtt_min         DOUBLE,
                                rtt_max         DOUBLE,
                                rtt_avg         DOUBLE,
                                flow_count      INTEGER)
            """)
            dbcur.execute("""
            CREATE TABLE single_values (iterationNo     INTEGER,
                                        scenarioNo      INTEGER,
                                        runNo           INTEGER,
                                        flowNo          INTEGER,
                                        test            VARCHAR(50),
                                        thruput         DOUBLE,
                                        rtt_min         DOUBLE,
                                        rtt_max         DOUBLE,
                                        rtt_avg         DOUBLE)
            """)
            # store failed test as a mapping from run_label to number
            self.failed = dict()
            # only load flowgrind test records
            self.loadRecords(tests=["multiflowgrind"])
            self.dbcon.commit()
        else:
            warn("Database already exists, don't load records.")

        if self.options.dry_run:
            return

        # Do Plots
        for y in ("thruput", "rtt_max","rtt_min","rtt_avg"):
            self.generateYOverXLinePlot(y)


    def main(self):
        """Main method of the ping stats object"""
        self.parse_option()
        self.set_option()
        self.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    MultipathTCPAnalysis().main()
