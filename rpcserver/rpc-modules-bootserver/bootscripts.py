#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.web import xmlrpc, server
from twisted.internet import reactor, defer
from logging import info, debug, warn, error
import string
# umic-mesh imports
from um_twisted_meshdb import MeshDbPool
from um_twisted_functions import twisted_call
from um_application import Application


class Bootscripts(xmlrpc.XMLRPC):

	# name of the default profile

        def __init__(self, allowNone=False, parent=None):
            self.allowNone = allowNone      # for defers
            self.servicename = 'netboot'

            self.node_profile = "/opt/umic-mesh/boot/pxe/meshrouter/nodes"
            self.profile_folder_link = "../profiles"
            self.profile_folder = "/opt/umic-mesh/boot/pxe/meshrouter/profiles"
            self.profile_template = '/opt/umic-mesh/boot/pxe/meshrouter/profile.template'
             
            # default profile if no explicit profile is given for a node
            self.profile_default = "default"

            # create database connection pool
            self._dbpool = None
            try:
                self._dbpool = MeshDbPool(username='rpcserver',
                                          password='2PZrfjNXYNBxwru')
                info("Connection to Database established.")
            except Exception, inst:
                error("Failed to establish database connection: %s" % inst)
                exit(1)

        def linkProfileDone(self, ret):
            debug("twisted_call: %s" % ret)
            if (ret == 0):
                return 'Done.'
            else:
                return 'Failed.'

        def linkProfile(self, nodedat,  node):
            debug("Data from database: %s" % nodedat)
	    if nodedat:
          	flavorName = nodedat['flavorName']
	    else:
		flavorName = self.profile_default
  		debug("Node %s has no assigned profile using %s" %(node, flavorName))
            
	    ret = twisted_call(["ln", "-s", "-f", 
                                "%s/%s" %(self.profile_folder_link, flavorName),
                                "%s/%s" %(self.node_profile, node)], shell=False)

            return ret.addCallback(self.linkProfileDone)

        def writeProfile(self, profile, kernel, initrd, image, optarg, version):
            debug("Writing profile %s" % profile)
            template = open(self.profile_template,'r')
            str_dat = template.read()
            template.close()
            str_dat = str_dat.replace("@NAME@", profile)
            str_dat = str_dat.replace("@KERNEL@", kernel)
            str_dat = str_dat.replace("@INITRD@", initrd)
            str_dat = str_dat.replace("@IMAGE@", image)
            str_dat = str_dat.replace("@OPT_ARGS@", optarg)
            str_dat = str_dat.replace("@VERSION@", str(version))
            file = open("%s/%s" % (self.profile_folder, profile), "w")
            file.write(str_dat)
            file.close()
            return 'Updated %s' % profile

        def hasData(self, d, flavorName):
            debug("hasData: %s" % d)
            if (d != {}):       # if the query-result d is empty there is no such profile in the database
                return self.writeProfile(d['profile'], d['kernel'], d['initrd'], d['image'], d['opt_args'], d['version'])
            else:
                return 'No such profile: %s' % flavorName

        def getProfile(self, flavorName):
            # get the data of the profile
            profid = self._dbpool.getNetbootProfile(self.servicename, flavorName)
            return profid.addCallback(self.hasData, flavorName)

        @defer.inlineCallbacks 
        def writeAllProfiles(self, profiles):
            for profile in profiles:
                yield self.getProfile(profile['flavorName'])
            defer.returnValue("Updated "+",".join(map(lambda p: p['flavorName'], profiles)))

        # update node link -> link /opt/umic-mesh/boot/pxe/meshrouter/nodes/mrouter$$ to ../profiles/$$PROFILE$$
        def xmlrpc_updateNodelink(self, node):
            debug("updateNodelink(%s)" %node)
            nodedat = self._dbpool.getCurrentServiceConfig(self.servicename, node)
            return nodedat.addCallback(self.linkProfile, node)

        # update profile -> gets data out of the database and writes it to /opt/umic-mesh/boot/pxe/meshrouter/nodes/profiles/$$PROFILE$$
        def xmlrpc_updateProfile(self, profile):
            return self.getProfile(profile)

        # update all profiles 
        def xmlrpc_updateAllProfiles(self):
            profnames = self._dbpool.getNetbootProfileNames(self.servicename)
            return profnames.addCallback(self.writeAllProfiles)

class BootscriptsApp(Application):
        def __init__(self):
            "Constructor of the object"
            self._restart = True
            Application.__init__(self)

        def main(self):
            "Main method of the Bootscripts Application"

            self.parse_option()
            self.set_option()

            r = Bootscripts()
            reactor.listenTCP(8009, server.Site(r))
            reactor.run()


if __name__ == '__main__':
    BootscriptsApp().main()

