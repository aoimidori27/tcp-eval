#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import optparse
import logging
import logging.handlers


class Application(object):
    """Framework for UMIC-Mesh applications"""


    def __init__(self):
        """Constructor of the generic Application object"""
        
        # object variables
        self.parser = optparse.OptionParser()

        # initialization of the option parser
        usage = "usage: %prog [options]"
        self.parser.set_usage(usage)
        self.parser.set_defaults(syslog = False, server = "logserver",
                                 verbose = True, debug = False)
        
        self.parser.add_option("--syslog",
                action = "store_true", dest = "syslog",
                help = "log to syslog")
        self.parser.add_option("--syslog-server", type="string", metavar = "HOST",
                action = "callback", callback=self.check_option, dest = "server",
                help = "sends log to a specific server [default: %default]")                               
        self.parser.add_option("-v", "--verbose",
                action = "store_true", dest = "verbose",
                help = "being more verbose [default]")
        self.parser.add_option("-q", "--quiet",
                action = "store_false", dest = "verbose",
                help = "being more quiet")
        self.parser.add_option("--debug",
                action = "store_true", dest = "debug",
                help = "being even more verbose")


    def check_option(self, option, opt_str, value, parser):
        """Check the options for generic Application object"""

        # if this option is set, the "--syslog" option is also enabled
        if opt_str == "--syslog-server":
            parser.values.syslog = True
        

    def parse_option(self, args = None):
        """Parse the options for generic Application object"""

        # parse options
        (self.options, self.args) = self.parser.parse_args(args)


    def set_option(self):
        """Set the options for generic Application object"""

        # being verbose?
        if self.options.debug:
            log_level = logging.DEBUG
        elif self.options.verbose:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING

        # using syslog?
        if self.options.syslog:
            syslog_host = (self.options.server, 514)
            syslog_facility = logging.handlers.SysLogHandler.LOG_DAEMON
            syslog_format = self.parser.get_prog_name() + \
                            "%(levelname)s: %(message)s"
            syslog_Handler = logging.handlers.SysLogHandler(
                                syslog_host, syslog_facility)
            syslog_Handler.setFormatter(logging.Formatter(syslog_format))
            logging.getLogger("").addHandler(syslog_Handler)
            logging.getLogger("").setLevel(log_level)

        # using standard logger
        else:
            log_format = "%(asctime)s %(levelname)s: %(message)s"
            log_datefmt = "%b %d %H:%M:%S"
            logging.basicConfig(level = log_level, format = log_format,
                                datefmt = log_datefmt)
