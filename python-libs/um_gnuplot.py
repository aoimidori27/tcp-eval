#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# python imports
import gc
import os.path
import Gnuplot
from logging import info, debug, warn, error

# umic-mesh imports
from um_functions import call

"""Module for gnuplot scripting."""

class UmGnuplot():
    """A specific umic-mesh plot with convenience functions"""

    def __init__(self, plotname):
        """Plotname is for filename generation"""

        self.gplot = Gnuplot.Gnuplot()

        # turn on math environment for axis
        self.gplot('set format "$%g$"')

        # empty title use caption instead
        self.gplot('set title ""')
        # default size
        self.size = "14cm,5cm"
        # name of the plot (for building filenames)
        self._plotname = plotname

        # actual plotcmd
        self._plotcmd = None

        # colors and line styles
        self.gplot(
        """
        set style line 1 lt rgb "#F593A1" lw 1 pt 6
        set style line 2 lt rgb "dark-green" lw 1 pt 1
        set style line 3 lt rgb "navy" lw 1 pt 7 ps 1
        set style line 4 lt rgb "grey" lw 1
        set style line 5 lt rgb "#98E2E7" lw 1 pt 7 ps 1
        set style line 6 lt rgb "#B83749" lw 1 pt 7 ps 1
        set style line 7 lt rgb "#2BB1BA" lw 1 pt 7 ps 1
        """)

        # grid and other styles
        self.gplot(
        """
        set border 31 front linetype -1 linewidth 1.000
        set grid noxtics ytics nopolar back
        set boxwidth 0.9 relative
        set style fill solid 1.00 border -1
        """)

    def setYLabel(self, *args, **kwargs):
        self.gplot.set_label("ylabel", *args, **kwargs)

    def setXLabel(self, *args, **kwargs):
        self.gplot.set_label("xlabel", *args, **kwargs)

    def setOutput(self, output):
        self.gplot('set output "%s"' %output)

    def setYRange(self, *args):
        self.gplot.set_range("yrange",*args)

    def setXRange(self, *args):
        self.gplot.set_range("xrange",*args)

    def setPlotname(self, plotname):
        self._plotname = plotname

    def setXDataTime(self, timefmt="%s", format="$%H:%M$"):
        self.gplot("set xdata time")
        self.gplot('set timefmt "%s"' %timefmt)
        self.gplot('set format x "%s"' %format)

    def setTimeFmt(self, timefmt):
        self.gplot("set timefmt %s" %timefmt)

    def setSize(self, size):
        self.size = size;

    def plot(self, cmd):
        """Extends plotcmd with cmd"""

        debug("plot(): %s", cmd)
        if not self._plotcmd:
            self._plotcmd = "plot %s" %cmd
        else:
            self._plotcmd = "%s, %s" %(self._plotcmd, cmd)

    def save(self, outdir, verbose=False, cfgfile=None):
        """Generates .gplot and .pdf file of this plot.
           After this this object is not usable anymore,
           because the underlying Gnuplot instance is destroyed.
        """

        plotname = self._plotname

        texfilename   = os.path.join(outdir, plotname+".tex")
        gplotfilename = os.path.join(outdir, plotname+".gplot")
        pdffilename   = os.path.join(outdir, plotname+".pdf")

        info("Generating %s" %texfilename)
        # always epslatex output
        if self.size:
            self.gplot('set terminal epslatex input color solid "default" size %s font 6' %self.size)
        else:
            self.gplot('set terminal epslatex input color solid "default" font 6')
        self.setOutput(texfilename)

        # do the actual plotting
        if self._plotcmd:
            debug(self._plotcmd)
            self.gplot(self._plotcmd)
        else:
            error("Nothing to plot, maybe not a xplot-color file?")
            quit(1)

        info("Generating %s" %gplotfilename)
        self.gplot.save(gplotfilename)

        # make sure gplot output is flushed
        self.gplot = None
        gc.collect()

        info("Generating %s" %pdffilename)
        cmd = ["um_gnuplot2pdf", "-f", "-p", pdffilename]
        if cfgfile:
            cmd.extend(["-c", cfgfile])
        if verbose:
            cmd.append("--debug")
        cmd.append(os.path.join(outdir,plotname))
        call(cmd, shell=False)


class UmHistogram(UmGnuplot):
    """Represents a Histogram plot"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

        # gap in bars between bar clusters
        self._gap = 1

        self.gplot('set style data histogram')
        self.gplot('set style histogram clustered gap %u title offset character 0,0,0' %self._gap)

        self._clusters = None
        self._barspercluster = 0
        self._scenarios = None

    def setClusters(self, clusters):
        """How many clusters to plot"""
        right = clusters+0.5
        left  = -0.5

        self.setXRange((left,right))

        # background rect
        self.gplot('set object 2 rect from %f, graph 0, 0 to %f, graph 1, 0 '\
                'behind lw 1.0 fc rgb "#98E2E7" fillstyle solid 0.15 border -1' %(left,right))

        self._clusters = clusters

    def setBarsPerCluster(self, barspercluster):
        """How many values per row to plot."""
        self._barspercluster = barspercluster

    def getGap(self):
        return self._gap

    def setGap(self, gap):
        self._gap = gap

    def plotBar(self, values, title, using=None, linestyle=3):
        # autoupdate barspercluster
        self._barspercluster += 1

        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" ls %u' %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

    def plotErrorbar(self, values, barNo, valColumn, errColumn, title=None, linestyle=2):
        """Plot errorbars, barNo identifies the bar the errobar should be plotted on
           counting starts with 0
        """

        if title is None:
            titlestr='notitle'
        else:
            titlestr='title "%s"' %title

        # calculate middle of cluster
        middle = self._barspercluster*self.getBarWidth()/2

        # calculate left edge of bar
        left_edge = barNo*self.getBarWidth()-middle

        # calculate actual offset by moving to the middle of the bar
        off = left_edge+self.getBarWidth()/2

        usingstr = "($0+%f):%s:%s" %(off, valColumn, errColumn)

        cmd = '"%s" using %s %s with errorbars ls %u' %(values,usingstr,titlestr,linestyle)

        UmGnuplot.plot(self, cmd)

    def getBarWidth(self):
        return 1.0 / (self._barspercluster + self._gap)


class UmPointPlot(UmGnuplot):
    """Represents a plot with points"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with points ls %u' %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)


class UmLinePlot(UmGnuplot):
    """Represents a plot with points connected by lines"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with lines ls %u' %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)


class UmLinePointPlot(UmGnuplot):
    """Represents a plot with shaped points connected by lines"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plotYerror(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with yerrorbars ls %u' %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with linespoints ls %u' %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)


class UmStepPlot(UmGnuplot):
    """Represents a plot with points connected by steps"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with steps ls %u' %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)


class UmBoxPlot(UmGnuplot):
    """Plots a histogram representing the distribution of a dataset"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with boxes ls %u' %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

    def rawPlot(self, *args, **kwargs):
        UmGnuplot.plot(self, *args, **kwargs)


class UmXPlot(UmGnuplot):
    """Plots a xplot file, used for xpl2pdf.py"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)
        self.gplot(
        """
        set terminal epslatex color solid colortext "default" 5

        set tics border out mirror;
        unset x2tics;
        unset y2tics;
        #set mxtics;
        #set mytics;
        set format x "$%.2f$";
        set format y "$%.0f$";

        # set position of legend
        set key on left top box lt rgb "gray50" samplen 3 width -6
        #
""")
        # edit here
        self.gplot("""
        # line width
        LW = 1
        # point size (used in macroview for segments)
        STANDARDPS = 0.1 #standardsegments
        OTHERPS = 0.4 #retransmit, reorders etc are plotted big

        # styles, nohead for line, heads for arrows
        # for aditional colors check
        # http://www.uni-hamburg.de/Wiss/FB/15/Sustainability/schneider/gnuplot/colors.htm
        #
        # reminder: label defaults are in xpl2pdf.py
        #
        set style arrow 1 nohead lw LW lc rgb "blue" #window
        set style arrow 2 nohead lw LW lc rgb "#32CD32" #ack
        set style arrow 3 nohead lw LW lc rgb "black" #data
        set style arrow 4 nohead lw LW lc rgb "red" #retransmit
        set style arrow 5 nohead lw LW lc rgb "cyan" #reorder
        set style arrow 6 nohead lw LW lc rgb "magenta" #hw_dup
        set style arrow 7 nohead lw LW lc rgb "purple" #sack
        set style arrow 10 nohead lw LW lc rgb "orange" #sinfin
        """)

    def arrowheads(self):
        self.gplot("""
        # override definitions with arrowheads
        set style arrow 3 heads back nofilled size 0.004,90 lw LW lc rgb "black" #data
        set style arrow 4 heads back nofilled size 0.004,90 lw LW lc rgb "red" #retransmit
        set style arrow 5 heads back nofilled size 0.004,90 lw LW lc rgb "cyan" #reorder
        set style arrow 6 heads back nofilled size 0.004,90 lw LW lc rgb "magenta" #hw_dup
        set style arrow 7 heads back nofilled size 0.004,90 lw LW lc rgb "purple" #sack
        set style arrow 10 heads back nofilled size 0.004,90 lw LW lc rgb "orange" #sinfin

        """)

    def plot(self, outdir, basename, color, datatype, microview=False):
        # defaults settings
        # no title and dont plot (we use a whitelist for what to plot)
        title = ""
        plot = False
        if datatype == "line":
            style = 'vectors'
        else:
            style = 'points'

        # um "colors" override standard definitions (therefore if instead of elif)
        #window data divided in line and tick
        if (color == 'window' and datatype == 'line'):
            style = 'vectors arrowstyle 1'
            title = 'Advertised Window'
            plot = True
        # single adv, plot only in microview
        elif (color == 'window' and datatype == 'tick'):
            style = 'points pointtype 2 pointsize STANDARDPS linewidth LW linecolor rgb "blue"'
            title = ""
            if microview:
                plot = True

        # ack data: line, tick
        elif (color == 'ack' and datatype == 'line'):
            style = 'vectors arrowstyle 2'
            title = 'Cumulative ACK'
            plot = True
        # single acks, plot only in microview
        elif (color == 'ack' and datatype == 'tick'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth LW linecolor rgb "#32CD32"'
            title = ""
            if microview:
                plot = True

        # data vectors use in microview
        elif (color == 'data' and datatype == 'line'):
            style = 'vectors arrowstyle 3'
            title = ""
            if microview:
                plot = True
                # ugly hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "black" title "Sent Segments"')

        # data point use in macroview
        elif (color == 'data' and datatype == 'varrow'):
            style = 'points pointtype 2 pointsize STANDARDPS linewidth LW linecolor rgb "black"'
            title = ""
            if not microview:
                plot = True
                # hack for key
                UmGnuplot.plot(self, '1/0 with points pointtype 7 pointsize OTHERPS '\
                        'linewidth LW linecolor rgb "black" title "Sent Segments"')

        # misc data points, print points in standardview,
        # arrows in microview
        elif (color == 'retransmit' and datatype =='line'):
            style = 'vectors arrowstyle 4'
            title = ""
            if microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "red" '\
                        'title "Retransmitted Segment"')

        elif (color == 'retransmit' and datatype == 'varrow'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth LW linecolor rgb "red"'
            title = "Retransmitted Segment"
            if not microview:
                plot = True

        elif (color == 'reorder' and datatype =='line'):
            style = 'vectors arrowstyle 5'
            if microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "cyan" '\
                        'title "Reordered Segment"')

        elif (color == 'reorder' and datatype == 'varrow'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth LW linecolor rgb "cyan"'
            title = "Reordered Segment"
            if not microview:
                plot = True

        elif (color == 'duplicate' and datatype =='line'):
            style = 'vectors arrowstyle 6'
            title = ""
            if microview:
                plot = True
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "magenta" '\
                        'title "Duplicate Segment"')

        elif (color == 'duplicate' and datatype == 'varrow'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth LW linecolor rgb "magenta"'
            title = "Reordered Segment"
            if not microview:
                plot = True

        elif (color == 'icmp' and datatype == 'diamond'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth LW linecolor rgb "yellow"'
            title = "ICMP"
            plot = True

        elif (color == 'sack' and datatype == 'line'):
            style = 'vectors arrowstyle 7'
            title = ''
            if microview:
                plot = True
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "purple" title "SACK"')

        # single acks, plot only in microview
        elif (color == 'sack' and datatype == 'tick'):
            style = 'points pointtype 7 pointsize OTHERPS linewidth LW linecolor rgb "purple"'
            title = ""
            if not microview:
                plot = True
                UmGnuplot.plot(self, '1/0 with points pointtype 7 pointsize OTHERPS '\
                                'linewidth LW linecolor rgb "purple" title "SACK"')

        # garbade datatypes, you usually dont plot them
        # sinfin
        elif (color == 'sinfin' and datatype == 'line'):
            style = 'vectors arrowstyle 10'
            title = ""
            plot = False
        elif (color == 'sinfin' and datatype == 'dots'):
            plot = False

        # if no title is defined, set "notitle"
        if title:
            title = "title \"%s\"" %title
        else:
            title = "notitle"

        # concat plotcmd, for line data use 4 parameter style, else 2 parameter
        if datatype == 'line':
            cmd = '"%s/%s.dataset.%s.%s" using 1:2:($3-$1):($4-$2) with %s %s' %(outdir,
                    basename, color, datatype, style, title)
        else:
            cmd = '"%s/%s.dataset.%s.%s" using 1:2 with %s %s' %(outdir, basename,
                    color, datatype, style, title)

        if (plot == True):
            UmGnuplot.plot(self, cmd)

    def rawPlot(self, *args, **kwargs):
        UmGnuplot.plot(self, *args, **kwargs)
