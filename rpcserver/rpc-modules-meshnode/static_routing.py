#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import os
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

#umic-mesh imports
from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call

class Static_routing(RPCService):
    """Class for configuring static routing"""

    #
    # Public XMLRPC Interface
    #

    @defer.inlineCallbacks
    def xmlrpc_restart(self):
        rc = yield self.reread_config()

        if rc == 0:
            # don't complain if stopping doesnt work
            yield self.stop()
            rc = yield self.start()
        defer.returnValue(rc)

    @defer.inlineCallbacks
    def xmlrpc_start(self):
        rc = yield self.reread_config()
        if rc == 0:
            rc = yield self.start()
        defer.returnValue(rc)

    def xmlrpc_stop(self):
        return self.stop()

    def xmlrpc_isAlive(self):
        return True

    #
    # Internal stuff
    #

    def __init__(self, parent = None):
        # Call super constructor
        RPCService.__init__(self, parent)

        # servicename in database
        self._name = "static_routing"
        self._config = None

    @defer.inlineCallbacks
    def reread_config(self):
        """Rereads the configuration

           The static_routing service table has the following important columns
                  dest   : destination the server to log to
                  gw     : gateway
                  prefix : prefix
                  metric : routing metric
                  nic    : interface name

           Will return 0 on success.
        """

        assocList = yield self._parent._dbpool.getStaticRouting()
        if not assocList:
            info("Found no configuration")
            defer.returnValue(-1)

        self._config = assocList


        defer.returnValue(0)

    @defer.inlineCallbacks
    def start(self):
        """This function loads the routing entries module."""

        final_rc = 0

        for config in self._config:

            # iterate over routing entries
            errmsg = ""
            # first rc != 0 which happens
            tmp_rc  = 0
            for rentry in config["rentries"]:
                cmd = ["ip", "route", "add",
                       "%s/%s"   %(rentry["dest"], rentry["prefix"]),
                       "via",    rentry["gw"],
                       "dev",    rentry["nic"],
                       "metric", str(rentry["metric"])]
                if rentry["rt_table"]:
                    cmd.append("table")
                    cmd.append(str(rentry["rt_table"]))
                (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
                if len(stdout):
                    debug(stdout)

                if (rc != 0):
                    self.error("start(): failed to setup route entry: %s" %rentry)
                    errmsg += stderr
                    tmp_rc = rc
                for line in stderr.splitlines():
                    error(" %s" %line)

            if (tmp_rc != 0):
                final_rc = tmp_rc
            yield self._parent._dbpool.startedService(config,
                                                      tmp_rc, message=errmsg)
        defer.returnValue(final_rc)

    @defer.inlineCallbacks
    def stop(self):
        """This function removes static routing entries"""

        final_rc = 0

        for config in self._config:

            # iterate over routing entries
            errmsg = ""
            # first rc != 0 which happens 
            tmp_rc  = 0
            for rentry in config["rentries"]:
                cmd = ["ip", "route", "del",
                       "%s/%s"   %(rentry["dest"], rentry["prefix"]),
                       "via",    rentry["gw"],
                       "dev",    rentry["nic"],
                       "metric", str(rentry["metric"])]
                if rentry["rt_table"]:
                    cmd.append("table")
                    cmd.append(str(rentry["rt_table"]))
                (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
                if len(stdout):
                    debug(stdout)

                if (rc != 0):
                    self.error("stop(): failed to delete route entry: %s" %rentry)
                    errmsg += stderr
                    tmp_rc = rc
                for line in stderr.splitlines():
                    error(" %s" %line)

            if (tmp_rc != 0):
                final_rc = tmp_rc
            yield self._parent._dbpool.stoppedService(config,
                                                      tmp_rc, message=errmsg)
        defer.returnValue(final_rc)
