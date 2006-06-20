#!/usr/bin/python

# imports
import os, logging, logging.handlers, signal, sre, socket, sys, optparse, time
from logging import info, debug, warn, error
from pyPgSQL import PgSQL
from subprocess import Popen, PIPE



# class for the database
class Database(object):
    # global variables
	db_name			  = 'mcg-mesh'
	db_table		  = 'ipmonitor.rt_entry'
	db_host			  = 'meshserver'
	db_user			  = 'meshnode'
	max_con_error	  = 5
	max_sql_error	  = 2
	db_con_error	  = 0
	db_sql_error	  = 0
	db_reconnect_time = 5

							
	def __init__(self):
		# connecting database
		info('Connecting to the database...')
		self.dbcon = self.connect()
		self.node_id = self.get_node_id()

		# flush old routes
		info('Flush old routes for this node...')
		cursor = self.dbcon.cursor()
		query = "UPDATE %s SET valid_until=now() WHERE node_id='%s' " \
				"AND valid_until IS NULL;" \
				%(self.db_table, self.node_id)
		cursor = self.execute_sql(query)
		info('%s rows affected' %(cursor.rowcount))
		cursor.close()
		
		# fill routing table with new routes
		ip_route = IPRoute(('ip','-4','route'))

		while True:
			result = ip_route.parseLine()
			if result == None:
				break
			self.send(result)

		
	def __del__(self):
		self.close()


	# connect to database
	def connect(self):
		try:
			self.dbcon = PgSQL.connect(user = self.db_user, host = self.db_host,
									   database = self.db_name)
			self.dbcon.autocommit = True
			self.con_error = 0

			return self.dbcon
			
		except PgSQL.DatabaseError:
			if self.con_error <= self.max_con_error:			
				warn('Could not connect to database.')
				warn('Try it again in %s seconds.' %(self.db_reconnect_time))
				self.con_error += 1
				time.sleep(self.db_reconnect_time)
				self.connect()
			else:
				exctype, value = sys.exc_info()[:2]	
				error('Unable to connect to database. Exit now.')
				error('%s %s' %(exctype, value))
				sys.exit(1)
	
	
	# close database
	def close(self):
		self.dbcon.close()


	# execute sql query
	def execute_sql(self, query):
		try:
			cursor = self.dbcon.cursor()
			cursor.execute(query)
			info('Execute SQL: %s' %(query))
			self.sql_error = 0
			
			return cursor

		except PgSQL.OperationalError:
			if self.sql_error <= self.max_sql_error:
				warn('Can not execute sql query.')
				warn('Probably database connection lost. Try to reconnect.')
				self.sql_error += 1
				self.connect()
				self.execute_sql(query)
			else:
				exctype, value = sys.exc_info()[:2]
				error('Unable to execute sql query. Exit now.')
				error('%s %s' %(exctype, value))
				sys.exit(1)


	# send changes to database
	def send(self, route_change):
		if route_change['via'] == 'NULL':
			insert_via = 'NULL';
			update_via = 'nxthop IS NULL'
		else:
			insert_via = "'%s'" %(route_change['via'])
			update_via = "nxthop='%s'" %(route_change['via'])
				
		# add a new routing entry
		if not route_change['delete']:
			query = "INSERT INTO %s (node_id, dest, nxthop, iface) " \
					"VALUES ('%s', '%s', %s, '%s');" \
					%(self.db_table, self.node_id, route_change['dest'], \
					  insert_via, route_change['dev'])
			cursor = self.execute_sql(query)
				
		# search the existing routing entry, and invalidate it
		else:		
			query = "UPDATE %s SET valid_until=now() WHERE " \
					"node_id='%s' AND dest='%s' AND %s AND valid_until IS NULL;" \
					%(self.db_table, self.node_id, route_change['dest'], update_via)
			cursor = self.execute_sql(query)	
			
		# if there are more or less than 1 row affected, throw a warning
		if cursor.rowcount != 1:
			warn('%s rows affected by last query!' %(cursor.rowcount))
			
		cursor.close()


	# get node_id of the node running on
	def get_node_id(self):
		query = "SELECT node.id_by_hostname('%s');" %(socket.gethostname())
		cursor = self.execute_sql(query)
		node_id = str(cursor.fetchone()[0])
		cursor.close()

		return node_id



# class for the ipmonitor
class IPRoute(object):
	def __init__(self, command):
		self.program = Popen(command, stdout = PIPE, shell = False)
	

	def __del__(self):
		self.stop()
	
	
	def stop(self):
		# check if process is still running
		if self.program.poll() == None:
			info('Child still running, sending KILL signal...')
			os.kill(self.program.pid, signal.SIGTERM)

		return_code = self.program.wait()

		if return_code != 0:
			warn('Terminating unsuccessfull! Return code: %s' %(return_code))
		
		return return_code		

	
	# parse the output of ip (monitor) route
	def parseLine(self):
		invalid_line = True
		while invalid_line:
			
			lines = self.program.stdout.readline().splitlines()
			if len(lines) == 0:
				return None
		
			line = lines[0]

			# determine if the change is a "route delete" or a "route add"
			if line.startswith('Deleted'):
				route_del = True
				line = line[8:] # remove "Deleted "
			else:
				route_del = False

			# filter unwanted output
			if line.startswith('local') or line.startswith('broadcast'):
				invalid_line = True
			else:
				invalid_line = False

		# insert dest at the beginning to ease key/value separation
		line = 'dest %s' %(line);
		info('Route change detected: %s' %(line))
		
		# all informations are seperated by whitespaces
		line = line.split()
		
		# initialize associative array
		route_change = {'delete' : route_del, 'via' : 'NULL'}
		
		# interpret key / value pairs
		for j, element in enumerate(line):
			if (j + 1) % 2 == 0:
				if element == 'default': element = '0.0.0.0'
				route_change[line[j-1]] = element

		return route_change



# main function
def main():
	# options parser
	usage = 'usage: %prog [options] arg'
	parser = optparse.OptionParser(usage)
	parser.add_option('-s', '--syslog',
					  action = 'store_true', dest = 'syslog',
					  help = 'log to syslog instead of stdout')
	parser.add_option('-v', '--verbose',
					  action = 'store_true', dest = 'verbose',
					  help = 'being more verbose')
	(options, args) = parser.parse_args()

	# being verbose?
	if options.verbose:
		log_level = logging.INFO
	else:
		log_level = logging.WARN
											
	# using syslog
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

	# create database object
	info('Create database object...')
	database = Database()

	# starting ip monitor route
	info('Starting ip monitor route...')
	ip_monitor_route = IPRoute(('ip','-4','monitor','route'))

	info('Entering endless loop...')
	try:
		while True:
			# parse ip monitor route
			result = ip_monitor_route.parseLine()
			
			# send changes to database
			database.send(result)
	
	except KeyboardInterrupt:
		info('Aborted...')
		

if __name__ == '__main__':
    main()

