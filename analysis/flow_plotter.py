#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

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
        usage = "Usage: %prog [options] flowgrind-log [flowgrind-log] ...\n"\
                "Creates graphs given by -G for every flowgrind-log specified."

        self.parser.set_usage(usage)
        self.parser.set_defaults(outdir = "./", flownumber="0", resample='0',
                                 plotsrc='True', plotdst='False', graphics='tput,cwnd,rtt,segments' )
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
                        action = 'store', type = 'float', dest = 'resample',
                        help = 'resample to this sample rate [default:'\
                               ' dont resample]')
        self.parser.add_option("-s", "--plot-source", metavar = "Bool",
                        action = 'store', dest = 'plotsrc', choices = ['True','False'],
                        help = 'plot source cwnd and throughput '\
                               '[default: %default]')
        self.parser.add_option("-d", "--plot-dest", metavar = "Bool",
                        action = 'store', dest = 'plotdst', choices = ['True','False'],
                        help = 'plot destination cwnd and throughput '\
                               '[default: %default]')
        self.parser.add_option("-G", "--graphics", metavar = "list",
                        action = 'store', dest = 'graphics',
                        help = 'Graphics that will be plotted '\
                                '[default: %default; optional: dupthresh]')

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        if len(self.args) < 1:
            error("no input files, stop.")
            sys.exit(1)

        if not os.path.exists(self.options.outdir):
            info("%s does not exist, creating. " % self.options.outdir)
            os.mkdir(self.options.outdir)

        if self.options.graphics:
            self.graphics_array = self.options.graphics.split(',')
        else:
            self.graphics_array = ['tput','cwnd','rtt','segments']

    def resample(self, record, directions, nosamples, flow):
        # get sample rate for resampling
        sample = float(record.results['reporting_interval'][0])
        resample = float(self.options.resample)
        rate = resample/sample
        debug("sample = %s, resample = %s -> rate = %s" %(sample, resample, rate))

        if resample > 0:
            if rate <= 1 :
                error("sample = %s, resample = %s -> rate = %s -> rate <= 1 !" %(sample, resample, rate))
                sys.exit(1)

            for d in directions:
                for key in (flow[d].keys()):
                    data = flow[d][key]

                    # check if data is number
                    try:
                        float(data[0])
                    except:
                        continue
                    debug("type: %s" %key)

                    #actual resampling happens here
                    next = 0    # where to store the next resample (at the end this is the number of points)
                    all = 0     # where are we in the list?
                    while all < nosamples:
                        sum = 0         # sum of all parts
                        r = rate        # how much to sum up

                        if all != int(all):             # not an int
                            frac = 1 - (all - int(all)) # get the fraction which has not yet been included
                            sum += frac * data[int(all)]
                            all += frac
                            r -= frac

                        while r >= 1:
                            if all < nosamples:
                                sum += data[int(all)]
                                all += 1
                                r -= 1
                            else: break

                        if r > 0 and all < nosamples:
                            sum += r * data[int(all)]
                            all += r
                            r = 0

                        out = sum/(rate-r)  # out is the value for the interval
                                            # r is not 0, if we are at the end of the list
                        data[next] = out
                        next += 1

                    #truncate table to new size
                    del flow[d][key][next:nosamples]

                # set begin and end time
                for i in range(next):
                    flow[d]['begin'][i] = i*resample
                    flow[d]['end'][i] = (i+1)*resample

            debug("new nosamples: %i" %next)
            return next
        else: return nosamples  # resample == 0


    def plot(self, infile, outdir=None):
        """Plot one file"""

        def ssth_max(ssth):
            SSTHRESH_MAX = 2147483647
            X = 50
            if ssth == SSTHRESH_MAX:  return 0
            elif ssth > cwnd_max + X: return cwnd_max + X
            else:                     return ssth

        def rto_max(rto):
            if rto == 3000: return 0
            else:           return rto

        if not outdir:
            outdir=self.options.outdir

        # create record from given file
        flownumber = self.options.flownumber
        record = self.factory.createRecord(infile, "flowgrind")
        flows = record.calculate("flows")

        cwnd_max = 0

        if flownumber > len(flows):
            error("requested flow number %i greater then flows in file: %i"
                    %(flownumber,len(flows) ) )
            sys.exit(1)
        flow = flows[flownumber]

        plotname = os.path.splitext(os.path.basename(infile))[0]
        valfilename = os.path.join(outdir, plotname+".values")

        # to avoid code duplicates
        directions = ['S', 'R']
        nosamples = min(flow['S']['size'], flow['R']['size'])
        debug("nosamples: %i" %nosamples)

        # get max cwnd for ssth output
        for i in range(nosamples):
            for dir in directions:
                if flow[dir]['cwnd'][i] > cwnd_max:
                    cwnd_max = flow[dir]['cwnd'][i]

        # resampling
        nosamples = self.resample(record, directions, nosamples, flow)  # returns the new value for nosamples if anything was changed

        info("Generating %s..." % valfilename)
        fh = file(valfilename, "w")
        # header
        fh.write("# start_time end_time forward_tput reverse_tput forward_cwnd reverse_cwnd ssth krtt krto lost reor fret tret dupthresh\n")
        for i in range(nosamples):
            formatfields = (flow['S']['begin'][i],
                            flow['S']['end'][i],
                            flow['S']['tput'][i],
                            flow['R']['tput'][i],
                            flow['S']['cwnd'][i],
                            flow['R']['cwnd'][i],
                            ssth_max(flow['S']['ssth'][i]),
                            flow['S']['krtt'][i],
                            rto_max(flow['S']['krto'][i]),
                            flow['S']['lost'][i],
                            flow['S']['reor'][i],
                            flow['S']['fret'][i],
                            flow['S']['tret'][i] )
            formatstring = "%f %f %f %f %f %f %f %f %f %f %f %f %f"
            if 'dupthresh' in self.graphics_array:
                formatfields += tuple([flow['S']['dupthresh'][i]])
                formatstring += " %f"
            formatstring += "\n"
            fh.write( formatstring % formatfields )
        fh.close()

        if 'tput' in self.graphics_array:
            # tput
            p = UmLinePlot(plotname+'_tput')
            p.setYLabel(r"Throughput ($\\si[per=frac,fraction=nice]{\\Mbps}$)")
            p.setXLabel(r"time ($\\si{\\second}$)")
            if self.options.plotsrc == 'True': p.plot(valfilename, "forward path", using="2:3", linestyle=2)
            if self.options.plotdst == 'True': p.plot(valfilename, "reverse path", using="2:4", linestyle=3)
            # output plot
            p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        if 'cwnd' in self.graphics_array:
            # cwnd
            p = UmLinePlot(plotname+'_cwnd_ssth')
            p.setYLabel(r"$\\#$")
            p.setXLabel(r"time ($\\si{\\second}$)")
            if self.options.plotsrc == 'True': p.plot(valfilename, "Sender CWND", using="2:5", linestyle=2)
            if self.options.plotdst == 'True': p.plot(valfilename, "Receiver CWND", using="2:6", linestyle=3)
            p.plot(valfilename, "SSTH", using="2:7", linestyle=1)
            # output plot
            p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        if 'rtt' in self.graphics_array:
            # rto, rtt
            p = UmLinePlot(plotname+'_rto_rtt')
            p.setYLabel(r"$\\si{\\milli\\second}$")
            p.setXLabel(r"time ($\\si{\\second}$)")
            p.plot(valfilename, "RTO", using="2:9", linestyle=2)
            p.plot(valfilename, "RTT", using="2:8", linestyle=3)
            # output plot
            p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        if 'segments' in self.graphics_array:
            # lost, reorder, retransmit
            p = UmLinePlot(plotname+'_lost_reor_retr')
            p.setYLabel(r"$\\#$")
            p.setXLabel(r"time ($\\si{\\second}$)")
            p.plot(valfilename, "lost segments", using="2:10", linestyle=2)
            p.plot(valfilename, "reordered segments", using="2:11", linestyle=3)
            p.plot(valfilename, "fast retransmits", using="2:12", linestyle=4)
            p.plot(valfilename, "timeout retransmits", using="2:13", linestyle=5)
            # output plot
            p.save(self.options.outdir, self.options.debug, self.options.cfgfile)

        if 'dupthresh' in self.graphics_array:
            # dupthresh, tp->reordering
            p = UmLinePlot(plotname+'_reordering_dupthresh')
            p.setYLabel(r"dupack threshold $\\mathit{metric}$")
            p.setXLabel(r"time ($\\si{\\second}$)")
            max_y_value = max(flow['S']['dupthresh'])
            p.setYRange("[*:%u]" % int(max_y_value + ((20 * max_y_value) / 100 )))
            p.plot(valfilename, "tp->reordering", using="2:11", linestyle=2)
            p.plot(valfilename, "Algorithm DupThresh", using="2:14", linestyle=3)
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

