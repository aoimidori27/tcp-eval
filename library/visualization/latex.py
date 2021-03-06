#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
# Copyright (C) 2007 Arnd Hannemann <arnd@arndnet.de>
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
import tempfile
import shutil
from pyPdf import PdfFileWriter, PdfFileReader
from logging import info, debug, warn, error

# tcp-eval imports
from common.functions import call

class UmLatex():
    """Class to convert latex figures (e.g. tikz) to pdf graphics"""

    def __init__(self, texfile="main.tex", outdir=os.getcwd(), force=False,
            debug=False, defaultPackages=True, defaultSettings=True,
            siunitx=True, tikz=True):
        """Constructor of the object"""

        # tex filename and figures names (for building output files)
        self._figures = list()
        self._texfile = "main.tex"
        self._outdir = os.getcwd()
        self._tempdir = tempfile.mkdtemp()

        # set members only if arguments are not None
        self._texfile = self.__getValidTexfile(texfile)
        self._outdir = self.__getValidOutdir(outdir)

        # force/debug mode
        self._force = force
        self._debug = debug

        # latex content
        self._documentclass = ''
        self._packages = list()
        self._settings = list()
        self._content = list()

        # load default values for the latex document (class/packages/settings)
        self.loadDefaults(defaultPackages, defaultSettings, siunitx, tikz)

    def __del__(self):
        """Destructor of the object"""

        shutil.rmtree(self._tempdir)

    def loadDefaults(self, defaultPackages=True, defaultSettings=True,
                       siunitx=True, tikz=True):
        """Load default settings for the generated latex file. Currently, we
        default values for the following packages

        1. defaultPackages: includes etex, babel, inputenc, fontenc, lmodern,
        textcomp, graphicx, xcolor
        2. defaultSettings: pagestyle empty
        3. default values for siunitx, tikz
        """

        self.setDocumentclass("scrartcl")

        if defaultPackages:
            self.addPackage("etex")
            self.addPackage("babel", "english")
            self.addPackage("inputenc", "utf8")
            self.addPackage("fontenc", "T1")
            self.addPackage("lmodern")
            self.addPackage("textcomp")
            self.addPackage("graphicx")
            self.addPackage("xcolor")

        if defaultSettings:
            self.addSetting(r"\pagestyle{empty}")

            # some arrows
            self.addSetting(r"\newcommand*{\Implies}"\
                    r"{\ensuremath{\rightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\IFF}"\
                    r"{\ensuremath{\leftrightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\IF}"\
                    r"{\ensuremath{\Rightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\SRA}"\
                    r"{\ensuremath{\shortrightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\SLA}"\
                    r"{\ensuremath{\shortleftarrow}\xspace}")

        # load siunitx
        if siunitx:
            self.addPackage("xfrac")
            self.addPackage("siunitx")
            self.addSetting(r"\sisetup{detect-weight,per-mode=fraction,"\
                    r"fraction-function=\sfrac,separate-uncertainty,"\
                    r"load-configurations=binary,"\
                    r"load-configurations=abbreviations}")
            self.addSetting(r"\DeclareSIUnit{\Second}{Sekunden}")
            self.addSetting(r"\DeclareSIUnit{\mps}{\meter\per\second}")
            self.addSetting(r"\DeclareSIUnit{\kmps}{\km\per\second}")
            self.addSetting(r"\DeclareSIUnit{\bit}{b}")
            self.addSetting(r"\DeclareSIUnit{\Bit}{bit}")
            self.addSetting(r"\DeclareSIUnit{\kb}{\kilo\bit}")
            self.addSetting(r"\DeclareSIUnit{\Mb}{\mega\bit}")
            self.addSetting(r"\DeclareSIUnit{\Gb}{\giga\bit}")
            self.addSetting(r"\DeclareSIUnit{\Byte}{byte}")
            self.addSetting(r"\DeclareSIUnit{\kB}{\kilo\byte}")
            self.addSetting(r"\DeclareSIUnit{\MB}{\mega\byte}")
            self.addSetting(r"\DeclareSIUnit{\GB}{\giga\byte}")
            self.addSetting(r"\DeclareSIUnit{\bps}{\bit\per\second}")
            self.addSetting(r"\DeclareSIUnit{\Bitps}{\Bit\per\second}")
            self.addSetting(r"\DeclareSIUnit{\Bps}{\byte\per\second}")
            self.addSetting(r"\DeclareSIUnit{\Byteps}{\Byte\per\second}")
            self.addSetting(r"\DeclareSIUnit{\kbps}{\kb\per\second}")
            self.addSetting(r"\DeclareSIUnit{\Mbps}{\Mb\per\second}")
            self.addSetting(r"\DeclareSIUnit{\Gbps}{\Gb\per\second}")
            self.addSetting(r"\DeclareSIUnit{\blocks}{blocks}")
            self.addSetting(r"\DeclareSIUnit{\transactions}{transactions}")
            self.addSetting(r"\DeclareSIUnit{\nnumber}{\#}")

        # load tikz
        if tikz:
            self.addPackage("tikz")
            self.addSetting(r"\usetikzlibrary{backgrounds,arrows,calc,"\
                    "positioning,fit}")

    def __buildDocument(self):
        packages = "\n".join(self._packages)
        settings = "\n".join(self._settings)
        content  = "\n".join(self._content)
        document = "%s\n%s\n%s\n\\begin{document}\n%s\n\\end{document}"\
            %(self._documentclass , packages, settings, content)

        return document

    def __getValidTexfile(self, texfile):
        """If the parameter "texfile" is "None" return the privat member
        variable "self._texfile" otherwise return the parameter itself """

        if texfile:
            return texfile
        else:
            return self._texfile

    def __getValidOutdir(self, outdir):
        """If the parameter "outdir" is "None" return the privat member
        variable "self._outdir" otherwise return the parameter itself """

        if outdir:
            return outdir
        else:
            return self._outdir

    def __getValidTempdir(self, tempdir):
        """If the parameter "tempdir" is "None" return the privat member
        variable "self._tempdir" otherwise return the parameter itself """

        if tempdir:
            return tempdir
        else:
            return self._tempdir

    def setDocumentclass(self, documentclass, *options):
        """Set the latex documentclass for the document"""

        if options:
            options = ", ".join(options)
            self._documentclass = "\\documentclass[%s]{%s}"\
                    %(options, documentclass)
        else:
            self._documentclass = "\\documentclass{%s}" %(documentclass)

    def addPackage(self, package, *options):
        """Add the given package with its options to the document. Only the
        name of the package is needed. The "\usepackage{}" latex command will
        be automatically added """

        if options:
            options = ", ".join(options)
            command = "\\usepackage[%s]{%s}" %(options, package)
        else:
            command = "\\usepackage{%s}" %(package)

        self._packages.append(command)

    def addSetting(self, command):
        """Add an arbitrary latex command/setting to the document. The given
        command the will be added before the latex "\begin{document}" """

        self._settings.append(command)

    def addContent(self, content):
        """Add arbitrary latex content to the document. The content will be
        added after the latex "\begin{document}" """

        self._content.append(content)

    def addLatexFigure(self, latexfig, figname, command=None):
        """Add a latex figure to the document. The figure given by the
        parameter "latexfig" is included by the latex command "\input{}". All
        necessary commands like "\begin{figure}" or "\end{figure}" are
        automatically added. The last added command is "\clearpage", so that
        all figures are on a new page. If the optional parameter "command" is
        given, it will be added before the figure is included """

        # save the name of the figure for further uses
        self._figures.append(figname)

        self.addContent("\\begin{figure}\n\\centering")
        # if an additional command is given, we added it
        if command:
            self.addContent(command)
        self.addContent("\\input{%s}\n\\end{figure}\n\\clearpage" %(latexfig))

    def save(self, texfile=None, outdir=None):
        """Save the generated latex file to "outdir/texfile"""

        # build document
        document = self.__buildDocument()

        # build output path
        texfile = self.__getValidTexfile(texfile)
        destdir = self.__getValidOutdir(outdir)
        texDst = os.path.join(destdir, texfile)

        if not self._force and os.path.exists(texDst):
            error("%s already exists. Skipped." %texDst)
            return

        # write content
        info("Write LaTeX document to %s..." %texDst)
        latex = open(texDst, "w")
        latex.write(document)
        latex.close()

    def toPdf(self, texfile=None, outdir=None, tempdir=None):
        """Generate the actual pdf figures. First, the document is build. Then
        pdflatex will run on the document. Afterwards, the new generated pdf
        will be splitted into single pages, each graphic on a new page.
        Finally, each page will be cropped by pdfcrop """

        # building document and output path
        document = self.__buildDocument()
        texfile = self.__getValidTexfile(texfile)
        destdir = self.__getValidOutdir(outdir)
        tempdir = self.__getValidTempdir(tempdir)

        # run pdflatex
        info("Run pdflatex on %s..." %texfile)
        cmd = "pdflatex -jobname %s -output-directory %s" %(texfile, tempdir)
        if self._debug:
            call(cmd, input=document)
        else:
            call(cmd, input=document, noOutput=True)

        # open new generated pdf file
        combinedPDF = os.path.join(tempdir, "%s.pdf" %texfile)
        pdfIn = PdfFileReader(open(combinedPDF, "r"))

        # iterate over the number of figures to spit and crop the pdf
        for page, figure in enumerate(self._figures):
            # output path
            splitPDF = os.path.join(tempdir, "%s.a4.pdf" %figure)
            cropPDF = os.path.join(tempdir, "%s.crop.pdf" %figure)

            # spit pdf into multiple pdf files
            info("Write PDF file %s..." %figure)
            pdfOut = PdfFileWriter()
            pdfOut.addPage(pdfIn.getPage(page))

            filestream = open(splitPDF, "w")
            pdfOut.write(filestream)
            filestream.close()

            # crop pdf
            info("Run pdfcrop on %s..." %figure)
            cmd = "pdfcrop %s %s" %(splitPDF, cropPDF)
            if self._debug:
                call(cmd)
            else:
                call(cmd, noOutput = True)

            # copy cropped pdfs to final destination
            pdfDst = os.path.join(destdir, "%s.pdf" %figure)
            if not self._force and os.path.exists(pdfDst):
                error("%s already exists. Skipped." %pdfDst)
            else:
                shutil.copy(cropPDF, pdfDst)

