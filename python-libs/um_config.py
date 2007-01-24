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
)

# informations about olsr
olsrinfos = dict(
    remote_repos    = ':pserver:anonymous@olsrd.cvs.sourceforge.net:/cvsroot/olsrd',
    remote_module   = 'olsrd-current',
    local_upstream  = '/routing/olsr/trunk',
    local_trunk     = '/routing/olsr/branches/um-version-olsr5'
)

# informations about madwifi
madwifiinfos = dict(
    remote_repos    = 'http://svn.madwifi.org',
    remote_module   = '/trunk',
    local_upstream  = '/drivers/madwifi-ng/trunk',
    local_trunk     = '/drivers/madwifi-ng/branches/um-version'
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
        hostnameprefix = 'mrouter',
        imagetype      = 'meshnode',
        imageversion   = 'um_edgy',
        wlandevs       = {'ath0' : 'config0'},
#        startup        = ['execpy("/usr/local/sbin/um_madwifi",["--debug","autocreate"])'], 
        startup        = [],
        daemons        = []
    )
)

# informations about the different images
imageinfos = dict(
    vmeshhost = dict(
        mounts = [],
        svnmappings = { '/config/vmeshhost/trunk' : '/config',
                        '/linux/xen/trunk' : '/linux/default',
                        '/tools/nuttcp/trunk' : '/tools/nuttcp',
                        '/scripts/python-libs' : '/scripts/python-libs' },
        # folders which content is mapped to /usr/local/bin
        scriptfolders = []        
    ),
    vmeshnode = dict(
        mounts = [],
        svnmappings = { '/config/vmeshnode/trunk' : '/config',
                        '/linux/xen/trunk' : '/linux/default',
                        '/routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
                        '/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
                        '/scripts/mesh-init' : '/scripts/mesh-init',
                        '/scripts/mesh-stat' : '/scripts/mesh-stat',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/tools/nuttcp/trunk' : '/tools/nuttcp' },
        # folders which content is mapped to /usr/local/bin
        scriptfolders = [ '/scripts/mesh-init', '/scripts/mesh-stat' ]
    ),
    meshnode = dict(
        mounts = [],
        svnmappings = { '/config/vmeshnode/trunk' : '/config',
                        '/drivers/madwifi-ng/branches/um-version' : '/drivers/madwifi-ng',
                        '/linux/vanilla/trunk' : '/linux/default',
                        '/routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
                        '/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
                        '/scripts/mesh-init' : '/scripts/mesh-init',
                        '/scripts/mesh-stat' : '/scripts/mesh-stat',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/tools/nuttcp/trunk' : '/tools/nuttcp',
                        '/tools/net-snmp/branches/um-version' : '/tools/net-snmp' },
        # folders which content is mapped to /usr/local/bin
        scriptfolders = [ '/scripts/mesh-init', '/scripts/mesh-stat' ]
    )
)

# informations about the wlan devices
wlaninfos = dict(
    config0 = dict(
        hwdevice = 'wifi0',
        essid    = 'umic-mesh-ah',
        channel  = 1,
        antenna  = 2,
        address  = '169.254.9.@NODENR/16',
        wlanmode = 'ahdemo',
        txpower  = 17
    ),
    config1 = dict(
        hwdevice = 'wifi1',
        essid    = 'umic-mesh-sta',
        channel  = 11,
        antenna  = 2,
        address  = '169.254.10.@NODENR/16',
        wlanmode = 'sta',
        txpower  = 17
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
