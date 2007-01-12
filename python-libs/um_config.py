#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# common umic-mesh configs
#

# global informations
svnrepos    = 'svn://mesh.umic.rwth-aachen.de/umic-mesh'
imageprefix = '/opt/umic-mesh/images'
svnprefix   = '/opt/checkout'

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

# informations about the umic-mesh nodes
nodeinfos = dict(
    vmeshhost = dict(
        hostnameprefix = 'vmeshhost',
        imagetype      = 'vmeshhost',
        imageversion   = 'um_edgy',
        wlandevs       = {},
        startup        = [],
        daemons        = []
    ),
    vmeshrouter = dict(
        hostnameprefix = 'vmrouter',
        imagetype      = 'vmeshnode',
        imageversion   = 'um_edgy',
        wlandevs       = {},
        startup        = [],
        daemons        = []
    ),
    meshrouter = dict(
        hostnameprefix = 'bootserver',
        imagetype      = 'meshnode',
        imageversion   = 'um_edgy',
        wlandevs       = {'ath0' : 'config0',
                          'ath1' : 'config1'},
        startup        = ['execpy("/usr/local/bin/um_madwifi",["--debug","autocreate"])'],
        daemons        = []
    )
)

# informations about the different images
imageinfos = dict(
    vmeshhost = dict(
        mounts = {},
        svnmappings = { '/config/vmeshhost/trunk' : '/config',
                        '/linux/xen/trunk' : '/linux/default',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/scripts/mesh-util' : '/scripts/mesh-util'},
        # folders which content is mapped to /usr/local/bin
        scriptfolders = [ '/scripts/mesh-util' ]        
    ),
    vmeshnode = dict(
        mounts = {},
        svnmappings = { '/config/vmeshnode/trunk' : '/config',
                        '/linux/xen/trunk' : '/linux/default',
                        '/routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
                        '/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
                        '/scripts/mesh-init' : '/scripts/mesh-init',
                        '/scripts/mesh-util' : '/scripts/mesh-util',
                        '/scripts/mesh-stat' : '/scripts/mesh-stat',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/tools/nuttcp/trunk' : '/tools/nuttcp'},
        # folders which content is mapped to /usr/local/bin
        scriptfolders = [ '/scripts/mesh-util', '/scripts/mesh-init' ]
    ),
    meshnode = dict(
        mounts = {},
        svnmappings = { '/config/vmeshnode/trunk' : '/config',
                        '/drivers/madwifi-ng/branches/um-version' : '/drivers/madwifi-ng',
                        '/linux/vanilla/trunk' : '/linux/default',
                        '/routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
                        '/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
                        '/scripts/mesh-init' : '/scripts/mesh-init',
                        '/scripts/mesh-stat' : '/scripts/mesh-stat',
                        '/scripts/mesh-util' : '/scripts/mesh-util',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/tools/nuttcp/trunk' : '/tools/nuttcp'},
        # folders which content is mapped to /usr/local/bin
        scriptfolders = [ '/scripts/mesh-util' ]
    )
)

# informations about the wlan devices
wlaninfos = dict(
    config0 = dict(
        hwdevice = 'wifi0',
        essid    = 'umic-mesh-ah',
        channel  = '1',
        antenna  = '2',
        address  = '169.254.9.$NODENR$/16',
        wlanmode = 'ahdemo',
        txpower  = '17'
    ),
    config1 = dict(
        hwdevice = 'wifi1',
        essid    = 'umic-mesh-sta',
        channel  = '11',
        antenna  = '2',
        address  = '169.254.10.$NODENR$/16',
        wlanmode = 'sta',
        txpower  = '17'
    )
)

# informations about the daemons
daemoninfos = dict(
    watchdog = dict(
        path = '/usr/local/bin/um_watchdog',
        args = []
    )
)


#
# specific project configs
#

# informations about elcn-project
elcninfos = dict(
    imageinfos = dict(
        svnmappings = { '/linux/branches/elcn-linux-2.6.16.29-xen' : '/linux/elcn'}
    )
)
