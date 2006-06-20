#!/bin/bash
DIR=${0#./chr}
mount -o bind /opt/mcg-mesh/images/gentoo/portage /opt/mcg-mesh/images/gentoo/$DIR/usr/portage/
chroot /opt/mcg-mesh/images/gentoo/$DIR /bin/bash
umount /opt/mcg-mesh/images/gentoo/$DIR/usr/portage/
