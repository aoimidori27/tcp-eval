#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys
import os.path
from logging import info, debug, warn, error

# umic-mesh imports
from um_analysis.testrecords_flowgrind import FlowgrindRecordFactory
from um_gnuplot import UmHistogram, UmGnuplot, UmLinePlot, UmBoxPlot
from um_application import Application

class FlowPlotter(Application):
    def __init__(self):
        Application.__init__(self)

        # object variables
        self.factory = FlowgrindRecordFactory()

        # initialization of the option parser
        usage = "usage: %prog [options] file [file]..."

        self.parser.set_usage(usage)
        self.parser.set_defaults(outdir = "./", number="0")
        self.parser.add_option('-O', '--output', metavar="OutDir",
                        action = 'store', type = 'string', dest = 'outdir',
                        help = 'Set outputdirectory [default: %default]')
        self.parser.add_option("-c", "--cfg", metavar = "FILE",
                        action = "store", dest = "cfgfile",
                        help = "use the file as config file for LaTeX. "\
                               "No default packages will be loaded.")
        self.parser.add_option("-n", "--number", metavar = "Number",
	                    action = 'store', type = 'int', dest = 'number',
			            help = 'print flow number [default: %default]')

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        if len(self.args) < 1:
            error("no input files, stop.")
            sys.exit(1)

        if not os.path.exists(self.options.outdir):
            info("%s does not exist, creating. " % self.options.outdir)
            os.mkdir(self.options.outdir)

    def plot(self, infile, outdir=None):
        def ssth_max(ssth, cwnd_max, x):
            if ssth > cwnd_max+x:
                return cwnd_max+x
            else:
                return ssth

        if not outdir:
            outdir=self.options.outdir
        number = self.options.number
        record = self.factory.createRecord(infile, "flowgrind")
        flows = record.calculate("flows")

        plotname = os.path.splitext(os.path.basename(infile))[0]
        valfilename = os.path.join(outdir, plotname+".values")

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        if number > len(flows):
	        warn("requested flow number %i greater then flows in file: %i" %(number,len(flows) ) )
		    exit(1)
        flow = flows[number]

        #get max cwnd for ssth output
        cwnd_max = 0
        for i in range(flow['S']['size']):
            if flow['S']['cwnd'][i] > cwnd_max:
                cwnd_max = flow['S']['cwnd'][i]
            if flow['R']['cwnd'][i] > cwnd_max:
                cwnd_max = flow['R']['cwnd'][i]

        # header
        fh.write("# start_time end_time forward_tput reverse_tput\n")
        for i in range(flow['S']['size']):
            fh.write("%f %f %f %f %f %f %f %f %f\n" %(flow['S']['begin'][i], flow['S']['end'][i],
                                                   flow['S']['tput'][i], flow['R']['tput'][i],
                                                   flow['S']['cwnd'][i], flow['R']['cwnd'][i],
                                                   ssth_max(flow['S']['ssth'][i], cwnd_max, 50),
                                                   flow['S']['krtt'][i], flow['S']['krto'][i]))
        fh.close()

        # tput
        p = UmLinePlot(plotname+'_tput')
        p.setYLabel(r"$\\si{\mega\bit\per\second}$")
        p.setXLabel("time")
        p.plot(valfilename, "Throughput", using="2:3", linestyle=2)
        p.plot(valfilename, "reverse Throughput", using="2:4", linestyle=3)
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        # cwnd
        p = UmLinePlot(plotname+'_cwnd_ssth')
        p.setYLabel(r"$\\#$")
        p.setXLabel("time")
        p.plot(valfilename, "Sender CWND", using="2:5", linestyle=2)
        p.plot(valfilename, "Receiver CWND", using="2:6", linestyle=3)
        p.plot(valfilename, "SSTH", using="2:7", linestyle=4)
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        # rto, rtt
        p = UmLinePlot(plotname+'_rto_rtt')
        p.setYLabel(r"$\\si{\milli\second}$")
        p.setXLabel("time")
        p.plot(valfilename, "RTO", using="2:9", linestyle=2)
        p.plot(valfilename, "RTT", using="2:8", linestyle=3)
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)


    def run(self):
        """Run..."""
        for infile in self.args:
            self.plot(infile)

    def main(self):
        self.parse_options()
        self.set_options()
        self.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    FlowPlotter().main()

