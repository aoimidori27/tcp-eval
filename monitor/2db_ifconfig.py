#!/usr/bin/python

# imports
import os, logging, logging.handlers, sre, socket, sys, optparse, time
from logging import info, debug, warn, error
from pyPgSQL import PgSQL



# class for the database
class Database(object):
	# global variables
	db_name		  = 'mcg-mesh'
	db_table	  = 'node.ifconfig'
	db_host		  = 'meshserver'
	db_user		  = 'meshnode'
	max_con_error     = 5
	max_sql_error     = 2
	db_con_error      = 0
	db_sql_error      = 0
	db_reconnect_time = 5


	def __init__(self):
		# connecting database
		info('Connecting to the database...')
		self.dbcon = self.connect()
		self.node_id = self.get_node_id()

		# flush all old entries
		info('Flush all old entries for this node...')
		cursor = self.dbcon.cursor()
		query = "DELETE FROM %s WHERE node_id='%s';" \
				%(self.db_table, self.node_id)
		cursor = self.execute_sql(query)
		info('%s rows affected' %(cursor.rowcount))
		cursor.close()


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
			warn('Can not execute sql query.')
			warn('Probably database connection lost. Try to reconnect.')
			if self.db_error <= self.max_db_error:
				self.sql_error += 1
				self.connect()
				self.execute_sql(query)
			else:
				exctype, value = sys.exc_info()[:2]
				error('Unable to execute sql query. Exit now.')
				error('%s %s' %(exctype, value))
				sys.exit(1)


	# send changes to database
	def send(self, added_ifaces, removed_ifaces, changed_ifaces):
		# add new interfaces
		if not added_ifaces.empty():
			for iface in added_ifaces.list.itervalues():
				query = "INSERT INTO %s (node_id, iface, hwaddr, inet_addr, " \
						"inet_bcast, inet_mask) VALUES ('%s', '%s', '%s', '%s', '%s', '%s');" \
						%(self.db_table, self.node_id, iface.name, iface.hwaddr, iface.inet_addr, \
						  iface.inet_bcast, iface.inet_mask)
				self.execute_sql(query).close()

		# remove old interfaces
		if not removed_ifaces.empty():
			for iface in removed_ifaces.list.itervalues():
				query = "DELETE FROM %s WHERE node_id='%s' AND iface='%s';" \
						%(self.db_table, self.node_id, iface.name)
				self.execute_sql(query).close()

		# change modified interfaces
		if not changed_ifaces.empty():
			for iface in changed_ifaces.list.itervalues():
				query = "UPDATE %s SET hwaddr='%s', inet_addr='%s', "\
						"inet_bcast='%s', inet_mask='%s' " \
						"WHERE node_id='%s' AND iface='%s';" \
						%(self.db_table, iface.hwaddr, iface.inet_addr, \
						  iface.inet_bcast, iface.inet_mask, self.node_id, \
						  iface.name)
				self.execute_sql(query).close()
						

	# get node_id of the node running on
	def get_node_id(self):
		query = "SELECT node.id_by_hostname('%s');" %(socket.gethostname())
		cursor = self.execute_sql(query)
		node_id = str(cursor.fetchone()[0])
		cursor.close()

		return node_id



# class for a interface
class Interface(object):
	def __init__(self, name, hwaddr, inet_addr, inet_bcast, inet_mask):
		self.name = name
		self.hwaddr = hwaddr
		self.inet_addr = inet_addr
		self.inet_bcast = inet_bcast
		self.inet_mask = inet_mask


	def __eq__(self, other):
		return self.name == other.name and \
			   self.hwaddr == other.hwaddr and \
			   self.inet_addr == other.inet_addr and \
			   self.inet_bcast == other.inet_bcast and \
			   self.inet_mask == other.inet_mask


	def __str__(self):
		return 'Iface:%s HWaddr:%s Inet addr:%s Bcast:%s Mask:%s' \
			   %(self.name, self.hwaddr, self.inet_addr, self.inet_bcast,
			     self.inet_mask)



# class for a list of interfaces
class InterfaceList(object):
	def __init__(self):
		self.list = {}


	def copy(self, other):
		self.list = other.list.copy()


	def empty(self):
		return len(self.list) == 0


	def __str__(self):
		slist = [('(%s) ' %(iface)) for iface in self.list.itervalues()]
		return "".join(slist)
	
		
	# compare to interface lists
	def compare(self, other):
		removed_ifaces = InterfaceList()
		changed_ifaces = InterfaceList()
		for iface_self in self.list.itervalues():
			# search the iface name in the other interface list
			iface_other = other.list.get(iface_self.name)
			
			# the iface does not exist
			if type(iface_other) == type(None):
				removed_ifaces.list[iface_self.name] = iface_self

			# the iface exists, but the values have changed
			elif not iface_other == iface_self:
				changed_ifaces.list[iface_self.name] = iface_self

		return (removed_ifaces, changed_ifaces)

	
	# create a new interface list with the ifconfig's output
	@staticmethod	
	def get_ifconfig():
		# command
		command = 'export LANG=C; ifconfig'
		
		# regular expression
		device_ReExpr = sre.compile("^(\w+)"
									".* HWaddr ([\w:]+).*\n"
									".* inet addr:([\d\.]+)"
									".* Bcast:([\d\.]+)"
									".* Mask:([\d\.]+).*\n"
									, sre.MULTILINE)
		# get ifconfig
		program = os.popen(command)
		output = program.read()

		# parse ifconfig
		result = device_ReExpr.finditer(output)

		# create a new interface list
		ifaces = InterfaceList()

		# for each interface
		for match in result:
			# create a new interface
			iface = Interface(match.group(1), match.group(2), match.group(3),
							  match.group(4), match.group(5))
			
			# insert interface in the list
			ifaces.list[iface.name] = iface

		return ifaces



# main function
def main():
	# options parser
	usage = 'usage: %prog [options] arg'
	parser = optparse.OptionParser(usage)
	parser.add_option('-t', '--time',
					  action = 'store', type = 'float', dest = 'time',
					  default = 120,
					  help = 'parse ifconfig every TIME seconds')
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

	# create interface list object and send the results to the database
	info('Create interface list object...')
	ifaces = InterfaceList.get_ifconfig()
	database.send(ifaces, InterfaceList(), InterfaceList())

	info('Entering endless loop...')
	try:
		while True:
			# get new ifconfig's output and compare it with the old one
			new_ifaces = InterfaceList.get_ifconfig()
			(removed_ifaces, changed_ifaces) = ifaces.compare(new_ifaces)
			(added_ifaces, changed_ifaces) = new_ifaces.compare(ifaces)

			# something change?
			if not added_ifaces.empty() or not removed_ifaces.empty() \
			   or not changed_ifaces.empty():

				# send changes to database
				if not added_ifaces.empty():
					info('Ifconfig changed. Added ifaces: %s' %(added_ifaces))
				if not removed_ifaces.empty():
					info('Ifcondig changed. Removed ifaces: %s' %(removed_ifaces))
				if not changed_ifaces.empty():
					info('Ifconfig changed. Changed ifaces: %s' %(changed_ifaces))
				database.send(added_ifaces, removed_ifaces, changed_ifaces)

			# update interface list
			ifaces = new_ifaces

			# sleep for a while
			time.sleep(options.time)

	except KeyboardInterrupt:
		info('Aborted...')
	


if __name__ == '__main__':
	main()

