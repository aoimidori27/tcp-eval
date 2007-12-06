#!/usr/bin/envpython
# -*- coding: utf-8 -*-

# python imports
import re
from logging import info, debug, warn, error

from numpy import array

# import neccessary for the testrecord factory
# um import
from testrecords_ping import PingRecordFactory
from testrecords_fping import FpingRecordFactory
from testrecords_flowgrind import FlowgrindRecordFactory
    
class TestRecordFactory:
    """ A factory for test records. """

    def __init__(self):
        self.factories = dict()

    def initFactory(self, test):
        debug("Initializing test record factory for %s..." %test)
        if test=="ping":
            factory = PingRecordFactory()
        elif test=="fping":
            factory = FpingRecordFactory()
        elif test=="flowgrind":
            factory = FlowgrindRecordFactory()
        else:
            error("No factory found for:%s" %test)
            return None
        self.factories[test] = factory
        return factory
        

    def createRecord(self, filename, test):
        
        try:
            createRecord = self.factories[test].createRecord
        except KeyError:
            createRecord = self.initFactory(test).createRecord
        return createRecord(filename, test)


