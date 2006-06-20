#!/bin/bash
KERNELDIR=/opt/meshserver/kernel/gentoo/686/linux-2.6.16-rc3-xen-r1/
TARGET=/opt/mcg-mesh/boot/kernel/xenkernel

if [ -e "$TARGET" ]; then cp "$TARGET" "$TARGET.last"; fi
cp $IMAGEDIR/usr/src/linux/vmlinuz $TARGET
