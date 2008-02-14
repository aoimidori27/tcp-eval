#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
import os
import re
import sys
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_image import Image, ImageException
from um_functions import requireroot, call, execute, CommandFailed


class Chroot(Application):
    """Class to chroot into a UMIC-Mesh.net image"""    

    def __init__(self):
        """Creates a new Chroot object"""

        Application.__init__(self)

        # object variables   
        self._mtab = None
        self._image = None
        self._command = None
        self._executables = {"su" : "/bin/su",
                             "bash" : "/bin/bash",
                             "mount" : "/bin/mount",
                             "umount" : "/bin/umount",
                             "automount" : "/usr/sbin/automount",
                             "chroot" : "/usr/sbin/chroot",
                             "linux32" : "/usr/bin/linux32"}
        
        self._mount_map = [{"device" : "/dev", "mountpoint" : "dev", "args" : "-o bind"},
                           {"device" : "/proc", "mountpoint" : "proc", "args" : "-o bind"},
                           {"device" : "/tmp", "mountpoint" : "tmp", "args" : "-o bind"}]
       
        self._automount_map = [{"mountpoint" : "home",
                                "mapfile" : "ldap ou=auto.home,ou=automount,"\
                                            "ou=admin,dc=umic-mesh,dc=net",
                                "args" : "--timeout=60 --ghost"}]

        # get the current user name
        if os.environ.has_key("SUDO_USER"):
            default_user = os.environ["SUDO_USER"]
        else:
            default_user = os.environ["USER"]

        # initialization of the option parser
        usage = "usage: %prog [options] [COMMAND] \n" \
                "where COMMAND is a command which is execute in chroot"
        self.parser.set_usage(usage)
        self.parser.set_defaults(image_type = "meshnode", prompt = "debian_chroot",
                user = default_user, image_version = "default")

        self.parser.add_option("-I", "--image_type", metavar = "TYPE",
                action = "store", dest = "image_type", choices = Image.types(),
                help = "the image type for chroot [default: %default]")
        self.parser.add_option("-p", "--prompt", metavar = "VAR", type="string",
                action = "store", dest = "prompt",
                help = "the variable identifying the chroot (used in the prompt) "\
                       "[default: %default]")
        self.parser.add_option("-u", "--user", metavar = "NAME", type="string",
                action = "store", dest = "user",
                help = "the user to be in the chroot [default: %default]")
        self.parser.add_option("-V", "--image_version", metavar = "VERSION",
                action = "store", dest = "image_version", type="string",
                help = "the image version for chroot [default: %default]")


    def set_option(self):
        """Set the options for the Chroot object"""

        Application.set_option(self)

        # set arguments
        if len(self.args) > 0:
            self._command = " ".join(self.args)
        else:
            self._command = self._executables["bash"]


    def checkMount(self, mountpoint):
        """Return true if the mountpoint is already mounted, otherwise return false"""
        
        # get all mount points
        if self._mtab is None:
            self._mtab = execute(self._executables["mount"], shell = True)[0]
            self._mtab = self._mtab.split('\n')

        # check mountpoint
        regex = re.compile(mountpoint)
        for line in self._mtab:
            if regex.search(line):
                return True

        return False


    def automount(self):
        """
        Starts the automounter for all mount points that are denoted in the
        object variable "automount_map"
        """

        # for all entries in the automount map
        for automount in self._automount_map:
            mountpoint = os.path.join(self._image.getImagePath(),
                                      automount["mountpoint"])
            mapfile = automount["mapfile"]
            args = automount["args"]
            
            # check mountpoint            
            if not self.checkMount(mountpoint):
                cmd = "%s %s %s %s" % (self._executables["automount"],
                                       mountpoint, mapfile, args)
                info(cmd)
                call(cmd, shell = True)


    def mount(self):
        """Mount all devices that are denoted in the object variable "mount_map" """
        
        # for all entries in the mount map
        for mount in self._mount_map:
            device = mount["device"]
            mountpoint = os.path.join(self._image.getImagePath(),
                                      mount["mountpoint"])
            args = mount["args"]
            
            # check mountpoint            
            if not self.checkMount(mountpoint):
                cmd = "%s %s %s %s" % (self._executables["mount"], args, device, mountpoint)
                info(cmd)
                call(cmd, shell = True)

        # since we probably add manualy some mountpoints, we have to reset
        # the cache variable self._mtab
        self._mtab = None


    def umount(self):
        """Unmount all devices that are denoted in the object variable "mount_map" """

        # for all entries in the mount map
        for mount in self._mount_map:
            mountpoint = os.path.join(self._image.getImagePath(),
                                      mount["mountpoint"])
            
            # check mountpoint
            if self.checkMount(mountpoint):           
                cmd = "%s %s" % (self._executables["umount"], mountpoint)
                info(cmd)
                call(cmd, shell = True)    

 
    def chroot(self):
        """Chroot into the image and execute the command"""
       
        # build chroot command
        cmd = "%s %s %s %s -c 'export %s=%s && %s'" \
              %(self._executables["chroot"], self._image.getImagePath(),
                self._executables["su"], self.options.user,
                self.options.prompt, self._image.getType(), self._command)

        # on a 64bit linux machine, we need the 32bit userland wrapper
        if os.uname()[4] == "x86_64":
            cmd = "%s %s " %(self._executables["linux32"], cmd)

        # execute command
        call(cmd, shell = True)          


    def run(self):
        """
        Main method of the Chroot object. Mount all devices and chroot into
        the image. After chroot is terminated all devices are proper unmouted
        """
        
        try:
            # must be root
            requireroot()

            # create a new Image object   
            self._image = Image(self.options.image_type, self.options.image_version) 
            info("Image type: %s" % self._image.getType())

            # mount the file system and start automounter
            self.mount()
            self.automount()

            # chroot into the image
            self.chroot()

            # unmount the file system
            self.umount()
        
        except ImageException, exception:
            error(exception.msg)
        except CommandFailed, exception:
            error(exception)



if __name__ == "__main__":
    inst = Chroot()
    inst.parse_option()
    inst.set_option()
    inst.run()
