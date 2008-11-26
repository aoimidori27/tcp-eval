#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.web import xmlrpc, server
from twisted.internet import reactor
from logging import info, debug, warn, error
import string
# umic-mesh imports
from um_twisted_meshdb import MeshDbPool
from um_twisted_functions import twisted_call
from um_application import Application


class Bootscripts(xmlrpc.XMLRPC):

        node_profile = "/opt/umic-mesh/boot/pxe/meshrouter/nodes"
        profile_folder_link = "../profile"
        profile_folder = "/opt/umic-mesh/boot/pxe/meshrouter/profiles"
        profile_template = '/opt/umic-mesh/boot/pxe/meshrouter/profile.template'

        def __init__(self, allowNone=False):
            self.allowNone = allowNone      # for defers
            self.servicename = 'netboot'

            self.node_profile = "/opt/umic-mesh/boot/pxe/meshrouter/nodes"
            self.profile_folder_link = "../profile"
            self.profile_folder = "/opt/umic-mesh/boot/pxe/meshrouter/profiles"
            self.profile_template = '/opt/umic-mesh/boot/pxe/meshrouter/profile.template'

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

        def linkProfile(self, nodedat):
            debug("Data from database: %s" % nodedat)
            if (nodedat != {}):
                ret = twisted_call("ln -s -f %s/%s %s/%s" % (self.profile_folder_link, nodedat['flavorName'], self.node_profile, self.node))
                return ret.addCallback(self.linkProfileDone)
            else:
                return 'No such node: %s' % self.node

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

        def hasData(self, d):
            debug("hasData: %s" % d)
            if (d != {}):       # if the query-result d is empty there is no such profile in the database
                return self.writeProfile(d['profile'], d['kernel'], d['initrd'], d['image'], d['opt_args'], d['version'])
            else:
                return 'No such profile: %s' % self.p

        def getProfile(self, profile):
            # get the data of the profile
            profid = self._dbpool.getNetbootProfile(self.servicename, profile)
            return profid.addCallback(self.hasData)

        def writeAllProfiles(self, d):
            debug("Data: %s" % d)
            str_done = "Updated "
            for prof in d:
                #print prof
                str_done += prof['flavorName'] + ", "
                self.getProfile(prof['flavorName'])
            return str_done


        # update node link -> link /opt/umic-mesh/boot/pxe/meshrouter/nodes/mrouter$$ to ../profiles/$$PROFILE$$
        def xmlrpc_updateNodelink(self, node):
            self.node = node
            nodedat = self._dbpool.getCurrentServiceConfig(self.servicename, node)
            return nodedat.addCallback(self.linkProfile)

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

