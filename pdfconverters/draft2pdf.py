#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import optparse, sys, os, subprocess
from logging import info, debug, warn, error


class Draft2Pdf(object):
    "Class to convert internet draft text files to pdf"


    def __init__(self):
        "Constructor of the object"

        # initialization of the option parser
        usage = "usage: %prog [options] <file1> <file2> .."
        self.parser = optparse.OptionParser()
        self.parser.set_usage(usage)
        self.parser.set_defaults(force = False, textsuffix = 'txt', pdfsuffix = 'pdf')

        self.parser.add_option("-f", "--force",
                               action = "store_true", dest = "force",
                               help = "overwrite existing output pdf file")
        self.parser.add_option("--debug",
                               action = "store_true", dest = "debug",
                               help = "being even more verbose")
        self.parser.add_option("-t", "--textIn", metavar = "SUF",
                               action = "store", dest = "textsuffix",
                               help = "define suffix of input text files [default: %default]")
        self.parser.add_option("-p", "--pdfOut", metavar = "SUF",
                               action = "store", dest = "pdfsuffix",
                               help = "define suffix of output pdf file [default: %default]")


    def main(self):
        "Main method of the DraftToPdf object"

        # parse options
        (self.options, self.args) = self.parser.parse_args()

	# process every file given on command line
        for entry in self.args:
            if not os.path.isfile(entry):
                warn("%s is not a regular file. Skipped." %entry)
                continue

            pdfoutput = "%s.%s" %(os.path.splitext(os.path.basename(entry))[0],
                                  self.options.pdfsuffix)

            if not self.options.force and os.path.exists(pdfoutput):
                warn("%s already exists. Skipped." %pdfoutput)
                continue

            # convert the text file to a PDF file
            if self.options.debug:
                cmd1 = ("enscript", "-v", "-B", "-f", "Courier10",
                        "--margins=70::50:", entry, "-p", "-")
            else:
                cmd1 = ("enscript", "-q", "-B", "-f", "Courier10",
                        "--margins=70::50:", entry, "-p", "-")

            cmd2 = ("ps2pdf", "-", pdfoutput)

            enscript = subprocess.Popen(cmd1, stdout = subprocess.PIPE)
            pstopdf = subprocess.Popen(cmd2, stdin = enscript.stdout)
            (stdout, stderr) = pstopdf.communicate()



if __name__ == "__main__":
    Draft2Pdf().main()

