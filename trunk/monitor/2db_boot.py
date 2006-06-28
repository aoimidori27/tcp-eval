#!/usr/bin/python
import pyPgSQL, os, socket
from pyPgSQL import PgSQL

uptime 	= os.popen('cut -f1 -d" " /proc/uptime').read()
node_id = os.popen('echo -n ${HOSTNAME/mrouter/}').read()

dbcon = PgSQL.connect()
dbcon.autocommit = True
cursor = dbcon.cursor()
cursor.execute("INSERT INTO node.boot (node_id,uptime) VALUES (node.id_by_hostname('%s'),interval '1 second'*(%s::int))" % (socket.gethostname(),uptime))
cursor.close()
dbcon.close()
