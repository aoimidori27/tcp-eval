#!/bin/sh




####################################################
################### Configuration ##################
####################################################

# Image path 
IMAGEDIR_UBUNTU="/opt/mcg-mesh/images/ubuntu/meshrouter"
IMAGEDIR_GENTOO="/opt/mcg-mesh/images/gentoo/meshrouter"

# Empty ext3 filesystem
INITRD_SRC=/opt/mcg-mesh/boot/initrd/blank.ext3

# Destination -$IMAGE will be appended to this
INITRD_DST=/opt/mcg-mesh/boot/initrd/initrd     

# Mountpoint for loopback mounting initrd
INITRD_MP=/mnt/initrd

# path of configuration files etc, to copy in
FILE_DIR=/opt/meshserver/boot/initrd

# Directorys to create
DIRS="/usr/sbin,/mnt/homes,/mnt/srv,/proc,/sbin,/dev,/var/lib/dhcp,/var/lib/dhcp3,/var/log,/var/run,/etc"
DIRS="$DIRS,/bin,/lib,/etc,/lib/dhcp3-client"

# Files which belong to /bin
BINFILES="bash,cat,chmod,echo,expr,grep,hostname,"
BINFILES="$BINFILES,kill,logger,ls,mknod,mount,ping,rm,sed"
BINFILES="$BINFILES,sh,sleep,umount,uname"

# Files which belong to /sbin
SBINFILES="brctl,dhclient3,dhclient,hwclock,ifconfig,insmod,ip,losetup"
SBINFILES="$SBINFILES,modprobe,ntpdate,pivot_root,portmap,route"
SBINFILES="$SBINFILES,openvpn,ethtool,syslog-ng,strace"

# Some static files, which are copied only for ubuntu
STATIC="/bin/ip,/lib/dhcp3-client/call-dhclient-script"

# Where to search for executables and librarys
LIB_SEARCHPATH="/lib,/usr/lib,/usr/lib/i586"
BIN_SEARCHPATH="/bin,/usr/bin,/sbin,/usr/sbin"


# Librarys which are copied for ubuntu initrd
LIBS_UBUNTU="ld-2.3.6.so,ld-linux.so.2,libblkid.so.1,libblkid.so.1.0,libc-2.3.6.so,libcap.so.1,libcap.so.1.10,libcrypto.so.0.9.8,libc.so.6,libdl-2.3.6.so,libdl.so.2,liblzo.so.1,liblzo.so.1.0.0,libncurses.so.5,libncurses.so.5.5,libnsl.so.1,libnss_dns.so.2,libnss_dns-2.3.6.so,libnss_files.so.2,libnss_files-2.3.6.so,libproc-3.2.6.so,libpthread-0.10.so,libpthread.so.0,libresolv-2.3.6.so,libresolv.so.2,librt-2.3.6.so,librt.so.1,libssl.so.0.9.8,libutil-2.3.6.so,libutil.so.1,libuuid.so.1,libuuid.so.1.2,libwrap.so.0,libwrap.so.0.7.6,libz.so.1,libz.so.1.2.3,libacl.so.1,libacl.so.1.1.0,libselinux.so.1,libattr.so.1,libattr.so.1.1.0,libsepol.so.1,libnsl.so.1,libnsl-2.3.6.so,libnss_compat.so.2,libnss_compat-2.3.6.so"

# Librarys which are copied for gentoo initrd
LIBS_GENTOO="ld-2.3.6.so,ld-linux.so.2,libblkid.so.1,libblkid.so.1.0,libc-2.3.6.so,libcap.so.1,libcap.so.1.10,libcrypto.so.0,libcrypto.so.0.9.7,libc.so.6,libdl-2.3.6.so,libdl.so.2,libncurses.so,libncurses.so.5,libncurses.so.5.5,libnsl.so.1,libnss_dns.so.2,libnss_dns-2.3.6.so,libnss_files.so.2,libnss_files-2.3.6.so,libproc-3.2.6.so,libpthread-0.10.so,libpthread.so.0,libresolv-2.3.6.so,libresolv.so.2,librt-2.3.6.so,librt.so.1,libssl.a,libssl.so,libssl.so.0,libssl.so.0.9.7,libutil-2.3.6.so,libutil.so.1,libuuid.so.1,libuuid.so.1.2,libwrap.so,libwrap.so.0,libwrap.so.0.7.6,libz.so,libz.so.1,libz.so.1.2.3,libnsl.so.1,libnsl-2.3.6.so,libnss_compat.so.2,libnss_compat-2.3.6.so,liblzo2.so,liblzo2.so.2,liblzo2.so.2.0.0"


####################################################
################ End of Configuration ##############
####################################################

function usage ()
{
    this=`basename $0`
	cat <<!EOF!
usage: $this [options] image
options:
  -h        Print this help summary and exit.
  -v        Be more verbose.

image should be either ubuntu or gentoo.
!EOF!
}


# usage:
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
 "v") VERBOSE=y; shift ;;
 "h") usage; exit 0;;
esac


# if there is no image argument, print usage and exit
IMAGE=$1;
if [ -z $IMAGE ]; then
  echo "You have to specify an image name."
  usage; exit 1;
fi


case $IMAGE in
	ubuntu) LIBS=$LIBS_UBUNTU
		    IMAGEDIR=$IMAGEDIR_UBUNTU ;;
	gentoo) LIBS=$LIBS_GENTOO
		    IMAGEDIR=$IMAGEDIR_GENTOO ;;
	*) echo "Unknown image type: $IMAGE"; usage; exit 2; ;;
esac


INITRD_DST="$INITRD_DST-$IMAGE";



echo "Generating $INITRD_DST..."
# Options for invocation of "cp"
CPOPTS="--update --no-dereference --preserve=mode,ownership,timestamps,link"
if [ $VERBOSE = y ]; then
  CPOPTS="--verbose $CPOPTS"
fi;

# Options for invocation of "mkdir"
MKOPTS="-p"
if [ $VERBOSE = y ]; then
  MKOPTS="-v $MKOPTS"
fi;

# copy initrd
cp $INITRD_SRC $INITRD_DST

# Mount initrd
if [ ! -d $INITRD_MP ]; then mkdir $INITRD_MP; fi
if [ "`grep $INITRD_MP /etc/mtab`" ]; then
  echo "Opps, $INITRD_MP, seems to be mounted. Unmounting first..."
  umount $INITRD_MP
  if [ $? -ne 0 ]; then exit $?; fi;
fi;

mount $INITRD_DST $INITRD_MP -o loop

# create directories
for dir in ${DIRS//,/ }; do
  mkdir $MKOPTS $INITRD_MP/$dir 
done

# copy binfiles
filecopy "$BINFILES" "$BIN_SEARCHPATH" "$INITRD_MP/bin/"

# copy sbinfiles
filecopy "$SBINFILES" "$BIN_SEARCHPATH" "$INITRD_MP/sbin/"

# copy libs
filecopy "$LIBS" "$LIB_SEARCHPATH" "$INITRD_MP/lib/"

#for file in ${LIBS//,/ }; do
#  FOUND=n
#  for dir in ${LIB_SEARCHPATH//,/ }; do
#    if [ -e $dir/$file ]; then
#      cp $CPOPTS $dir/$file $INITRD_MP/lib;
#     FOUND=y
#      break;
#    fi;
#  done;
#  if [ $FOUND = n ]; then
#     echo "Warning: failed to locate $file!"
#  fi
#done;

# copy static files only for ubuntu
if [ $IMAGE = ubuntu ]; then
	for file in ${STATIC//,/ }; do
		cp $CPOPTS ${IMAGEDIR}$file ${INITRD_MP}${file}
	done;
fi;

# make a dhcp client link for gentoo
if [ $IMAGE = gentoo ]; then
    ln -vs /etc/dhcp/dhclient-script $INITRD_MP/sbin
fi;

# uuuuuuuugly hack
# chmod u+s ${INITRD_MP}/bin/ip
# chmod u+s ${INITRD_MP}/bin/hostname

cp -a /opt/meshserver/boot/initrd/etc $INITRD_MP/
cp -a /opt/meshserver/boot/initrd/dev $INITRD_MP/
cp -a /opt/meshserver/boot/initrd/*rc $INITRD_MP/
cp -a /opt/meshserver/boot/initrd/initrd $INITRD_MP/

# Umount initrd
umount $INITRD_MP

# Gzip initrd
gzip -f $INITRD_DST

echo "Done."



