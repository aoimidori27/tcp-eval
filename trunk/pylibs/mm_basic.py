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

def host_exec(host,args):
	p = Popen(["ssh",host,args], stdout=PIPE, stderr=PIPE)
	ret = p.communicate()
	if (p.returncode!=0): raise "run failed on host %s with %s" % (host,args), ret[1]
	return ret[0]
	
def host_check(host,args):
	#TODO: raise exception if retcode is 255?! (means SSH error)
	return call(["ssh",host,args],stdout=PIPE,stderr=PIPE)==0

def host_check_online(host):
	return host_check(host,"ping -w 3 -c 1 "+host)

#
# Generic Node control
#

def node_exec(nodes,args):
	output = ""
	for host in nodes:
		info("Running %s on %s" %(args,nodename(host)));
		output+= nodename(host)+":"+host_exec(nodename(host),args)
	return output
	
def node_check_cmd(nodes,args):
	return [node for node in nodes if host_check(nodename(node),args)]

def node_check_online(nodes):
	return [node for node in nodes if host_check_online(nodename(node))]


if nodetype=='xen':
	import mmxen
	from mmxen import *


from mmdymo import *
from mmdbttcp import *