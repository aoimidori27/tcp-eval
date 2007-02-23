#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import dircache, copy, sets

# umic-mesh imports
from um_application import Application
from um_config import *
from um_functions import *


class Subversion(Application):
    "Class to manage Subvserions repositories within the images"


    def __init__(self):
        "Constructor of the object"

        Application.__init__(self);

        # initialization of the option parser
        usage = "usage: %prog [options] COMMAND \n" \
                "where  COMMAND := { status | update }"
        self.parser.set_usage(usage)
        self.parser.set_defaults(updatelinks = True)
        
        self.parser.add_option("-l", "--links",
                               action = "store_false", dest = "updatelinks",
                               help = "update symlinks in /usr/local/[s]bin [default: %default]")


    def set_option(self):
        "Set options"

        Application.set_option(self);

        # correct numbers of arguments?
        if len(self.args) != 1:
            self.parser.error("incorrect number of arguments")

        # set arguments
        self.action = self.args[0]

        # does the command exists?
        if not self.action in ('update', 'status'):
            self.parser.error('unkown COMMAND %s' %(self.action))


    def update(self):
        "Subversion update"

        # allow group mates to write and exec files
        os.umask(0002)
        for image, imageinfo in imageinfos.iteritems():
            svnmappings = imageinfo['svnmappings']
            imagepath = "%s/%s" %(imageprefix, image)

            # iterate through svn mappings
            for src, dst in svnmappings.iteritems():
                dst = "%s%s%s" %(imagepath, svnprefix, dst)
                src = "%s%s" %(svnrepos, src)
                if not os.path.exists(dst):
                    warn("%s got lost! doing a new checkout" %(dst))
                    call("mkdir -p %s" % dst, shell = True)
                    cmd = ('svn', 'checkout', src, dst)
                else:
                    cmd = ('svn', 'update', dst)
                info(cmd)
                prog = call(cmd, shell = False)

            # update links
            if self.options.updatelinks:
                scriptmappings = imageinfo['scriptmappings']
                pattern = "%s/scripts/*" %(svnprefix)
                
                # delete all links
                info("Delete every symbolic link whose contents %s" %(pattern))
                
                # hit every folder only once
                scriptfolders = sets.Set(scriptmappings.values())
                
                for dst in scriptfolders:
                    dst = "%s%s" %(imagepath, dst)               
                    cmd = "find %s -lname '%s/scripts/*' -print0 | xargs -r -0 rm -v " %(dst, svnprefix)
                    try:
                        call(cmd,shell=True)
                    except CommandFailed:
                        warn("Removing of links in %s failed" %(dst))
                
                # recreate all links
                info("Recreate symbolic links")
                
                for src, dst in scriptmappings.iteritems():
                    nsrc = "%s%s%s" % (imagepath, svnprefix, src)
                    ndst = "%s%s" %(imagepath, dst)
                    for f in dircache.listdir(nsrc):
                        # ignore files which start with a .
                        if f.startswith("."):
                            continue
                        # cut off .sh and .py extensions
                        fn=f.replace(".py","")
                        fn=f.replace(".sh","")                        
                        cmd = "ln -vsf %s%s/%s %s/%s" %(svnprefix,src, f, ndst, fn)
                        # use os.system because call() is too slow
                        os.system(cmd)
                    

    def status(self):
        "Subversion status"

        for image,imageinfo in imageinfos.iteritems():
            imagepath = "%s/%s" %(imageprefix, image)

            for src, dst in imageinfo['svnmappings'].iteritems():
                dst = "%s%s%s" %(imagepath, svnprefix, dst)
                cmd = ('svn', 'status', dst)
                info(cmd)
                prog = call(cmd, shell = False)


    def main(self):
        "Main method of subversion object"

        self.parse_option()
        self.set_option()

        # call the corresponding method
        eval("self.%s()" %(self.action))



if __name__ == '__main__':
    Subversion().main()

