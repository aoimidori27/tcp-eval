#!/usr/bin/python
import pyPgSQL, os, socket
from pyPgSQL import PgSQL

dbcon = PgSQL.connect()
dbcon.autocommit = True
cursor = dbcon.cursor()
cursor.execute(
	"""INSERT INTO node.boot (node_id,uptime) VALUES 
		(node.id_by_hostname('%s'),interval '1 second'*%s)
		""" % (socket.gethostname(),open("/proc/uptime").readline().split(".")[0]))
cursor.close()
dbcon.close()
