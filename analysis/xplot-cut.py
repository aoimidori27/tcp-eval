#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys
import os
import os.path
from subprocess import Popen, PIPE
import re

from logging import info, debug, warn, error


# umic-mesh imports
#from um_application import Application
#from um_config import *
#from um_functions import call
    


def cut(begin, end, infile, outfile):
	ifh = open(infile,  'r')
	ofh = open(outfile, 'w')
	state = 0
	buf   = ''
	print "Cutting %s" % infile
	for line in ifh.xreadlines():
		line = line.rstrip("\n")
		if state == 0:
			ofh.write(line + "\n")
			if line == 'sequence offset' or line == 'sequence number':
				state += 1
			continue
		if state == 1:
			buf += line + "\n"
			if re.match('^(\D+|\d+)$', line):
				continue
			m = re.match('\w+ ([\d.]+) \d+(?: ([\d.]+))?', line)
			if not m:
				raise 'Something wrong in state 1: %s' % line
			d = float(m.group(2) if m.group(2) else m.group(1))
			if d < begin:
				buf = ''
				continue
			elif begin <= d and d <= end:
				ofh.write(buf)
				buf = ''
				state = state + 1
				continue
		if state == 2:
			buf += line + "\n"
			if re.match('^(\D+|\d+)$', line):
				continue
			m = re.match('\w+ ([\d.]+)', line)
			if not m:
				raise 'Something wrong in state 2: %s' % line
			d = float(m.group(1))
			if begin <= d and d <= end:
				ofh.write(buf)
				buf = ''
				continue
			elif d > end:
				continue
	ofh.close()
	ifh.close()


def xplot(file):
	xplot = Popen(["xplot", file], bufsize=0, stdout=PIPE, shell=False).stdout
	while True:
		line = xplot.readline()
		if not line:
			break
		begin, end = re.match("<time_begin:time_end> = <([\d.]+):([\d.]+)>", line).group(1, 2)
		begin = float(begin)
		end   = float(end)
		cut(begin, end, file, "%s_%s_%s.xpl" % (file, begin, end))

xplot(sys.argv[1])
