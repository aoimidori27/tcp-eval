import mmbasic, sre, string, sys, operator, time
from mmbasic import *


xen_dom0_candidates = ["hiwil1","hiwil2","hiwil3","hiwir2","hiwir3"]

xen_domU_startup = "xm create /etc/xen/mel2 vmid=%d vpnserver=none"

xen_domU_destroy = "xm destroy gen%d"

xen_domU_restart = xen_domU_startup + " && sleep 3 && " + xen_domU_destroy

#'startupgw'	: "ip route flush table 200 && ip route add table 200 default dev eth0",

def xen_dom0_detect():
	if 'domnulls' in nodeinfo.keys(): return

	nodeinfo['domnulls'] = [dom0 for dom0 in xen_dom0_candidates if host_check_online(dom0)]

	info("Detected dom0s %s" % nodeinfo['domnulls']);

def xen_domu_dict():
	xen_dom0_detect()
	return dict([(dom0,
			[string.atoi(match.group(1)) for match in 
				sre.compile(
					"^gen([0-9]*)\s",sre.MULTILINE
					).finditer(host_exec(dom0,"xm list"))
				]) for dom0 in nodeinfo['domnulls']])


def xen_check(dostart):
	xen_dom0_detect()
	
	domu_dict = xen_domu_dict()
	
	info("dom0 to domU map: %s" % domu_dict)
	
	running = node_check_online(nodeinfo['host'])
	
	# created and not running
	hanging = [domu for domu in reduce(operator.concat, domu_dict.values()) if domu not in running]
	
	info("Nodes %s are hanging" % hanging)
	
	# not running and not created
	missing = [node for node in nodeinfo['host'] if node not in (running+hanging)]
	
	info("Nodes %s are missing" % missing)
	
	if dostart and (missing or hanging):
		for hanger in hanging:
			info("Recreating hanging node %d" % hanger)
			
			host_exec(dom0,xen_domU_restart % (hanger,hanger))
		
		dom0_usage_order = []
		for dom0 in nodeinfo['domnulls']:
			dom0_usage_order += [dom0]*(4-len(domu_dict[dom0]))
		
		for domu in missing:
			if len(dom0_usage_order)==0:
				raise "xen error","Not enough dom0s"

			dom0 = dom0_usage_order.pop()
			
			info("Firing up %s on %s" % (domu,dom0))
			
			host_exec(dom0,xen_domU_startup % domu)
		
		# sleep 50 + invokations per dom0 * 20, i.e. min 70, max 115
		if missing: time.sleep(55 + (4-min(map(len,domu_dict.values())))*15)
		
		running = node_check_online(nodeinfo['host'])
		
		if len(running)<len(nodeinfo['host']):
			raise "xen error","Starting all nodes failed, running are %s" % running
	
	return running
