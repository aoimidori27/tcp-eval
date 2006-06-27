#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, optparse, subprocess
from logging import info, debug, warn, error
from pyPgSQL import PgSQL
from mmbasic import *

#
# Parse args
#

parser = optparse.OptionParser("%prog [options]")
parser.add_option("-c", "--continue", dest="continued")
parser.add_option("-r", "--retry", dest="retry")
options, args = parser.parse_args()

#
# Recovery
#

def recovery(msrmt,retries):
	info("Entering Recovery");

	if retries>3:
		error("Retried this measurement %d times, aborting" % retries);
		sys.exit(1)

	check_routing = retries==2

	cursor.execute("""
		UPDATE msrmt SET started=NULL WHERE msrmt_id=%d;
		UPDATE dbttcp SET phase=0 WHERE msrmt_id=%d;
		""" % (msrmt.msrmt_id,msrmt.msrmt_id))
	info("Measurement %d reset" % msrmt.msrmt_id);

	nodes_on = node_check_online(senders+gws)

	if len(nodes_on)<len(senders+gws):
		nodes_off = [node for node in senders+gws if node not in nodes_on]
		if nodeinfo['hostprefix']=="mrouter": waitsecs = 300
		else: waitsecs = 100

		info("Doing xen check");
		xen_check()

		info("Nodes %s are offline, waiting for %d secs" % (nodes_off,waitsecs));
		time.sleep(waitsecs);

		nodes_on = node_check_online(senders+gws)

		if len(nodes_on)!=len(senders+gws):
			nodes_off = [node for node in senders+gws if node not in nodes_on]
			error("Nodes %s are still off, aborting" % nodes_off);
			sys.exit(1);

		info("Nodes are back on. Continueing");

		check_routing = True
	
	nodes_dbttcpcd = node_check_cmd(senders,"ps -C dbttcpcd")

	if len(nodes_dbttcpcd)<senders:
		node_exec([sender for sender in senders if sender not in nodes_dbttcpcd],"cat /dev/null | dbttcpcd -b &>/dev/null");

	if check_routing: 
		nodeinfo['routing'](senders,gws,'restart')
		nodes_routing = nodeinfo['routing'](senders,gws,'check')
		if len(nodes_routing)<len(senders+gws):
			error("Routing protocol restart failed, only running on nodes %s, aborting" % nodes_routing)
			sys.exit(1)

#
# Fetch measurement
#

def fetchmsrmt():
		if not options.retry:
			# All not yet started
			where_clause = "started IS NULL" 
		else:
			# All not successful
			where_clause = "msrmt_id>=%d AND COALESCE(msrmt_result(msrmt.msrmt_id),false)=false" % retry_start

		cursor.execute("""
			BEGIN;
			SELECT msrmt_id, cons, senders, gws 
			FROM msrmt JOIN dbttcp_msrmt USING (msrmt_id) 
			WHERE node_type='%s' AND %s
			ORDER BY msrmt_id ASC
			LIMIT 1""" % (nodetype,where_clause))

		msrmt = cursor.fetchone()
		
		if not msrmt:
			info("Done!");
			cursor.execute("COMMIT");
			cursor.close()
			sys.exit(0)

		return msrmt


def msrmt_cancel(msrmt):
	cursor.execute("""
		UPDATE dbttcp SET phase=-1 WHERE msrmt_id=%d;
		UPDATE msrmt SET started=NULL WHERE msrmt_id=%d""" % (msrmt.msrmt_id,msrmt.msrmt_id))
	time.sleep(15)
	cursor.execute("UPDATE dbttcp SET phase=0 WHERE msrmt_id=%d;" % (msrmt.msrmt_id))
	info("Measurement %d canceled" % msrmt.msrmt_id)

#
# Main
#

checkperiod = 80

info("Welcome")

#info("dbttcps on %s" % node_check_cmd(nodeinfo['host'],"ps -C dbttcpcd"))

info("Measuring for "+nodeinfo['hostprefix'])

try:
	dbcon = PgSQL.connect()
	dbcon.autocommit = True

	cursor = dbcon.cursor()

	retries = 0

	msrmt = fetchmsrmt()

	while True:
		
		senders = nodeinfo['sender'][:msrmt.senders]
		gws 	= nodeinfo['gw'][:msrmt.gws]

		# Install Multipath routes
		node_exec(senders,nodeinfo['instbal']+" %d" % msrmt.gws)

		# Start the measurement
		cursor.execute("""
			UPDATE msrmt SET started=now() WHERE msrmt_id=%d;
			COMMIT;""" % msrmt.msrmt_id)

		info("Started Measurement %d, (cons,senders,gws) = (%d,%d,%d)" % tuple(msrmt));

		# Wait for it to finish
		
		waited = 0

		success = False

		while True:
			cursor.execute("SELECT msrmt_result(%d);" %(msrmt.msrmt_id))
			res = cursor.fetchone()
			if res[0]!=None: 
				success = res[0]
				break

			if waited>0 and waited%checkperiod==0:
				info("Waited %d seconds, checking nodes..." % waited);

				nodes_on = node_check_online(senders+gws)

				if len(nodes_on)<msrmt.senders+msrmt.gws:
					warn("Only nodes %s are on, canceling measurement" % nodes_on);
					msrmt_cancel(msrmt);
					break

				info("All online");

				ok_senders = node_check_cmd(senders,"ps -C dbttcpcd && ps -C dymod")
				ok_gws = node_check_cmd(gws,"ps -C dymod")

				if (len(ok_senders+ok_gws)<msrmt.gws+msrmt.senders):
					warn("Only nodes %s are running neccessary processes, canceling measurement" % (ok_senders+ok_gws));
					msrmt_cancel(msrmt);
					break

				info("All processes running");

			time.sleep(10)
			waited = waited + 10


		# Check result
		if success: 
			info("Measurement %d succeeded!" % msrmt.msrmt_id);
			retries = 0
			msrmt = fetchmsrmt()
		else:
			error("Measurement %d failed!" % msrmt.msrmt_id);
			recovery(msrmt,retries)
			retries = retries + 1

		info("Continueing in 10 seconds...");
		time.sleep(10)
			
	dbcon.close();

except PgSQL.DatabaseError:
	error("DB con: %s" %(sys.exc_info()[1]))
	exit

except "ssh failed":
	error(sys.exc_info()[1])
