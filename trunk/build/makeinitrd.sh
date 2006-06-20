#!/bin/bash

[ "$RC_GOT_FUNCTIONS" != "yes" ] && source /usr/local/bin/functions.sh

FILE_DIR=/opt/mcg-mesh/boot/src/initrd
INITRD_SRC=/opt/mcg-mesh/boot/bin/initrd/blank.ext3
INITRD_DST=/opt/mcg-mesh/boot/bin/initrd/initrd
INITRD_MP=/mnt/initrd

copy_initrd() {
	ebegin Copy $INITRD_SRC to $INITRD_DST
	cp $INITRD_SRC $INITRD_DST
	eend $?
}

mount_initrd() {
        ebegin Mount $INITRD_DST '=>' $INITRD_MP
        if [ ! -d $INITRD_MP ]; then mkdir $INITRD_MP; fi
	mount $INITRD_DST $INITRD_MP -o loop
	eend $?
}

copy_files() {
        ebegin Copy $FILE_DIR'/*' into $INITRD_MP
        cp -r $FILE_DIR/* $INITRD_MP
	eend $?
}

umount_initrd() {
        ebegin Umount $INITRD_MP
	umount $INITRD_MP
        eend $?
}

gzip_initrd() {
        ebegin GZip $INITRD_DST
	cat $INITRD_DST | gzip > $INITRD_DST.gz && \
        eend $?
}

clean_up() {
        ebegin Delete $INITRD_DST
        rm $INITRD_DST
        eend $?
}

copy_initrd && mount_initrd && copy_files && umount_initrd && gzip_initrd && clean_up
