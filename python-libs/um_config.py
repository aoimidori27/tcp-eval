# global informations
svnrepos    = 'svn://mesh.umic.rwth-aachen.de/umic-mesh'
imageprefix = '/opt/umic-mesh/images'
svnprefix 	= '/opt/checkout'

# informations about the kernel
kernelinfos = dict(
	mirror = 'http://sunsite.informatik.rwth-aachen.de/ftp/pub/Linux/kernel/',
	version = '2.6.16.29',
	srcpath = '/usr/src',
	modifiedfiles = ['include/net/ip_fib.h','include/net/route.h',
					 'net/ipv4/fib_semantics.c','net/ipv4/route.c']
)

# informations about olsr
olsrinfos = dict(
	remote_repos    = ':pserver:anonymous@olsrd.cvs.sourceforge.net:/cvsroot/olsrd',
	remote_module   = 'olsrd-current',
	local_upstream  = '/routing/olsr/branches/upstream',
	local_trunk     = '/routing/olsr/trunk'
)

# informations about madwifi
madwifiinfos = dict(
	remote_repos    = 'http://svn.madwifi.org',
	remote_module   = '/trunk',
	local_upstream  = '/drivers/madwifi-ng/branches/upstream',
	local_trunk     = '/drivers/madwifi-ng/trunk'
)

# informations about the wlan devices
wlaninfos = dict(
    ath0 = dict(
        wlandev  = 'wifi0',
        essid    = 'umic-mesh',
        channel  = '1',
        antenna  = '2',
        address  = '169.254.9.$NODENR/16',
        wlanmode = 'ahdemo',
        txpower  = '18'
    ),
    ath1 = dict(
        wlandev  = 'wifi1',
        essid    = 'umic-mesh',
        channel  = '11',
        antenna  = '2',
        address  = '169.254.10.$NODENR/16',
        wlanmode = 'sta',
        txpower  = '18'
    )
)

# informations about the daemons
daemoninfos = dict(
    watchdog = dict(
        path = '/usr/local/bin/um_watchdog',
        args = []
    )
)

# informations about the umic-mesh nodes
nodeinfos = dict(
	vmeshhost = dict(
		hostprefix  = 'vmeshhost',
		wlandevices = [],
		startup     = [],
		daemons		= []
	),
	vmeshnode = dict(
		hostprefix  = 'vmeshnode',
		wlandevices = [],
		startup     = [],
        daemons     = []
	),
	meshnode = dict(
	    hostprefix 	= 'meshrouter',
		wlandevices = ['ath0', 'ath1'],
		startup     = ['execpy('/usr/local/bin/um_madwifi',['--debug','autocreate'])'],
        daemons     = []
	)
)

# informations about the different images
imageinfos = dict(
    vmeshhost = dict(
		default_image = 'um_edgy',
		versions = ['um_edgy'],
		mounts = {},
		svnmappings = { '/config/vmeshhost/trunk' : '/config',
						'/linux/xen/trunk' : '/linux/default',
						'/scripts/python-libs' : '/scripts/python-libs'}
	),
	vmeshnode = dict(
        default_image = 'um_edgy',
        versions = ['um_edgy'],
		mounts = {},
		svnmappings = { '/config/vmeshnode/trunk' : '/config',
						'/linux/xen/trunk' : '/linux/default',
						'routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
						'/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
						'/scripts/mesh-init' : '/scripts/mesh-init',
						'/scripts/mesh-stat' : '/scripts/mesh-stat',
						'/scripts/python-libs' : '/scripts/python-libs',
						'/tools/nuttcp/trunk' : '/tools/nuttcp'}
	),
	meshnode = dict(
        default_image = 'um_edgy',
        versions = ['um_dapper', 'um_edgy'],
		mounts = {},
        svnmappings = { '/config/vmeshnode/trunk' : '/config',
                        '/drivers/madwifi-ng/branches/um-version' : '/drivers/madwifi-ng',
                        '/linux/vanilla/trunk' : '/linux/default',
                        '/routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
                        '/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
                        '/scripts/mesh-init' : '/scripts/mesh-init',
                        '/scripts/mesh-stat' : '/scripts/mesh-stat',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/tools/nuttcp/trunk' : '/tools/nuttcp'}
    )
)

# informations about the different projects
projectinfos = dict(
        elcn = dict(
            svnmappings = { '/linux/xen/trunk' : '/linux/elcn'}
        )
)

