#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys
import os
import os.path
import subprocess
import re
import optparse
from logging import info, debug, warn, error

#from pysqlite2 import dbapi2 as sqlite 
from sqlite3 import dbapi2 as sqlite

import numpy
import scipy.stats


# umic-mesh imports
from um_application import Application
from um_functions import call

from um_analysis.analysis import Analysis
from um_gnuplot import UmHistogram, UmGnuplot, UmLinePlot, UmBoxPlot

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
        if test == "rate":
            return self.onLoadRate(record, iterationNo, scenarioNo, runNo, test)
        
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
        
        
        thruput = record.calculate("thruput")
        
        if not thruput:
            if not self.failed.has_key(run_label):
                self.failed[run_label] = 1
            else:
                self.failed[run_label] = self.failed[run_label]+1            
            return
    
        # hack to support two parallel flows 
        thruput_list = record.calculate("thruput_list")
        if len(thruput_list) == 2:
            thruput_0 = thruput_list[0]
            thruput_1 = thruput_list[1]
        else:
            thruput_0 = 0.0
            thruput_1 = 0.0

        dbcur.execute("""
                      INSERT INTO tests VALUES (%u, %u, %u, %s, %s, %f, %f, %f, %u, "$%s$", "%s", "%s")
                      """ % (iterationNo, scenarioNo, runNo, src, dst, thruput, thruput_0, thruput_1,
                             start_time, run_label, scenario_label, test))

    def onLoadRate(self, record, iterationNo, scenarioNo, runNo, test):
        dbcur = self.dbcon.cursor()

        recordHeader = record.getHeader()
        src = recordHeader["rate_src"]
        dst = recordHeader["rate_dst"]
        run_label = recordHeader["run_label"]
        scenario_label = recordHeader["scenario_label"]

        rates = record.calculate("pkt_rates_tx")
        avg_rate = record.calculate("average_rate")

        if not avg_rate:
            return
        
        dbcur.execute("""
                      INSERT INTO tests_rate VALUES (%u, %u, %u, %f)
                      """ % (iterationNo,scenarioNo,runNo,avg_rate))


    def generateTputOverTime(self, orderby="iterationNo, runNo, scenarioNo ASC"):

        dbcur = self.dbcon.cursor()

        thruputs = dict()
        times    = dict()
        dbcur.execute('''
        SELECT iterationNo, runNo, scenarioNo, thruput, start_time
        FROM tests 
        ORDER by %s
        ''' %orderby )

        sorted_keys = list()
        for row in dbcur:
            (iterationNo, runNo, scenarioNo, thruput, time) = row
            key = (iterationNo,runNo,scenarioNo)        
            thruputs[key] = thruput
            if time != 0:
                times[key] = time
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
        if times:
            fh.write("# thruput rate start_time\n")
        else:
            fh.write("# thruput rate\n")

        for key in sorted_keys:
            thruput = thruputs[key]
            try:
                rate = rates[key]
            except KeyError:
                if rates:
                    warn("Oops: no rate for %u,%u,%u" %key)
                rate = 0
            if times:
                fh.write("%f %f %u\n" %(thruput,rate,times[key]))
            else:
                fh.write("%f %f\n" %(thruput,rate))

        fh.close()

        p = UmLinePlot(plotname)
        p.setYLabel(r"$\\SI{\Mbps}$")
        if times:
            p.setXLabel("Time")
            p.setXDataTime()
            # +1 hour offset to GMT
            time_offset = "+3600"
            using_str = "($3%s):" %time_offset
        else:
            using_str = ""
            p.setXLabel("test")

        p.plot(valfilename, "Throughput", using=using_str+"1", linestyle=2)

        if rates:
            p.plot(valfilename, "Avg. Rate", using=using_str+"2", linestyle=9)
    
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)
        

    def generateTputOverTimePerRun(self):
        dbcur = self.dbcon.cursor()

        # get runs
        dbcur.execute('''
        SELECT DISTINCT runNo, run_label
        ROM tests ORDER BY runNo'''
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

        outdir = self.options.outdir
        p = UmLinePlot("tput_over_time_per_run")
        p.setYLabel(r"$\\SI{\Mbps}$")


        for runNo in runs.keys():

            thruputs = dict()
            rates    = dict()
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

            dbcur.execute('''
            SELECT iterationNo, scenarioNo, avg_rate
            FROM tests_rate
            WHERE runNo=%u
            ORDER by iterationNo ASC
            ''' %(runNo) )

            for row in dbcur:
                (iterationNo, scenarioNo, avg_rate) = row
                key = (iterationNo,runNo,scenarioNo)        
                rates[key] = avg_rate

            plotname = "tput_over_time_per_run_r%u" %(runNo)
            valfilename = os.path.join(outdir, plotname+".values")

            info("Generating %s..." % valfilename)
            fh = file(valfilename, "w")
            
            # header
            if times:
                fh.write("# thruput rate start_time\n")
            else:
                fh.write("# thruput rate\n")


            
            # generate values file
            for key in sorted_keys:
                thruput = thruputs[key]
                try:
                    rate = rates[key]
                except KeyError:
                    rate = 0

                if times:
                    fh.write("%f %f %u\n" %(thruput,rate,times[key]))
                else:
                    fh.write("%f %f\n" %(thruput,rate))
                    
            fh.close()

                
            if runNo == 0 and times:
                p.setXLabel("time")
                p.setXDataTime()
                # +1 hour offset to GMT
                time_offset = "+3600"
                using_str = "($3%s):" %time_offset
            elif runNo == 0 and not times:
                p.setXLabel("test")
                using_str = ""

            p.plot(valfilename, "thruput "+runs[runNo], linestyle=runNo+1, using=using_str+"1")

            if rates:
                p.plot(valfilename, "rate "+runs[runNo], linestyle=runNo+1, using=using_str+"2")
        

        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

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
        fh.write("# label MIN(thruput) MAX(thruput) avg_thruput no_of_tests\n")

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
        g.setBarsPerCluster(limit)
        g.plot('"%s" using 4:xtic(1) title "Throughput" ls 1' % bestfilename)
        
        g.save(self.options.outdir, self.options.debug, self.options.cfgfile)
        

    def calculateStdDev(self, rlabel, slabel, key="thruput"):
        """
        Calculates the standarddeviation of all values of the same rlabel
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



    def generateHistogram2Flows(self):
        """ Generates a histogram with scenario labels for two parallel flows
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
        MIN(thruput_0) as min_thruput_0,
        MAX(thruput_0) as max_thruput_0,
        AVG(thruput_0) as avg_thruput_0,
        MIN(thruput_1) as min_thruput_1,
        MAX(thruput_1) as max_thruput_1,
        AVG(thruput_1) as avg_thruput_1,
        SUM(1)
        FROM tests GROUP BY run_label, scenarioNo ORDER BY avg_thruput DESC, scenarioNo ASC
        ''')

        # outfile
        outdir        = self.options.outdir
        plotname      = "scenario_compare_2flow" 
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
            fh.write("min_tput_0%(v)s max_tput_0%(v)s avg_tput_0%(v)s std_tput_0%(v)s notests_%(v)s" %{ "v" : val })
            fh.write("min_tput_1%(v)s max_tput_1%(v)s avg_tput_1%(v)s std_tput_1%(v)s notests_%(v)s" %{ "v" : val })
            
        fh.write("\n")

        sorted_labels = list()
        for row in dbcur:
            (rlabel,slabel,sno,
             min_thruput,max_thruput,avg_thruput,
             min_thruput_0,max_thruput_0,avg_thruput_0,
             min_thruput_1,max_thruput_1,avg_thruput_1,
             notests) = row

            std_thruput  = self.calculateStdDev(rlabel, slabel, "thruput")
            std_thruput_0 = self.calculateStdDev(rlabel, slabel, "thruput_0")
            std_thruput_1 = self.calculateStdDev(rlabel, slabel, "thruput_1")

            if not data.has_key(rlabel):
                tmp = list()
                for key in keys:
                    tmp.append("0.0 0.0 0.0 0.0 0")
                    tmp.append("0.0 0.0 0.0 0.0 0")
                    tmp.append("0.0 0.0 0.0 0.0 0")
                data[rlabel] = tmp
                sorted_labels.append(rlabel)

            data[rlabel][sno] = "%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" % (
                                 min_thruput,max_thruput,avg_thruput,std_thruput,notests,
                                 min_thruput_0,max_thruput_0,avg_thruput_0,std_thruput_0,notests,
                                 min_thruput_1,max_thruput_1,avg_thruput_1,std_thruput_1,notests)
                                
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

        g.setYLabel(r"Throughput in $\\SI{\Mbps}$")
        g.setClusters(limit)
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
#            buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key], using="%u:xtic(1)" %(4+(i*15)), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" Flow 0", using="%u:xtic(1)" %(9+(i*15)), linestyle=(i+1))
            g.plotBar(valfilename, title=scenarios[key]+" Flow 1", using="%u:xtic(1)" %(14+(i*15)), linestyle=(i+1))
        
        # errobars
        for i in range(len(keys)):
            # TODO: calculate offset with scenarios and gap
            if i == 0:
                g.plotErrorbar(valfilename, i, 4+(i*15),5+(i*15), "Standard Deviation")
                g.plotErrorbar(valfilename, i+1, 9+(i*15),10+(i*15))
                g.plotErrorbar(valfilename, i+2, 14+(i*15),15+(i*15))
            else:            
                g.plotErrorbar(valfilename, i*3, 4+(i*15),5+(i*15))
                g.plotErrorbar(valfilename, i*3+1, 9+(i*15),10+(i*15))
                g.plotErrorbar(valfilename, i*3+2, 14+(i*15),15+(i*15))

        # output plot
        g.save(self.options.outdir, self.options.debug, self.options.cfgfile)


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

        g.setYLabel(r"Throughput in $\\SI{\Mbps}$")
        g.setClusters(limit)
        g.setYRange("[ 0 : * ]")

        # bars
        for i in range(len(keys)):
            key = keys[i]
#            buf = '"%s" using %u:xtic(1) title "%s" ls %u' %(valfilename, 4+(i*5), scenarios[key], i+1)
            g.plotBar(valfilename, title=scenarios[key], using="%u:xtic(1)" %(4+(i*5)), linestyle=(i+1))
        
        # errobars
        for i in range(len(keys)):
            # TODO: calculate offset with scenarios and gap
            if i == 0:
                g.plotErrorbar(valfilename, i, 4+(i*5),5+(i*5), "Standard Deviation")
            else:            
                g.plotErrorbar(valfilename, i, 4+(i*5),5+(i*5))

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

        g.setXLabel(r"Throughput in $\\SI{\Mbps}$")
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
            self.generateTputDistribution(run, 100)
    

    def normaltest(self, data, m):
        ary = numpy.array(data)        
        (hist, bins) = numpy.histogram(ary, bins=m)

        # number of observations
        n = len(data)

        # parameter estimation for the normal distribution
        mu  = ary.mean()
        std = ary.std()

        # create normal distribution with these values
        norm = scipy.stats.norm(loc=mu, scale=std)

        # literature recommends at least non zero frequency for each bin
        if (hist.min() == 0):
            warn("chisquaretonormal: there are empty bins! Please lower classes!")

        chi_square = 0

        # expected frequencies
        exp = list()
        for i in range(m):
            left = bins[i]
            if (m-1)==i:
                right = ary.max()
            else:
                right = bins[i+1]            
            
            # compute the expected 0-hyptohesis count for bin i
            hyp = (norm.cdf(right) - norm.cdf(left)) * n
            exp.append(hyp)

            # observed value for bin i
            obs = hist[i]

            # update chi square score
            chi_square += (obs-hyp)**2/hyp

        # degrees of freedom (2 parameters were estimated for normal distribution)
        df = m-2-1

#        info("Chi-Square-Test score (mine) : %f" %chi_square)
        #(chi_square_score, p_value) = scipy.stats.chisquare(hist, numpy.array(exp))
        chi_p_value = scipy.stats.chisqprob(chi_square, df)
        info("Chi-square test score     : %f" %chi_square)
        info("Chi-square deg. of freed. : %d" %df)
        info("Chi-square test p-value   : %f" %chi_p_value)
        info("Chi-square test passed    : %s" %(chi_p_value > 0.05))

        # omnibus test
	try:
        	(omnibus_score, omnibus_tail) = scipy.stats.normaltest(data)
        	omnibus_p_value = scipy.stats.chisqprob(omnibus_score, 2)[0]
        	info("Omnibus test score        : %f" %omnibus_score)
        	info("Omnibus test p-value      : %f" %omnibus_p_value)
        	info("Omnibus test 2-tail       : %f" %omnibus_tail)
        	info("Omnibus test passed       : %s" %(omnibus_p_value > 0.05))
	except:
		info("Omnibus computation raised an exception!")
        
    
               
    def generateTputDistribution(self, run, noBins):
        (runNo, run_label) = run

        dbcur = self.dbcon.cursor()
        # load data into a numpy array
        dbcur.execute('''
        SELECT thruput
        FROM tests
        WHERE runNo=%u;
        ''' %runNo)

        ary = numpy.array(dbcur.fetchall())

        plotname = "tput_distribution_r%u_b%u" %(runNo, noBins)

        outdir = self.options.outdir
        valfilename = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        # header
        fh.write("# %s\n" %plotname)
        fh.write("# lower_edge_of_bin tput\n")

        (n, bins) = numpy.histogram(ary, bins=noBins, normed=1)

        for i in range(len(n)):
            fh.write("%0.2f %f\n" %(bins[i], n[i]))

        fh.close()

        p = UmBoxPlot(plotname)
        p.setXLabel(r"Throughput in $\\SI{\Mbps}$")
        p.setYLabel("Frequency")
        p.plot(valfilename,"Frequency", using="1:2", linestyle=1)

        mu  = ary.mean()
        std = ary.std()
        self.normaltest(ary,noBins)
        
        f = "exp(-0.5*((x-%f)/%f)**2)/(%f*sqrt(2*pi))" %(mu,std,std)
        p.rawPlot('%s with lines title "Normal Distribution"' %f)
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)
        
        

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
                            thruput_0   DOUBLE,
                            thruput_1   DOUBLE,
                            start_time  INTEGER,
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
        self.loadRecords(tests=["flowgrind","rate"])

        self.dbcon.commit()
        self.generateHistogram()
        self.generateHistogram2Flows()
        self.generateTputOverTimePerRun()
        self.generateTputOverTime()
        self.generateTputDistributions()
        self.generateAccTputDistribution(50)
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

