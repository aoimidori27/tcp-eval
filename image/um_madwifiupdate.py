#!/usr/bin/env python
# -*- coding: utf-8 -*

# python imports
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import *


class MadwifiUpdate(Application):
    "Class to handle update madwifi files in repos"

    def __init__(self):
        "Constructor of the object"

        Application.__init__(self)


    def set_option(self):
        "Set options"

        Application.set_option(self)


    def madwifiupdate(self):
        "Update Madwifi-ng source"

        # create temporary directory
        tmp   = "/tmp/madwifiupdate"
        dst   = "%s/upstream" %(tmp)
        trunk = "%s/trunk" %(tmp)
        cmd   = "mkdir -p %s" %(tmp)
        call(cmd, shell = True)

        remote_repos   = madwifiinfos["remote_repos"]
        remote_module  = madwifiinfos["remote_module"]
        remote_tag     = madwifiinfos["remote_tag"]
        local_repos    = svnrepos
        local_upstream = madwifiinfos["local_upstream"]
        local_trunk    = madwifiinfos["local_trunk"]

        # check out upstream files
        info("Checking out madwifi local upstream...")
        cmd = ("svn", "co", "-q", "%s%s" %(local_repos, local_upstream), dst)
        call(cmd, shell = False)

        # get revision
        cmd = "svn info %s | grep Revision | awk '{print $2;}'" %(dst)
        (stdout, stderr) = execute(cmd, shell = True)
        local_revision = stdout.splitlines()[0]
        info("Revision of checkout is: %s" %(local_revision))

        # clean up upstream
        info("Cleaning up upstream checkouts...")
        cmd = "find %s ! -path '*.svn*' -type f | xargs rm -f" %(dst)
        call(cmd, shell = True)

        # check out trunk from remote repos
        info("Checking out madwifi trunk from remote...")
        save_path = os.getcwd()
        os.chdir(tmp)
        cmd = ("svn","export","--force","-q", "%s%s/%s" %(remote_repos, remote_module, remote_tag), dst)
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
        cmd = ("svn", "ci", dst, "-m","new madwifi version (tag: %s)" %remote_tag)
        call(cmd, shell = False)

        # switch upstream to trunk
        info("Switching local checkout to trunk...")
        cmd = ("svn", "switch", "%s/%s" %(local_repos, local_trunk), dst)
        call(cmd, shell = False)

        # just for completeness rename it
        cmd = "mv %s %s" %(dst, trunk)
        call(cmd, shell = True)

        # merging changes from upstream local trunk
        info("Merging changes with local trunk...")
        cmd = ("svn","merge","-r","%s:HEAD" %(local_revision),
               "%s/%s" %(local_repos, local_upstream), trunk)
        call(cmd, shell = False)

        # commiting changes to local trunk
        info("Commiting these changes to repository...")
        cmd = ("svn","commit", trunk, "-m","merging new madwifi version (tag: %s)" %remote_tag)
        call(cmd, shell = False)

        # cleanup
        info("Cleaning up %s..." %(tmp))
        cmd = "rm -rf %s" %(tmp)
        call(cmd, shell = True)

        info("Done.")


    def main(self):
        "Main method of the MadwifiUpdate object"
        
        self.parse_option()
        self.set_option()
        self.madwifiupdate()



if __name__ == "__main__":
    MadwifiUpdate().main()
