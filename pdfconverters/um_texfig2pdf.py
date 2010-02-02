#!/usr/bin/env python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-

# python imports
import os.path
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_latex import UmLatex


class Texfig2Pdf(Application):
    """Class to convert LaTeX figures to pdf graphics"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        # object variables
        self._filename = None
        self._directory = None

        # initialization of the option parser
        usage = "usage: %prog [options] <texfig1> <texfig1> .."
        self.parser.set_usage(usage)
        self.parser.set_defaults(force = False)

        self.parser.add_option("-f", "--force",
                               action = "store_true", dest = "force",
                               help = "overwrite existing output pdf file")
        self.parser.add_option("-n", "--name", metavar = "NAME",
                               action = "store", dest = "basename",
                               help = "basename for output files, instead of "\
                                      "deriving it from the input files")
        self.parser.add_option("-d", "--output-directory", metavar = "DIR",
                               action = "store", dest = "outdir",
                               help = "output directory, instead of the current directory")
        self.parser.add_option("-s", "--save", metavar = "NAME",
                               action = "store", dest = "latexfile",
                               help = "save generated latex file for further use")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) == 1:
            self.parser.error("incorrect number of arguments.") 
                     
        # latex file name is given?       
        if self.options.latexfile:        
            self._filename = self.options.latexfile
        
        # is a specific directory given?
        if self.options.outdir:
            self._directory = self.options.outdir

    def run(self):
        """Main method of the Texfig2Pdf object"""

        latexdoc = UmLatex(self._filename, self._directory)
        
        # debug mode 
        if self.options.debug:
            latexdoc.setDebug()
            latexdoc.setVerbose()
            
        # being more verbose
        if self.options.verbose:
            latexdoc.setVerbose()
        
        # overwrite existing files 
        if self.options.force:
            latexdoc.setForce()
        
	    # add all figures into one latex document
        for index, figure in enumerate(self.args):
            if not os.path.isfile(figure):
                warn("%s is not a regular file. Skipped." %figure)
                continue
            
            info("Load figure %s..." %figure)
            if self.options.basename:
                latexdoc.addLatexFigure(figure,"%s.%s"\
                                        %(self.options.basename, index))
            else:
                latexdoc.addLatexFigure(figure)

        # should we save generated latex file for further purpose?
        if self.options.latexfile:
           info("Save LaTeX file...")
           latexdoc.save()
            
        # build pdf graphics
        info("Generate PDF files...")
        latexdoc.toPdf()
        
    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__":
    Texfig2Pdf().main()
