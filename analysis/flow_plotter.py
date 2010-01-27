#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys
import os.path
import math
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
        self.parser.set_defaults(outdir = "./", flownumber="0", resample='0' )
        self.parser.add_option('-O', '--output', metavar="OutDir",
                        action = 'store', type = 'string', dest = 'outdir',
                        help = 'Set outputdirectory [default: %default]')
        self.parser.add_option("-c", "--cfg", metavar = "FILE",
                        action = "store", dest = "cfgfile",
                        help = "use the file as config file for LaTeX. "\
                               "No default packages will be loaded.")
        self.parser.add_option("-n", "--number", metavar = "Flownumber",
                        action = 'store', type = 'int', dest = 'flownumber',
                        help = 'print flow number [default: %default]')
        self.parser.add_option("-r", "--resample", metavar = "Count",
                        action = 'store', type = 'int', dest = 'resample',
                        help = 'resample to this number of data [default:'\
                        'dont resample]')
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

        resample = self.options.resample
        flownumber = self.options.flownumber
        record = self.factory.createRecord(infile, "flowgrind")
        flows = record.calculate("flows")

        if flownumber > len(flows):
            warn("requested flow number %i greater then flows in file: %i"
                    %(flownumber,len(flows) ) )
            exit(1)
        flow = flows[flownumber]

        plotname = os.path.splitext(os.path.basename(infile))[0]
        valfilename = os.path.join(outdir, plotname+".values")

        # to avoid code duplicates
        directions = ['S', 'R']
        nosamples = min(flow['S']['size'], flow['R']['size'])
        debug("nosamples: %i" %nosamples)

        #get max cwnd for ssth output
        cwnd_max = 0
        for i in range(nosamples):
            for dir in directions:
                if flow[dir]['cwnd'][i] > cwnd_max:
                    cwnd_max = flow[dir]['cwnd'][i]

        #resample in place
        if resample > 0:
            if resample > nosamples:
                warn("sorry, upsampling not possible")
                exit(1)
            for d in directions:
                for key in (flow[d].keys()):
                    # check if data is number
                    data = flow[d][key]
                    try:
                        float(data[0])
                    except:
                        continue
                    debug("type: %s" %key)
                    # TODO: handle _time correctly

                    for i in range(resample):
                        debug("run: %i" %i)
                        # calculate interval
                        low  = int ( math.ceil(nosamples/resample*i) ) if (i > 0) else 0
                        high = low+nosamples/resample-1
                        debug("interval: %i to %i, dir: %s" %(low,high,d) )
                        # calculate avg over interval
                        data[i] = sum(data[j] for j in range(low,high) ) / (high-low)
                        debug("resampled no: %i dir: %s value: %f " %(i,d,data[i]) )

                    #truncate table to new size
                    del flow[d][key][resample+1:nosamples]

            nosamples = resample
            debug("new nosamples: %i" %nosamples)

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")
        # header
        fh.write("# start_time end_time forward_tput reverse_tput forward_cwnd reverse_cwnd ssth krtt krto lost reor fret tret fack\n")
        for i in range(nosamples):
            fh.write("%f %f %f %f %f %f %f %f %f %f %f %f %f\n"
                                                    %(
                                                    flow['S']['begin'][i],
                                                    flow['S']['end'][i],
                                                    flow['S']['tput'][i],
                                                    flow['R']['tput'][i],
                                                    flow['S']['cwnd'][i],
                                                    flow['R']['cwnd'][i],
                                                    ssth_max(flow['S']['ssth'][i], cwnd_max, 50),
                                                    flow['S']['krtt'][i],
                                                    flow['S']['krto'][i],
                                                    flow['S']['lost'][i],
                                                    flow['S']['reor'][i],
                                                    flow['S']['fret'][i],
                                                    flow['S']['tret'][i],
                                                    ) )
        fh.close()

        # tput
        p = UmLinePlot(plotname+'_tput')
        p.setYLabel(r"Throughput ($\si{\mega\bit\per\second}$)")
        p.setXLabel(r"time ($\si{\second}$)")
        p.plot(valfilename, "forward path", using="2:3", linestyle=2)
        p.plot(valfilename, "reverse path", using="2:4", linestyle=3)
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        # cwnd
        p = UmLinePlot(plotname+'_cwnd_ssth')
        p.setYLabel(r"$\\#$")
        p.setXLabel("time ($\si{\second}$)")
        p.plot(valfilename, "Sender CWND", using="2:5", linestyle=2)
        p.plot(valfilename, "Receiver CWND", using="2:6", linestyle=3)
        p.plot(valfilename, "SSTH", using="2:7", linestyle=4)
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        # rto, rtt
        p = UmLinePlot(plotname+'_rto_rtt')
        p.setYLabel(r"$\\si{\milli\second}$")
        p.setXLabel("time ($\si{\second}$)")
        p.plot(valfilename, "RTO", using="2:9", linestyle=2)
        p.plot(valfilename, "RTT", using="2:8", linestyle=3)
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        # lost, reorder, retransmit
        p = UmLinePlot(plotname+'_lost_reor_retr')
        p.setYLabel(r"$\\#$")
        p.setXLabel("time ($\si{\second}$)")
        p.plot(valfilename, "lost packages", using="2:10", linestyle=2)
        p.plot(valfilename, "reordered packages", using="2:11", linestyle=3)
        p.plot(valfilename, "fast retransmit", using="2:12", linestyle=4)
        p.plot(valfilename, "limited transmit", using="2:13", linestyle=5)
        # output plot
        p.save(self.options.outdir, self.options.debug, self.options.cfgfile)


    def run(self):
        """Run..."""
        for infile in self.args:
            self.plot(infile)

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    FlowPlotter().main()

