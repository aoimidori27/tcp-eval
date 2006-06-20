#!/bin/bash
KERNELDIR=/opt/mcg-mesh/src/kernel/gentoo/686/linux-2.6.15-gentoo-r1
TARGET=/opt/mcg-mesh/boot/kernel/newkernel

if [ -e "$TARGET" ]; then cp "$TARGET" "$TARGET.last"; fi
cp $KERNELDIR/arch/i386/boot/bzImage $TARGET

#mkelf-linux --ip=rom --rootdir=rom --rootmode=ro $TARGET >$TARGET.nb
#mkelf-linux --rootdir=rom --rootmode=ro --append="ip=:192.168.171.111:::::dhcp" $TARGET >$TARGET.nb

#mkelf-linux --ip=rom --append="root=/dev/nfs ro nfsroot=/diskless/basic" /diskless/newkernel >/diskless/newkernel.nb
#mkelf-linux --append="root=/dev/nfs ro nfsroot=/diskless/basic,ro ip=:192.168.171.111:::::dhcp" /diskless/newkernel >/diskless/newkernel.nb
