#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.web import xmlrpc, server
from twisted.internet import reactor
from logging import info, debug, warn, error
import string
# umic-mesh imports
from um_twisted_meshdb import MeshDbPool
from um_functions import call


class Bootscripts(xmlrpc.XMLRPC):

        def __init__(self, allowNone=False):
            self.allowNone = allowNone      # for defers

            # create database connection pool
            self._dbpool = None
            try:
                self._dbpool = MeshDbPool(username='rpcserver',
                                          password='2PZrfjNXYNBxwru')
                print "Connection to Database established."
            except Exception, inst:
                error("Failed to establish database connection: %s" % inst)
                exit(1)

        def linkProfile(self, nodedat):
            if (nodedat != {}):
                    ret = call("ln -s -f ../profile/%s /opt/umic-mesh/boot/pxe/meshrouter/nodes/%s-ttest" % (nodedat['flavorName'], self.p))
                    if (ret != 0):
                        return 'Done.'
                    else:
                        return 'Failed.'
            else:
                return 'No such node: %s' % self.p

        def writeProfile(self, profile=None, kernel=None, initrd=None, image=None):
            str_dat = """SERIAL 0 38400

SAY --------------------------------------------------------------------------------
SAY --------------------------------- MESH ROUTER ----------------------------------
SAY --------------------------------------------------------------------------------
SAY ------------- LOADING KERNEL ---------------------------------------------------

DEFAULT ubuntu
PROMPT 1
TIMEOUT 50

LABEL ubuntu
KERNEL %s
APPEND id=default image=meshnode/%s nodetype=meshrouter rw root=/dev/ram0 reboot=c,b console=ttyS0,38400n8 initrd=%s init=/linuxrc

LABEL memtest
KERNEL /linux/default/meshrouter-memtest.bin

LABEL freedos
KERNEL /linux/default/memdisk
APPEND initrd=/linux/default/freedos.img raw
""" % (kernel, image, initrd)
            file = open("/opt/umic-mesh/boot/pxe/meshrouter/profiles/%s-test" % profile, "w")
            file.write(str_dat)
            file.close()
            return 'Done.'

        def hasData(self, d):
            print d
            if (d != {}):       # if the query-result d is empty there is no such profile in the database
                return self.writeProfile(self.p, d['kernel'], d['initrd'], d['image'])
            else:
                return 'No such profile: %s' % self.p

        def getProfile(self, name):
            # get the data of the profile
            str_profid = "SELECT `flavorID` FROM `services_flavors` WHERE `flavorName`=\"%s\" AND `servID`=9" % name     # gets the flavor ID
            str_profdat = "SELECT `initrd`,`image`,`kernel` FROM `service_netboot` WHERE `flavorID`=( %s )" % str_profid
            print str_profdat
            profid = self._dbpool.fetchAssoc(str_profdat)
            return profid.addCallback(self.hasData)

        def writeAllProfiles(self, d):
            print d
            for prof in d:
                self.getProfile(prof['flavorName'])


        # node-profil ändern -> link /opt/umic-mesh/boot/pxe/meshrouter/nodes/mrouter$$ auf ../profiles/$$PROFILE$$ umbiegen
        def xmlrpc_node(self, p):
            self.p = p
            nodedat = self._dbpool.getCurrentServiceConfig('netboot', p)
            return nodedat.addCallback(self.linkProfile)

        # profil ändern -> auslesen des profils aus der datenbank, neu-schreiben der datei /opt/umic-mesh/boot/pxe/meshrouter/nodes/profiles/$$PROFILE$$
        def xmlrpc_profile(self, p):
            self.p = p
            return self.getProfile(p)

        # alle profile ändern -> auslesen aller profilnamen aus der datenbank, jedes profil neu-schreiben
        def xmlrpc_allprofiles(self):
            str_profnames = "SELECT `flavorName` FROM `services_flavors` WHERE `servID` = 9"    # 9 is netboot
            profnames = self._dbpool.fetchAssoc(str_profnames)
            profnames.addCallback(self.writeAllProfiles)
            return "Done."


if __name__ == '__main__':
    r = Bootscripts()
    reactor.listenTCP(8009, server.Site(r))
    reactor.run()

