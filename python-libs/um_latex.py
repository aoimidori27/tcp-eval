#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os.path
import tempfile
import shutil
from pyPdf import PdfFileWriter, PdfFileReader
from logging import info, debug, warn, error

# umic-mesh imports
from um_functions import execute, call


class UmLatex():

    def __init__(self, filename = None, outdir = None, defaultPackages = True, 
                 defaultSettings = True, siunitx = True, tikz = True):
        # tex filename and figures named (for building output files)
        self._filename = None
        self._outdir = None
        self._figures = list()
        self.__setFilename(filename)
        self.__setOutdir(outdir)
               
        # verbose/debug/force mode
        self._verbose = False
        self._debug = False
        self._force = False
        
        # latex content     
        self._documentclass = ''
        self._packages = list()
        self._settings = list()
        self._content = list()
        
        # load default values for the latex document (class/packages/settings)
        self.__loadDefaults(defaultPackages, defaultSettings, siunitx, tikz)

    def __loadDefaults(self, defaultPackages = True, defaultSettings = True,
                       siunitx = True, tikz = True):
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
            self.addSetting(r"\newcommand*{\Implies}{\ensuremath{\rightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\IFF}{\ensuremath{\leftrightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\IF}{\ensuremath{\Rightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\SRA}{\ensuremath{\shortrightarrow}\xspace}")
            self.addSetting(r"\newcommand*{\SLA}{\ensuremath{\shortleftarrow}\xspace}")

        # load siunitx
        if siunitx:
            self.addPackage("siunitx", "alsoload=accepted", "alsoload=binary")
            self.addSetting(r"\sisetup{per=fraction,fraction=nice,seperr}")
            self.addSetting(r"\newunit{\mps}{\meter\per\second}")
            self.addSetting(r"\newunit{\kmps}{\km\per\second}")
            self.addSetting(r"\renewunit{\bit}{b}")
            self.addSetting(r"\newunit{\Bit}{bit}")
            self.addSetting(r"\newunit{\kb}{\kilo\bit}")
            self.addSetting(r"\newunit{\Mb}{\mega\bit}")
            self.addSetting(r"\newunit{\Gb}{\giga\bit}")
            self.addSetting(r"\newunit{\Byte}{byte}")
            self.addSetting(r"\newunit{\kB}{\kilo\byte}")
            self.addSetting(r"\newunit{\MB}{\mega\byte}")
            self.addSetting(r"\newunit{\GB}{\giga\byte}")
            self.addSetting(r"\newunit{\kbps}{\kb\per\second}")
            self.addSetting(r"\newunit{\Mbps}{\Mb\per\second}")
            self.addSetting(r"\newunit{\Gbps}{\Gb\per\second}")
        
        # load tikz
        if tikz:
            self.addPackage("tikz")
            self.addSetting(r"\usetikzlibrary{backgrounds,arrows,calc}")


    def __getFilename(self, filename = None):
        if filename == None:
            return self._filename
        else:
            return filename

    def __setFilename(self, filename = None):
        if filename == None:
            self._filename = "main"
        else:
            self._filename = filename
            
    def __getOutdir(self, outdir = None):
        if outdir == None:
            return self._outdir
        else:
            return outdir

    def __setOutdir(self, outdir = None):
        if outdir == None:
            self._outdir = os.getcwd()
        else:
            self._outdir = outdir

    def __buildDocument(self):
        packages = "\n".join(self._packages)
        settings = "\n".join(self._settings)
        content  = "\n".join(self._content)
        document = "%s\n%s\n%s\n\\begin{document}\n%s\n\\end{document}"\
            %(self._documentclass , packages, settings, content)  
        
        return document

    def setVerbose(self):
        self._verbose = True
        
    def setDebug(self):
        self._debug = True
        
    def setForce(self):
        self._force = True
        
    def setDocumentclass(self, documentclass, *options):
        if options:
            options = ", ".join(options)
            self._documentclass = "\\documentclass[%s]{%s}" %(options, documentclass)
        else:
            self._documentclass = "\\documentclass{%s}" %documentclass

    def addPackage(self, package, *options):    
        if options:
            options = ", ".join(options)
            command = "\\usepackage[%s]{%s}" %(options, package) 
        else:
            command = "\\usepackage{%s}" %package

        self._packages.append(command)
            
    def addSetting(self, command):
        self._settings.append(command)
        
    def addContent(self, content):
        self._content.append(content)
    
    def addLatexFigure(self, latexfile, name = None):
        if not name:
            # get basename
            name = os.path.basename(latexfile)
            # and we want the name without extension
            name = os.path.splitext(name)[0] 
            
        figure = r"""
            \begin{figure}
            \centering
            \input{%s}
            \end{figure}
            \clearpage""" %latexfile

        self._figures.append(name)
        self.addContent(figure)

    def save(self, filename = None, outdir = None):
        # build document
        if self._verbose:
            info("Bulding LaTeX document...")
        document = self.__buildDocument()
    
        # build output path
        filename = self.__getFilename(filename)
        finaldir = self.__getOutdir(outdir)
        texfile = os.path.join(finaldir, "%s.tex" %filename)
       
        if not self._force and os.path.exists(texfile):
            error("%s already exists. Skipped." %texfile)
            return
            
        # write content
        if self._verbose:
            info("Write LaTeX document to %s..." %texfile)
        latex = open(texfile, "w")
        latex.write(document)
        latex.close()

    def toPdf(self, filename = None, outdir = None):
        # building document
        if self._verbose:
            info("Bulding LaTeX document...")
        document = self.__buildDocument()

        # build output path
        filename = self.__getFilename(filename)
        finaldir = self.__getOutdir(outdir)
        tempdir = tempfile.mkdtemp()
              
        # run pdflatex
        cmd = "pdflatex -jobname %s -output-directory %s" %(filename, tempdir)
        if self._verbose:
            info("Run pdflatex on %s..." %filename)
        
        if self._debug:
            call(cmd, input = document)
        else:
            call(cmd, input = document, noOutput = True)

        # open new generated pdf file
        combinedPDF = os.path.join(tempdir, "%s.pdf" %filename)
        pdfIn = PdfFileReader(open(combinedPDF, "r"))
 
        # iterate over the number of figures to spit and crop the pdf
        for page, figname in enumerate(self._figures):
            # output path
            splitPDF = os.path.join(tempdir, "%s.a4.pdf" %figname)
            cropPDF = os.path.join(tempdir, "%s.crop.pdf" %figname)
        
            # spit pdf into multiple pdf files
            if self._verbose:
                info("Write PDF file %s..." %figname) 
            pdfOut = PdfFileWriter()
            pdfOut.addPage(pdfIn.getPage(page))
                       
            filestream = open(splitPDF, "w")
            pdfOut.write(filestream)
            filestream.close()
  
            # crop pdf  
            cmd = "pdfcrop %s %s" %(splitPDF, cropPDF)
            if self._verbose:
                info("Run pdfcrop on %s..." %figname)
                        
            if self._debug:
                call(cmd)
            else:
                call(cmd, noOutput = True)
            
            # copy croped pdfs to final destination
            finalPDF = os.path.join(finaldir, "%s.pdf" %figname)
            if not self._force and os.path.exists(finalPDF):
                error("%s already exists. Skipped." %finalPDF)
            else:
                shutil.copy(cropPDF, finalPDF)
                
        #clean up
        shutil.rmtree(tempdir)
        