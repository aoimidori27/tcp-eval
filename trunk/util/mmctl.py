#!/usr/bin/python

#
# Imports
#

import logging,sys,os,time, optparse, subprocess, time
from logging import info, debug, warn, error
from pyPgSQL import PgSQL
from mmbasic import *
from subprocess import *

#
# Parse args
#

parser = optparse.OptionParser("%prog [options] program cmd")
parser.add_option("-n", "--nodes", dest="nodes")
options, args = parser.parse_args()

if options.nodes: nodetype = options.nodes
else: nodetype = 'host'
		
#
# Generic cmd
#
def cmd(cmd="echo"):
	print node_exec(nodeinfo[nodetype],cmd)

#
# Xen
#

def xen(action="check"):
	output = {
		'startup'	: xen_startup,
		'check'		: xen_check,
		'info'		: lambda : "\n".join(["Running domUs %s on %s" % (xen_dom0_domus(dom0),dom0) for dom0 in nodeinfo['domnulls']])
	}[action]()
	print output

	
#
# DYMO
#

def dymo(action="check"):
	output = {
		'check'		: lambda: "DYMO running on %s" % dymo_check(nodeinfo[nodetype]),
		'restart'	: lambda: dymo_restart(nodeinfo['sender'],nodeinfo['gw']),
		'stop'		: lambda: dymo_stop(nodeinfo[nodetype])
	}[action]()
	print output

#
# Main
#

if len(args)>1: action = args[1]
else: action = ""

eval("%s(\"%s\")" %(args[0],action))
