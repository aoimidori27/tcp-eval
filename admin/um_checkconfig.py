#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
import os.path
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import *

class CheckConfig(Application):
    """Class to check the configuration of an installation"""

    def __init__(self):
        "Constructor of the object"

        Application.__init__(self);

        # object variables
        self.checked = list()

        # initialization of the option parser
        usage = "usage: %prog [options]\n"

        self.parser.set_usage(usage)
        self.parser.set_defaults(config_local = "/opt/checkout/config.local",
                                 config_common = "/opt/checkout/config.common",
                                 etc = "/etc/",
                                 update = False)

        self.parser.add_option("-l", "--local",
                               action = "store", dest = "config_local", metavar = "DIR",
                               help = "folder containing local configuration [%default]")
        self.parser.add_option("-c", "--common",
                               action = "store", dest = "config_common", metavar = "DIR",
                               help = "folder containing common configuration [%default]")
        self.parser.add_option("-e", "--etc",
                               action = "store", dest = "etc", metavar = "DIR",
                               help = "location of the etc folder [%default]")
        self.parser.add_option("-u", "--update",
                               action = "store_true", dest = "update",
                               help = "try to correct found errors [%default]")

    def set_option(self):
        """Set options"""
        Application.set_option(self);

    def check_against(self, config_dir):
        etc = self.options.etc

        for root, dirs, files in os.walk(config_dir):
            # don't visit subversion dirs
            if '.svn' in dirs:
                dirs.remove('.svn')
            rel_root=root[len(config_dir):].strip('/')
            for filename in files:
                abs_file=os.path.join(root, filename)
                rel_file=os.path.join(rel_root, filename)
                etc_file=os.path.join(etc, rel_file)
                # ignore files already checked
                if etc_file in self.checked:
                    continue
                else:
                    self.checked.append(etc_file)
                debug("Checking %s ..." %etc_file)
                if not os.path.exists(etc_file):
                    warn("File %s does not exists, but %s does." %(etc_file, abs_file))
                    if (self.options.update):
                        info("Create link %s pointing to %s ..." %(etc_file, abs_file))
                        os.symlink(abs_file, etc_file)
                    continue
                if not os.path.islink(etc_file):
                    warn("File %s is a regular file, but should be a link to %s" %(etc_file, abs_file))
                    if (self.options.update):
                        info("Overwrite file %s, now pointing to %s ..." %(etc_file, abs_file))
                        # try to be as atomic as possible by using ln with "force"
                        execute(['ln','-sf',abs_file, etc_file], shell=False)
                    continue
                link = os.readlink(etc_file)
                if not link == abs_file:
                    warn("File %s links to %s but should link to %s" %(etc_file, link, abs_file))
                    if (self.options.update):
                        info("Overwrite link %s, now pointing to %s ..." %(etc_file, abs_file))
                        # try to be as atomic as possible by using ln with "force"
                        execute(['ln','-sf',abs_file, etc_file], shell=False)

    def main(self):
        """Main method of image object"""

        try:
            # must be root
            requireroot()

        except CommandFailed, exception:
            error(exception)

        self.parse_option()
        self.set_option()

        # check local folder first because it has priority
        self.check_against(self.options.config_local)
        self.check_against(self.options.config_common)

if __name__ == '__main__':
    CheckConfig().main()

