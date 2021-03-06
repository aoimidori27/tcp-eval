#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
# Copyright (C) 2010 Carsten Wolff <carsten@wolffcarsten.de>
# Copyright (C) 2009 Damian Lukowski <damian@tvk.rwth-aachen.de>
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
import sys
import re
import textwrap
from subprocess import Popen, PIPE
from logging import info, debug, warn, error

# tcp-eval imports
from common.application import Application

class XplotCut(Application):
    """xplot-cut generates a new xpl file based on the current view of xplot"""

    def __init__(self):
        """Creates a new XplotCut object"""

        # initialization of argparse
        description = textwrap.dedent("""
                xplot-cut opens a xpl-file with xplot. The modified version of
                xplot should print the start and end time of the current view
                to stdout when 'c' is pressed. xplot-cut then grabs the output
                and creates a new xpl-file with the given start and end
                time""")
        Application.__init__(self, description=description)
        self.parser.add_argument("xpl_file", metavar="xpl", help="a xplot "\
                "xpl file")

    def apply_options(self):
        """Configure XplotCut object based on the options form the argparser"""

        Application.apply_options(self)

    def cut(self, begin, end):
        """Write the current view to a new file"""

        infile = self.args.xpl_file
        outfile = "%s-%s-%s.xpl" %(self.args.xpl_file, begin, end)

        ifh = open(infile,  'r')
        ofh = open(outfile, 'w')
        state = 0
        buf   = ''
        info("Cutting %s" %(infile))
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
                    warn('Something wrong in state 1: %s' %(line))
                    continue
                d = float(m.group(2) if m.group(2) else m.group(1))
                if d < begin:
                    buf = ''
                    continue
                elif begin <= d and d <= end:
                    ofh.write(buf)
                    buf = ''
                    state += 1
                    continue
            if state == 2:
                buf += line + "\n"
                if re.match('^(\D+|\d+)$', line):
                    continue
                m = re.match('\w+ ([\d.]+)', line)
                if not m:
                    warn('Something wrong in state 2: %s' %(line))
                    continue
                d = float(m.group(1))
                if begin <= d and d <= end:
                    ofh.write(buf)
                    buf = ''
                    continue
                elif d > end:
                    continue
        ofh.close()
        ifh.close()

    def run(self):
        """Xplot file is opened (and normally doesn't print anything to
        stdout). The modified version prints by pressing 'c' the begin and end
        time of the current view. This view is then written to a new file.
        """

        xplot = Popen(["xplot", self.args.xpl_file], bufsize=0, stdout=PIPE,
                shell=False).stdout
        while True:
            line = xplot.readline()
            if not line: break
            print line
            begin, end = re.match("<time_begin:time_end> = "\
                    "<(-?[\d.]+):(-?[\d.]+)>", line).group(1, 2)
            self.cut(float(begin), float(end))

    def main(self):
        self.parse_options()
        self.apply_options()
        self.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    XplotCut().main()

