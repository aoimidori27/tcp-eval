#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
import os.path
import sys
import codecs
import re
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application



class Btex2utf8(Application):
    "Class to convert bibtex special symbols to utf8"


    def __init__(self):
        "Constructor of the object"

        Application.__init__(self);
        
        # object variables
        self.bibtex2unicode_map = { # latin-1 characters upper case
                       r'\\`A'   : u'\u00C0', # capital A with grave accent 
                       r"\\'A"   : u'\u00C1', # capital A with acute accent
                       r'\\^A'   : u'\u00C2', # capital A with circumflex accent
                       r'\\~A'   : u'\u00C3', # capital A with tilde
                       r'\\"A'   : u'\u00C4', # capital A with diaresis
                       r'\\AA'   : u'\u00C5', # capital A with ring above
                       r'\\AE'   : u'\u00C6', # capital diphthong A with E
                       r'\\c{C}' : u'\u00C7', # capital C with cedilla
                       r'\\`E'   : u'\u00C8', # capital E with grave accent 
                       r"\\'E"   : u'\u00C9', # capital E with acute accent
                       r'\\^E'   : u'\u00CA', # capital E with circumflex accent
                       r'\\"E'   : u'\u00CB', # capital E with diaresis
                       r'\\`I'   : u'\u00CC', # capital I with grave accent 
                       r"\\'I"   : u'\u00CD', # capital I with acute accent
                       r'\\^I'   : u'\u00CE', # capital I with circumflex accent
                       r'\\"I'   : u'\u00CF', # capital I with diaresis
                       r'\\~N'   : u'\u00D1', # capital N with tilde 
                       r'\\`O'   : u'\u00D2', # capital O with grave accent 
                       r"\\'O"   : u'\u00D3', # capital O with acute accent
                       r'\\^O'   : u'\u00D4', # capital O with circumflex accent
                       r'\\~O'   : u'\u00D5', # capital O with tilde
                       r'\\"O'   : u'\u00D6', # capital O with diaresis
                       r'\\O'    : u'\u00D8', # capital O with oblique stroke
                       r'\\`U'   : u'\u00D9', # capital U with grave accent
                       r"\\'U"   : u'\u00DA', # capital U with acute accent
                       r'\\^U'   : u'\u00DB', # capital U with circumflex accent
                       r'\\"U'   : u'\u00DC', # capital U with diaresis
                       r"\\'Y"   : u'\u00DD', # capital Y with acute accent

                       # latin-1 characters lower case
                       r'\\ss'   : u'\u00DF', # small german sharp s 
                       r'\\`a'   : u'\u00E0', # small a with grave accent 
                       r"\\'a"   : u'\u00E1', # small a with acute accent
                       r'\\^a'   : u'\u00E2', # small a with circumflex accent
                       r'\\~a'   : u'\u00E3', # small a with tilde
                       r'\\"a'   : u'\u00E4', # small a with diaresis
                       r'\\aa'   : u'\u00E5', # small a with ring above
                       r'\\ae'   : u'\u00E6', # small diphthong a with e
                       r'\\c{c}' : u'\u00E7', # small c with cedilla 
                       r'\\`e'   : u'\u00E8', # small e with grave accent
                       r"\\'e"   : u'\u00E9', # small e with acute accent
                       r'\\^e'   : u'\u00EA', # small e with circumflex accent
                       r'\\"e'   : u'\u00EB', # small e with diaresis
                       r'\\`i'   : u'\u00EC', # small i with grave accent
                       r"\\'i"   : u'\u00ED', # small i with acute accent
                       r'\\^i'   : u'\u00EE', # small i with circumflex accent
                       r'\\"i'   : u'\u00EF', # small i with diaresis
                       r'\\~n'   : u'\u00F1', # small n with tilde 
                       r'\\`o'   : u'\u00F2', # small o with grave accent 
                       r"\\'o"   : u'\u00F3', # small o with acute accent
                       r'\\^o'   : u'\u00F4', # small o with circumflex accent
                       r'\\~o'   : u'\u00F5', # small o with tilde
                       r'\\"o'   : u'\u00F6', # small o with diaresis
                       r'\\o'    : u'\u00F8', # small o with oblique stroke
                       r'\\`u'   : u'\u00F9', # small u with grave accent
                       r"\\'u"   : u'\u00FA', # small u with acute accent
                       r'\\^u'   : u'\u00FB', # small u with circumflex accent
                       r'\\"u'   : u'\u00FC', # small u with diaresis
                       r"\\'y"   : u'\u00FD', # small y with acute accent
                       r'\\"y'   : u'\u00FF', # small y with diaresis
     
                       # latin Extended-A
                       r'\\OE'   : u'\u0152', # capital dipthong o with e
                       r'\\oe'   : u'\u0153', # small dipthong o with e
                       r'\\c{S}' : u'\u015E', # capital S with cedilla 
                       r'\\c{s}' : u'\u015F', # small s with cedilla 
     
                       # special symbols 
                       r'\\\\'   : u'\\', # backslash
                       r'\\{'    : u'{',  # left brace
                       r'\\}'    : u'}',  # right brace         
                         
                       # eat non-escaped braces
                       r'{'      : u'',
                       r'}'      : u'',
                     }


        # initialization of the option parser
        usage = "usage: %prog [options] [inputfile]\n" \
                "if no inputfile is given stdin is used"
        self.parser.set_usage(usage)
        self.parser.set_defaults(outfile = None, encoding = "UTF-8")

        self.parser.add_option("-o", "--outfile", metavar="OUT",
                               action = "store", dest = "outfile",
                               help = "use this as the output file [default: stdout]")
        self.parser.add_option("-e", "--encoding", metavar="ENC",
                               action = "store", dest = "encoding",
                               help = "use this as the output encoding [default: %default]")

    def set_option(self):
        "Set options"

        Application.set_option(self);

        # correct numbers of arguments?
        if len(self.args) > 1:
            self.parser.error("Incorrect number of arguments")
       
        # use stdin as input? 
        if len(self.args) == 0:
            self.infile = sys.stdin
        else:
            self.infile = self.args[0]

            # does the input file exists
            if not os.path.exists(self.infile):
                self.parser.error('Inputfile %s does not exist.' %self.infile)
    
            # is it an directory?
            if os.path.isdir(self.infile):
                self.parser.error('Inputfile %s is a directory.' %self.infile)
 
            # open it
            self.infile = file(self.infile,'r')
  
        # use stdout as output?
        if not self.options.outfile:
            self.outfile = sys.stdout
        else:
            self.outfile = file(self.outfile,'w')


    def main(self):
        "Main method of application object"


        self.parse_option()
        self.set_option()
    
        (e,d,sr,sw) = codecs.lookup(self.options.encoding)
        outstream = sw(self.outfile)

        # build up re
        regexes = list()
        for (key, value) in self.bibtex2unicode_map.iteritems():
            regexes.append(r"(%s)" % re.escape(key))
        regex = "|".join(regexes)
    
        for inline in self.infile.xreadlines():
            inline = inline.replace('\\', '\\\\')
            last = 0 
            for match in re.finditer(regex, inline):
                outstream.write(inline[last:match.start()])
                last = match.end()
                for group in match.groups():
                    if group:
                        outstream.write(self.bibtex2unicode_map[group])
                        break;
            outstream.write(inline[last:])
        outstream.flush() 

if __name__ == '__main__':
    Btex2utf8().main()
