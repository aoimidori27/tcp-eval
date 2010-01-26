#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import os
from logging import info, debug, warn, error, critical
from tempfile import mkstemp

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

# umic-mesh imports
from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call

class Sysctl(RPCService):
    """Class for managing the settings of kernel variables"""

    #
    # Public XMLRPC Interface
    #

    @defer.inlineCallbacks
    def xmlrpc_restart(self):
        rc = yield self.reread_config()
        if rc == 0:
            rc = yield self.start()
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_start(self):
        rc = yield self.reread_config()
        if rc == 0:
            rc = yield self.start()
        defer.returnValue(rc)

    def xmlrpc_stop(self):
        """Not yet implemented."""
        return self.stop()

    @defer.inlineCallbacks
    def xmlrpc_isAlive(self):
        """Not yet implemented."""
        defer.returnValue(True)

    #
    # Internal stuff
    #

    def __init__(self, parent = None):
        # Call super constructor
        RPCService.__init__(self, parent)

        # name of this service in the database
        self._name = "sysctl"
        self._configfile = None
        self._configs = None

    @defer.inlineCallbacks
    def reread_config(self):
        """Rereads the configuration

           The sysctl service table has the following important columns
                config : see sysctl.conf(5)
           Will return 0 on success.
        """

        list_of_assoc = yield self._parent._dbpool.getCurrentServiceConfigMany(self._name)
        if not list_of_assoc:
            info("Found no configuration")
            defer.returnValue(-1)

        self._configs = list_of_assoc

        if self._configfile and os.path.exists(self._configfile):
            tempfile = file(self._configfile, 'w')
        else:
            # create new tempfile
            (temp_fd, self._configfile) = mkstemp(".conf", self._name)
            info("Created new configfile: %s", self._configfile)
            tempfile = os.fdopen(temp_fd, 'w')

        for row in list_of_assoc:
            tempfile.write("# values loaded from %s\n" %row['flavorName'])
            tempfile.write(row['config'])
            tempfile.write("\n")
        tempfile.close()

        defer.returnValue(0)

    @defer.inlineCallbacks
    def start(self):
        """This function invokes sysctl(8) to configure kernel parameters"""

        cmd = [ "/sbin/sysctl","-p", self._configfile ]
        (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
        if len(stdout):
            debug(stdout)
        if (rc != 0):
            error("sysctl.start(): Command failed with RC=%s", rc)
            for line in stderr.splitlines():
                error(" %s" %line)


        for config in self._configs:
            # ignore already started configs
            yield self._parent._dbpool.startedService(config,
                                                      rc, message=stderr, ignoreDups=True)
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def stop(self):
        """ This function does nothing. """

        for config in self._configs:
            yield self._parent._dbpool.stoppedService(config,
                                                      0, message="")
        defer.returnValue(0)
