import os,sys,logging, types, subprocess
from logging import info, debug, warn, error
from mm_cfg import *
from subprocess import *

#
# Log
#

logging.basicConfig(
	level = logging.INFO,
	format = '%(asctime)s %(levelname)s: %(message)s',
	datefmt = '%b %d %H:%M:%S')

#
# Check Environment Variables
#
if os.environ.has_key('MESH') and nodeinfos.has_key(os.environ['MESH']):
	nodetype = os.environ['MESH']
	nodeinfo = nodeinfos[nodetype]

if os.environ.has_key('MESH_IMAGE') and imageinfos.has_key(os.environ['MESH_IMAGE']):
	imagetype = os.environ['MESH_IMAGE']
	imageinfo = imageinfos[imagetype]
	if globals().has_key('nodetype'):
		imagepath = "%s/%s/%s" % (imageprefix,imagetype,nodetype)


def requirenodetype():
	global nodetype,nodeinfo
	if not globals().has_key('nodetype'):
		error("please set environment variable MESH to one of %s" % nodeinfos.keys())
		sys.exit(1)
	

def requireimagetype():
	global imagetype,imageinfo,imagepath
	if not globals().has_key('imagetype'):
		error("please set environment variable MESH_IMAGE to one of %s" % imageinfos.keys())
		sys.exit(1)

def requireroot():
	if not os.getuid()==0:
		error("you must be root to do this")
		sys.exit(1)
	

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


if globals().has_key('nodetype') and nodetype=='vmeshnode':
	import mm_xen
	from mm_xen import *


from mm_dymo import *
from mm_dbttcp import *
