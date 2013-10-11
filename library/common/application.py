#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2009 - 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
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
import logging.handlers
import argparse

class Application(object):
    """Framework for generic Applications"""

    def __init__(self, prog=None, usage=None, description=None, epilog=None, **kwargs):
        """Constructor for generic Application object"""

        # object variables
        self.parser = argparse.ArgumentParser(prog=prog, usage=usage,
                description=description, epilog=epilog, **kwargs)
        self._log_group = self.parser.add_mutually_exclusive_group()

        # initialization of the argument parser
        self._log_group.add_argument("-q", "--quiet", action = "store_false",
                default=False, help="being more quiet")
        self._log_group.add_argument("-v", "--verbose", action="store_true",
                default=False, help="being more verbose")
        self._log_group.add_argument("--debug", action="store_true",
                default=False, help="being even more verbose")
        self.parser.add_argument("--syslog", metavar="HOST", action="store",
                nargs="?", const="localhost", help="log to syslog server "\
                        "'%(metavar)s' (default: %(const)s)")

    def parse_options(self, args=None):
        """Parse options for generic Application object"""

        # parse options
        self.args = self.parser.parse_args(args)

    def apply_options(self):
        """Configure generic Application object based on the options from
        the argparser"""

        # setting log level
        if self.args.debug:
            log_level = logging.DEBUG
        elif self.args.verbose:
            log_level = logging.INFO
        elif self.args.quiet:
            log_level = logging.ERROR
        else:
            log_level = logging.WARNING

        # using syslog
        if self.args.syslog:
            syslog_host = (self.args.syslog, 514)
            syslog_facility = logging.handlers.SysLogHandler.LOG_DAEMON
            syslog_format = "%(prog)s [%(levelname)s]: %(message)s"
            syslog_Handler = logging.handlers.SysLogHandler(syslog_host,
                    syslog_facility)
            syslog_Handler.setFormatter(logging.Formatter(syslog_format))
            logging.getLogger("").addHandler(syslog_Handler)
            logging.getLogger("").setLevel(log_level)
        # using standard logger
        else:
            log_format = "%(asctime)s %(levelname)s: %(message)s"
            log_datefmt = "%b %d %H:%M:%S"
            logging.basicConfig(level=log_level, format=log_format,
                    datefmt=log_datefmt)

