#!/usr/bin/envpython
# -*- coding: utf-8 -*-

# python imports
from logging import info, debug, warn, error

class TestRecord:
    """A record of a single Test.
       For performance reasons it expects already compiled regexes and
       an initialize dict with function pointers to calculate results,
       from parsed values.
    """

    def __init__(self, filename, regexes, whats):
        self.results = dict()
        self.filename = filename
        self.whats = whats
        self.valid = True
        self.header = dict()

        self.parse(regexes)

    def parse(self, regexes):
        """Parses the file associated with this record."""

        fh = open(self.filename, "r")

        # read header
        while 1:
            line = fh.readline()
            line = line.strip()
            if line.startswith("BEGIN_TEST_OUTPUT"):
                break
            try:
                (key, value) = line.split("=",1)
                self.header[key] = value
            except ValueError:
                warn("%s: Error parsing Header! No Header??" % self.filename)
                fh.seek(0)
                break

        # read the rest
        output = fh.read()

        for regex in regexes:
            matches = regex.finditer(output)

            for match in matches:
                for key, value in match.groupdict().iteritems():
                    try:
                        self.results[key].append(value)
                    except KeyError:
                        self.results[key] = [value]

        fh.close()

    def getHeader(self):
        """Returns the header as a dictionary. """
        return self.header

    def calculate(self, what, optional = False, **kwargs):
        """Calculate the given value from parsed values.
           If calculation failes, this record is marked invalid, and None is returned.
        """

        if not self.valid:
            return None

        try:
            return self.whats[what](self.results, **kwargs);
        except KeyError, inst:
            if not optional:
                warn("Failed to get required value %s out of %s: KeyError:%s" %(what, self.filename, inst))
                self.valid = False
            else:
                info("Failed to get optional value %s out of %s: KeyError:%s" %(what, self.filename, inst))
            return None

    def isValid(self):
        return self.valid

