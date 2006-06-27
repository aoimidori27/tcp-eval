import mmbasic, sre, string, sys
from mmbasic import *


xen_dom0_candidates = ["hiwil1","hiwil2","hiwil3","hiwir2","hiwir3"]

xen_domU_startup = "xm create /etc/xen/mel2 vmid=%d vpnserver=none"

xen_domU_destroy = "xm destroy gen%d"

xen_domU_restart = xen_domU_startup + " && sleep 3 && " + xen_domU_destroy

#'startupgw'	: "ip route flush table 200 && ip route add table 200 default dev eth0",

def xen_dom0_detect():
	if 'domnulls' in nodeinfo.keys(): return

	nodeinfo['domnulls'] = [node for node in xen_dom0_candidates if call(["ping","-c","2",node],stdout=PIPE,stderr=PIPE)==0]
	info("Detect dom0s %s" % nodeinfo['domnulls']);

def xen_dom0_domus(dom0):
	matches = sre.compile("^gen([0-9]*)\s",sre.MULTILINE).finditer(runonhost(dom0,"xm list"))
#	for match in matches:
#		print "found a match: %s" % match.group(0)
#	return []
	return [string.atoi(match.group(1)) for match in matches]

def xen_check():
	running = node_check_online(nodeinfo['host'])
	for dom0 in nodeinfo['domnulls']:
		domus = xen_dom0_domus(dom0)
		info("On %s: %s" %(dom0,domus))
		hanging = [domu for domu in domus if domu not in running]
		for hanger in hanging:
			info("Node %d hangs, restart" % hanger);
			runonhost(dom0,xen_domU_restart % (hanger,hanger))

def xen_startup():
#	running = node_check_online(nodeinfo['host'])

	running = []

	dom0_domU_map = {}

	dom0_order = []

	for dom0 in nodeinfo['domnulls']:
		domus = xen_dom0_domus(dom0)
		running += domus
		dom0_domU_map[dom0]=domus
		dom0_order += [dom0]*(4-len(domus))

	info("Already running domUs: %s" % running)

	#dom0_domU_map = dict([(dom0, xen_dom0_domus(dom0)) for dom0 in nodeinfo['domnulls']])

	print [node for node in nodeinfo['host'] if node not in running]

	for domu in [node for node in nodeinfo['host'] if node not in running]:
		#for domuset in 
		if len(dom0_order)==0:
			error("Not enough dom0s, aborting")
			sys.exit(1)

		dom0 = dom0_order.pop()
		info("Firing up %s on %s" % (domu,dom0))
		runonhost(dom0,xen_domU_startup % domu)


xen_dom0_detect()
