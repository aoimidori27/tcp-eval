#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# Script to update subversion repos with a recent kernel release.
#
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

# python imports
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import *
from um_config import *

class KernelUpdate(Application):
    """Class to handle kernel source update within images"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        usage = "usage: %prog -k <kernelversion> [OPTIONS]"
        self.parser.set_usage(usage)

        self.parser.set_defaults(mirror="http://sunsite.informatik.rwth-aachen.de/ftp/pub/Linux/kernel/v2.6", usertmp="/tmp/kernelupdate")
        self.parser.add_option("-p", "--tmp",
                               action = "store", dest = "usertmp",
                               help = "Set the temporary dir")
        self.parser.add_option("-k", "--kernelversion",
                               action = "store", dest = "kernelversion",
                               help = "Set the kernel version to download")
        self.parser.add_option("-m", "--mirror",
                               action = "store", dest = "mirror",
                               help = "Set the mirror to download from (default: %default)")

    def set_option(self):
        """Set options"""
        Application.set_option(self)


    def kernelupdate(self):
        """Update Kernel source"""

        # set parameter
        kernelinfos = dict()
        kernelinfos["mirror"] = self.options.mirror
        kernelinfos["version"] = self.options.kernelversion
        svninfos = dict()
        svninfos["svnrepos"] = "svn+ssh://svn.umic-mesh.net/umic-mesh"

        # create temp dir
        kernel = "linux-%s" %(kernelinfos["version"])
        tmp = self.options.usertmp
        dst = "%s/%s" %(tmp, kernel)
        cmd = "mkdir -p %s" %(dst)
        execute(cmd, shell = True)

        # check out trunk files
        info("Check out kernel trunk")
        cmd = ("svn",  "checkout", "%s/linux/vanilla/trunk" \
              %(svninfos["svnrepos"]), dst)
        info(cmd)
        call(cmd, shell = False)

        # download kernel image and extract
        cmd = "wget %s/%s.tar.gz -O - | tar xz -C %s" \
              %(kernelinfos["mirror"], kernel, tmp)
        info(cmd)
        call(cmd, shell = True)

        # add new files
        cmd = "echo `svn st %s | grep '?' | awk '{ print $2; }'`" %(dst)
        (stdout,stderr) = execute(cmd, shell = True)
        debug("Stdout: %s" %stdout)
        if (stdout != "\n"):
            info("Found new files. Adding them...")
            cmd = "svn add %s" %(stdout)
            call(cmd, shell = True)

        # remove files, which were removed in upstream
        cmd = "echo `svn st %s | grep '!' | awk '{ print $2; }'`" %(dst)
        (stdout, stderr) = execute(cmd, shell = True)
        debug("Stdout: %s" %stdout)
        if (stdout != "\n"):
            info("Found removed files. Deleting them...")
            cmd = "svn rm %s" %(stdout)
            call(cmd, shell = True)

        # commit new versions of files to upstream repository
        cmd = ("svn", "commit", dst, "-m","linux: updated trunk to %s" %(kernelinfos["version"]))
        info(cmd)
        call(cmd, shell = False)

        # clean up
        info("Cleaning up %s..." %(tmp))
        cmd = "rm -rf %s" %(tmp)
        execute(cmd, shell = True)
        info("Done.")


    def main(self):
        """Main method of the kernelupdate object"""

        self.parse_option()
        self.set_option()
        self.kernelupdate()


if __name__ == "__main__":
    KernelUpdate().main()

