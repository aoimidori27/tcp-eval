#!/bin/bash
DIR=`basename $0 .sh | tr -d [:alpha:]`
mount -o bind /opt/mcg-mesh/images/gentoo/portage /opt/mcg-mesh/images/gentoo/$DIR/usr/portage/
chroot /opt/mcg-mesh/images/gentoo/$DIR /bin/bash
umount /opt/mcg-mesh/images/gentoo/$DIR/usr/portage/
