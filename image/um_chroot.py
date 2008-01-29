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
        self.mtab = None
        self.image = None
        self.command = None
        self.executables = {"su" : "/bin/su",
                            "bash" : "/bin/bash",
                            "mount" : "/bin/mount",
                            "umount" : "/bin/umount",
                            "automount" : "/usr/sbin/automount",
                            "chroot" : "/usr/sbin/chroot",
                            "linux32" : "/usr/bin/linux32"}
        
        self.mount_map = [{"device" : "/dev", "mountpoint" : "dev", "args" : "-o bind"},
                          {"device" : "/proc", "mountpoint" : "proc", "args" : "-t proc"}]
       
        self.automount_map = [{"mountpoint" : "home",
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
        self.parser.set_defaults(user = default_user, prompt = "debian_chroot",
                                 imagetype = "meshnode", imageversion = "default")

        self.parser.add_option("-p", "--prompt", metavar = "VAR", type="string",
                               action = "store", dest = "prompt",
                               help = "set variable identifying the chroot " \
                                      "(used in the prompt) [default: %default]")
        self.parser.add_option("-T", "--imagetype", metavar = "TYPE",
                               action = "store", dest = "imagetype",
                               choices = Image.gettypes(),
                               help = 'set the "imagetype" for chroot [default: %default]')
        self.parser.add_option("-u", "--user", metavar = "NAME", type="string",
                               action = "store", dest = "user",
                               help = "set the user to be in the chroot [default: %default]")
        self.parser.add_option("-V", "--imageversion", metavar = "VERSION",
                               action = "store", dest = "imageversion",
                               help = 'set the "imageversion" for chroot [default: %default]')


    def set_option(self):
        """Set the options for the Chroot object"""

        Application.set_option(self)

        # set arguments
        if len(self.args) > 0:
            self.command = " ".join(self.args)
        else:
            self.command = self.executables["bash"]


    def checkmount(self, mountpoint):
        """Return true if the mountpoint is already mounted, otherwise return false """
        
        # get all mount points
        if not self.mtab:
            self.mtab = execute(self.executables["mount"], shell = True)[0]
            self.mtab = self.mtab.split('\n')

        # check mountpoint
        regex = re.compile(mountpoint)
        for line in self.mtab:
            if regex.search(line):
                return True

        return False


    def automount(self):
        """
        Starts the automounter for all mount points that are denoted in the
        object variable "automount_map"
        """

        # for all entries in the automount map
        for automount in self.automount_map:
            mountpoint  = os.path.join(self.image.getimagepath(), automount["mountpoint"])
            mapfile  = automount["mapfile"]
            args = automount["args"]
            
            # check mountpoint            
            if not self.checkmount(mountpoint):
                cmd = "%s %s %s %s" % (self.executables["automount"], mountpoint, mapfile, args)
                info(cmd)

                call(cmd, shell = True)

    def mount(self, ):
        """Mount all devices that are denoted in the object variable "mount_map" """        

        # for all entries in the mount map
        for mount in self.mount_map:
            device  = mount["device"]
            mountpoint  = os.path.join(self.image.getimagepath(), mount["mountpoint"])
            args = mount["args"]
            
            # check mountpoint            
            if not self.checkmount(mountpoint):
                cmd = "%s %s %s %s" % (self.executables["mount"], args, device, mountpoint)
                info(cmd)

                call(cmd, shell = True)


    def umount(self):
        """Unmount all devices that are denoted in the object variable "mount_map" """        

        # for all entries in the mount map
        for mount in self.mount_map:
            mountpoint  = os.path.join(self.image.getimagepath(), mount["mountpoint"])
            
            # check mountpoint
            if not self.checkmount(mountpoint):           
                cmd = "%s %s" % (self.executables["umount"], mountpoint)
                info(cmd)
                call(cmd, shell = True)    

 
    def chroot(self):
        """Chroot into the image and execute the command"""
       
        # build chroot command
        cmd = "%s %s %s %s -c 'export %s=%s && %s'" \
              %(self.executables["chroot"], self.image.getimagepath(),
                self.executables["su"], self.options.user,
                self.options.prompt, self.image.gettype(), self.command)

        # on a 64bit linux machine, we need the 32bit userland wrapper
        if os.uname()[4] == "x86_64":
            cmd = "%s %s " %(self.executables["linux32"], cmd)

        # execute command
        call(cmd, shell = True)          


    def run(self):
        """
        Main method of the Chroot object. Mount all devices and chroot into
        the image. After the chroot is terminated all devices are proper unmouted
        """
        
        try:
            # must be root
            requireroot()

            # create a new Image object   
            self.image = Image(self.options.imagetype, self.options.imageversion) 
            info("Imagetype: %s" % self.image.gettype())

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
