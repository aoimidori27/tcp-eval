#!/bin/bash
# vim:softtabstop=4:shiftwidth=4:expandtab

# Script to generate a initial ramfs.
#
# Copyright (C) 2010 Christian Samsel <christian.samsel@rwth-aachen.de>
# Copyright (C) 2006 Alexander Zimmermann <alexander.zimmermann@rwth-aachen.de>
# Copyright (C) 2006 Arnd Hannemann <arnd@arndnet.de>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# image path 
IMAGEDIR_EDGY="/opt/umic-mesh/images/vmeshnode/edgy"
IMAGEDIR_HARDY="/opt/umic-mesh/images/vmeshhost/hardy"
IMAGEDIR_LUCID="/opt/umic-mesh/images/vmeshhost/lucid"

# destination -$IMAGE will be appended to this
INITRD_DST=/opt/umic-mesh/boot/initrd/initramfs

# temp directory copying files
INITRD_TMP=/tmp/initrd

# path of configuration files etc, to copy in
FILE_DIR=/opt/checkout/boot/initrd

# directories to create
DIRS="/usr/sbin,/newroot,/proc,/sbin,/dev/net,/var/lib/dhcp"
DIRS="$DIRS,/var/lib/dhcp3,/var/log,/var/run,/etc"
DIRS="$DIRS,/bin,/lib,/etc,/lib/dhcp3-client"

# files which belong to /bin
BINFILES="bash,cat,chmod,echo,expr,grep,hostname,xargs"
BINFILES="$BINFILES,kill,logger,ls,mknod,mount,ping,rm,sed"
BINFILES="$BINFILES,sh,sleep,umount,uname,run-init,chroot"

# files which belong to /sbin
SBINFILES="brctl,dhclient3,dhclient,hwclock,ifconfig,insmod,ip,losetup,usplash_write"
SBINFILES="$SBINFILES,modprobe,ntpdate,portmap,route,iptables"
SBINFILES="$SBINFILES,ethtool,syslog-ng,strace,mount.nfs"

# some static files, which are copied only for ubuntu
STATIC="/bin/ip,/lib/dhcp3-client/call-dhclient-script"

# where to search for executables and librarys
LIB_SEARCHPATH="/lib,/usr/lib,/usr/lib/i586,/lib/tls/i686/nosegneg"
BIN_SEARCHPATH="/bin,/usr/bin,/sbin,/usr/sbin,/usr/lib/klibc/bin"

# librarys which are copied for ubuntu edgy initramfs
LIBS_EDGY="ld-2.4.so,ld-linux.so.2,libblkid.so.1,libblkid.so.1.0,libc-2.4.so,libcap.so.1,libcap.so.1.10,libcrypto.so.0.9.8,libc.so.6,libdl-2.4.so,libdl.so.2,liblzo.so.1,liblzo.so.1.0.0,libncurses.so.5,libncurses.so.5.5,libnsl.so.1,libnss_dns.so.2,libnss_dns-2.4.so,libnss_files.so.2,libnss_files-2.4.so,libproc-3.2.7.so,libpthread-2.4.so,libpthread.so.0,libresolv-2.4.so,libresolv.so.2,librt-2.4.so,librt.so.1,libssl.so.0.9.8,libutil-2.4.so,libutil.so.1,libuuid.so.1,libuuid.so.1.2,libwrap.so.0,libwrap.so.0.7.6,libz.so.1,libz.so.1.2.3,libacl.so.1,libacl.so.1.1.0,libselinux.so.1,libattr.so.1,libattr.so.1.1.0,libsepol.so.1,libnsl.so.1,libnsl-2.4.so,libnss_compat.so.2,libnss_compat-2.4.so,libsysfs.so.2,libsysfs.so.2.0.0,klibc-gk2XW_qpdO7ELQ5NYkvZBbv1VsI.so"

# ... for hardy initramfs


LIBS_HARDY="ld-2.7.so,ld-linux.so.2,libblkid.so.1,libblkid.so.1.0,libc-2.7.so,libcap.so.1,libcap.so.1.10,libcrypto.so.0.9.8,libc.so.6,libdl-2.7.so,libdl.so.2,liblzo.so.1,liblzo.so.1.0.0,libncurses.so.5,libncurses.so.5.6,libnsl.so.1,libnss_dns.so.2,libnss_dns-2.7.so,libnss_files.so.2,libnss_files-2.7.so,libproc-3.2.7.so,libpthread-2.7.so,libpthread.so.0,libresolv-2.7.so,libresolv.so.2,librt-2.7.so,librt.so.1,libssl.so.0.9.8,libutil-2.7.so,libutil.so.1,libuuid.so.1,libuuid.so.1.2,libwrap.so.0,libwrap.so.0.7.6,libz.so.1,libz.so.1.2.3.3,libacl.so.1,libacl.so.1.1.0,libselinux.so.1,libattr.so.1,libattr.so.1.1.0,libsepol.so.1,libnsl.so.1,libnsl-2.7.so,libnss_compat.so.2,libnss_compat-2.7.so,libsysfs.so.2,libsysfs.so.2.0.1,klibc-B9LS-Gjx2D7BYcbQig0RlgHKO9Y.so"

# lucid

LIBS_LUCID="ld-2.11.1.so,libc-2.11.1.so,libdl-2.11.1.so,libnss_dns-2.11.1.so,libnss_files-2.11.1.so,libnss_compat-2.11.1.so,libpthread-2.11.1.so,libresolv-2.11.1.so,librt-2.11.1.so,libutil-2.11.1.so,libnsl-2.11.1.so,libutil.so.1,libdl.so.2,libc.so.6,ld-linux.so.2,libcap.so.2.17,libcap.so.2,libcrypto.so.0.9.8,liblzo.so.1.0.0,liblzo.so.1,liblzo2.so.2.0.0,liblzo2.so.2,liblzo2.so,libtermcap.so,libncurses.so.5.7,libncurses.so.5,libncurses.so,libtermcap.so,libnsl.so.1,libnsl.so,libnss_dns.so.2,libnss_dns.so,libnss_files.so.2,libnss_compat.so.2,libproc-3.2.8.so,libpthread.so.0,libresolv.so.2,librt.so.1,libssl.so.0.9.8,libuuid.so.1,libuuid.so.1.3.0,libwrap.so.0,libwrap.so.0.7.6,libz.so.1,libz.so.1.2.3.3,libacl.so.1,libacl.so.1.1.0,libselinux.so.1,libattr.so.1,libattr.so.1.1.0,libsepol.so.1,libsysfs.so.2,libsysfs.so,klibc-3l753vPzJwYEL0GJGYa3oGaUPp4.so,libblkid.so.1,libblkid.so.1.1.0,libevtlog.so.0,libevtlog.so.0.0.0,libpcre.so.3,libpcre.so.3.12.1"

function makedev() {
   cd $INITRD_TMP/dev
   MAKEDEV std

   mknod $INITRD_TMP/dev/console c 5 1
   mknod $INITRD_TMP/dev/tty12   c 4 12

   # net tun
   mknod $INITRD_TMP/dev/net/tun c 10 200

   # watchdog
   mknod $INITRD_TMP/dev/watchdog c 10 130 
}

# filecopy "$files" "$searchpath" "$dstdir"
function filecopy () {
    for file in ${1//,/ }; do
        FOUND=n
        for dir in ${2//,/ }; do
            dir="${IMAGEDIR}$dir"
            if [ -e $dir/$file ]; then
                cp $CPOPTS $dir/$file $3;
                FOUND=y
                break;
            fi;
        done;
        if [ $FOUND = n ]; then
            echo "Warning: failed to locate $file!"
        fi
    done;
}


function usage ()
{
    this=`basename $0`
    cat <<!EOF!
usage: $this [options] image
options:
  -h        Print this help summary and exit.
  -v        Be more verbose.

image should be edgy, hardy or lucid.
!EOF!
}


# check if root
if [ $UID -ne 0 ]; then
    echo "Must be root!"
    usage;
    exit 1;
fi;

# parse optional arguments
getopts vh FLAG
if [ "$?" -ne 0 ]; then
    FLAG="null"
fi

VERBOSE=n 
case $FLAG in
    "v")
        VERBOSE=y; shift ;;
    "h")
        usage; exit 0;;
esac


# if there is no image argument, print usage and exit
IMAGE=$1;
if [ -z $IMAGE ]; then
    echo "You have to specify an image name."
    usage; exit 1;
fi

case $IMAGE in
    edgy)
        LIBS=$LIBS_EDGY
        IMAGEDIR=$IMAGEDIR_EDGY ;;
    hardy)
	LIBS=$LIBS_HARDY
	IMAGEDIR=$IMAGEDIR_HARDY ;;
    lucid)
    	LIBS=$LIBS_LUCID
	IMAGEDIR=$IMAGEDIR_LUCID ;;
    *)
        echo "Unknown image type: $IMAGE"; usage; exit 2; ;;
esac

INITRD_DST="$INITRD_DST-$IMAGE";

echo "Generating $INITRD_DST..."

# options for invocation of "cp"
CPOPTS="--update --no-dereference --preserve=mode,ownership,timestamps,link"
if [ $VERBOSE = y ]; then
    CPOPTS="--verbose $CPOPTS"
fi;

# Options for invocation of "mkdir"
MKOPTS="-p"
if [ $VERBOSE = y ]; then
    MKOPTS="-v $MKOPTS"
fi;

# create tmp directory
mkdir $INITRD_TMP
if [ $? -ne 0 ]; then 
    echo Creating $INITRD_TMP failed, please remove it manually.
    exit 1;
fi

# create directories
for dir in ${DIRS//,/ }; do
  mkdir $MKOPTS $INITRD_TMP/$dir 
done

# copy binfiles
filecopy "$BINFILES" "$BIN_SEARCHPATH" "$INITRD_TMP/bin/"

# copy sbinfiles
filecopy "$SBINFILES" "$BIN_SEARCHPATH" "$INITRD_TMP/sbin/"

# copy libs
filecopy "$LIBS" "$LIB_SEARCHPATH" "$INITRD_TMP/lib/"

# copy static files 
for file in ${STATIC//,/ }; do
    cp $CPOPTS ${IMAGEDIR}$file ${INITRD_TMP}${file}
done;


# make a dhcp client link for ubuntu 
    ln -vs /etc/dhcp/dhclient-script $INITRD_TMP/sbin

# make /dev nodes
makedev;

cp -a $FILE_DIR/etc $INITRD_TMP/
cp -a $FILE_DIR/*rc $INITRD_TMP/
cp -a $FILE_DIR/initrd $INITRD_TMP/

# link /init to /linuxrc
(cd $INITRD_TMP && ln linuxrc init)

# build initramfs
(cd $INITRD_TMP && find . | cpio --quiet -o -H newc | gzip -9 > $INITRD_DST.gz)

# clean up
rm -rf $INITRD_TMP

echo "Done."
