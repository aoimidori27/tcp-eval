#!/bin/bash
KERNELDIR=/opt/mcg-mesh/src/kernel/gentoo/686/linux-2.6.16-rc3-xen-r1/
TARGET=/opt/mcg-mesh/boot/kernel/xenkernel

if [ -e "$TARGET" ]; then cp "$TARGET" "$TARGET.last"; fi
cp $IMAGEDIR/usr/src/linux/vmlinuz $TARGET

#mkelf-linux --ip=rom --rootdir=rom --rootmode=ro $TARGET >$TARGET.nb
#mkelf-linux --rootdir=rom --rootmode=ro --append="ip=:192.168.171.111:::::dhcp" $TARGET >$TARGET.nb

#mkelf-linux --ip=rom --append="root=/dev/nfs ro nfsroot=/diskless/basic" /diskless/newkernel >/diskless/newkernel.nb
#mkelf-linux --append="root=/dev/nfs ro nfsroot=/diskless/basic,ro ip=:192.168.171.111:::::dhcp" /diskless/newkernel >/diskless/newkernel.nb
