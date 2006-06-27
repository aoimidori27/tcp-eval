import os,sys,logging, types, subprocess
from logging import info, debug, warn, error
from mmcfg import *
from subprocess import *

#
# Log
#

logging.basicConfig(
	level = logging.INFO,
	format = '%(asctime)s %(levelname)s: %(message)s',
	datefmt = '%b %d %H:%M:%S')

#
# Check Environment Variable
#
	
if not os.environ.has_key('MESH'):
	error("please set environment variable MESH to mrouter or xen")
	sys.exit(1)

nodetype = os.environ['MESH']

if not (nodetype=='mrouter' or nodetype=='xen'):
	error("couldnt determine node type")
	sys.exit(1)

nodeinfo = nodeinfos[nodetype]


#
# Basic Functions
#

def nodename(nr):
	if type(nr) is types.StringType: return nr
	return "%s%d" % (nodeinfo['hostprefix'],nr)

#
# Util
#

def runonhost(host,args):
	p = Popen(["ssh",host,args], stdout=PIPE, stderr=PIPE)
	ret = p.communicate()
	if (p.returncode!=0): raise "run failed on host %s with %s" % (host,args), ret[1]
	return ret[0]
	
def checkonhost(host,args):
	return call(["ssh",host,args],stdout=PIPE,stderr=PIPE)==0

#
# Generic Node control
#

def node_exec(nodes,args):
	output = ""
	for host in nodes:
		info("Running %s on %s" %(args,nodename(host)));
		output+= nodename(host)+":"+runonhost(nodename(host),args)
	return output
	
def node_check_cmd(nodes,args):
	return [node for node in nodes if checkonhost(nodename(node),args)]

def node_check_online(nodes):
	return [node for node in nodes if call(["ping","-c","3",nodename(node)],stdout=PIPE,stderr=PIPE)==0]


if nodetype=='xen':
	import mmxen
	from mmxen import *


from mmdymo import *
