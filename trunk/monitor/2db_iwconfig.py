#!/usr/bin/python

# imports
import os, logging, logging.handlers, sre, socket, sys, optparse, time
from logging import info, debug, warn, error
from pyPgSQL import PgSQL



# class for the database
class Database(object):
	# global variables
	db_name       = 'mcg-mesh'
	db_table      = 'node.iwconfig'
	db_host       = 'meshserver'
	db_user       = 'meshnode'
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
			dbcon = PgSQL.connect(user = self.db_user, host = self.db_host,
								  database = self.db_name)
			dbcon.autocommit = True
			self.con_error = 0
			
			return dbcon

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
			if self.db_error <= self.max_db_error:
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
	def send(self, added_ifaces, removed_ifaces, changed_ifaces):
		# add new interfaces
		if not added_ifaces.empty():
			for iface in added_ifaces.list.itervalues():
				if iface.iw_cell == 'Not-Associated':
					iw_cell = 'NULL';
				else:
					iw_cell = "'%s'" %(iface.iw_cell)
				
				query = "INSERT INTO %s (node_id, iface, iw_essid, iw_mode, " \
						"iw_freq, iw_cell, iw_txpower) VALUES " \
						"('%s', '%s', '%s', '%s', '%s', %s, '%s');" \
						%(self.db_table, self.node_id, iface.name, \
						  iface.iw_essid, iface.iw_mode, iface.iw_freq, \
						  iw_cell, iface.iw_txpower)
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
				if iface.iw_cell == 'Not-Associated':
					update_cell = 'iw_cell IS NULL';
				else:
					update_cell = "iw_cell='%s'" %(iface.iw_cell)
				
				query = "UPDATE %s SET iw_essid='%s', iw_mode='%s', "\
						"iw_freq='%s', %s, iw_txpower='%s' " \
						"WHERE node_id='%s' AND iface='%s';" \
						%(self.db_table, iface.iw_essid, iface.iw_mode, \
						  iface.iw_freq, update_cell, iface.iw_txpower, \
						  self.node_id, iface.name)
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
	def __init__(self, name, iw_essid, iw_mode, iw_freq, iw_cell, iw_txpower):
		self.name = name
		self.iw_essid = iw_essid
		self.iw_mode = iw_mode
		self.iw_freq = iw_freq
		self.iw_cell = iw_cell
		self.iw_txpower = iw_txpower


	def __eq__(self, other):
		return self.name == other.name and \
			   self.iw_essid == other.iw_essid and \
			   self.iw_mode == other.iw_mode and \
			   self.iw_freq == other.iw_freq and \
			   self.iw_cell == other.iw_cell and \
			   self.iw_txpower == other.iw_txpower


	def __str__(self):
		return 'Iface:%s Essid:%s Mode:%s Freq:%s Cell:%s TxPower:%s' \
			   %(self.name, self.iw_essid, self.iw_mode, self.iw_freq, \
			     self.iw_cell, self.iw_txpower)


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


	# create a new interface list with the iwconfig's output
	@staticmethod
	def get_iwconfig():
		# command
		command = 'export LANG=C; iwconfig 2>/dev/null'
				
		# regular expression
		device_ReExpr = sre.compile("^(\w+)"
									".* ESSID:\"(.+)\".*\n"
									".* Mode:([\w:\-]+)"
									".* Frequency:(\d+\.\d+)"
									".* Cell: ([\w:\-]+).*\n"
									".* Tx-Power=(\d+).*\n"
									".*\n"
									".*\n"
									".*\n"				
									".* Link Quality=(\d+)/(\d+)"
									".* Signal level=(-\d+)"
									".* Noise level=(-\d+).*\n"
									, sre.MULTILINE)
									
		# get iwconfig
		program = os.popen(command)
		output = program.read()

		# parse iwconfig
		result = device_ReExpr.finditer(output)

		# create a new interface list
		ifaces = InterfaceList()

		# for each interface
		for match in result:
			# create a new interface
			iface = Interface(match.group(1), match.group(2), match.group(3),
							  match.group(4), match.group(5), match.group(6))
			
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
					  help = 'parse iwconfig every TIME seconds')
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
	ifaces = InterfaceList.get_iwconfig()
	database.send(ifaces, InterfaceList(), InterfaceList())

	info('Entering endless loop...')
	try:
		while True:
			# get new iwconfig's output and compare it with the old one
			new_ifaces = InterfaceList.get_iwconfig()
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

