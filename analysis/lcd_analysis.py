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
            if outages[0].has_key('S'):
                outages_0 += outages[0]['S']
            if outages[0].has_key('D'):
                outages_0 += outages[0]['D']
        if outages.has_key(1):
            if outages[1].has_key('S'):
                outages_1 += outages[1]['S']
            if outages[1].has_key('D'):
                outages_1 += outages[1]['D']


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

            using_str = ""
            if runNo == 0:
                p.setXLabel("time")
                p.setXDataTime()
                # +1 hour offset to GMT
                time_offset = "+3600"
                using_str = "($2%s):" %time_offset

            p.plot(valfilename, "Throughput "+runs[runNo], linestyle=runNo+1, using=using_str+"1")

        p.save()

    def calculateStdDev(self, rlabel=None, slabel=None, key="thruput"):
        """Calculates the standarddeviation of all values of the same rlabel
           and scenarioNo
        """

        dbcur = self.dbcon.cursor()

        where = ""
        if rlabel or slabel:
            where += 'WHERE '
        if slabel:
            where += ' scenario_label="%s" '
        if slabel and rlabel:
            where += ' AND '
        if rlabel:
            where += ' run_label="%s"'

        query = '''
        SELECT %s FROM tests %s;
        ''' %(key,where)

        dbcur.execute(query)
        ary = numpy.array(dbcur.fetchall())
        return ary.std()

    def generateOutagesRevertsLCD(self):
        """ Generate a outages and reverts histogram with scenario labels for
        lcd """

        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT run_label,
        AVG(outages_0) as outages_0, AVG(outages_1) as outages_1,
        AVG(reverts_0) as reverts_0, AVG(reverts_1) as reverts_1,
        AVG(thruput_0+thruput_1) as thruput_overall,
        SUM(1) as notests
        FROM tests
        GROUP BY run_label
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')
        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-reverts"
        valfilename  = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        fh.write("outages_0 outages_1 reverts_0 reverts_1 ")
        fh.write("std_outages_0 std_outages_1 std_reverts_0 std_reverts_1 ")
        fh.write("notests")
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,
             outages_0, outages_1,
             reverts_0, reverts_1,
             thrput_overall,
             notests) = row

            debug(row)
            std_outages_0 = self.calculateStdDev(key="outages_0")
            std_outages_1 = self.calculateStdDev(key="outages_1")
            std_reverts_0 = self.calculateStdDev(key="reverts_0")
            std_reverts_1 = self.calculateStdDev(key="reverts_1")

            if not data.has_key(rlabel):
                data[rlabel] = "0 0 0 0 0 0 0 0 0"

            data[rlabel] = "%d %d %d %d %d %d %d %d %d" %(
                                 outages_0, outages_1,
                                 reverts_0, reverts_1,
                                 std_outages_0, std_outages_1,
                                 std_reverts_0, std_reverts_1,
                                 notests)

            sorted_labels.append(rlabel)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            fh.write(" %s" %value)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        g.setYLabel(r"Outages and Reverts")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        g.plotBar(valfilename, title="Outages LCD", using="2:xtic(1)", linestyle=1,fillstyle="solid 0.7")
        g.plotBar(valfilename, title="Outages native", using="3:xtic(1)", linestyle=1)
        g.plotBar(valfilename, title="Reverts LCD", using="4:xtic(1)", linestyle=2,fillstyle="solid 0.7")
        g.plotBar(valfilename, title="Reverts native", using="5:xtic(1)", linestyle=2)

        # errobars
        g.plotErrorbar(valfilename, 0, 2, 6, "Standard Deviation")
        g.plotErrorbar(valfilename, 1, 3, 7)
        g.plotErrorbar(valfilename, 2, 4, 8)
        g.plotErrorbar(valfilename, 3, 5, 9)

        # output plot
        g.save()

    def generateRTTLCD(self):
        """ Generate a RTT histogram with scenario labels for
        lcd """

        dbcur = self.dbcon.cursor()

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-rtt"
        valfilename  = os.path.join(outdir, plotname+".values")

        # get all scenario labels
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests
        WHERE rtt_avg_0 > 0
        ORDER BY scenarioNo'''
        )
        scenarios = list()
        for row in dbcur:
            (key,val) = row
            scenarios.append(val)

        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        AVG(rtt_min_0) as rtt_min_0,
        AVG(rtt_avg_0) as rtt_avg_0,
        AVG(rtt_max_0) as rtt_max_0,
        AVG(rtt_min_1) as rtt_min_1,
        AVG(rtt_avg_1) as rtt_avg_1,
        AVG(rtt_max_1) as rtt_max_1,
        AVG(thruput_0+thruput_1) as thruput_overall,
        SUM(1) as notests
        FROM tests
        WHERE rtt_avg_0 > 0
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        # columns
        for val in scenarios:
            fh.write("rtt_min_0_%(v)s rtt_avg_0_%(v)s rtt_max_0_%(v)s" %{ "v" : val })
            fh.write("rtt_min_1_%(v)s rtt_avg_1_%(v)s rtt_max_1_%(v)s" %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        for row in dbcur:
            (rlabel,slabel,sno,
             rtt_min_0, rtt_avg_0, rtt_max_0,
             rtt_min_1, rtt_avg_1, rtt_max_1,
             thruput_overall,
             notests) = row

            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0 0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f %f %f %f %f %d" %(
                 rtt_min_0, rtt_avg_0, rtt_max_0,
                 rtt_min_1, rtt_avg_1, rtt_max_1,
                 notests)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        g.setYLabel(r"RTT")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # plot min/avg/mag as errorbars
        for i in range(len(scenarios)):
            g.plotErrorbar(valfilename, (i*2)+0, (i*7)+3, (i*7)+2,
                    title=scenarios[i]+" LCD", linestyle=(i+1), yHigh=(i*7)+4)
            g.plotErrorbar(valfilename, (i*2)+1, (i*7)+7, (i*7)+6,
                    title=scenarios[i]+" native", linestyle=(i+1),  yHigh=(i*7)+8)
        g.save()

    def generateTransacsLCD(self):
        """ Generate a network transactions histogram with scenario labels for
        lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-transactions"
        valfilename  = os.path.join(outdir, plotname+".values")

        dbcur = self.dbcon.cursor()

        # get all scenario labels
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests
        WHERE transac_0 > 0
        ORDER BY scenarioNo'''
        )
        scenarios = list()
        for row in dbcur:
            (key,val) = row
            scenarios.append(val)

        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
               AVG(transac_0) as transac_0,
               AVG(transac_1) as transac_1,
               AVG(thruput_0+thruput_1) as thruput_overall,
               SUM(1) as notests
        FROM tests
        WHERE transac_0 > 0
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # columns
        for val in scenarios:
            fh.write("transac_0_%(v)s transac_1_%(v)s " %{ "v" : val })
            fh.write("std_transac_0_%(v)s std_transac_1_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        for row in dbcur:
            (rlabel,slabel,sno,
             transac_0, transac_1,
             thruput_overall,
             notests) = row

            std_transac_0 = self.calculateStdDev(rlabel, slabel, "transac_0")
            std_transac_1 = self.calculateStdDev(rlabel, slabel, "transac_1")

            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f %f %f %d" %(
                                 transac_0, transac_1,
                                 std_transac_0, std_transac_1,
                                 notests
                                 )

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
        for i in range(len(scenarios)):
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[i]+" LCD",
                    using="%u:xtic(1)" %((5*i)+2), linestyle=(i+1), fillstyle="solid 0.7")
            g.plotBar(valfilename, title=scenarios[i]+" native",
                    using="%u:xtic(1)" %((5*i)+3), linestyle=(i+1))

        # errobars
        for i in range(len(scenarios)):
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
        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-throughput"
        valfilename  = os.path.join(outdir, plotname+".values")

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
        AVG(thruput_0+thruput_recv_0) as thruput_0,
        AVG(thruput_1+thruput_recv_1) as thruput_1,
        AVG(thruput_0+thruput_1) as thruput_overall,
        SUM(1) as notests
        FROM tests
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

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
            fh.write("tput_0_%(v)s tput_1_%(v)s " %{ "v" : val })
            fh.write("std_tput_0_%(v)s std_tput_1_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,slabel,sno,
             thruput_0, thruput_1,
             thruput_overall,
             notests) = row

            debug(row)

            std_thruput_0 = self.calculateStdDev(rlabel, slabel, "thruput_0")
            std_thruput_1 = self.calculateStdDev(rlabel, slabel, "thruput_1")

            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%f %f %f %f %d" %(
                                 thruput_0,thruput_1,
                                 std_thruput_0,std_thruput_1,
                                 notests)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        #g.gplot('set xtics nomirror rotate by -45 scale 0')
        g.setYLabel(r"Throughput in $\\si{\Mbps}$")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+" LCD",
                    using="%u:xtic(1)" %( (i*5)+2 ), linestyle=(i+1), fillstyle="solid 0.7")
            g.plotBar(valfilename, title=scenarios[key]+" native",
                    using="%u:xtic(1)" %( (i*5)+3 ), linestyle=(i+1))

        g.plot("newhistogram ''")
        # errobars
        for i in range(len(keys)):
        # TODO: calculate offset with scenarios and gap
            if i == 0:
                g.plotErrorbar(valfilename, 0, 2, 4, "Standard Deviation")
                g.plotErrorbar(valfilename, 1, 3, 5)
            else:
                g.plotErrorbar(valfilename, i*2,   (i*5)+2, (i*5)+4)
                g.plotErrorbar(valfilename, i*2+1, (i*5)+3, (i*5)+5)

        # output plot
        g.save()

    def generateTputImprovementHistogramLCD(self):
        """ Generates a tput histogram with scenario labels for lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-throughput-improvement"
        valfilename  = os.path.join(outdir, plotname+".values")

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
        AVG((thruput_0/thruput_1)-1)*100 as thruput_diff,
        AVG(COALESCE((thruput_recv_0/thruput_recv_1),1)-1)*100 as thruput_diff_recv,
        AVG(thruput_0+thruput_1) as thruput_overall,
        SUM(1) as notests
        FROM tests
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # columns
        keys = scenarios.keys()
        keys.sort()
        for key in scenarios.keys():
            val = scenarios[key]
            fh.write("tput_diff_%(v)s tput_diff_recv_%(v)s " %{ "v" : val })
            fh.write("std_tput_diff_%(v)s std_tput_diff_recv_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        for row in dbcur:
            (rlabel,slabel,sno,
             thruput_diff, thruput_diff_recv,
             thruput_overall,
             notests) = row

            debug(row)

            std_thruput_diff = self.calculateStdDev(rlabel, slabel,
                    "(COALESCE(thruput_0/thruput_1,1)-1)*100")
            std_thruput_diff_recv = self.calculateStdDev(rlabel, slabel,
                    "(COALESCE(thruput_recv_0/thruput_recv_1,1)-1)*100")

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

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir)
        g.setYLabel(r"Throughput Improvement for TCP LCD in $\\si{\percent}$")
        # g.setClusters(len(keys))
        g.setYRange("[ * : * ]")
        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+" out",
                    using="%u:xtic(1)" %( (i*5)+2 ), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" in",
                    using="%u:xtic(1)" %( (i*5)+3 ), linestyle=(i+1),
                    fillstyle="pattern 2")

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
        self.generateTputHistogramLCD()
        self.generateTputImprovementHistogramLCD()
        self.generateOutagesRevertsLCD()
        self.generateTransacsLCD()
        self.generateRTTLCD()
        # self.generateTputOverTimePerRun()
        for key in self.failed:
            warn("%d failed tests for %s" %(self.failed[key],key))

    def main(self):
        """Main method of the the LCD Analysis script"""

        self.parse_option()
        self.set_option()
        LCDAnalysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    LCDAnalysis().main()

