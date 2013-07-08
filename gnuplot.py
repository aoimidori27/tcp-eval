#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
# Copyright (C) 2007 Arnd Hannemann <arnd@arndnet.de>
# Copyright (C) 2008 - 2011 Christian Samsel <christian.samsel@rwth-aachen.de>
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
import gc
import os.path
import textwrap
import Gnuplot
from logging import info, debug, warn, error

# tcp-eval imports
from functions import call
from latex import UmLatex

class UmGnuplot():
    """Module for gnuplot scripting."""

    def __init__(self, plotname, outdir, debug = False, saveit=None, force=False):
        """Plotname is for filename generation"""

        self.debug = debug
        self.saveit = saveit
        self.outdir = outdir
        self.force = force

        self.gplot = Gnuplot.Gnuplot()

        # turn on math environment for axis
        self.gplot('set format "$%g$"')

        # empty title use caption instead
        self.gplot('set title ""')

        # default size
        #self.plotsize = "14.4cm,9.7cm"
        # for 2 pictures with subcaption, one line caption
        #self.plotsize = "14.4cm,9.3cm"
        # for 2 pictures with subcaption, two line caption
        self.plotsize = "14.4cm,8.7cm"

        # font size
        self.fontsize = 6

        # name of the plot (for building filenames)
        self._plotname = plotname

        # actual plotcmd
        self._plotcmd = None

        # colors and line styles
        self.gplot(textwrap.dedent("""
        set style line  1 lt rgb "#DC143C" lw 1 pt 7 ps 1 #Crimson
        set style line  2 lt rgb "#008000" lw 1 pt 7 ps 1 #Green
        set style line  3 lt rgb "#1E90FF" lw 1 pt 7 ps 1 #DodgerBlue
        set style line  4 lt rgb "#FF8C00" lw 1 pt 7 ps 1 #DarkOrange
        set style line  5 lt rgb "#DA70D6" lw 1 pt 7 ps 1 #Orchid
        set style line  6 lt rgb "#B22222" lw 1 pt 7 ps 1 #FireBrick
        set style line  7 lt rgb "#9ACD32" lw 1 pt 7 ps 1 #YellowGreen
        set style line  8 lt rgb "#6495ED" lw 1 pt 7 ps 1 #CornflowerBlue
        set style line  9 lt rgb "#808000" lw 1 pt 7 ps 1 #Olive
        set style line 10 lt rgb "#C71585" lw 1 pt 7 ps 1 #MediumVioletRed
        set style line 11 lt rgb "#8B0000" lw 1 pt 7 ps 1 #DarkRed
        set style line 12 lt rgb "#006400" lw 1 pt 7 ps 1 #DarkGreen
        set style line 13 lt rgb "#00008B" lw 1 pt 7 ps 1 #DarkBlue
        set style line 14 lt rgb "#B8860B" lw 1 pt 7 ps 1 #DarkGoldenrod
        set style line 15 lt rgb "#9932CC" lw 1 pt 7 ps 1 #DarkOrchid
        set style line 16 lt rgb "#6B8E23" lw 1 pt 7 ps 1 #OliveDrab
        set style line 17 lt rgb "#8B008B" lw 1 pt 7 ps 1 #DarkMagenta
        set style line 18 lt rgb "#E9967A" lw 1 pt 7 ps 1 #DarkSalmon
        set style line 19 lt rgb "#4169E1" lw 1 pt 7 ps 1 #RoyalBlue
        set style line 20 lt rgb "#228B22" lw 1 pt 7 ps 1 #ForestGreen
        """))

        # grid and other styles
        self.gplot(textwrap.dedent("""
        set border 31 front linetype -1 linewidth 1.000
        set grid noxtics ytics nopolar back
        set boxwidth 0.8 relative
        set clip points
        set style fill solid 1.00 border -1
        set key on right top box lt rgb "gray50" samplen 3 width -6 spacing 1.05
        """))

        # offset may be changed
        self.xaxislabeloffset = 0,0.3
        self.yaxislabeloffset = 2.0,0

        # latex object
        save_name = "main.tex"
        if self.saveit:
            save_name = "%s_main.tex" %plotname
        self._latex = UmLatex(save_name, self.outdir, self.force, self.debug,
                tikz=False)
        # use sans serif font and set the correct font size
        self._latex.setDocumentclass("scrartcl", "fontsize=%spt" %self.fontsize)
        self._latex.addSetting(r"\renewcommand{\familydefault}{\sfdefault}")
        self._latex.addSetting(r"\usepackage{sfmath}")

    def setYLabel(self, *args, **kwargs):
        try:
            tmp = kwargs['offset']
        except:
            kwargs['offset'] = self.yaxislabeloffset
        self.gplot.set_label("ylabel", *args, **kwargs)

    def setY2Label(self, *args, **kwargs):
        try:
            tmp = kwargs['offset']
        except:
            kwargs['offset'] = (-self.yaxislabeloffset[0],\
                    self.yaxislabeloffset[1])
        self.gplot.set_label("y2label", *args, **kwargs)
        self.gplot('set ytics nomirror')
        self.gplot('set y2tics nomirror')
        # self.gplot('unset grid')

    def setXLabel(self, *args, **kwargs):
        try:
            tmp = kwargs['offset']
        except:
            kwargs['offset'] = self.xaxislabeloffset
        self.gplot.set_label("xlabel", *args, **kwargs)

    def setX2Label(self, *args, **kwargs):
        try:
            tmp = kwargs['offset']
        except:
            kwargs['offset'] = (self.yaxislabeloffset[0],\
                    -self.yaxislabeloffset[1])
        self.gplot.set_label("x2label", *args, **kwargs)

    def setOutput(self, output):
        self.gplot('set output "%s"' %output)

    def setYRange(self, *args):
        self.gplot.set_range("yrange",*args)

    def setXRange(self, *args):
        self.gplot.set_range("xrange",*args)

    def setY2Range(self, *args):
        self.gplot.set_range("y2range",*args)

    def setX2Range(self, *args):
        self.gplot.set_range("x2range",*args)

    def setPlotname(self, plotname):
        self._plotname = plotname

    def setXDataTime(self, timefmt="%s", format="$%H:%M$"):
        self.gplot("set xdata time")
        self.gplot('set timefmt "%s"' %timefmt)
        self.gplot('set format x "%s"' %format)

    def setTimeFmt(self, timefmt):
        self.gplot("set timefmt %s" %timefmt)

    def setPlotSize(self, plotsize):
        self.plotsize = plotsize

    def setFontSize(self, fontsize):
        self.fontsize = fontsize

    def setLogScale(self, axes="y"):
        self.gplot('set log %s' %axes)

    def plot(self, cmd):
        """Extends plotcmd with cmd"""

        debug("plot(): %s", cmd)
        if not self._plotcmd:
            self._plotcmd = "plot %s" %cmd
        else:
            self._plotcmd = "%s, %s" %(self._plotcmd, cmd)

    def save(self):
        """Generates .gplot and .pdf file of this plot. After this this object
        is not usable anymore, because the underlying Gnuplot instance is
        destroyed."""

        plotname = self._plotname

        texfilename   = os.path.join(self.outdir, plotname+"_eps.tex")
        gplotfilename = os.path.join(self.outdir, plotname+".gplot")
        pdffilename   = os.path.join(self.outdir, plotname+".pdf")
        epsfilename   = os.path.join(self.outdir, plotname+"_eps.eps")
        epspdffilename = os.path.join(self.outdir, plotname+"_eps.pdf")

        info("Generating %s" %texfilename)
        # always epslatex output
        self.gplot('set terminal epslatex input color colortext solid '\
                '"default" size %s font %u' \
                %(self.plotsize,(int(round(self.fontsize*1.2)))))
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

        # convert the EPS file to a PDF file
        info("Run epstopdf on %s..." %plotname)
        if self.debug:
            cmd = "epstopdf --debug --outfile=%s %s" \
                    %(epspdffilename, epsfilename)
            call(cmd)
        else:
            cmd = "epstopdf --outfile=%s %s" \
                    %(epspdffilename, epsfilename)
            call(cmd, noOutput = True)

        self._latex.addLatexFigure(texfilename, plotname)

        # should we save generated main latex file for further purpose?
        if self.saveit:
           info("Save main LaTeX file...")
           self._latex.save()

        # build pdf graphics
        info("Generate PDF files...")
        self._latex.toPdf()

        if not self.saveit:
            os.remove(epsfilename)
            os.remove(gplotfilename)
            os.remove(texfilename)
            os.remove(epspdffilename)

class UmHistogram(UmGnuplot):
    """Represents a Histogram plot"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

        # gap in bars between bar clusters
        self._gap = 1

        self.gplot('set style data histogram')
        self.gplot('set style histogram clustered gap %u title offset '\
                'character 0,0,0' %(self._gap))
        self.gplot('set key under horizontal right nobox spacing 1.05 '\
                'height 0.2 width 0')
        self.gplot('set xtics scale 0')
        self.gplot('set ytics')
        self.gplot('set grid y')

        self._clusters = None
        self._barspercluster = 0
        self._scenarios = None

    def setClusters(self, clusters):
        """How many clusters to plot"""
        right = clusters+0.5
        left  = -0.5

        self.setXRange((left,right))

        # background rect
        self.gplot('set object 2 rect from %f, graph 0, 0 to %f, '\
                'graph 1, 0 behind lw 1.0 fc rgb "#98E2E7" '\
                'fillstyle solid 0.15 border -1' %(left,right))

        self._clusters = clusters

    def setBarsPerCluster(self, barspercluster):
        """How many values per row to plot."""
        self._barspercluster = barspercluster

    def getGap(self):
        return self._gap

    def setGap(self, gap):
        self._gap = gap

    def plotBar(self, values, title=None, using=None, linestyle=None,
            fillstyle=None, axes=None, gradientCurrent=None, gradientMax=None):
        # autoupdate barspercluster
        self._barspercluster += 1

        titlestr= "notitle"
        if title: titlestr = 'title "%s" ' %title

        usingstr = ""
        if using: usingstr = "using %s " %using

        linestr = ""
        if linestyle: linestr = "linestyle %s " %linestyle

        fillstr = ""
        if fillstyle: fillstr = "fillstyle %s " %fillstyle

        gradientstr = ""
        if gradientMax:
            a_r = 255
            a_g = 0
            a_b = 0
            b_r = 255
            b_g = 255
            b_b = 0
            i = float(gradientCurrent)
            h = float(gradientMax)
            gradientstr = 'lt rgb "#%02X%02X%02X" lw 1' %(
                    max(0,a_r-(((b_r-a_r)/-h)*i)),
                    max(0,a_g-(((b_g-a_g)/-h)*i)),
                    max(0,a_b-(((b_b-a_b)/-h)*i)))

        axesstr = ""
        if  axes:
            axesstr = "axes %s " %axes

        cmd = '"%s" %s %s %s %s %s %s' %(values, usingstr, axesstr, titlestr,
                linestr, fillstr, gradientstr)
        UmGnuplot.plot(self, cmd)

    def plotErrorbar(self, values, barNo, valColumn, yDelta, title=None,
            linestyle=None, yHigh=None):
        """Plot errorbars, barNo identifies the bar the errobar should be
        plotted on counting starts with 0"""

        if title is None:
            titlestr='notitle'
        else:
            titlestr='title "%s"' %title

	    if linestyle is None:
	        linestr='lt rgb "black" lw 1 pt 1'
	    else:
	        linestr="linestyle %u" %linestyle

        # calculate middle of cluster
        middle = self._barspercluster*self.getBarWidth()/2

        # calculate left edge of bar
        left_edge = barNo*self.getBarWidth()-middle

        # calculate actual offset by moving to the middle of the bar
        off = left_edge+self.getBarWidth()/2
        if yHigh:
            usingstr = "($0+%f):%s:%s:%s" %(off, valColumn, yDelta, yHigh)
        else:
            usingstr = "($0+%f):%s:%s" %(off, valColumn, yDelta)
        cmd = '"%s" using %s %s with errorbars %s' \
                %(values, usingstr, titlestr, linestr)

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
        cmd = '"%s" %s title "%s" with points ls %u' \
                %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

class UmLinePlot(UmGnuplot):
    """Represents a plot with points connected by lines"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with lines ls %u' \
                %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

class UmLinePointPlot(UmGnuplot):
    """Represents a plot with shaped points connected by lines"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plotYerror(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with yerrorbars ls %u' \
                %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with linespoints ls %u' \
                %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

class UmStepPlot(UmGnuplot):
    """Represents a plot with points connected by steps"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with steps ls %u' \
                %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

class UmBoxPlot(UmGnuplot):
    """Plots a histogram representing the distribution of a dataset"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)

    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        cmd = '"%s" %s title "%s" with boxes ls %u' \
                %(values, usingstr, title, linestyle)
        UmGnuplot.plot(self, cmd)

    def rawPlot(self, *args, **kwargs):
        UmGnuplot.plot(self, *args, **kwargs)


class UmXPlot(UmGnuplot):
    """Plots a xplot file, used for xpl2pdf.py"""

    def __init__(self, *args, **kwargs):
        UmGnuplot.__init__(self, *args, **kwargs)
        self.gplot(textwrap.dedent("""
        set tics border in mirror;
        unset x2tics;
        unset y2tics;
        set format x "$%.2f$";
        set format y "$%.0f$";
        # set key to the left side
        set key on left top box lt rgb "gray50" samplen 3 width -2 spacing 1.05
        #"""))

        # edit here
        self.gplot(textwrap.dedent("""
        # line width
        LW = 1
        # point size (used in macroview for segments)
        STANDARDPS = 0.1 #standardsegments
        OTHERPS = 0.8 #retransmit, reorders etc are plotted big

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
        """))

        self.arrowsize = "0.004"

    def arrowheads(self):
        self.gplot(textwrap.dedent("""
        # override definitions with arrowheads
        set style arrow 3 heads back nofilled size %s,90 lw LW lc rgb "black" #data
        set style arrow 4 heads back nofilled size %s,90 lw LW lc rgb "red" #retransmit
        set style arrow 5 heads back nofilled size %s,90 lw LW lc rgb "cyan" #reorder
        set style arrow 6 heads back nofilled size %s,90 lw LW lc rgb "magenta" #hw_dup
        set style arrow 7 heads back nofilled size %s,90 lw LW lc rgb "purple" #sack
        set style arrow 10 heads back nofilled size %s,90 lw LW lc rgb "orange" #sinfin
        """ %(self.arrowsize, self.arrowsize, self.arrowsize, self.arrowsize,
                self.arrowsize, self.arrowsize)))

    def plot(self, outdir, basename, color, datatype, microview=False):
        # defaults settings
        # no title and dont plot (we use a whitelist for what to plot)
        title = ""
        plot = False
        if datatype == "line":
            style = 'vectors'
        else:
            style = 'points'

        # "colors" override standard definitions (therefore if instead of elif)
        # window data divided in line and tick
        if (color == 'window' and datatype == 'line'):
            style = 'vectors arrowstyle 1'
            title = 'Advertised Window'
            plot = True
        # single adv, plot only in microview
        elif (color == 'window' and datatype == 'tick'):
            style = 'points pointtype 2 pointsize STANDARDPS linewidth '\
                    'LW linecolor rgb "blue"'
            title = ""
            if microview: plot = True
        # ack data: line, tick
        elif (color == 'ack' and datatype == 'line'):
            style = 'vectors arrowstyle 2'
            title = 'Cumulative ACK'
            plot = True
        # single acks, plot only in microview
        elif (color == 'ack' and datatype == 'tick'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth '\
                    'LW linecolor rgb "#32CD32"'
            title = ""
            if microview: plot = True
        # draw ambigous ack as normal ack
        elif (color == 'ambigousack' and datatype == 'diamond'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth '\
                    'LW linecolor rgb "#32CD32"'
            title = ""
            if microview: plot = True
        # data as vector used in microview
        elif (color == 'data' and datatype == 'line'):
            style = 'vectors arrowstyle 3'
            title = ""
            if microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "black" '\
                        'title "Sent Segments"')
        # data as point used in macroview
        elif (color == 'data' and datatype == 'darrow'):
            style = 'points pointtype 2 pointsize STANDARDPS linewidth '\
                    'LW linecolor rgb "black"'
            title = ""
            if not microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 with points pointtype 7 '\
                        'pointsize OTHERPS linewidth LW '\
                        'linecolor rgb "black" title "Sent Segments"')
        # retransmit as vector used in microview
        elif (color == 'retransmit' and datatype =='line'):
            style = 'vectors arrowstyle 4'
            title = ""
            if microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "red" '\
                        'title "Retransmitted Segment"')
        # retransmit as point uses in macroview
        elif (color == 'retransmit' and datatype == 'darrow'):
            style = 'points pointtype 1 pointsize OTHERPS linewidth '\
                    'LW linecolor rgb "red"'
            title = "Retransmitted Segment"
            if not microview: plot = True
        # reordered data as vector used in microview
        elif (color == 'reorder' and datatype =='line'):
            style = 'vectors arrowstyle 5'
            if microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "cyan" '\
                        'title "Reordered Segment"')
        # reordered data as point used in macroview
        elif (color == 'reorder' and datatype == 'darrow'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth LW '\
                    'linecolor rgb "cyan"'
            title = "Reordered Segment"
            if not microview:  plot = True
        # duplicates as vector used in microview
        elif (color == 'duplicate' and datatype =='line'):
            style = 'vectors arrowstyle 6'
            title = ""
            if microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "magenta" '\
                        'title "Duplicate Segment"')
        # duplicates as point used in macroview
        elif (color == 'duplicate' and datatype == 'darrow'):
            style = 'points pointtype 2 pointsize OTHERPS linewidth LW '\
                    'linecolor rgb "magenta"'
            title = "Reordered Segment"
            if not microview: plot = True
        # icmps as diamonds
        elif (color == 'icmp' and datatype == 'diamond'):
            style = 'points pointtype 6 pointsize 1 linewidth LW '\
                    'linecolor rgb "brown"'
            title = "ICMP"
            plot = True
        # sacks as vector used in microview
        elif (color == 'sack' and datatype == 'line'):
            style = 'vectors arrowstyle 7'
            title = ''
            if microview:
                plot = True
                # key hack
                UmGnuplot.plot(self, '1/0 lw LW lc rgbcolor "purple" '\
                        'title "SACK"')
#        # single acks, plot only in macroview
#        elif (color == 'sack' and datatype == 'tick'):
#            style = 'points pointtype 7 pointsize OTHERPS linewidth LW '\
#                    'linecolor rgb "purple"'
#            title = ""
#            if not microview:
#                plot = True
#                # key hack
#                UmGnuplot.plot(self, '1/0 with points pointtype 7 pointsize '\
#                        'OTHERPS linewidth LW linecolor rgb "purple" '\
#                        'title "SACK"')
        # garbade datatypes, you usually dont plot them
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
            cmd = '"%s/%s.dataset.%s.%s" using 1:2:($3-$1):($4-$2) with %s %s' \
                    %(outdir, basename, color, datatype, style, title)
        else:
            cmd = '"%s/%s.dataset.%s.%s" using 1:2 with %s %s' \
                    %(outdir, basename, color, datatype, style, title)

        if (plot == True):
            UmGnuplot.plot(self, cmd)

    def rawPlot(self, *args, **kwargs):
        UmGnuplot.plot(self, *args, **kwargs)

