#!/bin/bash
KERNELDIR=/opt/meshserver/kernel/gentoo/686/linux-2.6.15-gentoo-r1
TARGET=/opt/mcg-mesh/boot/kernel/newkernel

if [ -e "$TARGET" ]; then cp "$TARGET" "$TARGET.last"; fi
cp $KERNELDIR/arch/i386/boot/bzImage $TARGET
