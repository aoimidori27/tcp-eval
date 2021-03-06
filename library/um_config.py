#!/usr/bin/env python
# -*- coding: utf-8 -*-

# information about the all UMIC-Mesh.net nodes
node_info = dict(
    vmeshhost = dict(
        hostname_prefix = "vmhost",
        image_names = ["vmeshhost"],
        virtual = False
    ),
    vmeshrouter = dict(
        hostname_prefix = "vmrouter",
        image_names = ["vmeshnode"],
        virtual = True
    ),
    meshrouter = dict(
        hostname_prefix = "mrouter",
        image_names = ["meshnode"],
        virtual = False
    )
)

# information about the images
image_info = dict(
    common = dict(
        repository    = "svn+ssh://svn.umic-mesh.net/umic-mesh",
        image_prefix  = "/opt/umic-mesh/images",
        kernel_prefix = "/opt/umic-mesh/boot/linux",
        initrd_prefix = "/opt/umic-mesh/boot/initrd",
        svn_prefix    = "/opt/checkout"
    ),
    vmeshhost = dict(
        svn_mappings = { "/config/vmeshhost/trunk" : "config.local",
                         "/config/common/trunk" : "config.common",
                         "/linux/xen/branches/linux-2.6.18-xen-um" : "linux/default",
                         "/tools/nuttcp/branches/um-version-tcp_info" : "tools/nuttcp",
                         "/projects/flowgrind/trunk" : "projects/flowgrind",
                         "/tools/twisted/branches/um-version" : "tools/twisted",
                         "/tools/net-snmp/branches/um-version" : "tools/net-snmp",
                         "/tools/xen/trunk" : "tools/xen",
                         "/tools/libnetfilter_queue/trunk" : "tools/libnetfilter_queue",
                         "/tools/libnfnetlink/trunk" : "tools/libnfnetlink",
                         "/tools/git/trunk" : "tools/git",
                         "/tools/graph-easy/trunk" : "tools/graph-easy",
                         "/boot/bios/trunk" : "boot/bios",
                         "/boot/etherboot/trunk" : "boot/etherboot",
                         "/scripts/python-libs" : "scripts/python-libs",
                         "/scripts/image" : "scripts/image",
                         "/scripts/vmesh" : "scripts/vmesh",
                         "/scripts/util" : "scripts/util",
                         "/scripts/measurement" : "scripts/measurement",
                         "/scripts/analysis" : "scripts/analysis",
                         "/scripts/pdfconverters" : "scripts/pdfconverters" },
        script_mappings = { "scripts/image" : "/usr/local/sbin",
                            "scripts/vmesh" : "/usr/local/sbin",
                            "scripts/measurement" : "/usr/local/bin",
                            "scripts/analysis": "/usr/local/bin",
                            "scripts/pdfconverters": "/usr/local/bin" }
    ),
    vmeshnode = dict(
        svn_mappings = { "/config/vmeshnode/trunk" : "config.local",
                         "/config/common/trunk" : "config.common",
                         "/linux/vanilla/branches/linux-2.6.24.x-um" : "linux/default",
                         "/linux/vanilla/branches/linux-2.6.24.x-um-reorder" : "linux/reorder",
                         "/linux/vanilla/branches/linux-2.6.27.x-tcp-ncr" : "linux/tcp-ncr",
                         "/linux/vanilla/branches/linux-2.6.31.x-um" : "linux/linux-2.6.31.x-um",
                         "/linux/xen/branches/linux-2.6.16.29-xen-elcn" : "linux/elcn",
                         "/routing/olsr/branches/um-version-olsr4" : "routing/olsr4",
                         "/routing/olsr/branches/um-version-olsr5" : "routing/olsr5",
                         "/routing/babel/trunk" : "routing/babel",
                         "/routing/dymoum/trunk" : "routing/dymoum",
                         "/routing/quagga/trunk" : "routing/quagga",
                         "/tools/nuttcp/branches/um-version-tcp_info" : "tools/nuttcp",
                         "/tools/tcpdump/branches/um-version-elcn" : "tools/tcpdump",
                         "/tools/set-elcn/trunk" : "tools/set-elcn",
                         "/tools/libnfnetlink/trunk" : "tools/libnfnetlink",
                         "/tools/libnetfilter_queue/trunk" : "tools/libnetfilter_queue",
                         "/scripts/python-libs" : "scripts/python-libs",
                         "/scripts/rpcserver" : "scripts/rpcserver",
                         "/scripts/vmesh" : "scripts/vmesh",
                         "/scripts/util" : "scripts/util",
                         "/projects/flowgrind/trunk" : "projects/flowgrind" },
        script_mappings = { "scripts/vmesh" : "/usr/local/sbin",
                            "scripts/util" : "/usr/local/bin", 
                            "scripts/rpcserver" : "/usr/local/sbin" }
    ),
    meshnode = dict(
        svn_mappings = { "/config/meshnode/trunk" : "config.local",
                         "/config/common/trunk" : "config.common",
                         "/linux/vanilla/branches/linux-2.6.24.x-um" : "linux/default",
                         "/linux/vanilla/branches/linux-2.6.16.29-icmp" : "linux/icmp",
                         "/linux/vanilla/branches/linux-2.6.16.29-elcn" : "linux/elcn",
                         "/linux/vanilla/branches/linux-2.6.27.x-tcp-ncr" : "linux/tcp-ncr",
                         "/linux/vanilla/branches/linux-2.6.24.x-um-reorder" : "linux/reorder",
                         "/linux/vanilla/branches/linux-2.6.31.x-um" : "linux/linux-2.6.31.x-um",
                         "/routing/olsr/branches/um-version-olsr4" : "routing/olsr4",
                         "/routing/olsr/branches/um-version-olsr5" : "routing/olsr5",
                         "/routing/babel/trunk" : "routing/babel",
                         "/routing/dymoum/trunk" : "routing/dymoum",
                         "/routing/dymoum/trunk" : "routing/quagga",
                         "/drivers/madwifi-ng/branches/um-version" : "drivers/madwifi-ng",
                         "/drivers/madwifi-ng/branches/um-version-elcn" : "drivers/madwifi-ng-elcn",
                         "/tools/net-snmp/branches/um-version" : "tools/net-snmp",
                         "/tools/set-elcn/trunk" : "tools/set-elcn",
                         "/tools/nuttcp/branches/um-version-tcp_info" : "tools/nuttcp",
                         "/tools/tcpdump/branches/um-version-elcn" : "tools/tcpdump",
                         "/tools/libpcap/branches/ring3" : "tools/libpcap",
                         "/tools/libpfring/branches/um-version" : "tools/libpfring",
                         "/tools/twisted/branches/um-version" : "tools/twisted",
                         "/tools/libnfnetlink/trunk" : "tools/libnfnetlink",
                         "/tools/libnetfilter_queue/trunk" : "tools/libnetfilter_queue",
                         "/tools/iw/trunk" : "tools/iw",
                         "/scripts/python-libs" : "scripts/python-libs",
                         "/scripts/rpcserver" : "scripts/rpcserver",
                         "/scripts/mesh" : "scripts/mesh",
                         "/scripts/util" : "scripts/util",
                         "/projects/flowgrind/trunk" : "projects/flowgrind",
                         "/projects/meshconf/monitoring/trunk" : "monitoring" },
        script_mappings = { "scripts/mesh" : "/usr/local/sbin",
                            "scripts/util" : "/usr/local/bin",
                            "scripts/rpcserver" : "/usr/local/sbin" }
    )
)

# kernel information
kernel_info = dict(
    mirror  = "http://sunsite.informatik.rwth-aachen.de/ftp/pub/Linux/kernel/",
    version = "2.6.16.29",
    srcpath = "/usr/src",
)

# olsr information
olsr_info = dict(
    remote_repos    = ":pserver:anonymous@olsrd.cvs.sourceforge.net:/cvsroot/olsrd",
    remote_module   = "olsrd-current",
    remote_tag      = "OLSRD_0_5_4",
    local_upstream  = "/routing/olsr/trunk",
    local_trunk     = "/routing/olsr/branches/um-version-olsr5"
)

# madwifi information
madwifi_info = dict(
    remote_repos    = "http://svn.madwifi.org",
    remote_module   = "/madwifi/tags",
    remote_tag      = "release-0.9.3.3",
    local_upstream  = "/drivers/madwifi-ng/trunk",
    local_trunk     = "/drivers/madwifi-ng/branches/um-version"
)
