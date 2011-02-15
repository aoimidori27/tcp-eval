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

        iat_avg_0 = iat_avg_1 = 0.0
        iat_avg_list = record.calculate(what = "iat_avg_list", optional = True)
        if iat_avg_list and len(iat_avg_list) == 2:
            iat_avg_0 = iat_avg_list[0]
            iat_avg_1 = iat_avg_list[1]

        iat_max_0 = iat_max_1 = 0.0
        iat_max_list = record.calculate(what = "iat_max_list", optional = True)
        if iat_max_list and len(iat_max_list) == 2:
            iat_max_0 = iat_max_list[0]
            iat_max_1 = iat_max_list[1]

        # icmp
        s_icmp_code_0 = s_icmp_code_1 = d_icmp_code_0 = d_icmp_code_1 = 0.0
        tmp = record.calculate(what = "s_icmp_code_0", optional = True)
        if tmp: s_icmp_code_0 = tmp

        tmp = record.calculate(what = "s_icmp_code_1", optional = True)
        if tmp: s_icmp_code_1 = tmp

        tmp = record.calculate(what = "d_icmp_code_0", optional = True)
        if tmp: d_icmp_code_0 = tmp

        tmp = record.calculate(what = "d_icmp_code_1", optional = True)
        if tmp: d_icmp_code_1 = tmp

        dbcur.execute("""
                      INSERT INTO tests VALUES
                      (%u, %u, %u, %s, %s,
                      %f, %f, %f, %f, %f, %f,
                      %f, %f,
                      %f, %f, %f, %f, %f, %f,
                      %f, %f, %f, %f, %f, %f,
                      %f, %f, %f, %f,
                      %u, "%s", "%s", "%s")
                      """ % (iterationNo, scenarioNo, runNo, src, dst,
                             thruput, thruput_recv, thruput_0, thruput_1, thruput_recv_0, thruput_recv_1,
                             transac_0, transac_1,
                             rtt_min_0, rtt_min_1, rtt_avg_0, rtt_avg_1, rtt_max_0, rtt_max_1,
                             iat_min_0, iat_min_1, iat_avg_0, iat_avg_1, iat_max_0, iat_max_1,
                             s_icmp_code_0, s_icmp_code_1, d_icmp_code_0, d_icmp_code_1,
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
        sum(retr)/(SELECT sum(1.0) FROM tests WHERE run_label = tests.run_label) as rtos,
        sum(revr)/(SELECT sum(1.0) FROM tests WHERE run_label = tests.run_label) as reverts,
        AVG(thruput_0+thruput_1) as thruput_overall
        FROM outages
        GROUP BY flowNo, run_label
        ORDER BY flowNo ASC, thruput_overall DESC
        ''')
        # outfile
        outdir        = self.options.outdir
        plotname      = "reverts-rtos"
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
        g.setYLabel(r"Average RTO Retransmissions and Backoff Reverts [$\\#$]")
        g.setYRange("[ 0 : * ]")


        g.plotBar(valfilename, title="RTO Retransmissions TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="RTO Retransmissions Standard",
                using="4:xtic(1)", linestyle=2, fillstyle="solid 0.5")
        # gap
        #g.plot("'empty.values' using 2:xtic(1) notitle")
        g.plotBar(valfilename, title="Backoff Reverts TCP-LCD",
                using="3:xtic(1)", linestyle=3)
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
        plotname      = "outages"
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
        g.setYLabel(r"Average Outages [$\\#$]")
        g.setY2Label(r"Average Outage Duration [$\\si{\\second}$]")
        g.setYRange("[ 0 : 8 ]")
        g.setY2Range("[ 0 : 20 ]")

        g.plotBar(valfilename, title="Outages TCP-LCD", using="2:xtic(1)",
                linestyle=4)
        g.plotBar(valfilename, title="Outages Standard", using="4:xtic(1)",
                linestyle=4, fillstyle="solid 0.5")
        # gap
        g.plot("'empty.values' using 2:xtic(1) notitle")
        g.plotBar(valfilename, title="Outage Duration TCP-LCD", using="3:xtic(1)",
                linestyle=5,  axes="x1y2")
        g.plotBar(valfilename, title="Outage Duration Standard", using="5:xtic(1)",
                linestyle=5, fillstyle="solid 0.5", axes="x1y2")

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateICMPsLCD(self):
        """ Generate a icmp and reverts histogram with scenario labels for lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "icmps-reverts"
        valfilename   = os.path.join(outdir, plotname+".values")

        dbcur = self.dbcon.cursor()

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        data = [[0 for i in range(10)] for j in range(2)]

        data[1][0] = "Reverts"
        data[0][0] = "ICMPs  "

        # get single values
        dbcur.execute('''
        SELECT run_label,
        avg(s_icmp_code_0+d_icmp_code_0)/2 as icmp_code_0,
        avg(s_icmp_code_1+d_icmp_code_1)/2 as icmp_code_1,
        AVG(thruput_0+thruput_1) as thruput_overall
        FROM tests
        GROUP BY run_label
        ORDER BY thruput_overall DESC
        ''' )

        fh.write("#label 8-c0 8-c1 8-r 17-c0 17-c1 17-r 6-c0 6-c1 6-r\n")

        for row in dbcur:
            (rlabel,
             icmp_code_0,  icmp_code_1,
             thruput_overall) = row

            debug(row)
            if rlabel == "Src14--Dst8":
                data[0][1] = icmp_code_0
                data[0][2] = icmp_code_1
            if rlabel == "Src14--Dst17":
                data[0][4] = icmp_code_0
                data[0][5] = icmp_code_1
            if rlabel == "Src14--Dst6":
                data[0][7] = icmp_code_0
                data[0][8] = icmp_code_1

        dbcur.execute('''
        SELECT run_label,
        sum(revr)/(SELECT sum(1.0) FROM tests WHERE run_label = tests.run_label) as reverts,
        AVG(thruput_0+thruput_1) as thruput_overall
        FROM outages
        WHERE flowNo = '0'
        GROUP BY run_label
        ORDER BY thruput_overall DESC
        ''')

        for row in dbcur:
            (rlabel,
             reverts,
             thruput_overall) = row

            debug(row)
            if rlabel == "Src14--Dst8":
              data[1][3] = reverts
            if rlabel == "Src14--Dst17":
              data[1][6] = reverts
            if rlabel == "Src14--Dst6":
              data[1][9] = reverts

        for i in range(2):
            fh.write("%s " %(data[i][0]) )
            for j in range(1,10):
                fh.write("%f " %(data[i][j]) )
            fh.write("\n")

        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Average ICMPs and Backoff Reverts [$\\#$]")
        g.setYRange("[ 0 : * ]")
        g.gplot("set style histogram rowstacked")
        g.gplot("set xtics offset 0,0.3")
        g.gplot("set boxwidth 0.8")
        g.plot("newhistogram 'Src14--Dst8',\
            '%s' using 2:xtic(1) title 'ICMPs Code 0' ls 1,\
            '' using 3:xtic(1) title 'ICMPs Code 1' ls 1 fillstyle solid 0.5,\
            '' using 4:xtic(1) title 'Backoff Reverts' ls 3" %valfilename
            )

        g.plot("newhistogram 'Src14--Dst17',\
            '' using 5:xtic(1) notitle ls 1,\
            '' using 6:xtic(1) notitle ls 1 fillstyle solid 0.5,\
            '' using 7:xtic(1) notitle ls 3"

            )

        g.plot("newhistogram 'Src14--Dst6',\
            '' using 8:xtic(1) notitle ls 1,\
            '' using 9:xtic(1) notitle ls 1 fillstyle solid 0.5,\
            '' using 10:xtic(1) notitle ls 3"

            )

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateICMPsLCDbyScenario(self):
        """ Generate a icmp and reverts histogram with scenario labels for lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "icmps-by-scenario"
        valfilename  = os.path.join(outdir, plotname+".values")

        dbcur = self.dbcon.cursor()

        # get all scenario labels
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests
        ORDER BY scenarioNo'''
        )
        scenarios = list()
        for row in dbcur:
            (key,val) = row
            scenarios.append(val)

        # get single values
        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        avg(s_icmp_code_0+d_icmp_code_0) as icmp_code_0,
        avg(s_icmp_code_1+d_icmp_code_1) as icmp_code_1,
        AVG(thruput_0+thruput_1) as thruput_overall
        FROM tests
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''' )

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")
        # columns
        for val in scenarios:
            fh.write("code_0_%(v)s code_1_%(v)s" %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()


        for row in dbcur:
            (rlabel,slabel,sno,
             icmp_code_0, icmp_code_1,
             thruput_overall) = row

            debug(row)

            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f" %(
                                 icmp_code_0,
                                 icmp_code_1,
                                 )

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
        g.setYLabel(r"Average ICMPs [$\\#$]")

        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(scenarios)):
            g.plotBar(valfilename, title=scenarios[i]+" ICMPs Code 0",
                    using="%u:xtic(1)" %((2*i)+2), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[i]+" ICMPs Code 1",
                    using="%u:xtic(1)" %((2*i)+3), linestyle=(i+1))

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateRTTLCD(self):
        """ Generate a RTT histogram with scenario labels for
        lcd """

        dbcur = self.dbcon.cursor()

        # outfile
        outdir        = self.options.outdir
        plotname      = "rtt"
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
            gavg.plotBar(valfilename, title=scenarios[i]+" TCP-LCD",
                    using="%u:xtic(1)" %((13*i)+3), linestyle=(i+2))
            gavg.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+6), linestyle=(i+2),
                    fillstyle="solid 0.5")

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
            gmax.plotBar(valfilename, title=scenarios[i]+" TCP-LCD",
                    using="%u:xtic(1)" %((13*i)+4), linestyle=(i+2))
            gmax.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+7), linestyle=(i+2),
                    fillstyle="solid 0.5")

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

    def generateRTTLCDImprovement(self):
        """ Generate a RTT improvement bar chart with scenario labels for
        lcd """

        dbcur = self.dbcon.cursor()

        # outfile
        outdir        = self.options.outdir
        plotname      = "rtt-improvement"
        valfilename   = os.path.join(outdir, plotname+".values")

        # get all scenario labels
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests
        WHERE rtt_min_0 > 0 AND rtt_avg_0 > 0 AND rtt_max_0 > 0
        ORDER BY scenarioNo'''
        )
        scenarios = list()
        for row in dbcur:
            (key,val) = row
            scenarios.append(val)

        dbcur.execute('''
        SELECT run_label, scenario_label, scenarioNo,
        AVG(rtt_min_1/rtt_min_0-1)*100 as rtt_min_improvement,
        AVG(rtt_avg_1/rtt_avg_0-1)*100 as rtt_avg_improvement,
        AVG(rtt_max_1/rtt_max_0-1)*100 as rtt_max_improvement,
        AVG(thruput_0+thruput_1) as thruput_overall,
        SUM(1) as notests
        FROM tests
        WHERE rtt_min_0 > 0 AND rtt_avg_0 > 0 AND rtt_max_0 > 0
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # columns
        for val in scenarios:
            fh.write("rtt_min_improvement_%(v)s rtt_avg_improvement_%(v)s rtt_max_improvement_%(v)s " %{ "v" : val })
            fh.write("std_rtt_min_improvement_%(v)s std_rtt_avg_improvement_%(v)s std_rtt_max_improvement_%(v)s " %{ "v" : val })
        fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        for row in dbcur:
            (rlabel,slabel,sno,
             rtt_min_improvement, rtt_avg_improvement, rtt_max_improvement,
             thruput_overall,
             notests) = row

            std_rtt_min_improvement = self.calculateStdDev(rlabel, slabel,
                    "(rtt_min_1/rtt_min_0-1)*100")
            std_rtt_avg_improvement = self.calculateStdDev(rlabel, slabel,
                    "(rtt_avg_1/rtt_avg_0-1)*100")
            std_rtt_max_improvement = self.calculateStdDev(rlabel, slabel,
                    "(rtt_max_1/rtt_max_0-1)*100")

            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0 0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f %f %f %f %f %d" %(
                 rtt_min_improvement, rtt_avg_improvement, rtt_max_improvement,
                 std_rtt_min_improvement, std_rtt_avg_improvement, std_rtt_max_improvement,
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
        gavg.setYLabel(r"Average RTT Improvement for TCP-LCD [$\\si{\\percent}$]")
        gavg.setYRange("[ * : * ]")

        # plot avg RTT improvement
        for i in range(len(scenarios)):
            gavg.plotBar(valfilename, title=scenarios[i],
                    using="%u:xtic(1)" %((7*i)+3), linestyle=(i+2))

        # plot errorbars
        #for i in range(len(scenarios)):
        #    if i == 0:
        #        gavg.plotErrorbar(valfilename, 0, 3, 6, "Standard Deviation")
        #    else:
        #        gavg.plotErrorbar(valfilename, i,   (i*7)+3, (i*7)+6)

        gavg.save()

        gmax = UmHistogram(plotname=plotname+"-max", outdir=outdir,
                saveit=self.options.save,
                debug=self.options.debug,force=self.options.force)
        gmax.setYLabel(r"Maximum RTT Improvement for TCP-LCD [$\\si{\\percent}$]")
        gmax.setYRange("[ * : * ]")

        # plot max RTT improvement
        for i in range(len(scenarios)):
            gmax.plotBar(valfilename, title=scenarios[i],
                    using="%u:xtic(1)" %((7*i)+4), linestyle=(i+2))

        # plot errorbars
        #for i in range(len(scenarios)):
        #   if i == 0:
        #        gmax.plotErrorbar(valfilename, 0, 4, 7, "Standard Deviation")
        #    else:
        #        gmax.plotErrorbar(valfilename, i,   (i*7)+4, (i*7)+7)

        gmax.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateIATLCD(self):
        """ Generate a IAT histogram with for scenario stream """

        dbcur = self.dbcon.cursor()

        # outfile
        outdir        = self.options.outdir
        plotname      = "iat"
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
            gavg.plotBar(valfilename, title=scenarios[i]+" TCP-LCD",
                    using="%u:xtic(1)" %((13*i)+3), linestyle=(i+1))
            gavg.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+6), linestyle=(i+1),
                    fillstyle="solid 0.5")

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
            gmax.plotBar(valfilename, title=scenarios[i]+" TCP-LCD",
                    using="%u:xtic(1)" %((13*i)+4), linestyle=(i+1))
            gmax.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((13*i)+7), linestyle=(i+1),
                    fillstyle="solid 0.5")

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


    def generateIATLCDImprovement(self):
        """ Generate a IAT improvement bar chart with scenario labels for
        lcd """

        dbcur = self.dbcon.cursor()

        # outfile
        outdir        = self.options.outdir
        plotname      = "iat-improvement"
        valfilename   = os.path.join(outdir, plotname+".values")

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
        AVG(iat_min_1/iat_min_0-1)*100 as iat_min_improvement,
        AVG(iat_avg_1/iat_avg_0-1)*100 as iat_avg_improvement,
        AVG(iat_max_1/iat_max_0-1)*100 as iat_max_improvement,
        AVG(thruput_0+thruput_1) as thruput_overall,
        SUM(1) as notests
        FROM tests
        WHERE iat_avg_0 > 0
        GROUP BY run_label, scenarioNo
        ORDER BY thruput_overall DESC, scenarioNo ASC
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")


    # print header
        fh.write("# run_label ")

        # columns
        for val in scenarios:
            fh.write("iat_min_improvement_%(v)s iat_avg_improvement_%(v)s iat_max_improvement_%(v)s " %{ "v" : val })
            fh.write("std_iat_min_improvement_%(v)s std_iat_avg_improvement_%(v)s std_iat_max_improvement_%(v)s " %{ "v" : val })
        fh.write("notests_%(v)s " %{ "v" : val })
        fh.write("\n")

        # one line per runlabel
        data = dict()
        sorted_labels = list()

        for row in dbcur:
            (rlabel,slabel,sno,
             iat_min_improvement, iat_avg_improvement, iat_max_improvement,
             thruput_overall,
             notests) = row

            std_iat_min_improvement = self.calculateStdDev(rlabel, slabel,
                    "(iat_min_1/iat_min_0)*100")
            std_iat_avg_improvement = self.calculateStdDev(rlabel, slabel,
                    "(iat_avg_1/iat_avg_0)*100")
            std_iat_max_improvement = self.calculateStdDev(rlabel, slabel,
                    "(iat_max_1/iat_max_0)*100")

            if not data.has_key(rlabel):
                tmp = list()
                for i in scenarios:
                    tmp.append("0.0 0.0 0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][scenarios.index(slabel)] = "%f %f %f %f %f %f %d" %(
                 iat_min_improvement, iat_avg_improvement, iat_max_improvement,
                 std_iat_min_improvement, std_iat_avg_improvement, std_iat_max_improvement,
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
        gavg.setYLabel(r"Average IAT Improvement for TCP-LCD [$\\si{\\percent}$]")
        gavg.setYRange("[ * : * ]")

        # plot avg IAT improvement
        for i in range(len(scenarios)):
            gavg.plotBar(valfilename, title=scenarios[i],
                    using="%u:xtic(1)" %((7*i)+3), linestyle=(i+1))

        # plot errorbars
        #for i in range(len(scenarios)):
        #    if i == 0:
        #       gavg.plotErrorbar(valfilename, 0, 3, 6, "Standard Deviation")
        #   else:
        #       gavg.plotErrorbar(valfilename, i,   (i*7)+3, (i*7)+6)

        gavg.save() 

        gmax = UmHistogram(plotname=plotname+"-max", outdir=outdir,
                saveit=self.options.save,
                debug=self.options.debug,force=self.options.force)
        gmax.setYLabel(r"Maximum IAT Improvement for TCP-LCD [$\\si{\\percent}$]")
        gmax.setYRange("[ * : * ]")

        # plot max IAT improvement
        for i in range(len(scenarios)):
            gmax.plotBar(valfilename, title=scenarios[i],
                    using="%u:xtic(1)" %((7*i)+4), linestyle=(i+1))

        # plot errorbars
        #for i in range(len(scenarios)):
        #    if i == 0:
        #        gmax.plotErrorbar(valfilename, 0, 4, 7, "Standard Deviation")
        #    else:
        #        gmax.plotErrorbar(valfilename, i,   (i*7)+4, (i*7)+7)

        gmax.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateTransacsLCD(self):
        """ Generate a network transactions histogram with scenario labels for
        lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "transactions"
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
        g.setYLabel(r"Average Network Transactions [$\\si{\\nnumber\\per\\second}$]")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(scenarios)):
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[i]+" TCP-LCD",
                    using="%u:xtic(1)" %((5*i)+2), linestyle=(i+2))
            g.plotBar(valfilename, title=scenarios[i]+" Standard",
                    using="%u:xtic(1)" %((5*i)+3), linestyle=(i+2),
                    fillstyle="solid 0.5")

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
        plotname      = "transactions-improvement"
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
        g.setYLabel(r"Average Network Transactions Improvement for TCP-LCD [$\\si{\\percent}$]")
        g.setYRange("[ * : * ]")
        g.gplot("set key horizontal")

        # bars
        for i in range(len(scenarios)):
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[i], using="%u:xtic(1)"
                    %((3*i)+2), linestyle=(i+2))

        # errobars
        #for i in range(len(scenarios)):
        #    if i == 0:
        #        g.plotErrorbar(valfilename, 0, 2, 3, "Standard Deviation")
        #    else:
        #        g.plotErrorbar(valfilename, i*2, (i*3)+2, (i*3)+3)

        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateTputLCD(self):
        """ Generates a tput histogram with scenario labels for lcd """

        dbcur = self.dbcon.cursor()
        # outfile
        outdir        = self.options.outdir
        plotname      = "goodput"
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

            std_thruput_0 = self.calculateStdDev(rlabel, slabel, "thruput_0+thruput_recv_0")
            std_thruput_1 = self.calculateStdDev(rlabel, slabel, "thruput_1+thruput_recv_1")

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
        g.setYLabel(r"Average Goodput [$\\si{\\Mbps}$]")
        # g.setClusters(len(sorted_labels))
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
            # buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key]+" TCP-LCD",
                    using="%u:xtic(1)" %( (i*5)+2 ), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" Standard",
                    using="%u:xtic(1)" %( (i*5)+3 ), linestyle=(i+1),
                    fillstyle="solid 0.5")

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

    def generateTputImprovementLCD(self):
        """ Generates a tput histogram with scenario labels for lcd """

        # outfile
        outdir        = self.options.outdir
        plotname      = "goodput-improvement"
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
        g.setYLabel(r"Average Goodput Improvement for TCP-LCD [$\\si{\\percent}$]")
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

    def generateHistogramOutagesPerRTOsLCD(self):
        """ Generate a RTO histogram with scenario labels for
        lcd """

        # outfile
        outdir      = self.options.outdir
        plotname    = "histogram-src14-dst6-rto"
        valfilename = os.path.join(outdir, plotname+".values")
        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT (revr+bkof) as bin, flowNo as flowNo, count(1) as count
        FROM outages
        WHERE run_label = 'Src14--Dst6'
        GROUP by bin, flowNo
        ORDER by bin ASC;
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per bin
        data = [[0 for i in range(2)] for j in range(1,self.histogrambins*10)]

        fh.write("# bin count_0 count_1")
        fh.write("\n")

        sorted_labels = list()

        for row in dbcur:
            (bin, flowNo, count) = row

            debug(row)

            data[int(bin)][int(flowNo)] = count

        for i in range(len(data)):
            fh.write("%d %d %d" %(i,data[i][0],data[i][1]) )
            fh.write("\n")

        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Total Outages [$\\#$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 1 : * ]")
        g.setXRange("[ %d : %d ]" %(0,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical top right box")
        g.plotBar(valfilename, title="TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Standard",
                using="3:xtic(1)", linestyle=2, fillstyle="solid 0.5")

        # output plot
        g.save()

	plotname += "-logscale"
        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Total Outages [$\\#$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 1 : * ]")
        g.setXRange("[ %d : %d ]" %(0,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical top right box")
        g.setLogScale()
        g.plotBar(valfilename, title="TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Standard",
                using="3:xtic(1)", linestyle=2, fillstyle="solid 0.5")

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateHistogramRetransmissionsPerRTOsLCD(self):
        """ Generate a RTO histogram with scenario labels for
        lcd """

        # outfile
        outdir      = self.options.outdir
        plotname    = "histogram-src14-dst6-retransmissions-per-rto"
        valfilename = os.path.join(outdir, plotname+".values")
        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT (revr+bkof) as bin, flowNo as flowNo, count(1)*(revr+bkof) as count
        FROM outages
        WHERE run_label = 'Src14--Dst6'
        GROUP by bin, flowNo
        ORDER by bin ASC;
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per bin
        data = [[0 for i in range(2)] for j in range(1,self.histogrambins*10)]

        fh.write("# bin count_0 count_1")
        fh.write("\n")

        sorted_labels = list()

        for row in dbcur:
            (bin, flowNo, count) = row

            debug(row)

            data[int(bin)][int(flowNo)] = count

        for i in range(len(data)):
            fh.write("%d %d %d" %(i,data[i][0],data[i][1]) )
            fh.write("\n")

        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Total RTO Retransmissions [$\\#$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 1 : * ]")
        g.setXRange("[ %d : %d ]" %(0,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical top right box")
        g.plotBar(valfilename, title="TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Standard",
                using="3:xtic(1)", linestyle=2, fillstyle="solid 0.5")

        # output plot
        g.save()

        plotname += "-logscale"
        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Total RTO Retransmissions [$\\#$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 1 : * ]")
        g.setXRange("[ %d : %d ]" %(0,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical top right box")
        g.setLogScale()
        g.plotBar(valfilename, title="TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Standard",
                using="3:xtic(1)", linestyle=2, fillstyle="solid 0.5")

        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateHistogramDurartionPerRTOsLCD(self):
        """ Generate a duration per RTO histogram """

        # outfile
        outdir      = self.options.outdir
        plotname    = "histogram-src14-dst6-duration-per-rto"
        valfilename = os.path.join(outdir, plotname+".values")
        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT (revr+bkof) as bin, flowNo as flowNo, avg(end-begin) as duration
        FROM outages
        WHERE run_label = 'Src14--Dst6'
        GROUP by bin, flowNo
        ORDER by bin ASC;
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per bin
        data = [[0 for i in range(2)] for j in range(self.histogrambins*100)]

        fh.write("# bin duration_0 duration_1")
        fh.write("\n")

        sorted_labels = list()

        for row in dbcur:
            (bin, flowNo, duration) = row

            debug(row)

            data[int(bin)][int(flowNo)] = duration

        for i in range(len(data)):
            fh.write("%d %f %f" %(i,data[i][0],data[i][1]) )
            fh.write("\n")

        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Average Outage Duration [$\\si{\\second}$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 0 : * ]")
        g.setXRange("[ %d : %d ]" %(0,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical top right box")
        g.plotBar(valfilename, title="TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Standard",
                using="3:xtic(1)", linestyle=2, fillstyle="solid 0.5")


        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateHistogramBackoffsPerRTOsLCD(self):
        """ Generate a backoff RTO histogram """

        # outfile
        outdir      = self.options.outdir
        plotname    = "histogram-src14-dst6-backoffs-per-rto"
        valfilename = os.path.join(outdir, plotname+".values")
        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT (revr+bkof) as bin, flowNo as flowNo, avg(bkof) as duration
        FROM outages
        WHERE run_label = 'Src14--Dst6'
        GROUP by bin, flowNo
        ORDER by bin ASC;
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per bin
        data = [[0 for i in range(2)] for j in range(0,self.histogrambins*10)]

        fh.write("# bin backoffs_0 backoffs_1")
        fh.write("\n")

        sorted_labels = list()

        for row in dbcur:
            (bin, flowNo, duration) = row

            debug(row)

            data[int(bin)][int(flowNo)] = duration

        for i in range(len(data)):
            fh.write("%d %f %f" %(i,data[i][0],data[i][1]) )
            fh.write("\n")

        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Average Backoffs not reverted [$\\#$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 0 : * ]")
        g.setXRange("[ %d : %d ]" %(0,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical top right box")
        g.plotBar(valfilename, title="TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Standard",
                using="3:xtic(1)", linestyle=2, fillstyle="solid 0.5")


        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)


    def generateHistogramtTputPerRevertsLCD(self):
        """ Generate a RTO histogram with scenario labels for
        lcd """

        # outfile
        outdir      = self.options.outdir
        plotname    = "histogram-goodput-per-rto"
        valfilename = os.path.join(outdir, plotname+".values")
        dbcur = self.dbcon.cursor()

        dbcur.execute('''
        SELECT (revr+bkof) as bin, flowNo as flowNo, avg(thruput_0+thruput_1) as tput
        FROM outages
        WHERE run_label = 'Src14--Dst6'
        GROUP by bin, flowNo
        ORDER by bin ASC;
        ''')

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label ")

        # one line per bin
        data = [[0 for i in range(2)] for j in range(1,self.histogrambins*10)]

        fh.write("# bin tput_0 tput_1")
        fh.write("\n")

        sorted_labels = list()

        for row in dbcur:
            (bin, flowNo, tput) = row

            debug(row)

            data[int(bin)][int(flowNo)] = tput

        for i in range(len(data)):
            fh.write("%d %f %f" %(i,data[i][0],data[i][1]) )
            fh.write("\n")

        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Average Goodput [$\\si{\\Mbps}$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 0 : * ]")
        g.setXRange("[ %d : %d ]" %(0,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical top right box")
        g.plotBar(valfilename, title="TCP-LCD",
                using="2:xtic(1)", linestyle=2)
        g.plotBar(valfilename, title="Standard",
                using="3:xtic(1)", linestyle=2, fillstyle="solid 0.5")


        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)

    def generateHistogramRevertsPerRTOsLCD(self):
        """ Generate a Reverts per RTO histogram for lcd """

        # outfile
        outdir      = self.options.outdir
        plotname    = "histogram-src14-dst6-reverts"
        valfilename = os.path.join(outdir, plotname+".values")
        dbcur = self.dbcon.cursor()

        # get single values
        dbcur.execute('''
        SELECT
        (revr+bkof) as bin_0,
        revr as bin_1,
        count(1) as count
        FROM outages
        WHERE run_label = 'Src14--Dst6' and flowNo = '0'
        GROUP by bin_1, bin_0
        ORDER by bin_0 ASC, bin_1 ASC;
        ''' )

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        data = [[0 for i in range(self.histogrambins*10)] for j in range(self.histogrambins*10)]
        sums = [0 for i in range(self.histogrambins*10)]

        fh.write("# bin_0 / values 1...max / sum ")
        fh.write("\n")

        sorted_labels = list()

        for row in dbcur:
            (bin_0, bin_1, count) = row
            debug(row)
            data[int(bin_0)][int(bin_1)] = count

        # get sum
        dbcur.execute('''
        SELECT
        (revr+bkof) as bin_0,
        count(1) as sum
        FROM outages
        WHERE run_label = 'Src14--Dst6' and flowNo = '0'
        GROUP by bin_0
        ORDER by bin_0 ASC;
        ''' )

        for row in dbcur:
            (bin_0, sum) = row
            debug(row)
            sums[int(bin_0)] = sum

        for i in range(self.histogrambins):
            fh.write("%d " %i)
            for j in range(self.histogrambins):
                fh.write("%d " %(data[i][j]))
            fh.write("%d \n" %(sums[i]))
        fh.close()

        g = UmHistogram(plotname=plotname, outdir=outdir,
                saveit=self.options.save, debug=self.options.debug,
                force=self.options.force)

        g.setYLabel(r"Backoff Reverts [$\\si{\\percent}$]")
        g.setXLabel(r"RTOs per Outage [$\\#$]")
        g.setYRange("[ 0 : 100 ]")
        g.setXRange("[ %d : %d ]" %(0.5,self.histogrambins) )
        g.gplot("set xtics 5 scale 0.5")
        g.gplot("set key inside vertical right box")
        g.gplot("set style histogram rowstacked")
        g.gplot("set boxwidth 0.6")
        for i in range(self.histogrambins):
            # gradient
            g.plotBar(valfilename, title="%d" %(i),
                      using="(100.*$%d/$%d):xtic(1)" %(i+2,self.histogrambins+2),
                      gradientCurrent=i, gradientMax=self.histogrambins)
            # colors
            #g.plotBar(valfilename, title="%d" %(i),
            #        using="(100.*$%d/$%d):xtic(1)" %(i+2,self.histogrambins+2), linestyle=(i+1) )


        # output plot
        g.save()

        if not self.options.save:
            os.remove(valfilename)


    def run(self):
        """Main Method"""

        self.histogrambins = 15 

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
                            s_icmp_code_0   DOUBLE,
                            s_icmp_code_1   DOUBLE,
                            d_icmp_code_0   DOUBLE,
                            d_icmp_code_1   DOUBLE,
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
        self.generateTputLCD()
        self.generateTputImprovementLCD()
        self.generateTransacsLCD()
        self.generateTransacsImprovementLCD()
        self.generateIATLCD()
        self.generateIATLCDImprovement()
        self.generateRTTLCD()
        self.generateRTTLCDImprovement()
        self.generateRTOsRevertsLCD()
        self.generateOutagesLCD()
        self.generateICMPsLCD()
        self.generateICMPsLCDbyScenario()
        self.generateHistogramRevertsPerRTOsLCD()
        self.generateHistogramDurartionPerRTOsLCD()
        self.generateHistogramBackoffsPerRTOsLCD()
        self.generateHistogramtTputPerRevertsLCD()
        self.generateHistogramOutagesPerRTOsLCD()
        self.generateHistogramRetransmissionsPerRTOsLCD()
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

