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
import logging

# twisted imports
from twisted.web import xmlrpc

class RPCService(xmlrpc.XMLRPC):
    """Base class for services"""

    def __init__(self, parent = None):
        xmlrpc.XMLRPC.__init__(self)

        self._name = None
        self._parent = parent

    # to make logging more meaningful use own logging methods!
    def info(self, msg, *args, **kwargs):
        logging.info("%s:%s" %(self._name, msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        logging.debug("%s:%s" %(self._name, msg), *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        logging.warn("%s:%s" %(self._name, msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        logging.error("%s:%s" %(self._name, msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        logging.critical("%s:%s" %(self._name, msg), *args, **kwargs)

    def stderror(self, multiline_msg):
        """Prints a multiline error message with indentation"""

        for line in multiline_msg.splitlines():
            self.error(" %s" %line)
