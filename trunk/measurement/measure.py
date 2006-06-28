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


def check_level1():
	nodes_on = node_check_online(nodeinfo['host'])
	
	def matchlen(a,b):
		#print "a %s b %s" % (a,b)
		return len(a)==len(b)
	
	return (matchlen(nodes_on,nodeinfo['host']) 
		and matchlen(dbttcp_check(False),nodeinfo['sender']) 
		and matchlen(dymo_check(False),nodeinfo['host']))

def check_level2():
	if nodeinfo['hostprefix']=='xenmachine': xen_check(True)
	else:
		nodes_on = node_check_online(nodeinfo['host'])
		if len(nodes_on)<len(nodeinfo['host']):
			time.sleep(300)
			
		nodes_on = node_check_online(nodeinfo['host'])
		if len(nodes_on)<len(nodeinfo['host']):
			raise "check failed", "after 300 secs only mrouters %s on" % nodes_on

	dymo_check(True)
	dbttcp_check(True)
	return True

#
# Recovery
#

def recovery(msrmt,retries):
	info("Entering Recovery");

#	cursor.execute("""
#		UPDATE msrmt SET started=NULL WHERE msrmt_id=%d;
#		UPDATE dbttcp SET phase=0 WHERE msrmt_id=%d;
#		""" % (msrmt.msrmt_id,msrmt.msrmt_id))

	msrmt_cancel(msrmt)

	if retries>3:
		error("Retried this measurement %d times, aborting" % retries);
		sys.exit(1)

	if (retries>0 and retries%2==0) or (not check_level1()):
		return check_level2()


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
	time.sleep(10)
	cursor.execute("UPDATE dbttcp SET phase=0 WHERE msrmt_id=%d;" % (msrmt.msrmt_id))
	info("Measurement %d canceled" % msrmt.msrmt_id)

#
# Main
#

checkperiod = 1200

info("Welcome")

#info("dbttcps on %s" % node_check_cmd(nodeinfo['host'],"ps -C dbttcpcd"))

info("Measuring for "+nodeinfo['hostprefix'])

try:
	dbcon = PgSQL.connect()
	dbcon.autocommit = True

	cursor = dbcon.cursor()

	retries = 0

	if not check_level1(): check_level2()
	
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

				if not check_level1():
					info("Not all ok, canceling measurement")
					msrmt_cancel(msrmt)
					break
				
				info("All ok");

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
