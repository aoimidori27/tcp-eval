#!/usr/bin/python

import mm_basic
from mm_basic import *

#
# DYMO cmds
#

dymo_cmd_kill 		= "killall dymod &>/dev/null; sleep 1 ; rmmod kdymo &>/dev/null"
dymo_cmd_start  	= "cd %s ; ./dymod -r -i %s </dev/null &>/dev/null &"
dymo_cmd_restart 	= dymo_cmd_kill+";"+dymo_cmd_start
dymo_cmd_check		= "ps -C dymod && lsmod | grep kdymo"


#
# DYMO functions
#

#def dymo_check(nodes):
#	return node_check_cmd(nodes,dymo_cmd_check)
	
def dymo_check(dostart):
	nodes_ok = node_check_cmd(nodeinfo['host'],dymo_cmd_check)
	info("DYMO running on %s" % nodes_ok)
	if not dostart: return nodes_ok
	
#	nodes_not_ok = [node for node in nodeinfo['host'] if node not in nodes_ok]
	
	info("Restarting dymo")
	dymo_restart(nodeinfo['host'])
	
	nodes_ok = dymo_check(False)
	
	if len(nodes_ok)<len(nodeinfo['host']):
		raise "dymo failed", "couldnt start DYMO on all nodes, ok : %s" % nodes_ok
	
	return nodes_ok


def dymo_restart(nodes):
	node_exec(
		[node for node in nodes if node in nodeinfo['sender']], 
		dymo_cmd_restart % (nodeinfo['dymoinst'],nodeinfo['wlandev']))
	
	node_exec(
		[node for node in nodes if node in nodeinfo['gw']], 
		dymo_cmd_restart % (nodeinfo['dymoinst'],nodeinfo['wlandev']+" -g"))

	
#def dymo_restart(senders,gws):
#	node_exec(senders, dymo_cmd_restart % (nodeinfo['dymoinst'],nodeinfo['wlandev']))
#	node_exec(gws    , dymo_cmd_restart % (nodeinfo['dymoinst'],nodeinfo['wlandev']+" -g"))

def dymo_stop(nodes):
	node_exec(nodes,dymo_cmd_kill)

#def dymo(senders,gws,action):

#def dymo_ctl(action,nodes=nodeinfo['host']):
#	return output = {
#		'check'		: lambda: dymo_check(nodes),
#		'restart'	: lambda: dymo_restart(nodeinfo['sender'],nodeinfo['gw']),
#		'stop'		: lambda: dymo_stop(nodes)
#	}[action]()


#nodeinfo['routing'] = dymo_ctl
