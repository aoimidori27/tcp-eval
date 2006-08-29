#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import optparse, logging, logging.handlers
from logging import info, debug, warning, error


class Application(object):
	"Framework for MCG-Mesh applications"
	

	def __init__(self):
		"Constructor of the object"
	
		# object variables
		self.parser = optparse.OptionParser()	
	
		# initialization of the option parser
		usage = "usage: %prog [options]"
		self.parser.set_usage(usage)
		self.parser.add_option("-s", "--syslog",
							   action = "store_true", dest = "syslog",
							   help = "log to syslog [default: %default]")
		self.parser.add_option("-v", "--verbose",
							   action = "store_true", dest = "verbose",
							   help = "being more verbose [default: %default]")


	def parse_option(self):
		"Parse options"
	
		# parse options
		(self.options, self.args) = self.parser.parse_args()


	def set_option(self):
		"Set options"
		
		# being verbose?
		if self.options.verbose:
			log_level = logging.INFO
		else:
			log_level = logging.WARNING
	
		# using syslog?
		if self.options.syslog:
			syslog_host = ("logserver", 514)
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