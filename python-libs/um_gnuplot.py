#!/usr/bin/env python
#g -*- coding: utf-8 -*-

"""

  Module for gnuplot scripting.
 

"""

# python imports
from logging import info, debug, warn, error

import Gnuplot


class UmGnuplot(Gnuplot.Gnuplot):
    """ A specific umic-mesh plot with convenience functions """

    def __init__(self):
        Gnuplot.Gnuplot.__init__(self)

        # always epslatex output
        self('set terminal epslatex color solid "default" 9')

        # turn on math environment for axis
        self('set format "$%g$"')

        # empty title use caption instead
        self('set title ""')

    def setYLabel(self, *args, **kwargs):
        self.set_label("ylabel", *args, **kwargs)

    def setXLabel(self, *args, **kwargs):
        self.set_label("xlabel", *args, **kwargs)

    def setOutput(self, output):
        self('set output "%s"' %output)

    def setYRange(self, *args):
        self.set_range("yrange",*args)

    def setXRange(self, *args):
        self.set_range("xrange",*args)
    
    

class UmHistogram(UmGnuplot):
    """ Represents a Histogram plot """

    def __init__(self):
        UmGnuplot.__init__(self)



        # colors and line styles
        self(
        """
        set style line 1 lt rgb "#F593A1" lw 1 pt 6
        set style line 2 lt rgb "dark-green" lw 1.5 pt 1
        set style line 3 lt rgb "navy" lw 1 pt 7 ps 1
        set style line 4 lt rgb "grey" lw 1
        set style line 5 lt rgb "#98E2E7" lw 1 pt 7 ps 1
        set style line 6 lt rgb "#B83749" lw 1 pt 7 ps 1
        set style line 7 lt rgb "#2BB1BA" lw 1 pt 7 ps 1
        """)
        

        # grid and other styles
        self(
        """
        set border 31 front linetype -1 linewidth 1.000
        set grid noxtics ytics nopolar back
        set boxwidth 0.9 relative
        set style fill solid 1.00 border -1
        """)

        # gap in bars between bar clusters
        self._gap = 1
        
        self('set style data histogram')
        self('set style histogram clustered gap %u title offset character 0,0,0' %self._gap)

        self._bars = None
        self._scenarios = None

    def setBars(self, bars):
        """ How many bars to plot """
        right = bars+0.5
        left  = -0.5
        
        self.set_range("xrange",(left,right))
        
        # background rect
        self('set object 2 rect from %f, graph 0, 0 to %f, graph 1, 0 behind lw 1.0 fc rgb "#98E2E7" fillstyle solid 0.15 border -1' %(left,right))

        self._bars = bars

    def setScenarios(self, scenarios):
        """ How many values per row to plot. """
        self._scenarios = scenarios

    def getGap(self):
        return self._gap

    
    def getBarWidth():
        return 1.0 / (self._scenarios + self._gap)

class UmPointPlot(UmGnuplot):
    """ Represents a plot with points """

    def __init__(self):
        UmGnuplot.__init__(self)


        # colors and line styles
        self(
        """
        set style line 1 lt rgb "#F593A1" lw 1 pt 6
        set style line 2 lt rgb "dark-green" lw 1.5 pt 1
        set style line 3 lt rgb "navy" lw 1 pt 7 ps 1
        set style line 4 lt rgb "grey" lw 1
        set style line 5 lt rgb "#98E2E7" lw 1 pt 7 ps 1
        set style line 6 lt rgb "#B83749" lw 1 pt 7 ps 1
        set style line 7 lt rgb "#2BB1BA" lw 1 pt 7 ps 1
        """)
        
        # grid and other styles
        self(
        """
        set border 31 front linetype -1 linewidth 1.000
        set grid noxtics ytics nopolar back
        set boxwidth 0.9 relative
        set style fill solid 1.00 border -1
        """)



    def plot(self, values, title, using=None, linestyle=3):
        usingstr = ""
        if using:
            usingstr = "using %s" %using
        self('plot "%s" %s title "%s" with points ls %u' %(values, usingstr, title, linestyle))
