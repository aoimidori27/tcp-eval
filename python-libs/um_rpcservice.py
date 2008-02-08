#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import logging

# twisted imports
from twisted.web import xmlrpc

    
class RPCService(xmlrpc.XMLRPC):
    """ Base class for services """


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
        """ Prints a multiline error message with indentation """
        
        for line in multiline_msg.splitlines():
            self.error(" %s" %line)
