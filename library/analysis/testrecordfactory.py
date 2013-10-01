#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2007 - 2011 Arnd Hannemann <arnd@arndnet.de>
# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
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
from logging import info, debug, warn, error

# tcp-eval imports
from testrecords_ping import PingRecordFactory
from testrecords_fping import FpingRecordFactory
from testrecords_flowgrind import FlowgrindRecordFactory
from testrecords_rate import RateRecordFactory

class TestRecordFactory:
    """A factory for test records."""

    def __init__(self):
        self.factories = dict()

    def initFactory(self, test):
        debug("Initializing test record factory for %s..." %test)

        if test=="ping":
            factory = PingRecordFactory()
        elif test=="fping":
            factory = FpingRecordFactory()
        elif test=="flowgrind" or test=="multiflowgrind":
            factory = FlowgrindRecordFactory()
        elif test=="rate":
            factory = RateRecordFactory()
        else:
            error("No factory found for: %s" %test)
            return None

        self.factories[test] = factory
        return factory

    def createRecord(self, filename, test):
        try:
            createRecord = self.factories[test].createRecord
        except KeyError:
            createRecord = self.initFactory(test).createRecord
        return createRecord(filename, test)

