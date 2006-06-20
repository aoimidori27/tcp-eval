#!/bin/bash

FILE_DIR=/opt/meshnode/boot/initrd
INITRD_SRC=/opt/mcg-mesh/boot/initrd/blank.ext3
INITRD_DST=/opt/mcg-mesh/boot/initrd/initrd
INITRD_MP=/mnt/initrd

# Copy initrd
cp $INITRD_SRC $INITRD_DST

# Mount initrd
if [ ! -d $INITRD_MP ]; then mkdir $INITRD_MP; fi
mount $INITRD_DST $INITRD_MP -o loop

# Copy files
cp -r $FILE_DIR/* $INITRD_MP

# Unmount initrd
umount $INITRD_MP

# Gzip initrd
cat $INITRD_DST | gzip > $INITRD_DST.gz && \

# Clean up
rm $INITRD_DST
