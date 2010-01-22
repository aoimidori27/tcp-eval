#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""xpl2gpl.py -- tcptrace / xplot 2 gnuplot converter

"""
import os, math, optparse, sys, subprocess
from logging import info, debug, warn, error
from simpleparse import generator
from simpleparse.parser import Parser
from mx.TextTools import TextTools

class xpl2gpl(object):
    "Class to convert xplot/tcptrace files to gnuplot files"

    def __init__(self):

        # initialization of the option parser
        usage = "usage: %prog [options] <file1> <file2> .."
        self.optparser = optparse.OptionParser()
        self.optparser.set_usage(usage)
        self.optparser.set_defaults(debug = False, title = '', xlabel = '', ylabel = '', includefile ='', terminaltype = 'x11', keyoptions = '', terminaloptions = '', labeloptions = '', execute = False, defaultstyle = 'points pt 2',linestyle = 'lines',dotstyle = 'dots',boxstyle = 'points pt 3',diamondstyle = 'points pt 1',varrowstyle = 'points pt 1', harrowstyle = 'points pt 5',dlinestyle = 'linepoints pt 4')

        self.optparser.add_option("-d", "--debug",
                    action = "store_true", dest = "debug",
                    help = "debug parsing [default: %default]")
        self.optparser.add_option("-e", "--execute-gnuplot",
                    action = "store_true", dest = "execute",
                    help = "execute gnuplot after conversion [default: %default]")
        self.optparser.add_option("--title", metavar = "text",
                    action = "store", dest = "title",
                    help = "gnuplot title [default: use xplot title]")
        self.optparser.add_option("--xlabel", metavar = "text",
                    action = "store", dest = "xlabel",
                    help = "gnuplot x label [default: use xplot xlabel]")
        self.optparser.add_option("--ylabel", metavar = "text",
                    action = "store", dest = "ylabel",
                    help = "gnuplot y label [default: use yplot xlabel]")
        self.optparser.add_option("-a", "--includefile", metavar = "filename",
                    action = "store", dest = "includefile",
                    help = "include additional gnuplot file [default: none]")
        self.optparser.add_option("-t", "--terminal", metavar = "terminaltype",
                    action = "store", dest = "terminaltype",
                    help = "use terminal type [default: x11] other possible selections: aqua, latex, mp, pdf, png, postscript, svg, etc")
        self.optparser.add_option("-o", "--terminaloptions", metavar = "terminaloptions",
                    action = "store", dest = "terminaloptions",
                    help = "use terminal options [default: none]")
        self.optparser.add_option("-l", "--labeloptions", metavar = "labeloptions",
                    action = "store", dest = "labeloptions",
                    help = "use label options [default: none]")
        self.optparser.add_option("--keyoptions", metavar = "keyoptions",
                    action = "store", dest = "defaultstyle",
                    help = "use key options [default: nokey]")
        self.optparser.add_option("--defaultstyle", metavar = "plotoptions",
                    action = "store", dest = "defaultstyle",
                    help = "use style options [default: %default]")
        self.optparser.add_option("--linestyle", metavar = "plotoptions",
                    action = "store", dest = "linestyle",
                    help = "use style options [default: %default]")
        self.optparser.add_option("--dotstyle", metavar = "plotoptions",
                    action = "store", dest = "dotstyle",
                    help = "use style options [default: %default]")
        self.optparser.add_option("--boxstyle", metavar = "plotoptions",
                    action = "store", dest = "boxstyle",
                    help = "use style options [default: %default]")
        self.optparser.add_option("--diamondstyle", metavar = "plotoptions",
                    action = "store", dest = "diamondstyle",
                    help = "use style options [default: %default]")
        self.optparser.add_option("--varrowstyle", metavar = "plotoptions",
                    action = "store", dest = "varrowstyle",
                    help = "use style options [default: %default]")
        self.optparser.add_option("--harrowstyle", metavar = "plotoptions",
                    action = "store", dest = "harrowstyle",
                    help = "use style options [default: %default]")
        self.optparser.add_option("--dlinestyle", metavar = "plotoptions",
                    action = "store", dest = "dlinestyle",
                    help = "use style options [default: %default]")
    def main(self):

        (self.options, self.args) = self.optparser.parse_args()

        for entry in self.args:
            if not os.path.isfile(entry):
                warn("%s not found." %entry)
                exit(1)

        declaration = r'''
            root        :=    timeval,title,xlabel,ylabel,(diamond / text / varrow / harrow / line / dline / dot / box / tick / color / linebreak)*,end*
            alphanum    :=     [a-zA-Z0-9]
            punct       :=     [!@#$%^&()+=|\{}:;<>,.?/"_]
            whitespace  :=     [ \t]
            string      :=     ( alphanum / punct / whitespace )*, linebreak
            keyword     :=    ([ A-Z]+ / int1)
            float1      :=    [0-9]+,".",[0-9]+
            float2      :=    [0-9]+,".",[0-9]+
            int1        :=    [0-9]+
            int2        :=    [0-9]+
            end         :=    'go', linebreak*
            timeval     :=    ( 'timeval double' / 'timeval signed' ), linebreak
            title       :=    'title\n',string
            xlabel      :=     'xlabel\n',string
            ylabel      :=     'ylabel\n',string
            linebreak   :=    [ \t]*,( '\n' / '\n\r' ),[ \t]*
            color       :=    ( 'green' / 'yellow' / 'white' / 'orange' / 'blue' / 'magenta' / 'red' / 'purple' / 'pink' )
            harrow      :=    ( 'larrow' / 'rarrow'),whitespace,float1,whitespace,int1,linebreak
            varrow      :=    ( 'darrow' / 'uarrow'),whitespace,float1,whitespace,int1,linebreak
            line        :=    ( 'line' ),whitespace,float1,whitespace,int1,whitespace,float2,whitespace,int2,linebreak
            dline       :=    ( 'dline' ),whitespace,float1,whitespace,int1,whitespace,float2,whitespace,int2,linebreak
            dot         :=    ('dot'),whitespace,float1,whitespace,int1,(whitespace,color)*, linebreak
            diamond     :=    ('diamond'),whitespace,float1,whitespace,int1,(whitespace,color)*,linebreak
            box         :=    ('box'),whitespace,float1,whitespace,int1,(whitespace,color)*,linebreak
            tick        :=    ('dtick' / 'utick' / 'ltick' / 'rtick' / 'vtick' / 'htick' ),whitespace,float1,whitespace,int1,linebreak
            text        :=    ('atext' / 'btext' / 'ltext' / 'rtext' ),whitespace,float1,whitespace,int1,linebreak,keyword,linebreak
        '''
        xplfile = open ( entry ).read()
        basename = os.path.splitext(os.path.basename(entry))[0]

        # debug declaration mode
        if self.options.debug:
            debugparser = Parser (declaration)
            import pprint
            pprint.pprint(debugparser.parse(xplfile))
            exit(0)

        parser = generator.buildParser(declaration).parserbyname('root')

        gploutput = open ( "%s.gpl" %(basename) , 'w')
        dataoutput = open ( "%s.datasets" %(basename) , 'w')
        labelsoutput = open ( "%s.labels" %(basename) , 'w')

        datasources = list()
        data = list()
        taglist = TextTools.tag(xplfile, parser)
        currentcolor = ""
        title = self.options.title
        xlabel = self.options.xlabel
        ylabel = self.options.ylabel
        for tag, beg, end, subtags in taglist[1]:
        # read options and labels from parse tree
        # convert keyword labels
            if tag == 'text':
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        xpoint = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        ypoint = xplfile[subbeg:subend]
                    elif subtag == 'keyword':
                        label = xplfile[subbeg:subend]
                if xplfile[beg:beg+1] == 'l': # 'l'text
                    position = "right"
                elif xplfile[beg:beg+1] == 'r':
                    position = "left"
                else:
                    position = "center"
                # write out
                labelsoutput.write('set label "%s" at (%s-946684800.000000), %s %s %s\n' %(label,xpoint,ypoint,position,self.options.labeloptions) )

            # read colors
            elif tag == 'color':
                currentcolor = xplfile[beg:end]

            # read l/r arrow
            elif tag == 'varrow':
                if ('varrow',currentcolor) not in datasources:
                    datasources.append( ('varrow',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        xpoint = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        ypoint = xplfile[subbeg:subend]
                    elif subtag == 'color':
                        currentcolor = xplfile[subbeg:subend]
                data.append( ( ('varrow', currentcolor), "%s %s\n" %(xpoint, ypoint) ) )

            elif tag == 'harrow':
                if ('harrow',currentcolor) not in datasources:
                    datasources.append( ('harrow',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        xpoint = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        ypoint = xplfile[subbeg:subend]
                    elif subtag == 'color':
                        currentcolor = xplfile[subbeg:subend]
                data.append( ( ('harrow', currentcolor), "%s %s\n" %(xpoint, ypoint) ) )

            # read dot
            elif tag == 'dot':
                if ('dot',currentcolor) not in datasources:
                    datasources.append( ('dot',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        xpoint = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        ypoint = xplfile[subbeg:subend]
                    elif subtag == 'color':
                        currentcolor = xplfile[subbeg:subend]
                data.append( ( ('dot', currentcolor), "%s %s\n" %(xpoint, ypoint) ) )

            # diamonds
            elif tag == 'diamond':
                if ('diamond',currentcolor) not in datasources:
                    datasources.append( ('diamond',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        xpoint = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        ypoint = xplfile[subbeg:subend]
                    elif subtag == 'color':
                        currentcolor = xplfile[subbeg:subend]
                data.append( ( ('diamond', currentcolor), "%s %s\n" %(xpoint, ypoint) ) )


            elif tag == 'box':
                if ('box',currentcolor) not in datasources:
                    datasources.append( ('box',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        xpoint = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        ypoint = xplfile[subbeg:subend]
                    elif subtag == 'color':
                        currentcolor = xplfile[subbeg:subend]
                data.append( ( ('box',currentcolor), "%s %s\n" %(xpoint, ypoint) ) )


            elif tag == 'tick':
                if ('tick',currentcolor) not in datasources:
                    datasources.append( ('tick',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        xpoint = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        ypoint = xplfile[subbeg:subend]
                    elif subtag == 'color':
                        currentcolor = xplfile[subbeg:subend]
                data.append( ( ('tick',currentcolor), "%s %s\n" %(xpoint, ypoint) ) )

            elif tag == 'line':
                if ('line',currentcolor) not in datasources:
                    datasources.append( ('line',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        x1point = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        y1point = xplfile[subbeg:subend]
                    elif subtag == 'float2':
                        x2point = xplfile[subbeg:subend]
                    elif subtag == 'int2':
                        y2point = xplfile[subbeg:subend]
                data.append( ( ('line',currentcolor), "%s %s\n%s %s\n\n" %(x1point, y1point, x2point, y2point) ) )

            elif tag == 'dline':
                if ('dline',currentcolor) not in datasources:
                    datasources.append( ('dline',currentcolor) )
                for subtag, subbeg, subend, subparts in subtags:
                    if subtag == 'float1':
                        x1point = xplfile[subbeg:subend]
                    elif subtag == 'int1':
                        y1point = xplfile[subbeg:subend]
                    elif subtag == 'float2':
                        x2point = xplfile[subbeg:subend]
                    elif subtag == 'int2':
                        y2point = xplfile[subbeg:subend]
                data.append( ( ('dline',currentcolor), "%s %s\n%s %s\n\n" %(x1point, y1point, x2point, y2point) ) )

            # read title
            elif tag == 'title':
                if self.options.title == '':
                    title = xplfile[beg+len("title\n"):end-len("\n")]

            # read axis labels
            elif tag == 'xlabel':
                if self.options.xlabel == '':
                    xlabel = xplfile[beg+len("xlabel\n"):end-len("\n")]

            elif tag == 'ylabel':
                if self.options.xlabel == '':
                    ylabel = xplfile[beg+len("ylabel\n"):end-len("\n")]

        #write optons to gpl file
        gploutput.write('set title "%s"\n' %title )
        gploutput.write('set ylabel "%s"\n' %ylabel )
        gploutput.write('set xlabel "%s"\n' %xlabel )
        gploutput.write('set format x "%.0f"\n')
        gploutput.write('set format y "%.0f"\n')
        gploutput.write('set xdata time\n')
        if self.options.keyoptions == '':
            gploutput.write('set nokey\n')
        else:
            gploutput.write('set key %s\n' %self.options.keyoptions)
        gploutput.write('load "%s.labels"\n' %basename)
        gploutput.write('\n')
        if self.options.includefile != '':
            gploutput.write('#load include file\nload "%s"\n' %self.options.includefile)
        gploutput.write('plot ')

        #iterate over data sources
        first = True
        for index,datasource in enumerate(datasources):
            if datasource[0] == "line":
                style = self.options.linestyle
            elif datasource[0] == "dot":
                style = self.options.dotstyle
            elif datasource[0] == "box":
                style = self.options.boxstyle
            elif datasource[0] == "diamond":
                style = self.options.diamondstyle
            elif datasource[0] == "varrow":
                style = self.options.varrowstyle
            elif datasource[0] == "harrow":
                style = self.options.harrowstyle
            elif datasource[0] == "dline":
                style = self.options.dlinestyle
            else:
                style = self.options.defaultstyle
            if first == False:
                gploutput.write(', ')
            gploutput.write('"%s.datasets" index %s using ($1-946684800.0):2 with %s' %(basename,index,style ) )
            first = False

            # write data with same source in order
            for dataline in data:
                if dataline[0] == datasource:
                    dataoutput.write("%s" %dataline[1] )
            dataoutput.write("\n \n")

        gploutput.write(';\n')

        #output options
        gploutput.write('set term %s %s\n' %(self.options.terminaltype,self.options.terminaloptions) )
        gploutput.write('set output "%s.%s"\n' %(basename,self.options.terminaltype) )
        gploutput.write('replot\n')
        gploutput.write('pause -1\n')

        gploutput.close()
        dataoutput.close()
        labelsoutput.close()

        if self.options.execute:
            os.system("gnuplot  -persist %s.gpl &" %basename)

if __name__ == "__main__":
    xpl2gpl().main()
