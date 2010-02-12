#!/usr/bin/env python -W ignore::DeprecationWarning
# -*- coding: utf-8 -*-

# python imports
import os.path
import shutil
import tempfile
import Gnuplot
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_latex import UmLatex
from um_functions import call


class Gnuplot2PDF(Application):
    """Class to convert epslatex gnuplot to plain pdf"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        # object variable
        self._latex = None

        # initialization of the option parser
        usage = "usage: %prog [options] <gplot> | <gplotdir> ...\n"\
                "       where 'gplotdir' is directory which contains one *.gpl or *.gplot file"

        self.parser.set_usage(usage)
        self.parser.set_defaults(force = False, outdir = os.getcwd(), fontsize = 9)

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
        self.parser.add_option("-g", "--save-figures",
                               action = "store_true", dest = "save_figures",
                               help = "save generated gnuplot latex plots")
        self.parser.add_option("-z", "--font-size", metavar = "NUM", type = int,
                               action = "store", dest = "fontsize",
                               help = "set font size [default: %default]")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) == 0:
            self.parser.error("incorrect number of arguments")

        # latex object
        self._latex = UmLatex(self.options.texfile, self.options.outdir,
                              self.options.force, self.options.debug, tikz = False)
        
        # use sans serif font and set the correct font size
        self._latex.setDocumentclass("scrartcl", "fontsize=%spt" %self.options.fontsize)
        self._latex.addSetting(r"\renewcommand{\familydefault}{\sfdefault}")

    def run(self):
        """Main method of the Gnuplot2PDF object"""

        # get all necessary directories
        srcdir = os.getcwd()
        destdir = self.options.outdir
        tempdir = tempfile.mkdtemp()   

        # work in tempdir
        if self.options.debug:
            debug("Change directory %s" %tempdir)
        os.chdir(tempdir)
                
	    # plot all plotfiles and put them into one latex document
        for index, gplot in enumerate(self.args):
       
            # get the full path of the figure or directory
            gplotSrc = os.path.join(srcdir, gplot)
        
            # 'gplotSrc' is a directory
            if os.path.isdir(gplotSrc):
            
                for entry in os.listdir(gplotSrc):
                    # get the full path
                    fileSrc = os.path.join(gplotSrc, entry)
                    # create symlinks into the temp directory
                    os.symlink(fileSrc, entry)

                    # get file extension
                    ext = os.path.splitext(entry)[1]
                    if ext == ".gpl" or ext == ".gplot":
                        if not os.path.isfile(gplotSrc):
                            gplotSrc = os.path.join(entry)
                        else:
                            warn("%s contains more than one *.gpl or gplot file. "\
                                 "Directory skipped." %gplot)
                            break
                
                if not os.path.isfile(gplotSrc):
                    warn("%s does not contain one *.gpl or *.gplot file. "\
                         "Directory skipped." %gplot)
                    continue
                
            # 'gplotSrc' is neither a directory nor file
            elif not os.path.isfile(gplotSrc):
                warn("%s is not a regular file or directory. Skipped." %gplot)
                continue
                
            # get the basename (without extension)
            if self.options.basename:
                basename = "%s_%s" %(self.options.basename, index)
            else:
                basename = os.path.basename(gplot)
                basename = os.path.splitext(basename)[0]
                
            # build names for output files
            gplotEps = "%s_gplot.eps" %basename
            gplotPdf = "%s_gplot.pdf" %basename
            gplotTex = "%s_gplot.tex" %basename

            # build gnuplot object and load the given gnuplot file
            # be safe; print a new line if the load file include a "pause" command
            info("Run gnuplot on %s..." %gplot)            
            gp = Gnuplot.Gnuplot(debug = int(self.options.debug))
            gp.load(gplotSrc)
            gp("\n")
            
            # replot with epslatex terminal
            gp('set terminal epslatex color solid "default" %s' %self.options.fontsize)
            gp('set output "%s"' %gplotTex)
            gp("replot")
            gp.close()
                        
            # convert the EPS file to a PDF file   
            info("Run epstopdf on %s..." %gplot)
            if self.options.debug:
                cmd = "epstopdf --debug --outfile=%s %s" %(gplotPdf, gplotEps)
                call(cmd)
            else:
                cmd = "epstopdf --outfile=%s %s" %(gplotPdf, gplotEps)
                call(cmd, noOutput = True)

            # should we save the xfig pdf and latex file and for further use?
            if self.options.save_figures:
                gplotPdfDst = os.path.join(destdir, gplotPdf)
                gplotTexDst = os.path.join(destdir, gplotTex)
            
                if not self.options.force and os.path.exists(gplotPdfDst):
                    error("%s already exists. Skipped." %gplotPdfDst)
                else:
                    info("Save gnuplot PDF file to %s..." %gplotPdfDst)
                    shutil.copy(gplotPdf, gplotPdfDst)
                              
                if not self.options.force and os.path.exists(gplotTexDst):
                    error("%s already exists. Skipped." %gplotTexDst)
                else:
                    info("Save gnuplot Tex file to %s..." %gplotTexDst)
                    shutil.copy(gplotTex, gplotTexDst)
                    
            # add new generated to the latex doc
            self._latex.addLatexFigure(gplotTex, basename)

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


if __name__ == "__main__" :
    Gnuplot2PDF().main()
