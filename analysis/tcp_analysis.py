#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys
import os
import os.path
import subprocess
import re
import optparse
import gc
from logging import info, debug, warn, error

#from pysqlite2 import dbapi2 as sqlite 
from sqlite3 import dbapi2 as sqlite

import numpy

# umic-mesh imports
from um_application import Application
from um_functions import call

from um_analysis.analysis import Analysis
from um_gnuplot import UmHistogram, UmGnuplot, UmPointPlot

class TcpAnalysis(Analysis):
    """ Application for analysis of flowgrind results """

    def __init__(self):

        Analysis.__init__(self)
        self.parser.set_defaults(outprefix= "neighbors", quality = 100,
                                 indir  = "./",
                                 outdir = "./",
                                 digraph=False)
        
        self.parser.add_option('-P', '--prefix', metavar="PREFIX",
                        action = 'store', type = 'string', dest = 'outprefix',
                        help = 'Set prefix of output files [default: %default]')



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
        
        thruput = record.calculate("thruput")
        
        if not thruput:
            if not self.failed.has_key(run_label):
                self.failed[run_label] = 1
            else:
                self.failed[run_label] = self.failed[run_label]+1            
            return

        dbcur.execute("""
                      INSERT INTO tests VALUES (%u, %u, %u, %s, %s, %f, "$%s$", "%s", "%s")
                      """ % (iterationNo,scenarioNo,runNo,src,dst, thruput, run_label, scenario_label, test))

    def onLoadRate(self, record, iterationNo, scenarioNo, runNo, test):
        dbcur = self.dbcon.cursor()

        recordHeader = record.getHeader()
        src = recordHeader["rate_src"]
        dst = recordHeader["rate_dst"]
        run_label = recordHeader["run_label"]
        scenario_label = recordHeader["scenario_label"]

        rates = record.calculate("pkt_rates_tx")
        avg_rate = record.calculate("average_rate")

        dbcur.execute("""
                      INSERT INTO tests_rate VALUES (%u, %u, %u, %f)
                      """ % (iterationNo,scenarioNo,runNo,avg_rate))


    def generateTputOverIterations(self):
        """ Generate a tput histogram """
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


        for runNo in runs.keys():
            self.generateTputOverIteration(runNo)


    def generateTputOverTime(self, orderby="iterationNo, runNo, scenarioNo ASC"):

        dbcur = self.dbcon.cursor()

        thruputs = dict()
        dbcur.execute('''
        SELECT iterationNo, runNo, scenarioNo, thruput
        FROM tests 
        ORDER by %s
        ''' %orderby )

        sorted_keys = list()
        for row in dbcur:
            (iterationNo, runNo, scenarioNo,val) = row
            key = (iterationNo,runNo,scenarioNo)        
            thruputs[key] = val
            sorted_keys.append(key)

        rates = dict()        
        dbcur.execute('''
        SELECT iterationNo, runNo, scenarioNo, avg_rate
        FROM tests_rate
        ORDER by %s
        ''' %orderby )

        for row in dbcur:
            (iterationNo, runNo, scenarioNo,val) = row
            key = (iterationNo,runNo,scenarioNo)
            rates[key] = val

        plotname = "tput_over_time" 
        outdir = self.options.outdir
        valfilename = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # header
        fh.write("# thruput rate\n")

        for key in sorted_keys:
            thruput = thruputs[key]
            try:
                rate = rates[key]
            except KeyError:
                if rates:
                    warn("Oops: no rate for %u,%u,%u" %key)
                rate = 0

            fh.write("%f %f\n" %(thruput,rate))

        fh.close()

        p = UmPointPlot(plotname)
        p.setYLabel(r"$\\Mbps$")
        p.setXLabel("test")
        
        p.plot(valfilename, "Thruput", using=1, linestyle=2)

        if rates:
            p.plot(valfilename, "Avg. Rate", using=2, linestyle=9)
    
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)
        

    def generateTputOverIteration(self, runNo):
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

        thruputs = dict()
        rates    = dict()
        scenarioNo = 0
        
        dbcur.execute('''
        SELECT iterationNo, thruput
        FROM tests 
        WHERE runNo=%u AND scenarioNo=%u
        ORDER by iterationNo ASC
        ''' %(runNo, scenarioNo) )

        for row in dbcur:
            (key,val) = row
            thruputs[key] = val

        debug(thruputs)

        dbcur.execute('''
        SELECT iterationNo, avg_rate
        FROM tests_rate
        WHERE runNo=%u AND scenarioNo=%u
        ORDER by iterationNo ASC
        ''' %(runNo, scenarioNo) )

        for row in dbcur:
            (key,val) = row
            rates[key] = val

        plotname = "tput_over_iteration_s%u_r%u" %(scenarioNo, runNo)
        outdir = self.options.outdir
        valfilename = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # header
        fh.write("# iteration thruput rate\n")

        keys = thruputs.keys()
        keys.sort()
        # generate values file
        for key in keys:
            thruput = thruputs[key]
            try:
                rate = rates[key]
            except KeyError:
                rate = 0

            fh.write("%s %f %f\n" %(key,thruput,rate))

        fh.close()            
        
    

    def generateAccHistogram(self):
        """ Generates a histogram of the 10 best pairs (avg_thruput).
            Thruput is accumulated for one run_label """

        dbcur = self.dbcon.cursor()

        # accumulate all scenarios and just distinct via run, limit to 10
        limit = 10
        sortby = "avg_thruput"

        # get unique "runs" and sum up thruput
        dbcur.execute('''
        SELECT run_label,
        MIN(thruput) as min_thruput,
        MAX(thruput) as max_thruput,
        SUM(thruput)/SUM(1) as avg_thruput,
        SUM(1)
        FROM tests GROUP BY src, dst ORDER BY %s DESC LIMIT %d
        ''' %(sortby, limit) )


        # outfile
        outdir = self.options.outdir
        plotname = "best_%d_pairs_acc" %limit
        bestfilename = os.path.join(outdir, plotname+".values")
        
        info("Generating %s..." % bestfilename)

        fh = file(bestfilename, "w")

        # print header
        fh.write("# label MIN(thruput) MAX(thruput) avg_thruput no_of_thruputs no_of_failed\n")

        for row in dbcur:
            (label,min_thruput,max_thruput,avg_thruput,notests) = row
            if self.failed.has_key(label):
                nofailed = self.failed[label]
            else:
                nofailed = 0
            fh.write('"%s" %f %f %f %d' % row)
            fh.write(' %d\n' % nofailed)

        fh.close()

        g = UmHistogram(plotname)

        g.setYLabel(r"Throughput in $\\Mbps$")
        g.setBars(limit)
        g.plot('"%s" using 4:xtic(1) title "Thruput" ls 1' % bestfilename)
        
        g.save(self.options.outdir, self.options.debug, self.options.cfgfile)
        

    def calculateStdDev(self, rlabel, slabel):
        """
        Calculates the standarddeviation of all values of the same rlabel
        and scenarioNo
        """

        dbcur = self.dbcon.cursor()

        query = '''
        SELECT thruput FROM tests WHERE
        scenario_label="%s" AND run_label="%s";
        ''' %(slabel,rlabel)

        dbcur.execute(query)

        ary = numpy.array(dbcur.fetchall())

        return ary.std()


    def generateHistogram(self):
        """ Generates a histogram with scenario labels.
        """

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
        MIN(thruput) as min_thruput,
        MAX(thruput) as max_thruput,
        AVG(thruput) as avg_thruput,
        SUM(1)
        FROM tests GROUP BY run_label, scenarioNo ORDER BY avg_thruput DESC, scenarioNo ASC
        ''')

        # outfile
        outdir        = self.options.outdir
        plotname      = "scenario_compare" 
        valfilename  = os.path.join(outdir, plotname+".values")

        
        info("Generating %s..." % valfilename)

        fh = file(valfilename, "w")

        # print header
        fh.write("# run_label no_of_thruputs no_of_failed ")

        # one line per runlabel
        data = dict()

        # columns
        keys = scenarios.keys()
        keys.sort()
        for key in scenarios.keys():
            val = scenarios[key]
            fh.write("min_tput_%(v)s max_tput_%(v)s avg_tput_%(v)s std_tput_%(v)s notests_%(v)s" %{ "v" : val })

            
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,slabel,sno,min_thruput,max_thruput,avg_thruput,notests) = row
            std_thruput = self.calculateStdDev(rlabel, slabel)
            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%s %s %s %s %s" %(min_thruput,max_thruput,avg_thruput,std_thruput,notests)
            debug(row)


        i = 0
        # only display first LIMIT scenarios
        limit = 10
        
        for key in sorted_labels:
            value = data[key]
            fh.write("%s" %key)
            for val in value:
                fh.write(" %s" %val)
            fh.write("\n")
            i += 1
            if i>limit:
                break
        
        fh.close()

        g = UmHistogram(plotname)

        g.setYLabel(r"Throughput in $\\Mbps$")
        g.setScenarios(len(scenarios))
        g.setBars(limit)
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
            buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key],i+1)
            g.plot(buf)
        

        # errobars
        for i in range(len(keys)):
            title = "notitle"
            # TODO: calculate offset with scenarios and gap
            if i == 0:
                title = 'title "Standard Deviation"'
                off = -0.3
            elif i == 1:
                off = -0.1
            elif i == 2:
                off = 0.1
            elif i == 3:
                off = 0.3

            buf = '"%s" using ($0+%f):%u:%u %s with errorbars ls 2' %(valfilename, off, 4+(i*5), 5+(i*5), title)
            g.plot(buf)

        

        # output plot
        g.save(self.options.outdir, self.options.debug, self.options.cfgfile)




    def generateCumulativeFractionOfPairs(self):
        dbcur = self.dbcon.cursor()
        
        # get number of unique pairs
        dbcur.execute('''
        SELECT COUNT(DISTINCT run_label) FROM tests 
        ''')

        pairs = dbcur.fetchone()[0]
        info("Found %u unique pairs" %pairs)
        
        # get unique pairs and calculate avg_thruput, sort by it
        dbcur.execute('''
        SELECT
        SUM(thruput)/SUM(1) as avg_thruput,
        SUM(1)
        FROM tests GROUP BY src, dst ORDER BY avg_thruput ASC
        ''')

        outdir = self.options.outdir
        plotname = "fraction_of_pairs" 
        valfilename = os.path.join(outdir, plotname+".values")
        
        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # header
        fh.write("# fraction of pairs\n")
        fh.write("# avg_thruput fraction\n")

        i = 1
        for row in dbcur:
            (avg_thruput,notests) = row
            fraction = float(i)/float(pairs)
            fh.write("%f %f\n" %(avg_thruput, fraction))
            i = i+1


        fh.close()

        g = UmGnuplot(plotname)

        g.setXLabel(r"Throughput in $\\Mbps$")
        g.setYLabel("Fraction of Pairs")
        
        g.plot('"%s" using 1:2 title "1-Hop" ls 1 with steps' % valfilename)


        # output plot
        g.save(self.options.outdir, self.options.debug, self.options.cfgfile)




    def generateTputDistributions(self):
        """ Generate a tput histogram """
        dbcur = self.dbcon.cursor()

        # get scenarios 
        dbcur.execute('''
        SELECT DISTINCT scenarioNo, scenario_label
        FROM tests ORDER BY scenarioNo'''
        )
        scenarios = dict()
        for row in dbcur:
            (key,val) = row
            scenarios[key] = val

        # and runs
        dbcur.execute('''
        SELECT DISTINCT runNo, run_label
        FROM tests ORDER BY runNo'''
        )
        runs = dict()
        for row in dbcur:
            (key,val) = row
            runs[key] = val


        # iterate over every scenario and run an generate a grahic
        for run in runs.iteritems():
            for scenario in scenarios.iteritems():
                self.generateTputDistribution(run, scenario, 10)
        

    def generateTputDistribution(self, run, scenario, noBins):
        (runNo, run_label) = run
        (scenarioNo, scenario_label) = scenario

        dbcur = self.dbcon.cursor()
        # load data into a numpy array
        dbcur.execute('''
        SELECT thruput
        FROM tests
        WHERE runNo=%u AND scenarioNo=%u;
        ''' %(runNo, scenarioNo))

        ary = numpy.array(dbcur.fetchall())

        plotname = "tput_distribution_s%u_r%u_b%u" %(scenarioNo, runNo, noBins)

        outdir = self.options.outdir
        valfilename = os.path.join(outdir, plotname+".values")


        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # header
        fh.write("# %s\n" %plotname)
        fh.write("# lower_edge_of_bin tput\n")

        (n, bins) = numpy.histogram(ary, bins=noBins, normed=1)

        for i in range(len(n)):
            fh.write("%f %f\n" %(bins[i], n[i]))

        fh.close()

    def generateAccTputDistribution(self, noBins):

        dbcur = self.dbcon.cursor()
        # load data into a numpy array
        dbcur.execute('''
        SELECT thruput
        FROM tests;
        ''')

        ary = numpy.array(dbcur.fetchall())

        plotname = "tput_distribution_acc_b%u" %(noBins)

        outdir = self.options.outdir
        valfilename = os.path.join(outdir, plotname+".values")


        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # header
        fh.write("# %s\n" %plotname)
        fh.write("# lower_edge_of_bin tput\n")

        (n, bins) = numpy.histogram(ary, bins=noBins, normed=1)

        for i in range(len(n)):
            fh.write("%f %f\n" %(bins[i], n[i]))

        fh.close()


    def run(self):
        "Main Method"

        # database in memory to access data efficiently
        self.dbcon = sqlite.connect(':memory:')
        dbcur = self.dbcon.cursor()
        dbcur.execute("""
        CREATE TABLE tests (iterationNo INTEGER,
                            scenarioNo  INTEGER,
                            runNo       INTEGER,
                            src         INTEGER,
                            dst         INTEGER,                            
                            thruput     DOUBLE,
                            run_label   VARCHAR(70),
                            scenario_label VARCHAR(70),
                            test        VARCHAR(50))
        """)

        dbcur.execute("""
        CREATE TABLE tests_rate (iterationNo INTEGER,
                                 scenarioNo  INTEGER,
                                 runNo       INTEGER,
                                 avg_rate    DOUBLE
                            )
        """)

        # store failed test as a mapping from run_label to number
        self.failed = dict()

        # only load flowgrind test records    
        self.loadRecords(tests=["rate"],onLoad=self.onLoadRate)
        self.loadRecords(tests=["flowgrind"])
                        
        self.dbcon.commit()
        self.generateTputOverTime()
        self.generateTputDistributions()
        self.generateAccTputDistribution(50)
        self.generateHistogram()
        self.generateAccHistogram()
        self.generateCumulativeFractionOfPairs()        
        
                    
    def main(self):
        "Main method of the ping stats object"

        self.parse_option()
        self.set_option()
        TcpAnalysis.run(self)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    TcpAnalysis().main()

