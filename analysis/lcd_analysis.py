#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# Script to plot various flowgrind_lcd_evaluation.py results.
#
# Copyright (C) 2010 Christian Samsel <christian.samsel@rwth-aachen.de>
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
from logging import info, debug, warn, error
from sqlite3 import dbapi2 as sqlite
import numpy
import scipy.stats

# umic-mesh imports
from um_functions import call
from um_analysis.analysis import Analysis
from um_gnuplot import UmHistogram, UmGnuplot, UmLinePlot, UmBoxPlot

class LCDAnalysis(Analysis):
    """Application for analysis of flowgrind results"""

    def __init__(self):
        Analysis.__init__(self)

    def set_option(self):
        "Set options"
        Analysis.set_option(self)

    def onLoad(self, record, iterationNo, scenarioNo, runNo, test):

        dbcur = self.dbcon.cursor()

        recordHeader = record.getHeader()
        src = recordHeader["flowgrind_src"]
        dst = recordHeader["flowgrind_dst"]
        run_label = recordHeader["run_label"]
        scenario_label = recordHeader["scenario_label"]

        # test_start_time was introduced later in the header, so its not in old test logs
        try:
            start_time = int(float(recordHeader["test_start_time"]))
        except KeyError:
            start_time = 0

        # check if run was completed
        thruput = record.calculate("thruput")
        if not thruput:
            if not self.failed.has_key(run_label):
                self.failed[run_label] = 1
            else:
                self.failed[run_label] = self.failed[run_label]+1
            return

        thruput_recv = record.calculate("thruput_recv")

        # hack to support two parallel flows
        thruput_list = record.calculate("thruput_list")
        if thruput_list:
            thruput_0 = thruput_list[0]
            thruput_1 = thruput_list[1]
        else:
            thruput_0 = thruput_1 = 0.0

        thruput_recv_list = record.calculate("thruput_recv_list")
        if thruput_recv_list:
            thruput_recv_0 = thruput_recv_list[0]
            thruput_recv_1 = thruput_recv_list[1]
        else:
            thruput_recv_0 = thruput_recv_1 = 0.0


        transac_0 = transac_1 = 0
        transac_list = record.calculate(what = "transac_list", optional = True)
        if transac_list and len(transac_list) == 2:
            transac_0 = transac_list[0]
            transac_1 = transac_list[1]

        rtt_min_0 = rtt_min_1 = 0.0
        rtt_min_list = record.calculate(what = "rtt_min_list", optional = True)
        if rtt_min_list and len(rtt_min_list) == 2:
            rtt_min_0 = rtt_min_list[0]
            rtt_min_1 = rtt_min_list[1]

        rtt_avg_0 = rtt_avg_1 = 0.0;
        rtt_avg_list = record.calculate(what = "rtt_avg_list", optional = True)
        if rtt_avg_list and len(rtt_avg_list) == 2:
            rtt_avg_0 = rtt_avg_list[0]
            rtt_avg_1 = rtt_avg_list[1]

        rtt_max_0 = rtt_max_1 = 0.0;
        rtt_max_list = record.calculate(what = "rtt_max_list", optional = True)
        if rtt_max_list and len(rtt_max_list) == 2:
            rtt_max_0 = rtt_max_list[0]
            rtt_max_1 = rtt_max_list[1]

        outages_0 =  outages_1 = 0
        outages = record.calculate(what = "outages", optional = True)
        if outages.has_key(0):
            outages_0 = outages[0]['S']+outages[0]['D']
        if outages.has_key(1):
            outages_1 = outages[1]['S']+outages[1]['D']

        reverts_0 = reverts_1 = 0;
        reverts_list = record.calculate(what = "revert_list", optional = True)
        if reverts_list and len(reverts_list) == 2:
            reverts_0 = reverts_list[0]
            reverts_1 = reverts_list[1]

        dbcur.execute("""
                      INSERT INTO tests VALUES (%u, %u, %u, %s, %s,
                      %f, %f, %f, %f, %f, %f,
                      %f, %f,
                      %f, %f, %f, %f, %f, %f,
                      %u, %u, %u, %u,
                      %u, "$%s$", "%s", "%s")
                      """ % (iterationNo, scenarioNo, runNo, src, dst,
                             thruput, thruput_recv, thruput_0, thruput_1, thruput_recv_0, thruput_recv_1,
                             transac_0, transac_1,
                             rtt_min_0, rtt_min_1, rtt_avg_0, rtt_avg_1, rtt_max_0, rtt_max_1,
                             outages_0, outages_1, reverts_0, reverts_1,
                             start_time, run_label, scenario_label, test))

    def generateTputOverTimePerRun(self):
        """Generates a line plot where every run number gets a
           dedicated line ignoring scenario.
        """ 
        dbcur = self.dbcon.cursor()

        # get runs
        dbcur.execute('''
        SELECT DISTINCT runNo, run_label
        FROM tests ORDER BY runNo'''
        )
        runs = dict()
        for row in dbcur:
            (key,val) = row
            runs[key] = val

        # get all scenario labels
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests ORDER BY scenarioNo'''
        )
        scenarios = dict()
        for row in dbcur:
            (key,val) = row
            scenarios[key] = val

        plotname = "tput_over_time_per_run"
        outdir = self.options.outdir
        valfilename = os.path.join(outdir, plotname+".values")

        outdir = self.options.outdir
        p = UmLinePlot(plotname = plotname, outdir = outdir)
        p.setYLabel(r"\\si{\Mbps}")

        for runNo in runs.keys():
            thruputs = dict()
            times    = dict()

            dbcur.execute('''
            SELECT iterationNo, scenarioNo, thruput, start_time
            FROM tests
            WHERE runNo=%u
            ORDER by iterationNo, scenarioNo ASC
            ''' %(runNo))

            sorted_keys = list()

            for row in dbcur:
                (iterationNo, scenarioNo, thruput, time) = row
                key = (iterationNo,runNo,scenarioNo)
                thruputs[key] = thruput
                if time != 0:
                    times[key] = time
                sorted_keys.append(key)

            plotname = "tput_over_time_per_run_r%u" %(runNo)
            valfilename = os.path.join(outdir, plotname+".values")

            info("Generating %s..." % valfilename)
            fh = file(valfilename, "w")

            # header
            fh.write("# thruput start_time\n")

            # generate values file
            for key in sorted_keys:
                thruput = thruputs[key]
                fh.write("%f %u\n" %(thruput,times[key]))

            fh.close()

            if runNo == 0:
                p.setXLabel("time")
                p.setXDataTime()
                # +1 hour offset to GMT
                time_offset = "+3600"
                using_str = "($2%s):" %time_offset

            p.plot(valfilename, "Throughput "+runs[runNo], linestyle=runNo+1, using=using_str+"1")

        p.save()

    def calculateStdDev(self, rlabel, slabel, key="thruput"):
        """Calculates the standarddeviation of all values of the same rlabel
           and scenarioNo
        """

        dbcur = self.dbcon.cursor()

        query = '''
        SELECT %s FROM tests WHERE
        scenario_label="%s" AND run_label="%s";
        ''' %(key,slabel,rlabel)

        dbcur.execute(query)
        ary = numpy.array(dbcur.fetchall())
        return ary.std()

    def generateOutagesRevertsLCD(self):
        """ Generate a outages and reverts histogram with scenario labels for
        lcd """

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

        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        outages_0, outages_1,
        reverts_0, reverts_1,
        SUM(1) as notests
        FROM tests GROUP BY run_label, scenarioNo ORDER BY outages_0 DESC, scenarioNo ASC
        ''')
        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd_analysis_reverts"
        valfilename  = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        # columns
        keys = scenarios.keys()
        keys.sort()
        for key in scenarios.keys():
            val = scenarios[key]
            fh.write("outages_0_%(v)s outages_1_%(v)s reverts_0_%(v)s reverts_1_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,slabel,sno,
             outages_0, outages_1,
             reverts_0, reverts_1,
             notests) = row

            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0 0 0 0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%d %d %d %d %d" %(
                                 outages_0, outages_1,
                                 reverts_0, reverts_1,
                                 notests)
            debug(row)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        g.setYLabel(r"Outages and Reverts")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+" Outages LCD",
                    using="%u:xtic(1)" %((i*5)+2), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" Outages native",
                    using="%u:xtic(1)" %((i*5)+3), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" Reverts LCD",
                    using="%u:xtic(1)" %((i*5)+4), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" Reverts native",
                    using="%u:xtic(1)" %((i*5)+5), linestyle=(i+1))

        # output plot
        g.save()

    def generateTransacsLCD(self):
        """ Generate a network transactions histogram with scenario labels for
        lcd """

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

        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        AVG(transac_0) as transac_0,
        AVG(transac_1) as transac_1,
        SUM(1) as notests
        FROM tests GROUP BY run_label, scenarioNo ORDER BY transac_0 DESC, scenarioNo ASC
        ''')
        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd_analysis_transactions"
        valfilename  = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        # columns
        keys = scenarios.keys()
        keys.sort()
        for key in scenarios.keys():
            val = scenarios[key]
            fh.write("transac_0_%(v)s transac_1_%(v)s " %{ "v" : val })
            fh.write("std_transac_0_%(v)s std_transac_1_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,slabel,sno,
             transac_0, transac_1,
             notests) = row

            std_transac_0 = self.calculateStdDev(rlabel, slabel, "transac_0")
            std_transac_1 = self.calculateStdDev(rlabel, slabel, "transac_1")

            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%f %f %f %f %d" %(
                                 transac_0, transac_1,
                                 std_transac_0, std_transac_1,
                                 notests)
            debug(row)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        g.setYLabel(r"Network Transactions per Second")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+"  LCD",
                    using="%u:xtic(1)" %((5*i)+2), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" native",
                    using="%u:xtic(1)" %((5*i)+3), linestyle=(i+1))

        # errobars
        for i in range(len(keys)):
            # TODO: calculate offset with scenarios and gap
            if i == 0:
                g.plotErrorbar(valfilename, 0, 2, 4, "Standard Deviation")
                g.plotErrorbar(valfilename, 1, 3, 5)

            else:
                g.plotErrorbar(valfilename, i*2,   (i*5)+2, (i*5)+4)
                g.plotErrorbar(valfilename, i*2+1, (i*5)+3, (i*5)+5)

        g.save()

    def generateTputHistogramLCD(self):
        """ Generates a tput histogram with scenario labels for lcd """

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

        # average thruput and sort by it and scenario_no
        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        AVG(thruput_0) as thruput_0,
        AVG(thruput_1) as thruput_1,
        AVG(thruput_recv_0) as thruput_recv_0,
        AVG(thruput_recv_1) as thruput_recv_1,
        SUM(1) as notests
        FROM tests GROUP BY run_label, scenarioNo ORDER BY thruput_0 DESC, scenarioNo ASC
        ''')

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd_analysis_throughput"
        valfilename  = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        # columns
        keys = scenarios.keys()
        keys.sort()
        for key in scenarios.keys():
            val = scenarios[key]
            fh.write("tput_0_%(v)s tput_1_%(v)s tput_recv_0_%(v)s tput_recv_1_%(v)s " %{ "v" : val })
            fh.write("std_tput_0_%(v)s std_tput_1_%(v)s std_tput_recv_0_%(v)s std_tput_recv_1_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,slabel,sno,
             thruput_0, thruput_1,
             thruput_recv_0, thruput_recv_1,
             notests) = row

            std_thruput_0 = self.calculateStdDev(rlabel, slabel, "thruput_0")
            std_thruput_1 = self.calculateStdDev(rlabel, slabel, "thruput_1")

            std_thruput_recv_0 = self.calculateStdDev(rlabel, slabel, "thruput_recv_0")
            std_thruput_recv_1 = self.calculateStdDev(rlabel, slabel, "thruput_recv_1")

            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%f %f %f %f %f %f %f %f %d" %(
                                 thruput_0,thruput_1,thruput_recv_0,thruput_recv_1,
                                 std_thruput_0,std_thruput_1,std_thruput_recv_0,std_thruput_recv_1,
                                 notests)
            debug(row)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        g.setYLabel(r"Throughput in $\\si{\Mbps}$")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+" TCP LCD out",
                    using="%u:xtic(1)" %( (i*9)+2 ), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" TCP LCD in",
                    using="%u:xtic(1)" %( (i*9)+4 ), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" native out",
                    using="%u:xtic(1)" %( (i*9)+3 ), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" native in",
                    using="%u:xtic(1)" %( (i*9)+5 ), linestyle=(i+1))

        # errobars
        for i in range(len(keys)):
            # TODO: calculate offset with scenarios and gap
            if i == 0:
                g.plotErrorbar(valfilename, 0, 2, 6, "Standard Deviation")
                g.plotErrorbar(valfilename, 1, 4, 7)
                g.plotErrorbar(valfilename, 2, 3, 8)
                g.plotErrorbar(valfilename, 3, 5, 9)

            else:
                g.plotErrorbar(valfilename, i*4,   (i*9)+2, (i*9)+6)
                g.plotErrorbar(valfilename, i*4+1, (i*9)+4, (i*9)+8)
                g.plotErrorbar(valfilename, i*4+2, (i*9)+3, (i*9)+7)
                g.plotErrorbar(valfilename, i*4+3, (i*9)+5, (i*9)+9)

        # output plot
        g.save()

    def generateTputDiffHistogramLCD(self):
        """ Generates a tput histogram with scenario labels for lcd """

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

        # average thruput and sort by it and scenario_no
        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        AVG(thruput_0-thruput_1) as thruput_diff,
        AVG(thruput_recv_0-thruput_recv_1) as thruput_diff_recv,
        SUM(1) as notests
        FROM tests GROUP BY run_label, scenarioNo ORDER BY thruput DESC, scenarioNo ASC
        ''')

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd_analysis_throughput_improvement"
        valfilename  = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        # columns
        keys = scenarios.keys()
        keys.sort()
        for key in scenarios.keys():
            val = scenarios[key]
            fh.write("tput_diff_%(v)s tput_diff_recv_%(v)s " %{ "v" : val })
            fh.write("std_tput_diff_%(v)s std_tput_diff_recv_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,slabel,sno,
             thruput_diff, thruput_diff_recv,
             notests) = row

            std_thruput_diff = self.calculateStdDev(rlabel, slabel, "thruput_0-thruput_1")
            std_thruput_diff_recv = self.calculateStdDev(rlabel, slabel, "thruput_recv_0-thruput_recv_1")

            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%f %f %f %f %d" %(
                                 thruput_diff,thruput_diff_recv,
                                 std_thruput_diff,std_thruput_diff_recv,
                                 notests)
            debug(row)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        g.setYLabel(r"Throughput Improvement for TCP LCD in $\\si{\Mbps}$")
        # g.setClusters(len(keys))
        g.setYRange("[ * : * ]")
        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+" out",
                    using="%u:xtic(1)" %( (i*5)+2 ), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" in",
                    using="%u:xtic(1)" %( (i*5)+3 ), linestyle=(i+1))

        # errobars
        for i in range(len(keys)):
            # TODO: calculate offset with scenarios and gap
            if i == 0:
                g.plotErrorbar(valfilename, 0, 2, 4, "Standard Deviation")
                g.plotErrorbar(valfilename, 1, 3, 5)

            else:
                g.plotErrorbar(valfilename, (i*2)+0, (i*5)+2, (i*5)+4)
                g.plotErrorbar(valfilename, (i*2)+1, (i*5)+3, (i*5)+5)

        # output plot
        g.save()

    def run(self):
        """Main Method"""

        # database in memory to access data efficiently
        self.dbcon = sqlite.connect(':memory:')
        dbcur = self.dbcon.cursor()
        dbcur.execute("""
        CREATE TABLE tests (iterationNo     INTEGER,
                            scenarioNo      INTEGER,
                            runNo           INTEGER,
                            src             INTEGER,
                            dst             INTEGER,
                            thruput         DOUBLE,
                            thruput_recv    DOUBLE,
                            thruput_0       DOUBLE,
                            thruput_1       DOUBLE,
                            thruput_recv_0  DOUBLE,
                            thruput_recv_1  DOUBLE,
                            transac_0       DOUBLE,
                            transac_1       DOUBLE,
                            rtt_min_0       DOUBLE,
                            rtt_min_1       DOUBLE,
                            rtt_avg_0       DOUBLE,
                            rtt_avg_1       DOUBLE,
                            rtt_max_0       DOUBLE,
                            rtt_max_1       DOUBLE,
                            outages_0       INTEGER,
                            outages_1       INTEGER,
                            reverts_0       INTEGER,
                            reverts_1       INTEGER,
                            start_time      INTEGER,
                            run_label   VARCHAR(70),
                            scenario_label VARCHAR(70),
                            test        VARCHAR(50))
        """)

        # store failed test as a mapping from run_label to number
        self.failed = dict()

        # only load flowgrind test records
        self.loadRecords(tests=["flowgrind"])

        self.dbcon.commit()
        self.generateTputOverTimePerRun()
        self.generateOutagesRevertsLCD()
        self.generateTransacsLCD()
        self.generateTputHistogramLCD()
        self.generateTputDiffHistogramLCD()
    def main(self):
        """Main method of the the LCD Analysis script"""

        self.parse_option()
        self.set_option()
        LCDAnalysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    LCDAnalysis().main()

