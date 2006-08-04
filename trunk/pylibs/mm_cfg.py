# global configuration
imageprefix = "/opt/mcg-mesh/images"
svnprefix = "/opt/meshnode"
# group id of "mcg-mesh" group
meshgid = 30012;

#
# Information about the subversion repository
#
svninfos = dict (
	svnrepos  = "svn://goldfinger.informatik.rwth-aachen.de/mcg-mesh",
	svnmappings = { '/config/meshnode/trunk' : '/config',
					'/drivers/madwifi-ng/trunk' : '/drivers/madwifi-ng',
					#'/boot/linux/trunk' : '/linux',
					'/routing/olsr/trunk' : '/routing/olsr',
					'/scripts/trunk' : '/scripts',
					'/tools/dbttcp/trunk' : '/tools/dbttcp' }		   
					
)
	

#
# MCG Mesh Node Information
#
nodeinfos = dict(
	vmeshnode = dict(
		hostprefix = 'xenmachine',
		sender 	   = [11,22,23,24,25,26],
		gw	       = [ 12+i for i in range(10)],
		instbal	   = "/opt/vmesh/bin/instbal.sh",
		dymoinst   = "/opt/vmesh/dymo",
		wlandev	   = "tap1"
	),
	meshnode = dict(
	    hostprefix 	= 'mrouter',
		sender 	    = [i+1 for i in range(2)],
		gw		    = [i+3 for i in range(3)],
		instbal	    = "instbal.sh",
		dymoinst	= "/usr/local/sbin",
		wlandev	    = "ath0"
	)
)

imageinfos = dict(
	gentoo = dict(
	    mounts = { '/usr/portage' : '/usr/portage' }
	),
	ubuntu = dict(
	    mounts = {}
	)
)

#
# Fill up nodeinfo
#
for data in nodeinfos.itervalues():
	data['host'] 		= data['sender']+data['gw']
	data['gwc'] 		= len(data['gw'])
	data['senderc'] 	= len(data['sender'])
	data['hostc'] 		= len(data['host'])
