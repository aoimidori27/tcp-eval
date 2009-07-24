#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
from logging import info, debug, warn, error

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
        self.parser.set_defaults(outdir = "./")
        self.parser.add_option('-O', '--output', metavar="OutDir",
                        action = 'store', type = 'string', dest = 'outdir',
                        help = 'Set outputdirectory [default: %default]')        
        self.parser.add_option("-c", "--cfg", metavar = "FILE",
                        action = "store", dest = "cfgfile",
                        help = "use the file as config file for LaTeX. "\
                               "No default packages will be loaded.")        
        
    def set_option(self):
        "Set options"
        Application.set_option(self)

        if len(self.args) < 1:
            error("no input files, stop.")
            sys.exit(1)
        
        if not os.path.exists(self.options.outdir):
            info("%s does not exist, creating. " % self.options.outdir)
            os.mkdir(self.options.outdir)

    def plot(self, infile, outdir=None):
        if not outdir:
            outdir=self.options.outdir
        record = self.factory.createRecord(infile, "flowgrind")
        flows = record.calculate("flows")

        plotname = os.path.splitext(os.path.basename(infile))[0]    
        valfilename = os.path.join(outdir, plotname+".values")
        
        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")

        flow = flows[0]

        # header
        fh.write("# start_time end_time forward_tput reverse_tput\n")
        for i in range(flow.size):
            fh.write("%f %f %f %f\n" %(flow.begin[i], flow.end[i],
                                       flow.forward_tput[i], flow.reverse_tput[i]))
        fh.close()
        
        p = UmLinePlot(plotname)
        p.setYLabel(r"$\\Mbps$")
        p.setXLabel("time")
        p.plot(valfilename, "Throughput", using="2:3", linestyle=2)
        
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)
        
    def run(self):
        """ Run... """

        for infile in self.args:
            self.plot(infile)

    
# this only runs if the module was *not* imported
if __name__ == '__main__':
    inst=FlowPlotter()
    inst.parse_option()
    inst.set_option()
    inst.run()
        

