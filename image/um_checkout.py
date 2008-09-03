#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import os
import os.path
import sets
import dircache
from logging import info, debug, warn, error

# umic-mesh imports
from um_application import Application
from um_functions import *
from um_image import Image

class Checkout(Application):
    "Class to update the checkout"


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
            self.parser.error("Incorrect number of arguments")

        # set arguments
        self.action = self.args[0]

        # does the command exists?
        if not self.action in self.commands:
            self.parser.error('Unkown COMMAND %s' %(self.action))


    def update_checkout(self):
        "Update checkout within the images"

        # allow group to write and exec files
        os.umask(0002)

        for imagetype in Image.types():
            image = Image(imagetype)
            
            svnmappings = image.getSvnMappings()
            imagepath = image.getImagePath()
            svnprefix = Image.svnPrefix()
            svnrepos  = Image.repositoryUrl()

            info("Update checkout within the image: %s" %(imagepath))

            for src, dst in svnmappings.iteritems():
                dst = "%s%s/%s" %(imagepath, svnprefix, dst)
                src = "%s%s" %(svnrepos, src)
                
                if not os.path.exists(dst):
                    info("svn checkout %s %s" %(src, dst))
                    call("mkdir -p %s" %(dst), shell = True)
                    cmd = ('svn', 'checkout', src, dst)
                else:
                    info("svn update %s" %(dst))
                    cmd = ('svn', 'update', dst)
                
                call(cmd, shell = False)


    def update_links(self):
        "Update symbolic links within the images"

        # allow group to write and exec files
        os.umask(0002)

        for imagetype in Image.types():
            image = Image(imagetype)
            
            scriptmappings = image.getScriptMappings()
            imagepath = image.getImagePath()
            svnprefix = Image.svnPrefix()
            pattern = "%s/scripts/*" %(svnprefix)       

            info("Update symbolic links within the image: %s" %(imagepath)) 
            
            # delete all links
            for dst in sets.Set(scriptmappings.values()):
                dst = "%s%s" %(imagepath, dst)               
                cmd = "find %s -lname '%s' -print0 | "\
                      "xargs -r -0 rm" %(dst, pattern)
                try:
                    call(cmd, shell = True)
                except CommandFailed:
                    warn("Removing of links in %s failed" %(dst))
            
            # recreate all links
            for src, dst in scriptmappings.iteritems():
                nsrc = "%s%s/%s" % (imagepath, svnprefix, src)
                dst = "%s%s" %(imagepath, dst)
                
                for file in dircache.listdir(nsrc):
                    # ignore files which start with a .
                    if file.startswith("."):
                        continue

                    # split filename and file extension
                    (file, ext) = os.path.splitext(file)

                    origfile = "%s/%s/%s%s" %(svnprefix, src, file, ext)
                    linksrc  = "%s/%s" %(dst, file)

                    try:
                        os.symlink(origfile, linksrc)
                    except OSError:
                        warn("Recreating of the link %s failed" %(origfile))


    def status_checkout(self):
        "Check the status of the checkout within the images"

        for imagetype in Image.types():
            image = Image(imagetype)
            
            svnmappings = image.getSvnMappings()
            imagepath = image.getImagePath()
            svnprefix = Image.svnPrefix()

            info("Check the status of the checkout within the images: %s" %(imagepath))
            
            for src, dst in svnmappings.iteritems():
                dst = "%s%s/%s" %(imagepath, Image.svnPrefix(), dst)
                if not os.path.exists(dst):
                    warn("%s is missing" %dst)
                    continue
                cmd = ('svn', 'status', dst)
                info("svn status %s" %(dst))
                call(cmd, shell = False)
        

    def status_links(self):
        "Check the symbolic links within the images"
        for imagetype in Image.types():
            image = Image(imagetype)
            
            scriptmappings = image.getScriptMappings()
            imagepath = image.getImagePath()
            svnprefix = Image.svnPrefix()

            info("Check the symbolic links within the image: %s" %(imagepath))
            
            for src, dst in scriptmappings.iteritems():
                nsrc = "%s%s/%s" % (imagepath, svnprefix, src)
                dst = "%s%s" %(imagepath, dst)
               
                for file in dircache.listdir(nsrc):
                    # ignore files which start with a .
                    if file.startswith("."):
                        continue

                    # split filename and file extension
                    (file, ext) = os.path.splitext(file)

                    origfile = "%s/%s/%s%s" %(svnprefix, src, file, ext)
                    linksrc  = "%s/%s" %(dst, file)
                    linkdst  = os.path.realpath(linksrc)
                   
                    if not os.path.lexists(linksrc):
                        warn("Missing symbolic link %s -> %s" %(linksrc, origfile))
                    elif not origfile == linkdst:
                        warn("Broken symbolic link %s -> %s" %(linksrc, os.readlink(linksrc)))
                    

    def main(self):
        "Main method of image object"

	requireNOroot()

        self.parse_option()
        self.set_option()

        # call the corresponding method
        if self.options.checkout:
            eval("self.%s_checkout()" %(self.action))
        if self.options.links:
            eval("self.%s_links()" %(self.action)) 



if __name__ == '__main__':
    Checkout().main()
