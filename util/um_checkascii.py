#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python import
import sys
import codecs

# umic-mesh import
from um_application import Application

class CheckASCII(Application):
    """Class to check whether there are non ASCII characters in a file"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        usage = "usage: %prog <file>"
        self.parser.set_usage(usage)

    def set_option(self):
        """Set options"""

        Application.set_option(self);

        # correct numbers of arguments?
        if len(self.args) == 0:
            print "Give a filename."
            sys.exit()

    def main(self):
        self.parse_option()
        self.set_option()

        # initialize ascii decoder
        codec = codecs.getdecoder("ascii")
        infile = file(sys.argv[1], 'r',0)

        # loop over all lines in the file
        line = 1
        rline = infile.readline()
        while (rline):
            try:
                codec(rline)    # if it fails there are non ascii characters in the line
            except Exception, e:
                pos = str(e).split()[8].split(":")[0]   # get the position out of the error message
                print "Non ASCII in line %s pos %s" %(line, int(pos)+1)
            line += 1
            rline = infile.readline()


if __name__ == '__main__':
    CheckASCII().main()
