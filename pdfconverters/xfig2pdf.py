#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import sys
import os
import shutil
import tempfile
import subprocess
import glob
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application

class Xfig2PDF(Application):
    """Class to convert combined xfig to plain pdf"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        # object variable
        self.settings = r"""
                        \usepackage[english]{babel}
                        \usepackage[utf8]{inputenc}
                        \usepackage[T1]{fontenc}
                        \usepackage{graphicx}
                        \usepackage{xcolor}
                        \usepackage{stmaryrd}

                        % turn off margins
                        \usepackage[paper=a4paper,left=0mm,right=0mm,top=0mm,bottom=0mm]{geometry}

                        % Arrows
                        \newcommand*{\implies}{\ensuremath{\rightarrow}\xspace}
                        \renewcommand*{\iff}{\ensuremath{\leftrightarrow}\xspace}
                        \newcommand*{\IF}{\ensuremath{\Rightarrow}\xspace}
                        \newcommand*{\sra}{\ensuremath{\shortrightarrow}\xspace}
                        \newcommand*{\sla}{\ensuremath{\shortleftarrow}\xspace}

                        """

        # initialization of the option parser
        usage = "usage: %prog [options] BASENAME"
        self.parser.set_usage(usage)
        self.parser.set_defaults(force = False, texsuffix = 'pdf_t',
                                 pdfsuffix = 'pdf', outputsuffix = 'comb.pdf')
        self.parser.add_option("-f", "--force",
                               action = "store_true", dest = "force",
                               help = "overwrite existing output pdf file")
        self.parser.add_option("-c", "--cfg", metavar = "FILE",
                               action = "store", dest = "cfgfile",
                               help = "use the file as config file for LaTeX. "\
                                      "No default packages will be loaded.")
        self.parser.add_option("-t", "--texIn", metavar = "SUF",
                               action = "store", dest = "texsuffix",
                               help = "define suffix of input tex file [default: %default]")
        self.parser.add_option("-p", "--pdfIn", metavar = "SUF",
                               action = "store", dest = "pdfsuffix",
                               help = "define suffix of input pdf file [default: %default]")
        self.parser.add_option("-P", "--pdfOut", metavar = "SUF",
                               action = "store", dest = "outputsuffix",
                               help = "define suffix of output pdf file [default: %default]")
        self.parser.add_option("--landscape",
                               action = "store_true", dest = "landscape",
                               help = "use landscape orientation")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) != 1:
            self.parser.error("incorrect number of arguments")

        # Config File?
        if self.options.cfgfile:
            self.settings = "\\input{%s}" %os.path.realpath(self.options.cfgfile)

        self.texinput  = os.path.realpath("%s.%s" %(self.args[0], self.options.texsuffix))
        self.pdfinput  = os.path.realpath("%s.%s" %(self.args[0], self.options.pdfsuffix))
        self.pdfoutput = os.path.realpath("%s.%s" %(self.args[0], self.options.outputsuffix))

    def run(self):
        """Main method of the Xfig2PDF object"""

        tempdir = tempfile.mkdtemp()

        if not os.path.isfile(self.texinput):
            error("%s is not a regular file." %self.texinput)
            sys.exit(1)

        if os.path.isfile(self.pdfinput):
            shutil.copy(self.pdfinput, tempdir)
        else:
            error("%s is not a regular file." %self.pdfinput)
            sys.exit(1)

        if not self.options.force and os.path.exists(self.pdfoutput):
            error("%s already exists." %self.pdfoutput)
            sys.exit(1)

        os.chdir(tempdir)

        # prepare the LaTeX file
        latex = open("latex_me", "w")

        if self.options.landscape:
            latex.write("\\documentclass[landscape]{scrartcl}\n"\
                        "%s\n" %self.settings)
        else:
            latex.write("\\documentclass{scrartcl}\n"\
                        "%s\n" %self.settings)

        latex.write("\\pagestyle{empty}\n"\
                    "\\begin{document}\n"\
                    "\\begin{figure}\n"\
                    "\\centering\n"\
                    "\\input{%s}\n"\
                    "\\end{figure}\n"\
                    "\\end{document}\n" % self.texinput)
        latex.close()

        # set the LaTeX file
        if self.options.debug:
            cmd = ("pdflatex %s" % latex.name)
        else:
            cmd = ("pdflatex -interaction=batchmode %s" % latex.name)

        if subprocess.call(cmd, shell = True):
            error("Texing %s was unsuccessful." %os.path.realpath(latex.name))
            sys.exit(1)

        # Crop the new PDF file
        pdfoutputbasename = os.path.basename(self.pdfoutput)
        if self.options.debug:
            cmd = ("pdfcrop %s.pdf %s" %(latex.name, pdfoutputbasename))
        else:
            cmd = ("pdfcrop --noverbose %s.pdf %s" % (latex.name, pdfoutputbasename))

        if subprocess.call(cmd, shell = True):
            error("Cropping %s.pdf was unsuccessful." %os.path.realpath(latex.name))
            sys.exit(1)

        # copy the final result
        shutil.copy(pdfoutputbasename, self.pdfoutput)

        #clean up
        os.remove(latex.name)
        for entry in glob.glob("%s.*"%latex.name):
            os.remove(entry)
        os.remove(os.path.basename(self.pdfinput))
        os.remove(pdfoutputbasename)
        os.rmdir(tempdir)

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__":
    Xfig2PDF().main()

