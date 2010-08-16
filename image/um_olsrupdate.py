#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# Script to update subversion repos with a recent olsr release.
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

class OlsrUpdate(Application):
    """Class to handle update of olsr files in the local svn repos"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        usage = "usage: %prog -o <olsrversion> [OPTIONS]"
        self.parser.set_usage(usage)

        self.parser.set_defaults(usertmp = "/tmp/olsrupdate")
        self.parser.add_option("-p", "--tmp",
                               action = "store", dest = "usertmp",
                               help = "Set the temporary dir")
        self.parser.set_defaults(mirror="http://www.olsr.org/releases/0.5")
        self.parser.add_option("-o", "--olsrversion",
                               action = "store", dest = "olsrversion",
                               help = "Set the OLSR version to download")
        self.parser.add_option("-m", "--mirror",
                               action = "store", dest = "mirror",
                               help = "Set mirror to download from (default: %default)")

    def set_option(self):
        """Set options"""
        Application.set_option(self)

    def olsrupdate(self):
        """Update OLSR source"""

        # create temporary directory
        tmp   = self.options.usertmp
        dst   = "%s/olsrd-%s" %(tmp, self.options.olsrversion)
        cmd   = "mkdir -p %s" %(dst)
        call(cmd, shell = True)

        remote_repos   = self.options.mirror
        remote_version = self.options.olsrversion
        local_repos    = "svn+ssh://svn.umic-mesh.net/umic-mesh"
        local_upstream = "routing/olsr/trunk"

        # check out trunk files
        info("Checking out olsr local upstream...")
        cmd = ("svn", "co", "%s/%s" %(local_repos, local_upstream), dst)
        debug(cmd)
        call(cmd, shell = False)

        # get new version from olsrd-page
        info("Getting OLSR %s from %s..." %(remote_version, remote_repos) )
        cmd = "wget %s/olsrd-%s.tar.gz -O - | tar xz -C %s" \
              %(remote_repos, remote_version, tmp)
        debug(cmd)
        call(cmd, shell = True)

        info("Searching updated files...")

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

        # commit changes
        info("Commiting changes...")
        cmd = ("svn", "ci", dst, "-m", "olsr: updated olsr trunk to olsrd %s release" %remote_version)
        call(cmd, shell = False)

        # cleanup
        info("Cleaning up %s..." %(tmp))
        cmd = "rm -rf %s" %(tmp)
        call(cmd, shell = True)

        info("Done.")

    def main(self):
        """Main method of the OlsrUpdate object"""

        self.parse_option()
        self.set_option()
        self.olsrupdate()


if __name__ == "__main__":
    OlsrUpdate().main()

