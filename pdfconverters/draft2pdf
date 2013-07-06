#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2009 - 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
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
import os.path
from logging import info, debug, warn, error

# tcp-eval imports
from application import Application
from functions import call, execute

class Draft2Pdf(Application):
    """Class to convert internet draft text files to pdfs"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        # initialization of the option parser
        usage = "usage: %prog [options] <file1> <file2> ..."
        self.parser.set_usage(usage)
        self.parser.set_defaults(force = False, outdir = os.getcwd())

        self.parser.add_option("-f", "--force",
                               action = "store_true", dest = "force",
                               help = "overwrite existing output pdf file")
        self.parser.add_option("-n", "--name", metavar = "NAME",
                               action = "store", dest = "basename",
                               help = "basename for all generated pdf files")
        self.parser.add_option("-d", "--directory", metavar = "DIR",
                               action = "store", dest = "outdir",
                               help = "output directory [default: %default]")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) == 0:
            self.parser.error("incorrect number of arguments")

    def run(self):
        """Main method of the DraftToPdf object"""
        
        # get all necessary directories
        srcdir = os.getcwd()
        destdir = self.options.outdir
                       
	    # for all ID given on command line
        for index, draft in enumerate(self.args):

            # get the full path of the figure
            draftSrc = os.path.join(srcdir, draft)
            
            if not os.path.isfile(draftSrc):
                warn("%s is not a regular file. Skipped." %draft)
                continue

            # get the basename (without extension)
            if self.options.basename:
                basename = "%s_%s" %(self.options.basename, index)
            else:
                basename = os.path.basename(draft)
                basename = os.path.splitext(basename)[0]
           
            # build name for output file
            draftDst = os.path.join(destdir, "%s.pdf" %basename)

            if not self.options.force and os.path.exists(draftDst):
                warn("%s already exists. Skipped." %draftDst)
                continue

            # convert the draft to a PS file
            if self.options.debug:
                cmd = ("enscript -v -B -f Courier10 --margins=70::50 %s -p -" %draftSrc)
            else:
                cmd = ("enscript -B -f Courier10 --margins=70::50 %s -p -" %draftSrc)

            # we want only stdout
            info("Run enscript on %s..." %draft)
            enscript = execute(cmd)[0]

            # convert the PS file to a PDF file
            info("Run ps2pdf on %s..." %draft)
            cmd = ("ps2pdf - %s" %draftDst)
            if self.options.debug:
                call(cmd, input = enscript)
            else:
                call(cmd, input = enscript, noOutput = True)

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__":
    Draft2Pdf().main()
