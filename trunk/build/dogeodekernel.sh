#!/bin/bash
KERNELDIR=/opt/meshserver/src/kernel/gentoo/geode/linux-2.6.15-gentoo-r1
TARGET=/opt/mcg-mesh/boot/kernel/geodekernel

if [ -e "$TARGET" ]; then cp "$TARGET" "$TARGET.last"; fi
cp $KERNELDIR/arch/i386/boot/bzImage $TARGET
