#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:softtabstop=4:shiftwidth=4:expandtab

# Script to update subversion repos with a recent madwifi release.
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

class MadwifiUpdate(Application):
    """Class to handle update madwifi files in repos"""

    def __init__(self):
        """Constructor of the object"""

        Application.__init__(self)

        usage = "usage: %prog [OPTIONS]"
        self.parser.set_usage(usage)

        self.parser.set_defaults(usertmp = "tmp/madwifiupdate")
        self.parser.add_option("-p", "--tmp",
                               action = "store", dest = "usertmp",
                               help = "Set the temporary dir")
        self.parser.set_defaults(repos="http://svn.madwifi.org/madwifi/trunk")
        self.parser.add_option("-r", "--repos",
                               action = "store", dest = "repos",
                               help = "Set the repository to download from")

    def set_option(self):
        """Set options"""
        Application.set_option(self)

    def madwifiupdate(self):
        """Update Madwifi-ng source"""

        # create temporary directory
        tmp   = self.options.usertmp
        dst   = "%s/upstream" %(tmp)
        cmd   = "mkdir -p %s" %(tmp)
        call(cmd, shell = True)

        remote_repos   = self.options.repos
        local_repos    = "svn+ssh://svn.umic-mesh.net/umic-mesh"
        local_upstream = "drivers/madwifi-ng/trunk"

        # check out upstream files
        info("Checking out madwifi local upstream...")
        cmd = ("svn", "co", "%s/%s" %(local_repos, local_upstream), dst)
        call(cmd, shell = False)

        # check out trunk from remote repos
        info("Checking out madwifi trunk from remote...")
        save_path = os.getcwd()
        os.chdir(tmp)
        cmd = ("svn","export","--force", "%s" % remote_repos, dst)
        call(cmd, shell = False)
        os.chdir(save_path)

        info("Searching updated files...")

        # add new files
        cmd = "echo `svn st %s | grep '?' | awk '{ print $2; }'`" %(dst)
        (stdout,stderr) = execute(cmd, shell = True)
        debug("Stdout: %s" %stdout)
        if (stdout != "\n"):
            info("Found new files. Adding them...")
            cmd = "svn add %s" %(stdout)
            info("CMD: %s" %cmd)
            call(cmd, shell = True)

        # remove files, which were removed in upstream
        cmd = "echo `svn st %s | grep '!' | awk '{ print $2; }'`" %(dst)
        (stdout,stderr) = execute(cmd, shell = True)
        debug("Stdout: %s" %stdout)
        if (stdout != "\n"):
            info("Found removed files. Deleting them...")
            cmd = "svn rm %s" %(stdout)
            call(cmd, shell = True)

        # commit changes
        info("Commiting changes...")
        cmd = ("svn", "ci", dst, "-m","madwifi: update trunk")
        call(cmd, shell = False)

        # cleanup
        info("Cleaning up %s..." %(tmp))
        cmd = "rm -rf %s" %(tmp)
        call(cmd, shell = True)

        info("Done.")

    def main(self):
        """Main method of the MadwifiUpdate object"""

        self.parse_option()
        self.set_option()
        self.madwifiupdate()


if __name__ == "__main__":
    MadwifiUpdate().main()

