#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import glob
import sys
import os
import shutil
import tempfile
import subprocess
import re
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application

class Gnuplot2PDF(Application):
    """Class to convert epslatex gnuplot to plain pdf"""

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
                        \usepackage[alsoload=accepted,alsoload=binary]{siunitx}

                        % siunitx
                        \newunit{\mps}{\meter\per\second}
                        \newunit{\kmps}{\km\per\second}
                        \renewunit{\bit}{b}
                        \newunit{\Bit}{bit}
                        \newunit{\kb}{\kilo\bit}
                        \newunit{\Mb}{\mega\bit}
                        \newunit{\Gb}{\giga\bit}
                        \newunit{\Byte}{byte}
                        \newunit{\kB}{\kilo\byte}
                        \newunit{\MB}{\mega\byte}
                        \newunit{\GB}{\giga\byte}
                        \newunit{\kbps}{\kb\per\second}
                        \newunit{\Mbps}{\Mb\per\second}
                        \newunit{\Gbps}{\Gb\per\second}

                        % Arrows
%                        \renewcommand*{\implies}{\ensuremath{\rightarrow}\xspace}
                        \renewcommand*{\iff}{\ensuremath{\leftrightarrow}\xspace}
                        \newcommand*{\IF}{\ensuremath{\Rightarrow}\xspace}
                        \newcommand*{\sra}{\ensuremath{\shortrightarrow}\xspace}
                        \newcommand*{\sla}{\ensuremath{\shortleftarrow}\xspace}

                        """

        # initialization of the option parser
        usage = "usage: %prog [options] BASENAME"
        self.parser.set_usage(usage)
        self.parser.set_defaults(force = False, fontsize = 7, serif = False,
                                 texsuffix = 'tex', epssuffix = 'eps')

        self.parser.add_option("-f", "--force",
                               action = "store_true", dest = "force",
                               help = "overwrite existing output pdf file")
        self.parser.add_option("-c", "--cfg", metavar = "FILE",
                               action = "store", dest = "cfgfile",
                               help = "use the file as config file for LaTeX. "\
                                      "No default packages will be loaded.")
        self.parser.add_option("-z", "--fsize", metavar = "NUM", type = int,
                               action = "store", dest = "fontsize",
                               help = "set font size [default: %default]")
        self.parser.add_option("-s", "--serif",
                               action = "store_false", dest = "serif",
                               help = "set the font family to Sans Serif [default]")
        self.parser.add_option("-r", "--roman",
                               action = "store_true", dest = "serif",
                               help = "set the font family to Roman")
        self.parser.add_option("-t", "--texIn", metavar = "SUF",
                               action = "store", dest = "texsuffix",
                               help = "define suffix of input tex file [default: %default]")
        self.parser.add_option("-e", "--epsIn", metavar = "SUF",
                               action = "store", dest = "epssuffix",
                               help = "define suffix of input eps file [default: %default]")
        self.parser.add_option("-p", "--pdfOut", metavar = "PDF",
                               action = "store", dest = "pdfoutput",
                               help = "define output pdf file [default: BASENAME.pdf]")

    def set_option(self):
        """Set options"""

        Application.set_option(self)

        # correct numbers of arguments?
        if len(self.args) != 1:
            self.parser.error("incorrect number of arguments")

        # Sans serif fonts?
        if self.options.serif:
            self.settings = self.settings + r"""\usepackage{lmodern}"""
        else:
            self.settings = self.settings + r"""\usepackage{cmbright}"""

        # Config File?
        if self.options.cfgfile:
            self.settings = "\\input{%s}" %os.path.realpath(self.options.cfgfile)

        self.filename  = os.path.basename(self.args[0])
        self.texinput  = os.path.realpath("%s.%s" %(self.args[0], self.options.texsuffix))
        self.epsinput  = os.path.realpath("%s.%s" %(self.args[0], self.options.epssuffix))

        if self.options.pdfoutput:
            self.pdfoutput = os.path.realpath(self.options.pdfoutput)
        else:
            self.pdfoutput = os.path.realpath("%s.pdf" %self.filename)

    def run(self):
        """Main method of the Gnuplot2PDF object"""

        tempdir = tempfile.mkdtemp()

        if not os.path.isfile(self.texinput):
            error("%s is not a regular file." %self.texinput)
            sys.exit(1)

        if not os.path.isfile(self.epsinput):
            error("%s is not a regular file." %self.epsinput)
            sys.exit(1)

        if not self.options.force and os.path.exists(self.pdfoutput):
            error("%s already exists." %self.pdfoutput)
            sys.exit(1)

        os.chdir(tempdir)

        # convert the eps graphic to a PDF one
        pdfinput = "%s.pdf" %os.path.splitext(os.path.basename(self.epsinput))[0]
        pdfinput = os.path.join(tempdir,pdfinput)
        if self.options.debug:
            cmd = ("epstopdf --debug --outfile=%s %s" %(pdfinput, self.epsinput))
        else:
            cmd = ("epstopdf --outfile=%s %s" %(pdfinput, self.epsinput))

        if subprocess.call(cmd, shell = True):
            error("Converting %s was unsuccessful." %os.path.realpath(self.epsinput))
            sys.exit(1)

        fh = file(self.texinput,'r')
        texinput = fh.read()
        # put correct graphic path in texinput because, original filename may be bogus (wrong folder)
        # use non-greedy +, to avoid matching of }}}}}}
        texinput = re.sub(r"\\includegraphics\{.+?\}", r"\\includegraphics{%s}" %pdfinput, texinput)
        fh.close()

        tmptexinput = os.path.join(tempdir,"graphic.tex")
        fh = file(tmptexinput,"w")
        fh.write(texinput)
        fh.close()

        # prepare the LaTeX file
        latex = open("latex_me", "w")
        latex.write("\\documentclass{scrartcl}\n"\
                    "%s\n"\
                    "\\pagestyle{empty}\n"\
                    "\\begin{document}\n"\
                    "\\begin{figure}\n"\
                    "\\centering\n"\
                    "\\fontsize{%s}{%s}\n"\
                    "\\selectfont\n"\
                    "\\input{%s}\n"\
                    "\\end{figure}\n"\
                    "\\end{document}\n"
                    %(self.settings, self.options.fontsize,
                      self.options.fontsize * 1.2, tmptexinput))

        latex.close()

        # set the LaTeX file
        if self.options.debug:
            cmd = ("pdflatex %s" %latex.name)
        else:
            cmd = ("pdflatex -interaction=batchmode %s" %latex.name)

        if subprocess.call(cmd, shell = True):
            error("Texing %s was unsuccessful." %os.path.realpath(latex.name))
            sys.exit(1)

        # Crop the new PDF file
        tmppdfoutput = os.path.join(tempdir,"tmp-crop.pdf")
        if self.options.debug:
            cmd = ("pdfcrop %s.pdf %s" %(latex.name, tmppdfoutput))
        else:
            cmd = ("pdfcrop --noverbose %s.pdf %s" %(latex.name, tmppdfoutput))

        if subprocess.call(cmd, shell = True):
            error("Cropping %s.pdf was unsuccessful." %os.path.realpath(latex.name))
            sys.exit(1)

        # copy the final result
        info("Copying file to %s" %self.pdfoutput)
        shutil.copy(tmppdfoutput, self.pdfoutput)

        # clean up
        os.remove(latex.name)
        for entry in glob.glob("%s.*"%latex.name):
            os.remove(entry)
        os.remove(pdfinput)
        os.remove(tmppdfoutput)
        os.remove(tmptexinput)
        os.rmdir(tempdir)

    def main(self):
        self.parse_option()
        self.set_option()
        self.run()


if __name__ == "__main__" :
    Gnuplot2PDF().main()
