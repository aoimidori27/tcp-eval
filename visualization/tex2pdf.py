#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2010 - 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
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
import shutil
from logging import info, debug, warn, error

# tcp-eval imports
from common.application import Application
from visualization.latex import UmLatex

class Texfig2Pdf(Application):
    """Class to convert LaTeX figures to pdf graphics"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        # object variables
        self._latex = None

        # initialization of the option parser
        usage = "usage: %prog [options] <texfig1> <texfig2> ..."
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
        self.parser.add_option("-l", "--save-texfile", metavar = "FILE",
                               action = "store", dest = "texfile",
                               help = "save main latex file")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) == 0:
            self.parser.error("incorrect number of arguments.")

        # latex object
        self._latex = UmLatex(self.options.texfile, self.options.outdir,
                              self.options.force, self.options.debug)

    def run(self):
        """Main method of the Texfig2Pdf object"""

        # get all necessary directories
        srcdir = os.getcwd()
        destdir = self.options.outdir

	    # add all figures into one latex document
        for index, figure in enumerate(self.args):

            # get the full path of the figure
            texfigSrc = os.path.join(srcdir, figure)

            if not os.path.isfile(texfigSrc):
                warn("%s is not a regular file. Skipped." %figure)
                continue

            # get the basename (without extension)
            if self.options.basename:
                basename = "%s_%s" %(self.options.basename, index)
            else:
                basename = os.path.basename(figure)
                basename = os.path.splitext(basename)[0]

            # add tex fig to the latex doc
            self._latex.addLatexFigure(figure, basename)

        # should we save generated main latex file for further purpose?
        if self.options.texfile:
           info("Save main LaTeX file...")
           self._latex.save()

        # build pdf graphics
        info("Generate PDF files...")
        self._latex.toPdf()


    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__":
    Texfig2Pdf().main()
