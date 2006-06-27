#!/usr/bin/python

import mmbasic
from mmbasic import *

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

def dymo_check(nodes):
	return node_check_cmd(nodes,dymo_cmd_check)
	
def dymo_restart(senders,gws):
	node_exec(senders, dymo_cmd_restart % (nodeinfo['dymoinst'],nodeinfo['wlandev']))
	node_exec(gws    , dymo_cmd_restart % (nodeinfo['dymoinst'],nodeinfo['wlandev']+" -g"))

def dymo_stop(nodes):
	node_exec(nodes,dymo_cmd_kill)


nodeinfo['routing'] = 'dymo'
