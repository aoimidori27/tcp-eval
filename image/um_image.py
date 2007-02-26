#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os, os.path, dircache
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_config import *
from um_functions import *


class Image(Application):
    "Class to manage/update the images"


    def __init__(self):
        "Constructor of the object"

        Application.__init__(self);
        
        # object variables
        self.commands = ('update', 'status')
        self.action = ''

        # initialization of the option parser
        usage = "usage: %prog [options] COMMAND \n" \
                "where  COMMAND := { status | update }"
        self.parser.set_usage(usage)
        self.parser.set_defaults(checkout = True, links = True)

        self.parser.add_option("-c", "--checkout",
                               action = "store_true", dest = "checkout",
                               help = "consider the checkout folder [default]")
        self.parser.add_option("-C", "--nocheckout",
                               action = "store_false", dest = "checkout",
                               help = "do not consider the checkout folder")
        self.parser.add_option("-l", "--links",
                               action = "store_true", dest = "links",
                               help = "consider links in /usr/local/[s]bin [default]")
        self.parser.add_option("-L", "--nolinks",
                               action = "store_false", dest = "links",
                               help = "do not consider links in /usr/local/[s]bin")


    def set_option(self):
        "Set options"

        Application.set_option(self);

        # correct numbers of arguments?
        if len(self.args) != 1:
            self.parser.error("incorrect number of arguments")

        # set arguments
        self.action = self.args[0]

        # does the command exists?
        if not self.action in self.commands:
            self.parser.error('unkown COMMAND %s' %(self.action))


    def update_checkout(self):
        "Update checkout within the images"

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


    def update_links(self):
        "Update symbolic links within the images"

        for image, imageinfo in imageinfos.iteritems():
            scriptmappings = imageinfo['scriptmappings']
            imagepath = "%s/%s" %(imageprefix, image)       
                
            # delete all links
            info("Delete every symbolic link whose contents %s" %(pattern))
            
            # hit every folder only once
            scriptfolders = sets.Set(scriptmappings.values())
            
            for dst in scriptfolders:
                dst = "%s%s" %(imagepath, dst)               
                cmd = "find %s -lname '%s/scripts/*' -print0 | "\
                      "xargs -r -0 rm -v" %(dst, svnprefix)
                try:
                    call(cmd, shell = True)
                except CommandFailed:
                    warn("Removing of links in %s failed" %(dst))
            
            # recreate all links
            info("Recreate symbolic links")
            
            for src, dst in scriptmappings.iteritems():
                nsrc = "%s%s%s" % (imagepath, svnprefix, src)
                ndst = "%s%s" %(imagepath, dst)
                
                for file in dircache.listdir(nsrc):
                    # ignore files which start with a .
                    if file.startswith("."):
                        continue
                    # cut off .sh and .py extensions
                    if file.endswith(".py"):
                        nfile = file.replace(".py","")
                    else:
                        nfile = file.replace(".sh","")                        
                    
                    cmd = "ln -vsf %s%s/%s %s/%s" %(svnprefix, src, file, ndst, nfile)
                    # use os.system because call() is too slow
                    os.system(cmd)


    def status_checkout(self):
        "Check the status of the checkout within the images"

        for image, imageinfo in imageinfos.iteritems():
            imagepath = "%s/%s" %(imageprefix, image)

            for src, dst in imageinfo['svnmappings'].iteritems():
                dst = "%s%s%s" %(imagepath, svnprefix, dst)
                cmd = ('svn', 'status', dst)
                info(cmd)
                prog = call(cmd, shell = False)


    def status_links(self):
        "Check the status of the symbolic links within the images"

        for image, imageinfo in imageinfos.iteritems():
            scriptmappings = imageinfo['scriptmappings']
            imagepath = "%s/%s" %(imageprefix, image)       

            for src, dst in scriptmappings.iteritems():
                nsrc = "%s%s%s" % (imagepath, svnprefix, src)
                ndst = "%s%s" %(imagepath, dst)
                
                for file in dircache.listdir(nsrc):
                    # ignore files which start with a .
                    if file.startswith("."):
                        continue
                    # cut off .sh and .py extensions
                    if file.endswith(".py"):
                        nfile = file.replace(".py","")
                    else:
                        nfile = file.replace(".sh","")                        
                    
                    if not os.path.islink("%s/%s" %(ndst, nfile))
                        info("No such symbolic link %s/%s" %(ndst, nfile))
                    

    def main(self):
        "Main method of image object"

        self.parse_option()
        self.set_option()

        # call the corresponding method
        if self.options.checkout:
            eval("self.%s_checkout()" %(self.action))        
        if self.options.links && self.action != ''
            eval("self.%s_links()" %(self.action)) 



if __name__ == '__main__':
    Image().main()
