# Global configuration
imageprefix = "/opt/mcg-mesh/images"
svnprefix = "/opt/meshnode"


# Startup configuration
#
# the keys in this dictionaries are allowed to be mrouter*, mclient*,
# meshrouter and meshclient
startupinfos = dict (
	meshrouter = ['execpy("/usr/local/bin/mm_madwifi.py",["--debug","autocreate"])',
				  'startdaemon("watchdog")'],
	goldfinger = ['startdaemon("watchdog")']
)

daemoninfos = dict (
	watchdog = dict (
	                  path = "/usr/local/bin/mm_watchdog.sh",
					  args = []
	)
)


# Common Wireless configuration
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


# Information about the kernel
kernelinfos = dict (
	mirror = "http://sunsite.informatik.rwth-aachen.de/ftp/pub/Linux/kernel/",
	version = "2.6.16.29",
	srcpath = "/usr/src",
	modifiedfiles = ('include/net/ip_fib.h','include/net/route.h',
					 'net/ipv4/fib_semantics.c','net/ipv4/route.c')
)

# Information about olsr
olsrinfos = dict (
	remote_repos    = ":pserver:anonymous@olsrd.cvs.sourceforge.net:/cvsroot/olsrd",
	remote_module   = "olsrd-current",
	local_upstream  = "/routing/olsr/branches/upstream",
	local_trunk     = "/routing/olsr/trunk"
)

# Information about madwifi
madwifiinfos = dict (
	remote_repos    = "http://svn.madwifi.org",
	remote_module   = "/trunk",
	local_upstream  = "/drivers/madwifi-ng/branches/upstream",
	local_trunk     = "/drivers/madwifi-ng/trunk"
)
	


# Information about the subversion repository
svninfos = dict (
	svnrepos  = "svn://goldfinger.informatik.rwth-aachen.de/mcg-mesh",
	svnmappings = { '/config/meshnode/trunk' : '/config',
					'/drivers/madwifi-ng/branches/mcg-version' : '/drivers/madwifi-ng',
					'/routing/olsr/branches/olsr4-mcg' : '/routing/olsr4',
					'/routing/olsr/branches/olsr5-mcg' : '/routing/olsr5',
					'/routing/aodv/trunk' : '/routing/aodv',
					'/routing/dymo/trunk' : '/routing/dymo',
					'/scripts' : '/scripts',
					'/tools/dbttcp/trunk' : '/tools/dbttcp',
					'/tools/nuttcp/trunk' : '/tools/nuttcp'
					},
	svnmappings_meshnode = {
					'/linux/vanilla/trunk' : '/linux/trunk'
	},
	svnmappings_vmeshnode = {
					'/linux/xen/trunk' : '/linux/trunk'
	}
)
	

# MCG-Mesh Node Information
nodeinfos = dict(
	vmeshnode = dict(
		hostprefix = 'xenmachine'
	),
	meshnode = dict(
	    hostprefix 	= 'mrouter',
		kernelsrc  = "http://sunsite.informatik.rwth-aachen.de/pub/Linux/kernel/v2.6/linux-2.6.16.27.tar.bz2",
		wlandev	    = "ath0"
	)
)

# Informations about the different images
imageinfos = dict(
	gentoo = dict(
	    mounts = { '/usr/portage' : '/usr/portage' }
	),
	ubuntu = dict(
	    mounts = {}
	)
)
