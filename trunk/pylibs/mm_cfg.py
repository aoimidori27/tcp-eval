# global configuration
imageprefix = "/opt/mcg-mesh/images"
svnprefix = "/opt/meshnode"
# group id of "mcg-mesh" group
# meshgid = 30012



#
# common Wireless configuration
#
wlaninfos =	dict (
	wifi0 = dict (  essid    = "mcg-mesh",
					device   = "ath0",
					channel  = "1",
					antenna  = 2,
					address  = "169.254.9.$NODENR/16",
					wlanmode = "ahdemo",
					txpower   = "20"					
				  )
)


#
# Information about the kernel
#
kernelinfos = dict (
	mirror = "http://sunsite.informatik.rwth-aachen.de/ftp/pub/Linux/kernel/",
	version = "2.6.16.27",
	srcpath = "/usr/src",
	modifiedfiles = ('include/net/ip_fib.h','include/net/route.h',
					 'net/ipv4/fib_semantics.c','net/ipv4/route.c')
)


#
# Information about the subversion repository
#
svninfos = dict (
	svnrepos  = "svn://goldfinger.informatik.rwth-aachen.de/mcg-mesh",
	svnmappings = { '/config/meshnode/trunk' : '/config',
					'/drivers/madwifi-ng/trunk' : '/drivers/madwifi-ng',
					'/boot/linux/branches/upstream' : '/linux',
					'/routing/olsr/branches/modified-0.4.10' : '/routing/olsr4',
					'/routing/olsr/trunk' : '/routing/olsr5',
					'/routing/aodv/trunk' : '/routing/aodv',
					'/routing/dymo/trunk' : '/routing/dymo',
					'/scripts/trunk' : '/scripts',
					'/tools/dbttcp/trunk' : '/tools/dbttcp',
					'/tools/nutccp/trunk' : '/tools/nuttcp'
					}		   
					
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
		kernelsrc  = "http://sunsite.informatik.rwth-aachen.de/pub/Linux/kernel/v2.6/linux-2.6.16.27.tar.bz2",
		wlandev	    = "ath0"
	)
)

#
# Informations about the different images
#
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
