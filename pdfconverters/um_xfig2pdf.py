#!/usr/bin/env python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-

# python imports
import os.path
import tempfile
import shutil
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_latex import UmLatex
from um_functions import call


class Xfig2PDF(Application):
    """Class to convert combined xfig to plain pdf"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        # object variable
        self._latex = None

        # initialization of the option parser
        usage = "usage: %prog [options] <xfig1> <xfig2> ..."
        self.parser.set_usage(usage)
        self.parser.set_defaults(force = False, outdir = os.getcwd(), save_figures = False)
        
        self.parser.add_option("-f", "--force",
                               action = "store_true", dest = "force",
                               help = "overwrite existing output pdf file")
        self.parser.add_option("-n", "--name", metavar = "NAME",
                               action = "store", dest = "basename",
                               help = "basename for all generated tex/pdf files")
        self.parser.add_option("-d", "--directory", metavar = "DIR",
                               action = "store", dest = "outdir",
                               help = "output directory [default: %default]")
        self.parser.add_option("-l", "--save-texfile", metavar = "FILE",
                               action = "store", dest = "texfile",
                               help = "save main latex file")
        self.parser.add_option("-x", "--save-figures",
                               action = "store_true", dest = "save_figures",
                               help = "save generated xfig latex figures")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) == 0:
            self.parser.error("incorrect number of arguments")

        # latex object
        self._latex = UmLatex(self.options.texfile, self.options.outdir,
                              self.options.force, self.options.debug, tikz = False) 

    def run(self):
        """Main method of the Xfig2PDF object"""
        
        # get all necessary directories
        srcdir = os.getcwd()
        destdir = self.options.outdir
        tempdir = tempfile.mkdtemp()
        
        # work in tempdir
        if self.options.debug:
            debug("Change directory %s" %tempdir)
        os.chdir(tempdir)
               
	    # convert all xfigs with fig2dev and put them into one latex document
        for index, xfig in enumerate(self.args):
        
            # get the full path of the figure
            xfigSrc = os.path.join(srcdir, xfig)
        
            if not os.path.isfile(xfigSrc):
                warn("%s is not a regular file. Skipped." %xfig)
                continue
                
            # get the basename (without extension)
            if self.options.basename:
                basename = "%s_%s" %(self.options.basename, index)
            else:
                basename = os.path.basename(xfig)
                basename = os.path.splitext(basename)[0]
            
            # build names for output files
            xfigPdf = "%s_xfig.pdf" %basename
            xfigTex = "%s_xfig.tex" %basename
                
            # run fig2dev
            info("Run fig2dev on %s..." %xfig)
            cmd1 = "fig2dev -L pdftex %s %s" %(xfigSrc, xfigPdf)
            cmd2 = "fig2dev -L pdftex_t -p %s %s %s" %(xfigPdf, xfigSrc, xfigTex)
            if self.options.debug:
                call(cmd1)
                call(cmd2)
            else:
                call(cmd1, noOutput = True)
                call(cmd2, noOutput = True)

            # should we save the xfig pdf and latex file and for further use?
            if self.options.save_figures:
                xfigPdfDst = os.path.join(destdir, xfigPdf)
                xfigTexDst = os.path.join(destdir, xfigTex)
            
                if not self.options.force and os.path.exists(xfigPdfDst):
                    error("%s already exists. Skipped." %xfigPdfDst)
                else:
                    info("Save xFig PDF file to %s..." %xfigPdfDst)
                    shutil.copy(xfigPdf, destdir)
                              
                if not self.options.force and os.path.exists(xfigTexDst):
                    error("%s already exists. Skipped." %xfigTexDst)
                else:
                    info("Save xFig Tex file to %s..." %xfigTexDst)
                    shutil.copy(xfigTex, destdir)
                    
            # add new generated to the latex doc
            self._latex.addLatexFigure(xfigTex, basename)

        # should we save generated main latex file for further purpose?
        if self.options.texfile:
           info("Save main LaTeX file...")
           self._latex.save()
            
        # build pdf graphics
        info("Generate PDF files...")
        self._latex.toPdf(tempdir = tempdir)

        # clean up
        shutil.rmtree(tempdir)

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__":
    Xfig2PDF().main()
