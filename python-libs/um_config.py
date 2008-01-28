#!/usr/bin/env python
# -*- coding: utf-8 -*-

# information about the all UMIC-Mesh.net nodes
nodeinfos = dict(
    vmeshhost = dict(
        hostnameprefix = "vmeshhost"
    ),
    vmeshrouter = dict(
        hostnameprefix = "vmrouter"
    ),
    meshrouter = dict(
        hostnameprefix = "mrouter"
    )
)

# information about the images
imageinfos = dict(
    common = dict(
        repository  = "svn://mesh.umic.rwth-aachen.de/umic-mesh",
        imageprefix = "/opt/umic-mesh/images",
        bootprefix  = "/opt/umic-mesh/boot",
        svnprefix   = "/opt/checkout"
    ),
    vmeshhost = dict(
        svnmappings = { "/config/vmeshhost/trunk" : "config",
                        "/linux/xen/trunk" : "linux/default",
                        "/tools/nuttcp/branches/um-version-tcp_info" : "tools/nuttcp",
                        "/tools/flowgrind/trunk" : "tools/flowgrind",
                        "/tools/twisted/branches/um-version" : "tools/twisted",
                        "/tools/net-snmp/branches/um-version" : "tools/net-snmp",
                        "/boot/bios/trunk" : "boot/bios",
                        "/boot/etherboot/trunk" : "boot/etherboot",
                        "/scripts/python-libs" : "scripts/python-libs",
                        "/scripts/image" : "scripts/image",
                        "/scripts/vmesh" : "scripts/vmesh",
                        "/scripts/util" : "scripts/util",
                        "/scripts/measurement" : "scripts/measurement",
                        "/scripts/analysis" : "scripts/analysis" },
        scriptmappings = { "scripts/image" : "/usr/local/sbin",
                           "scripts/vmesh" : "/usr/local/sbin",
                           "scripts/image" : "/usr/local/sbin",
                           "scripts/measurement" : "/usr/local/bin" }
    ),
    vmeshnode = dict(
        svnmappings = { "/config/vmeshnode/trunk" : "config",
                        "/linux/xen/trunk" : "linux/default",
                        "/linux/xen/branches/linux-2.6.16.29-xen-elcn" : "linux/elcn",
                        "/routing/olsr/branches/um-version-olsr4" : "routing/olsr4",
                        "/routing/olsr/branches/um-version-olsr5" : "routing/olsr5",
                        "/tools/nuttcp/branches/um-version-tcp_info" : "tools/nuttcp",
                        "/tools/flowgrind/trunk" : "tools/flowgrind",
                        "/tools/tcpdump/branches/um-version-elcn" : "tools/tcpdump",
                        "/tools/set-elcn/trunk" : "tools/set-elcn",
                        "/scripts/python-libs" : "scripts/python-libs",
                        "/scripts/vmesh" : "scripts/vmesh",
                        "/scripts/util" : "scripts/util" },
        scriptmappings = { "scripts/vmesh" : "/usr/local/sbin",
                           "scripts/util" : "/usr/local/bin" }
    ),
    meshnode = dict(
        svnmappings = { "/config/vmeshnode/trunk" : "config",
                        "/linux/vanilla/trunk" : "linux/default",
                        "/linux/vanilla/branches/linux-2.6.16.29-ring3" : "linux/ring3",
                        "/linux/vanilla/branches/linux-2.6.16.29-elcn" : "linux/elcn",
                        "/routing/olsr/branches/um-version-olsr4" : "routing/olsr4",
                        "/routing/olsr/branches/um-version-olsr5" : "routing/olsr5",
                        "/drivers/madwifi-ng/branches/um-version" : "drivers/madwifi-ng",
                        "/drivers/madwifi-ng/branches/um-version-elcn" : "drivers/madwifi-ng-elcn",
                        "/tools/net-snmp/branches/um-version" : "tools/net-snmp",
                        "/tools/set-elcn/trunk" : "tools/set-elcn",
                        "/tools/nuttcp/branches/um-version-tcp_info" : "tools/nuttcp",
                        "/tools/flowgrind/trunk" : "tools/flowgrind",
                        "/tools/tcpdump/branches/um-version-elcn" : "tools/tcpdump",
                        "/tools/libpcap/branches/ring3" : "tools/libpcap",
                        "/tools/libpfring/branches/um-version" : "tools/libpfring",
                        "/tools/twisted/branches/um-version" : "tools/twisted",
                        "/scripts/python-libs" : "scripts/python-libs",
                        "/scripts/rpcserver" : "scripts/rpcserver",
                        "/scripts/mesh" : "scripts/mesh",
                        "/scripts/util" : "scripts/util" },
        scriptmappings = { "scripts/mesh" : "/usr/local/sbin",
                           "scripts/util" : "/usr/local/bin",
                           "scripts/rpcserver" : "/usr/local/sbin" }
    )
)

# kernel information
kernelinfos = dict(
    mirror = "http://sunsite.informatik.rwth-aachen.de/ftp/pub/Linux/kernel/",
    version = "2.6.16.29",
    srcpath = "/usr/src",
)

# olsr information
olsrinfos = dict(
    remote_repos    = ":pserver:anonymous@olsrd.cvs.sourceforge.net:/cvsroot/olsrd",
    remote_module   = "olsrd-current",
    remote_tag      = "OLSRD_0_5_4",
    local_upstream  = "/routing/olsr/trunk",
    local_trunk     = "/routing/olsr/branches/um-version-olsr5"
)

# madwifi information
madwifiinfos = dict(
    remote_repos    = "http://svn.madwifi.org",
    remote_module   = "/madwifi/tags",
    remote_tag      = "release-0.9.3.3",
    local_upstream  = "/drivers/madwifi-ng/trunk",
    local_trunk     = "/drivers/madwifi-ng/branches/um-version"
)
