import optparse,logging
from logging import info, debug, warn, error

class Application(object):
	"Framework for mcg-mesh applications"

	# public attribute
	parser = optparse.OptionParser()

	
	# initialization
	def __init__(self):

		# standard options valid vor all scripts
		self.parser.add_option('-s', '--syslog',
							   action = 'store_true', dest = 'syslog',
							   help = 'log to syslog instead of stdout')
		self.parser.add_option('-v', '--verbose',
							   action = 'store_true', dest = 'verbose',
							   help = 'being more verbose')

	# parse options
	def start(self):
		(options, args) = self.parser.parse_args()

		# init logging stuff
		
		# being verbose?
		if options.verbose:
			log_level = logging.INFO
		else:
			log_level = logging.WARN
	
		# using syslog?
		if options.syslog:
			syslog_facility = logging.handlers.SysLogHandler.LOG_DAEMON
			syslog_host = ('logserver', 514)
			syslog_format = parser.get_prog_name() + ' %(levelname)s: %(message)s'
			syslog_Handler = logging.handlers.SysLogHandler(address = syslog_host,
															facility = syslog_facility)
			syslog_Handler.setFormatter(logging.Formatter(syslog_format))
			logging.getLogger('').addHandler(syslog_Handler)
			logging.getLogger('').setLevel(log_level)
					
		# using standard logger
		else:
			log_format = '%(asctime)s %(levelname)s: %(message)s'
			log_datefmt = '%b %d %H:%M:%S'
			logging.basicConfig(level = log_level, format = log_format,
								datefmt = log_datefmt)

		self.init(options,args)
		self.run()
