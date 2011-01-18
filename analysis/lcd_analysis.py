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
from um_application import Application

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

        try:
            start_time = int(float(recordHeader["test_start_time"]))
        except KeyError:
            start_time = 0

        thruput = record.calculate("thruput")
        thruput_recv = record.calculate("thruput_recv")

        # hack to support two parallel flows
        thruput_list = record.calculate("thruput_list")
        if thruput_list and thruput_list[0] > 0 and thruput_list[1] > 0:
            thruput_0 = thruput_list[0]
            thruput_1 = thruput_list[1]

        # mark test as failed if at least one thruput is zero
        else:
            if not self.failed.has_key(run_label):
                self.failed[run_label] = 1
            else:
                self.failed[run_label] = self.failed[run_label]+1
            return

        thruput_recv_list = record.calculate("thruput_recv_list")
        if thruput_recv_list:
            thruput_recv_0 = thruput_recv_list[0]
            thruput_recv_1 = thruput_recv_list[1]
        else:
            thruput_recv_0 = thruput_recv_1 = 0.0

        # network transactions
        transac_0 = transac_1 = 0
        transac_list = record.calculate(what = "transac_list", optional = True)
        if transac_list and len(transac_list) == 2:
            transac_0 = transac_list[0]
            transac_1 = transac_list[1]

        # rtt
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

        # iat
        iat_min_0 = iat_min_1 = 0.0
        iat_min_list = record.calculate(what = "iat_min_list", optional = True)
        if iat_min_list and len(iat_min_list) == 2:
            iat_min_0 = iat_min_list[0]
            iat_min_1 = iat_min_list[1]

        iat_avg_0 = iat_avg_1 = 0.0;
        iat_avg_list = record.calculate(what = "iat_avg_list", optional = True)
        if iat_avg_list and len(iat_avg_list) == 2:
            iat_avg_0 = iat_avg_list[0]
            iat_avg_1 = iat_avg_list[1]

        iat_max_0 = iat_max_1 = 0.0;
        iat_max_list = record.calculate(what = "iat_max_list", optional = True)
        if iat_max_list and len(iat_max_list) == 2:
            iat_max_0 = iat_max_list[0]
            iat_max_1 = iat_max_list[1]

        dbcur.execute("""
                      INSERT INTO tests VALUES
                      (%u, %u, %u, %s, %s,
                      %f, %f, %f, %f, %f, %f,
                      %f, %f,
                      %f, %f, %f, %f, %f, %f,
                      %f, %f, %f, %f, %f, %f,
                      %u, "%s", "%s", "%s")
                      """ % (iterationNo, scenarioNo, runNo, src, dst,
                             thruput, thruput_recv, thruput_0, thruput_1, thruput_recv_0, thruput_recv_1,
                             transac_0, transac_1,
                             rtt_min_0, rtt_min_1, rtt_avg_0, rtt_avg_1, rtt_max_0, rtt_max_1,
                             iat_min_0, iat_min_1, iat_avg_0, iat_avg_1, iat_max_0, iat_max_1,
                             start_time, run_label, scenario_label, test))

        outagesList = record.calculate('outages', optional = True)
        for flowNo in outagesList:
            for DIR in outagesList[flowNo]:
                for outage in outagesList[flowNo][DIR]:
                    b, e, tretr, revr, bkof = outage['begin'], outage['end'], outage['tretr'], outage['revr'], outage['bkof']
                    dbcur.execute("""INSERT INTO outages VALUES
                                (%u, %u, %u, %u, %f, %f,
                                 %f, %f, %d, %d, %d,
                                 %u, "%s", "%s", "%s"
                                 )"""
                                 % (iterationNo, scenarioNo, runNo, flowNo, thruput_0, thruput_1,
                                    b, e, tretr, revr, bkof,
                                    start_time, run_label, scenario_label, test)
                                 )

    def calculateStdDev(self, rlabel=None, slabel=None, key="thruput"):
        """Calculates the standarddeviation of all values of the same rlabel
           and scenarioNo
        """

        dbcur = self.dbcon.cursor()

        where = ""
        if rlabel or slabel:
            where += 'WHERE '
        if slabel:
            where += 'scenario_label="%s"' %(slabel)
        if slabel and rlabel:
            where += ' AND '
        if rlabel:
            where += 'run_label="%s"' %(rlabel)

        query = '''
        SELECT COALESCE(%s,0) FROM tests %s;
        ''' %(key,where)

        dbcur.execute(query)
        ary = numpy.array(dbcur.fetchall())
        return ary.std()

    def generateRTOsRevertsLCD(self):
        """ Generate a rtos and reverts histogram with scenario labels for
        lcd """

        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT run_label,
        flowNo,
        sum(retr)/(SELECT count(*) FROM tests WHERE run_label = tests.run_label) as rtos,
        sum(revr)/(SELECT count(*) FROM tests WHERE run_label = tests.run_label) as reverts,
        AVG(thruput_0+thruput_1) as thruput_overall
        FROM outages
        GROUP BY flowNo, run_label
        ORDER BY flowNo ASC, thruput_overall DESC
        ''')
        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-reverts-rtos"
        valfilename  = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        fh.write("rtos_0 reverts_0 rtos_1 reverts_1")
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel, flowNo,
             rtos, reverts,
             thruput_overall
             ) = row

            debug(row)
            #std_outages_0 = self.calculateStdDev(key="outages_0")
            if not data.has_key(rlabel):
                data[rlabel] = ""
            data[rlabel] += "%f %f " %(rtos, reverts)

            if not sorted_labels.count(rlabel):
                sorted_labels.append(rlabel)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            fh.write(" %s" %value)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)
        g.setYLabel(r"RTOs and Reverts [$\\#$]")
        g.setYRange("[ 0 : * ]")

        g.plotBar(valfilename, title="Timeout retransmissions LCD",
                using="2:xtic(1)", linestyle=2, fillstyle="solid 0.5")
        g.plotBar(valfilename, title="Timeout retransmissions Standard", using="4:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Backoff reverts LCD", using="3:xtic(1)",
                linestyle=3, fillstyle="solid 0.5")
        # g.plotBar(valfilename, title="Reverts Standard", using="5:xtic(1)", linestyle=3)

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateOutagesLCD(self):
        """ Generate a outage histogram with scenario labels for
        lcd """

        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT run_label,
        flowNo,
        sum(1.0)/(SELECT sum(1.0) FROM tests WHERE run_label = tests.run_label) as outages,
        sum(end-begin)/(SELECT sum(1.0) FROM tests WHERE run_label = tests.run_label) as time,
        AVG(thruput_0+thruput_1) as thruput_overall
        FROM outages
        GROUP BY flowNo, run_label
        ORDER BY flowNo ASC, thruput_overall DESC
        ''')
        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-outages"
        valfilename  = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()

        fh.write("outages_0 time_0 outages_1 time_1")
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel, flowNo,
             outages, time,
             thruput_overall
             ) = row

            debug(row)
            #std_outages_0 = self.calculateStdDev(key="outages_0")
            if not data.has_key(rlabel):
                data[rlabel] = ""
            data[rlabel] += "%f %f " %(
                            outages, time)

            if not sorted_labels.count(rlabel):
                sorted_labels.append(rlabel)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            fh.write(" %s" %value)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)
        g.setYLabel(r"Outages [$\\#$]")
        g.setY2Label(r"Duration [$\\si{\\second}$]")
        g.setYRange("[ 0 : 8 ]")
        g.setY2Range("[ 0 : 20 ]")

        g.plotBar(valfilename, title="Outages LCD", using="2:xtic(1)",
                linestyle=1,fillstyle="solid 0.5")
        g.plotBar(valfilename, title="Outages Standard", using="4:xtic(1)", linestyle=1)
        g.plotBar(valfilename, title="Outage duration LCD", using="3:xtic(1)",
                linestyle=2,fillstyle="solid 0.5", axes="x1y2")
        g.plotBar(valfilename, title="Outage duration Standard", using="5:xtic(1)",
                linestyle=2, axes="x1y2")

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateICMPsLCD(self):
        """ Generate a icmp and reverts histogram with scenario labels for lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-icmps"
        valfilename  = os.path.join(outdir, plotname+".values")

        if not os.path.exists(valfilename):
            warn("ICMP value file %s does not exists, create it manually",
                    valfilename)
            return

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)
        g.setYLabel(r"Total ICMPs and Reverts [$\\#$]")
        g.setYRange("[ 0 : 1600 ]")
        g.gplot("set style histogram rowstacked")
        g.gplot("set xtics offset 0,0.3")
        g.gplot("set boxwidth 0.8")
        g.plot("newhistogram 'src14-dst8',\
            'lcd-analysis-icmps.values' using 2:xtic(1) title 'ICMPs Code 0 (Network Unreachable)' ls 8,\
            '' using 3:xtic(1) title 'ICMPs Code 1 (Host Unreachable)'  ls 8 fillstyle solid 0.5,\
            '' using 4:xtic(1) title 'Backoff reverts'  ls 3 fillstyle solid 0.5\
            ")

        g.plot("newhistogram 'src14-dst17',\
            '' using 5:xtic(1) notitle ls 8,\
            '' using 6:xtic(1) notitle ls 8 fillstyle solid 0.5,\
            '' using 7:xtic(1) notitle ls 3 fillstyle solid 0.5\
            ")

        g.plot("newhistogram 'src14-dst6',\
            '' using 8:xtic(1) notitle ls 8,\
            '' using 9:xtic(1) notitle  ls 8 fillstyle solid 0.5,\
            '' using 10:xtic(1) notitle  ls 3 fillstyle solid 0.5\
            ")


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
        AVG(rtt_min_0)/1000 as rtt_min_0,
        AVG(rtt_avg_0)/1000 as rtt_avg_0,
        AVG(rtt_max_0)/1000 as rtt_max_0,
        AVG(rtt_min_1)/1000 as rtt_min_1,
        AVG(rtt_avg_1)/1000 as rtt_avg_1,
        AVG(rtt_max_1)/1000 as rtt_max_1,
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

        # columns
        for val in scenarios:
            fh.write("rtt_min_0_%(v)s rtt_avg_0_%(v)s rtt_max_0_%(v)s " %{ "v" : val })
            fh.write("rtt_min_1_%(v)s rtt_avg_1_%(v)s rtt_max_1_%(v)s " %{ "v" : val })
            fh.write("std_rtt_min_0_%(v)s std_rtt_avg_0_%(v)s std_rtt_max_0_%(v)s " %{ "v" : val })
            fh.write("std_rtt_min_1_%(v)s std_rtt_avg_1_%(v)s std_rtt_max_1_%(v)s " %{ "v" : val })

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

            std_rtt_min_0 = self.calculateStdDev(rlabel, slabel, "(rtt_min_0/1000)")
            std_rtt_avg_0 = self.calculateStdDev(rlabel, slabel, "(rtt_avg_0/1000)")
            std_rtt_max_0 = self.calculateStdDev(rlabel, slabel, "(rtt_max_0/1000)")

            std_rtt_min_1 = self.calculateStdDev(rlabel, slabel, "(rtt_min_1/1000)")
            std_rtt_avg_1 = self.calculateStdDev(rlabel, slabel, "(rtt_avg_1/1000)")
            std_rtt_max_1 = self.calculateStdDev(rlabel, slabel, "(rtt_max_1/1000)")


            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f %f %f %f %f %f %f %f %f %f %f %d" %(
                 rtt_min_0, rtt_avg_0, rtt_max_0,
                 rtt_min_1, rtt_avg_1, rtt_max_1,
                 std_rtt_min_0, std_rtt_avg_0, std_rtt_max_0,
                 std_rtt_min_1, std_rtt_avg_1, std_rtt_max_1,

                 notests)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        gavg = UmHistogram(plotname=plotname+"-avg", outdir=outdir,
                saveit=self.options.save,
                debug=self.options.debug,force=self.options.force)
        gavg.setYLabel(r"Average RTT [$\\si{\\second}$]")
        gavg.setYRange("[ 0 : * ]")

        # plot avg RTT
        for i in range(len(scenarios)):
            gavg.plotBar(valfilename, title=scenarios[i]+" LCD",
                    using="%u:xtic(1)" %((13*i)+3), linestyle=(i+2),
                    fillstyle="solid 0.5")
            gavg.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+6), linestyle=(i+2))

        # plot errorbars
        for i in range(len(scenarios)):
            if i == 0:
                gavg.plotErrorbar(valfilename, 0, 3, 9, "Standard Deviation")
                gavg.plotErrorbar(valfilename, 1, 6, 12)

            else:
                gavg.plotErrorbar(valfilename, i*2,   (i*13)+3, (i*13)+9)
                gavg.plotErrorbar(valfilename, i*2+1, (i*13)+6, (i*13)+12)

        gavg.save()

        gmax = UmHistogram(plotname=plotname+"-max", outdir=outdir,
                saveit=self.options.save,
                debug=self.options.debug,force=self.options.force)
        gmax.setYLabel(r"Maximum RTT [$\\si{\\second}$]")
        gmax.setYRange("[ 0 : * ]")

        # plot max RTT
        for i in range(len(scenarios)):
            gmax.plotBar(valfilename, title=scenarios[i]+" LCD",
                    using="%u:xtic(1)" %((13*i)+4), linestyle=(i+2),
                    fillstyle="solid 0.5")
            gmax.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+7), linestyle=(i+2))

        # plot error bars
        for i in range(len(scenarios)):
            if i == 0:
                gmax.plotErrorbar(valfilename, 0, 4, 10, "Standard Deviation")
                gmax.plotErrorbar(valfilename, 1, 7, 13)

            else:
                gmax.plotErrorbar(valfilename, i*2,   (i*13)+4, (i*13)+10)
                gmax.plotErrorbar(valfilename, i*2+1, (i*13)+7, (i*13)+13)

        gmax.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateIATLCD(self):
        """ Generate a IAT histogram with for scenario stream """

        dbcur = self.dbcon.cursor()

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-iat"
        valfilename  = os.path.join(outdir, plotname+".values")

        # get all scenario labels
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests
        WHERE iat_avg_0 > 0
        ORDER BY scenarioNo'''
        )
        scenarios = list()
        for row in dbcur:
            (key,val) = row
            scenarios.append(val)

        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        AVG(iat_min_0)/1000 as iat_min_0,
        AVG(iat_avg_0)/1000 as iat_avg_0,
        AVG(iat_max_0)/1000 as iat_max_0,
        AVG(iat_min_1)/1000 as iat_min_1,
        AVG(iat_avg_1)/1000 as iat_avg_1,
        AVG(iat_max_1)/1000 as iat_max_1,
        AVG(thruput_0+thruput_1) as thruput_overall,
        SUM(1) as notests
        FROM tests
        WHERE iat_avg_0 >  0
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        # columns
        for val in scenarios:
            fh.write("iat_min_0_%(v)s iat_avg_0_%(v)s iat_max_0_%(v)s " %{ "v" : val })
            fh.write("iat_min_1_%(v)s iat_avg_1_%(v)s iat_max_1_%(v)s " %{ "v" : val })
            fh.write("std_iat_min_0_%(v)s std_iat_avg_0_%(v)s std_iat_max_0_%(v)s " %{ "v" : val })
            fh.write("std_iat_min_1_%(v)s std_iat_avg_1_%(v)s std_iat_max_1_%(v)s " %{ "v" : val })

            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        for row in dbcur:
            (rlabel,slabel,sno,
             iat_min_0, iat_avg_0, iat_max_0,
             iat_min_1, iat_avg_1, iat_max_1,
             thruput_overall,
             notests) = row

            std_iat_min_0 = self.calculateStdDev(rlabel, slabel, "(iat_min_0/1000)")
            std_iat_avg_0 = self.calculateStdDev(rlabel, slabel, "(iat_avg_0/1000)")
            std_iat_max_0 = self.calculateStdDev(rlabel, slabel, "(iat_max_0/1000)")

            std_iat_min_1 = self.calculateStdDev(rlabel, slabel, "(iat_min_1/1000)")
            std_iat_avg_1 = self.calculateStdDev(rlabel, slabel, "(iat_avg_1/1000)")
            std_iat_max_1 = self.calculateStdDev(rlabel, slabel, "(iat_max_1/1000)")

            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f %f %f %f %f %f %f %f %f %f %f %d" %(
                 iat_min_0, iat_avg_0, iat_max_0,
                 iat_min_1, iat_avg_1, iat_max_1,
                 std_iat_min_0, std_iat_avg_0, std_iat_max_0,
                 std_iat_min_1, std_iat_avg_1, std_iat_max_1,
                 notests)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        gavg = UmHistogram(plotname=plotname+"-avg", outdir=outdir,
                saveit=self.options.save,
                debug=self.options.debug,force=self.options.force)
        gavg.setYLabel(r"Average IAT [$\\si{\\second}$]")
        gavg.setYRange("[ 0 : * ]")

        # plot avg iat
        for i in range(len(scenarios)):
            gavg.plotBar(valfilename, title=scenarios[i]+" LCD",
                    using="%u:xtic(1)" %((13*i)+3), linestyle=(i+1),
                    fillstyle="solid 0.5")
            gavg.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+6), linestyle=(i+1))

        # plot errorbars
        for i in range(len(scenarios)):
            if i == 0:
                gavg.plotErrorbar(valfilename, 0, 3, 9, "Standard Deviation")
                gavg.plotErrorbar(valfilename, 1, 6, 12)

            else:
                gavg.plotErrorbar(valfilename, i*2,   (i*13)+3, (i*13)+9)
                gavg.plotErrorbar(valfilename, i*2+1, (i*13)+6, (i*13)+12)

        gavg.save()

        gmax = UmHistogram(plotname=plotname+"-max", outdir=outdir,
                saveit=self.options.save,
                debug=self.options.debug,force=self.options.force)
        gmax.setYLabel(r"Maximum IAT [$\\si{\\second}$]")
        gmax.setYRange("[ 0 : * ]")

        # plot max iat
        for i in range(len(scenarios)):
            gmax.plotBar(valfilename, title=scenarios[i]+" LCD",
                    using="%u:xtic(1)" %((13*i)+4), linestyle=(i+1),
                    fillstyle="solid 0.5")
            gmax.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+7), linestyle=(i+1))

        # plot error bars
        for i in range(len(scenarios)):
            if i == 0:
                gmax.plotErrorbar(valfilename, 0, 4, 10, "Standard Deviation")
                gmax.plotErrorbar(valfilename, 1, 7, 13)

            else:
                gmax.plotErrorbar(valfilename, i*2,   (i*13)+4, (i*13)+10)
                gmax.plotErrorbar(valfilename, i*2+1, (i*13)+7, (i*13)+13)

        gmax.save()

        if not self.options.save:
            os.remove(valfilename)

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

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save,  debug=self.options.debug,
                force=self.options.force)
        g.setYLabel(r"Network Transactions [$\\si{\\nnumber\\per\\second}$]")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(scenarios)):
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[i]+" LCD",
                    using="%u:xtic(1)" %((5*i)+2), linestyle=(i+2),
                    fillstyle="solid 0.5")
            g.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((5*i)+3), linestyle=(i+2))

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

        if not self.options.save:
            os.remove(valfilename)

    def generateTransacsImprovementLCD(self):
        """ Generate a network transactions histogram with scenario labels for
        lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-transactions-improvement"
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
               AVG((transac_0/transac_1-1)*100) as transac_diff,
               AVG(thruput_0+thruput_1) as thruput_overall,
               SUM(1) as notests
        FROM tests
        WHERE transac_0 > 0 and transac_1 > 1
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # columns
        for val in scenarios:
            fh.write("transac_diff_%(v)s std_transac_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        for row in dbcur:
            (rlabel,slabel,sno,
             transac_diff,
             thruput_overall,
             notests) = row

            std_transac_diff = self.calculateStdDev(rlabel, slabel, "(transac_0/transac_1-1)*100")

            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f %d" %(
                                 transac_diff,
                                 std_transac_diff,
                                 notests
                                 )

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save,  debug=self.options.debug,
                force=self.options.force)
        g.setYLabel(r"Network Transactions improvement for TCP-LCD [$\\si{\\percent}$]")
        g.setYRange("[ * : * ]")

        # bars
        for i in range(len(scenarios)):
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[i], using="%u:xtic(1)" %((3*i)+2), linestyle=(i+2))

        # errobars
        #for i in range(len(scenarios)):
        #    if i == 0:
        #        g.plotErrorbar(valfilename, 0, 2, 3, "Standard Deviation")
        #    else:
        #        g.plotErrorbar(valfilename, i*2, (i*3)+2, (i*3)+3)

        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateTputHistogramLCD(self):
        """ Generates a tput histogram with scenario labels for lcd """

        dbcur = self.dbcon.cursor()
        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-goodput"
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

        g = UmHistogram(plotname=plotname, outdir=outdir,
                debug=self.options.debug, force=self.options.force)
        g.setYLabel(r"Goodput [$\\si{\\Mbps}$]")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+" LCD",
                    using="%u:xtic(1)" %( (i*5)+2 ), linestyle=(i+1),
                    fillstyle="solid 0.5")
            g.plotBar(valfilename, title=scenarios[key]+" Standard",
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

        if not self.options.save:
            os.remove(valfilename)

    def generateTputImprovementHistogramLCD(self):
        """ Generates a tput histogram with scenario labels for lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "lcd-analysis-goodput-improvement"
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
        (
            ( AVG(thruput_0)+AVG(thruput_recv_0) ) /
            ( AVG(thruput_1)+AVG(thruput_recv_1) )
            -1
        )*100 as thruput_diff,
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
            fh.write("tput_diff_%(v)s " %{ "v" : val })
            fh.write("std_tput_diff_%(v)s " %{ "v" : val })
            fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        for row in dbcur:
            (rlabel,slabel,sno,
             thruput_diff,
             thruput_overall,
             notests) = row

            debug(row)

            std_thruput_diff = self.calculateStdDev(rlabel, slabel,
                    "( ((thruput_0+thruput_recv_0) / (thruput_1+thruput_recv_1)) - 1)*100")

            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%f %f %d" %(
                                 thruput_diff,std_thruput_diff,
                                 notests)

        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)
        g.setYLabel(r"Goodput improvement for TCP LCD [$\\si{\\percent}$]")
        # g.setLogScale()
        g.setYRange("[ * : * ]")
        # bars
        for i in range(len(keys)):
            key = keys[i]
            g.plotBar(valfilename, title=scenarios[key],
                    using="%u:xtic(1)" %( (i*3)+2 ), linestyle=(i+1))

        # errobars
        #for i in range(len(keys)):
        #    # TODO: calculate offset with scenarios and gap
        #    if i == 0:
        #        g.plotErrorbar(valfilename, 0, 2, 3, "Standard Deviation")
        #    else:
        #        g.plotErrorbar(valfilename, (i*1)+0, (i*3)+2, (i*3)+3)

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def run(self):
        """Main Method"""

        # by default database in memory to access data efficiently
        if not self.options.save:
            self.dbcon = sqlite.connect(':memory:')
        else:
            self.dbcon = sqlite.connect('/tmp/lcd-analysis.sqlite')

        dbcur = self.dbcon.cursor()
        dbcur.execute("""DROP TABLE IF EXISTS tests;""")
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
                            iat_min_0       DOUBLE,
                            iat_min_1       DOUBLE,
                            iat_avg_0       DOUBLE,
                            iat_avg_1       DOUBLE,
                            iat_max_0       DOUBLE,
                            iat_max_1       DOUBLE,
                            start_time      INTEGER,
                            run_label       VARCHAR(70),
                            scenario_label  VARCHAR(70),
                            test            VARCHAR(50))
        """)

        dbcur.execute("""DROP TABLE IF EXISTS outages;""")
        dbcur.execute("""
        CREATE TABLE outages (
                    iterationNo INTEGER,
                    scenarioNo  INTEGER,
                    runNo       INTEGER,
                    flowNo      INTEGER,
                    thruput_0   DOUBLE,
                    thruput_1   DOUBLE,
                    begin       DOUBLE,
                    end         DOUBLE,
                    retr        DOUBLE,
                    revr        DOUBLE,
                    bkof        DOUBLE,
                    start_time  INTEGER,
                    run_label   VARCHAR(70),
                    scenario_label VARCHAR(70),
                    test        VARCHAR(50)
                    )
        """)

        # store failed test as a mapping from run_label to number
        self.failed = dict()

        # only load flowgrind test records
        self.loadRecords(tests=["flowgrind"])

        self.dbcon.commit()
        self.generateTputHistogramLCD()
        self.generateTputImprovementHistogramLCD()
        self.generateIATLCD()
        self.generateTransacsLCD()
        self.generateTransacsImprovementLCD()
        self.generateRTTLCD()
        self.generateRTOsRevertsLCD()
        self.generateOutagesLCD()
        self.generateICMPsLCD() # create value file manually!
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

