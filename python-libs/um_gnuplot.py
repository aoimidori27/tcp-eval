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
        
        self('set style data histogram')
        self('set style histogram clustered gap 1 title offset character 0,0,0')




    def setBars(self, bars):
        """ How many bars to plot """
        self.set_range("xrange",(-1,bars))
        
        # background rect
        self('set object 2 rect from -1, graph 0, 0 to %u, graph 1, 0 behind lw 1.0 fc rgb "#98E2E7" fillstyle solid 0.15 border -1' % bars)



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
