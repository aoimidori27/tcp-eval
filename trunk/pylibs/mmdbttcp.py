from mmbasic import *

dbttcpd_check = "ps -C dbttcpd"
dbttcpd_start = "killall dbttcpd ; dbttcpd &>dbttcpd.log &"

dbttcpcd_check = "ps -C dbttcpcd"
dbttcpcd_start = "killall dbttcpcd ; dbttcpcd -b"

def dbttcp_check(dostart):
	
	dbttcpcd_ok = node_check_cmd(nodeinfo['sender'],dbttcpcd_check)
	info("dbttcpcd running on %s" % dbttcpcd_ok)
	
	dbttcpd_ok = call(dbttcpd_check,stdout=PIPE,stderr=PIPE,shell=True)==0
	
	if dbttcpd_ok: 
		info("dbttcpd running")
	else: 
		info("dbttcpd NOT running")
		if not dostart: return []
	
	if not dostart: return dbttcpcd_ok
	
	#nodes_not_ok = [node for node in nodeinfo['sender'] if node not in dbttcpcd_ok]
	
	info("Starting dbttcpcd")
	
	node_exec(nodeinfo['sender'],dbttcpcd_start)
	
	if not dbttcpd_ok:
		info("Starting dbttcpd")
		#print "call "+dbttcpd_start
		if not call(dbttcpd_start,stdout=PIPE,stderr=PIPE,shell=True)==0:
			raise "dbttcp error", "couldnt start dbttcpd"
	
	dbttcpcd_ok = dbttcp_check(False)
	
	if len(dbttcpcd_ok)<len(nodeinfo['sender']):
		raise "dbttcp error", "couldnt start dbttcp, nodes ok: %s" % dbttcpcd_ok
	
	return dbttcpcd_ok
