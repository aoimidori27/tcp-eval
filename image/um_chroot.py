#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import *
from um_node import *


class Chroot(Application):
    "Class to chroot into the images"

    def __init__(self):
        "Constructor of the object"

        Application.__init__(self)

        # object variables
        self.command = "/bin/bash"

        if os.environ.has_key('SUDO_USER'):
            default_user = os.environ['SUDO_USER']
        else:
            default_user = os.environ['USER']

        # initialization of the option parser
        usage = "usage: %prog [options] [COMMAND] \n" \
                "where  COMMAND is a command to execute within chroot"
        self.parser.set_usage(usage)
        self.parser.set_defaults(user = default_user, nodetype = 'meshrouter')

        self.parser.add_option("-u", "--user", metavar = "NAME",
                               action = "store", dest = "user",
                               help = "set the user to be in the chroot [default: %default]")
        self.parser.add_option("-n", "--nodetype", metavar = "TYPE",
                               action = "store", dest = "nodetype",
                               help = "set the node type for chroot [default: %default]")

    def set_option(self):
        "Set options"

        Application.set_option(self)

        # set arguments
        if len(self.args) > 0:
            self.command = self.args[0]
            for arg in self.args[1:]:
                self.command = "%s%s" %(self.command, arg)


    def chroot_exec(self):
        "Chroot and execute the command"

        # must be root
        requireroot()

        # for chroot, imagetype and nodetype are required
        node      = Node(type = self.options.nodetype)
        nodetype  = node.type()
        imageinfo = node.imageinfo()
        imagepath = node.imagepath()

        info("Nodetype: %s" %(nodetype))

        # common mounts for all chroots
        mounts = [ {'args' : '-o bind', 'src' : '/dev', 'dst' : '/dev'},
                   {'args' : '-o bind', 'src' : '/proc', 'dst' : '/proc'} ]

        # mount
        for mountpoint in mounts:
            # check if directory is already mounted
            cmd = ('grep','%s%s'  % (imagepath, mountpoint['dst']), '/etc/mtab')
            rc = subprocess.call(cmd)
            if rc != 0:
                cmd = "mount %s %s %s%s" % (mountpoint['args'], mountpoint['src'],
                                            imagepath, mountpoint['dst'])
                print cmd
                execute(cmd, shell = True)

        # exec command
        cmd = "/usr/bin/linux32 /usr/sbin/chroot %s su %s -c " \
              "'export debian_chroot=%s && %s'" \
              % (imagepath, self.options.user, nodetype, self.command)
        call(cmd, shell = True)

        # umount
        for mountpoint in mounts:
            cmd = "umount %s%s" %(imagepath, mountpoint['dst'])
            call(cmd, shell = True, raiseError = False)


    def main(self):
        "Main method of the chroot object"

        self.parse_option()
        self.set_option()
        self.chroot_exec()



if __name__ == "__main__":
    Chroot().main()
