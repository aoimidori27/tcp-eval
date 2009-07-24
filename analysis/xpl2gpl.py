#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""xpl2gpl.py -- tcptrace / xplot 2 gnuplot converter

"""
import os, math, optparse, sys, logging
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
    self.optparser.set_defaults(debug = False, title = 'title', xlabel = 'x', ylabel = 'y', execute = False)

    self.optparser.add_option("-t", "--title", metavar = "SUF",
			    action = "store", dest = "title",
			    help = "gnuplot title [default: %default]")
    self.optparser.add_option("-x", "--xlabel", metavar = "SUF",
			    action = "store", dest = "xlabel",
			    help = "gnuplot x label [default: %default]")
    self.optparser.add_option("-y", "--ylabel", metavar = "SUF",
			    action = "store", dest = "ylabel",
			    help = "gnuplot y label [default: %default]")

    self.optparser.add_option("-d", "--debug", 
			    action = "store_true", dest = "debug",
			    help = "debug parsing [default: %default]")

    self.optparser.add_option("-e", "--execute-gnuplot", 
			    action = "store_true", dest = "execute",
			    help = "execute gnuplot after conversion [default: %default]")

  def main(self):

    (self.options, self.args) = self.optparser.parse_args()

  
    for entry in self.args:
      if not os.path.isfile(entry):
	warn("%s not found." %entry)
	exit(1)

      declaration = declaration = r'''
	root	:=	timeval,title,xlabel,ylabel,(diamond / text / varrow / harrow / line / dline / dot / box / tick / color / linebreak)*,end*
	alphanum	:= 	[a-zA-Z0-9]
	punct	:= 	[!@#$%^&()+=|\{}:;<>,.?/"_]
	whitespace	:= 	[ \t]
	string	:= 	( alphanum / punct / whitespace )*, linebreak
	keyword	:=	[ A-Z]+
	float1	:=	[0-9]+,".",[0-9]+
	float2	:=	[0-9]+,".",[0-9]+
	int1 	:=	[0-9]+
	int2 	:=	[0-9]+
	end		:=	'go', linebreak*
	timeval	:=	( 'timeval double' / 'timeval signed' ), linebreak
	title	:=	'title\n',string
	xlabel	:= 	'xlabel\n',string
	ylabel	:= 	'ylabel\n',string
	linebreak	:=	[ \t]*,( '\n' / '\n\r' ),[ \t]*
	color	:=	( 'green' / 'yellow' / 'white' / 'orange' / 'blue' / 'magenta' / 'red' / 'purple' / 'pink' )
	harrow 	:=	( 'larrow' / 'rarrow'),whitespace,float1,whitespace,int1,linebreak
	varrow 	:=	( 'darrow' / 'uarrow'),whitespace,float1,whitespace,int1,linebreak
	line	:=	( 'line' ),whitespace,float1,whitespace,int1,whitespace,float2,whitespace,int2,linebreak
	dline	:=	( 'dline' ),whitespace,float1,whitespace,int1,whitespace,float2,whitespace,int2,linebreak
	dot 	:=	('dot'),whitespace,float1,whitespace,int1,(whitespace,color)*, linebreak
	diamond	:=	('diamond'),whitespace,float1,whitespace,int1,(whitespace,color)*,linebreak
	box		:=	('box'),whitespace,float1,whitespace,int1,(whitespace,color)*,linebreak
	tick 	:=	('dtick' / 'utick' / 'ltick' / 'rtick' / 'vtick' / 'htick' ),whitespace,float1,whitespace,int1,linebreak
	text	:=	('atext' / 'btext' / 'ltext' / 'rtext' ),whitespace,float1,whitespace,int1,linebreak,keyword,linebreak                                                                                              
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
      dataoutput = open ( "%s.data" %(basename) , 'w')
      labelsoutput = open ( "%s.labels" %(basename) , 'w')

      datasources = list()
      data = list()
      taglist = TextTools.tag(xplfile, parser)
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
	  labelsoutput.write('set label "%s" at (%s-946684800.000000), %s %s' %(label,xpoint,ypoint,position) )

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
	  title = xplfile[beg+len("title\n"):end-len("\n")]
      # read axis labels
	elif tag == 'xlabel':
	  xlabel = xplfile[beg+len("xlabel\n"):end-len("\n")]
	elif tag == 'ylabel':
	  ylabel = xplfile[beg+len("ylabel\n"):end-len("\n")]
	  


      #write optons to gpl file
      gploutput.write('set title "%s"\n' %title )    
      gploutput.write('set ylabel "%s"\n' %ylabel )    
      gploutput.write('set xlabel "%s"\n' %xlabel )    
      gploutput.write('set format x "%.0f"\n')
      gploutput.write('set format y "%.0f"\n')
      gploutput.write('set xdata time\n')
      gploutput.write('set nokey\n')
      gploutput.write('load "%s.labels"\n' %basename)
      gploutput.write('plot ')
      
      #iterate over data sources
      first = True
      for index,datasource in enumerate(datasources):
	if datasource[0] == "line":
	  style = "lines"
	elif datasource[0] == "dot":
	  style = "dots"
	elif datasource[0] == "box":
	  style = "points pt 3"
	elif datasource[0] == "diamond":
	  style = "points pt 1"
	elif datasource[0] == "varrow":
	  style = "points pt 1"
	elif datasource[0] == "harrow":
	  style = "points pt 5"
	elif datasource[0] == "dline":
	  style = "linepoints pt 4"
	else: 
	  style = "points pt 2"
	if first == False:
	  gploutput.write(', ')
	gploutput.write('"%s.datasets" index %s using ($1-946684800.0):2 with %s' %(basename,index,style ) )
	first = False


      #write data with same source in order
	for dataline in data:
	  if dataline[0] == datasource:
	    dataoutput.write("%s" %dataline[1] )
	dataoutput.write("\n \n")

      gploutput.write(';\n')



    #output options 
      gploutput.write('set term postscript\n')
      gploutput.write('set output "%s.ps"\n' %basename)
      gploutput.write('replot\n')
      gploutput.write('pause -1\n')

      gploutput.close()
      dataoutput.close()
      labelsoutput.close()

  
if __name__ == "__main__":
  xpl2gpl().main()
 