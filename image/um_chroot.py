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
    

    def __init__(self, su = "/bin/su", command = "/bin/bash", mount = "/bin/mount",
                 umount = "/bin/umount", chroot = "/usr/sbin/chroot",
                 linux32 = "/usr/bin/linux32"):
        """Creates a new Chroot object"""

        Application.__init__(self)

        # object variables
        self.su = su
        self.command = command
        self.mount = mount
        self.umount = umount
        self.chroot = chroot
        self.linux32 = linux32
        self.mount_list = [{"args" : "-o bind", "src" : "/dev", "dst" : "dev"},
                           {"args" : "-t proc", "src" : "/proc", "dst" : "proc"}]

        if os.environ.has_key("SUDO_USER"):
            default_user = os.environ["SUDO_USER"]
        else:
            default_user = os.environ["USER"]

        # initialization of the option parser
        usage = "usage: %prog [options] [COMMAND] \n" \
                "where COMMAND is a command to execute within chroot"
        self.parser.set_usage(usage)
        self.parser.set_defaults(user = default_user, prompt = "debian_chroot",
                                 imagetype = "meshnode")

        self.parser.add_option("-i", "--imagetype", metavar = "TYPE",
                               action = "store", dest = "imagetype",
                               help = "set the imagetype for chroot [default: %default]")
        self.parser.add_option("-p", "--prompt", metavar = "VAR",
                               action = "store", dest = "prompt",
                               help = "set variable identifying the chroot " \
                                      "(used in the prompt) [default: %default]")
        self.parser.add_option("-u", "--user", metavar = "NAME",
                               action = "store", dest = "user",
                               help = "set the user to be in the chroot [default: %default]")


    def set_option(self):
        """Set the options for the Chroot object"""

        Application.set_option(self)

        # set arguments
        if len(self.args) > 0:
            self.command = self.args[0]
            for arg in self.args[1:]:
                self.command = "%s%s" %(self.command, arg)


    def run(self):
        """Chroot and execute the command"""

        # must be root
        requireroot()

        # create a new image object   
        try:
            image = Image(self.options.imagetype)  
        except ImageException, exception:
            error(exception.msg)
            sys.exit(1)
        
        info("Imagetype: %s" %image.gettype())
        
        # get all mount points
        mtab = execute(self.mount, shell = True)[0]
        mtab = mtab.split('\n')

        # mount
        for mount in self.mount_list:
            mount_args = mount["args"]
            mount_src  = mount["src"]
            mount_dst  = os.path.join(image.getimagepath(), mount["dst"])
                       
            # check if directory is already mounted  
            regex = re.compile(mount_dst)
            for line in mtab:
                result = regex.search(line)
                if result:
                    break
            
            if not result:
                cmd = "%s %s %s %s" % (self.mount, mount_args, mount_src, mount_dst)
                info(cmd)
                call(cmd, shell = True)
        
        # build chroot command
        cmd = "%s %s %s %s -c 'export %s=%s && %s'" \
              %(self.chroot, image.getimagepath(), self.su, self.options.user, \
                self.options.prompt, image.gettype(), self.command)

        # on a 64bit linux machine, we need the 32bit userland wrapper
        if os.uname()[4] == "x86_64":
            cmd = "%s %s " %(self.linux32, cmd)

        # execute command
        try:
            call(cmd, shell = True)
            
        except CommandFailed, exception:
            error(exception)
        
        for mount in self.mount_list:
            mount_dst  = os.path.join(image.getimagepath(), mount["dst"])
            cmd = "%s %s" % (self.umount, mount_dst)
            info(cmd)
            call(cmd, shell = True)            


    def main(self):
        """Main method of the Chroot object"""

        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    Chroot().main()
