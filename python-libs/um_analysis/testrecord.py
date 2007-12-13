#!/usr/bin/envpython
# -*- coding: utf-8 -*-

# python imports
import sys
import os
import os.path
import subprocess
import re
import time
import signal
import socket
from logging import info, debug, warn, error

from numpy import array
import traceback


class TestRecord:
    """
    A record of a single Test.
    For performance reasons it expects already compiled regexes and
    an initialize dict with function pointers to calculate results,
    from parsed values
    """

    def __init__(self, filename, regexes, whats):
        self.results = dict()
        self.regexes = regexes
        self.filename = filename
        self.whats = whats
        self.valid = True
        self.header = dict()
        self.parse()

    def parse(self):
        """ Parses the file associated with this record """

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

        for regex in self.regexes:
            matches = regex.finditer(output)

            for match in matches:
                for key, value in match.groupdict().iteritems():
                    if not self.results.has_key(key):
                        self.results[key] = []
                    self.results[key].append(value)

        fh.close()

    def getHeader(self):
        """ returns the header as a dictionary """
        return self.header
        
    def calculate(self, what):
        """
        
        Calculate the given value from parsed values.
        If calculation failes, this record is marked invalid, and None is returned.
        
        """
        
        if not self.valid:
            return None
           
        try:
            return self.whats[what](self.results);
        except KeyError:
            warn("Failed get %s out of %s" %(what, self.filename))
            self.valid = False
            return None

    def isValid(self):
        return self.valid

