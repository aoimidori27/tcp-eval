#!/usr/bin/env python
# -*- coding: utf-8 -*-

# global informations
svnrepos    = 'svn://mesh.umic.rwth-aachen.de/umic-mesh'
imageprefix = '/opt/umic-mesh/images'
bootprefix  = '/opt/umic-mesh/boot'
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
        startup        = [],
    ),
    vmeshrouter = dict(
        hostnameprefix = 'vmrouter',
        imagetype      = 'vmeshnode',
        imageversion   = 'um_edgy',
        xenconfig      = 'config0',
        startup        = [],
    ),
    meshrouter = dict(
        hostnameprefix = 'mrouter',
        imagetype      = 'meshnode',
        imageversion   = 'um_edgy',
        wlandevices    = {'ath0' : 'config0', 'ath1' : 'config1' },
        startup        = ['execpy(["/usr/local/sbin/um_madwifi", "--debug", "loadmod"])',
                          'execpy(["/usr/local/sbin/um_madwifi", "--debug", "--dev=ath0", "start"])',
                          'call(["/etc/init.d/snmpd", "start"], shell=False)'] 
    )
)

# informations about the different images
imageinfos = dict(
    vmeshhost = dict(
        svnmappings = { '/config/vmeshhost/trunk' : '/config',
                        '/linux/xen/trunk' : '/linux/default',
                        '/tools/nuttcp/trunk' : '/tools/nuttcp',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/scripts/image' : '/scripts/image',
                        '/scripts/vmesh' : '/scripts/vmesh',
                        '/scripts/util' : '/scripts/util',
                        '/scripts/measurement' : '/scripts/measurement' },
        scriptmappings = { '/scripts/image' : '/usr/local/sbin',
                           '/scripts/vmesh' : '/usr/local/sbin',
                           '/scripts/image' : '/usr/local/sbin',
                           '/scripts/measurement' : '/usr/local/bin'  }
    ),
    vmeshnode = dict(
        svnmappings = { '/config/vmeshnode/trunk' : '/config',
                        '/linux/xen/trunk' : '/linux/default',
                        '/routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
                        '/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
                        '/tools/nuttcp/branches/um-version' : '/tools/nuttcp',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/scripts/vmesh' : '/scripts/vmesh',
                        '/scripts/util' : '/scripts/util' },
        scriptmappings = { '/scripts/vmesh' : '/usr/local/sbin',
                           '/scripts/util' : '/usr/local/bin' }
    ),
    meshnode = dict(
        svnmappings = { '/config/vmeshnode/trunk' : '/config',
                        '/linux/vanilla/trunk' : '/linux/default',
                        '/routing/olsr/branches/um-version-olsr4' : '/routing/olsr4',
                        '/routing/olsr/branches/um-version-olsr5' : '/routing/olsr5',
                        '/drivers/madwifi-ng/branches/um-version' : '/drivers/madwifi-ng',
                        '/tools/nuttcp/branches/um-version' : '/tools/nuttcp',
                        '/tools/net-snmp/branches/um-version' : '/tools/net-snmp',
                        '/scripts/python-libs' : '/scripts/python-libs',
                        '/scripts/mesh' : '/scripts/mesh',
                        '/scripts/util' : '/scripts/util',
                        '/scripts/measurement' : '/scripts/measurement' },
        scriptmappings = { '/scripts/mesh' : '/usr/local/sbin',
                           '/scripts/util' : '/usr/local/bin',
                           '/scripts/init' : '/usr/local/sbin' }    
    )
)

# wlan device configurations
wlanconfig = dict(
    config0 = dict(
        hwdevice = 'wifi0',
        essid    = 'umic-mesh-ah',
        channel  = 1,
        antenna  = 2,
        address  = '169.254.9.@NODENR/16',
        wlanmode = 'ahdemo',
        txpower  = 0
    ),
    config1 = dict(
        hwdevice = 'wifi1',
        essid    = 'umic-mesh-sta',
        channel  = 11,
        antenna  = 2,
        address  = '169.254.10.@NODENR/16',
        wlanmode = 'sta',
        txpower  = 0
    )
)

# xen configurations
xenconfig = dict(
    config0 = dict(
        ramdisk = '%s/initrd/vmeshnode-initrd' %(bootprefix),
        kernel  = '%s/linux/default/vmeshnode-vmlinuz' %(bootprefix),
        memory  = 40
    )
)
