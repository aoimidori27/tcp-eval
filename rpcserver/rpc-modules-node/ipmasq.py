#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer, threads, protocol, utils
from twisted.web import xmlrpc

# umic-mesh imports
from um_rpcservice import RPCService
from um_twisted_functions import twisted_execute, twisted_call

class Ipmasq(RPCService):
    """Class for configuring simple IP masquerading"""

    #
    # Public XMLRPC Interface
    #

    @defer.inlineCallbacks
    def xmlrpc_restart(self):
        # don't complain if stopping doesnt work
        yield self.stop()

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
        return self.stop()

    @defer.inlineCallbacks
    def xmlrpc_isAlive(self):
        """returns always true"""
        defer.returnValue(True)

    #
    # Internal stuff
    #

    def __init__(self, parent = None):
        # Call super constructor
        RPCService.__init__(self, parent)

        # service name in the database
        self._name = "ipmasq"

        # stores a list of device configuration
        self._configs = None

        self._rule_incoming = ["FORWARD","-m","state","--state","ESTABLISHED,RELATED","-j","ACCEPT"]
        self._rule_outgoing = ["FORWARD","-j","ACCEPT"]
        self._rule_nat = ["POSTROUTING", "-t", "nat", "-j", "MASQUERADE"] 

    @defer.inlineCallbacks
    def reread_config(self):
        """Rereads the configuration

           The ipmasq service table has the following important columns
           internal_interface : internal interface to masq
           external_interface : interface with visible IP

           Will return 0 on success.
        """

        list_of_assoc = yield self._parent._dbpool.getCurrentServiceConfigMany(self._name)
        if not list_of_assoc:
            info("Found no configuration.")
            defer.returnValue(-1)

        self._configs = list_of_assoc

        defer.returnValue(0)

    def iptables_add(self,rulespec, if_in = None, if_out = None):
        cmd = [ "iptables", "-A" ]
        cmd.extend(rulespec)
        if if_in:
            cmd.extend(["-i", if_in])
        if if_out:
            cmd.extend(["-o", if_out])
        return cmd

    def iptables_del(self,rulespec, if_in = None, if_out = None):
        cmd = [ "iptables", "-D" ]
        cmd.extend(rulespec)
        if if_in:
            cmd.extend(["-i", if_in])
        if if_out:
            cmd.extend(["-o", if_out])
        return cmd

    @defer.inlineCallbacks
    def start(self):
        """This function brings up masquerading on a interface pair"""

        final_rc = 0

        for config in self._configs:
            internal_interface = config["internal_interface"]
            external_interface = config["external_interface"]

            self.info("Enabling masquerading for %s..." %internal_interface)
            cmd1 = self.iptables_add(if_in=external_interface,
                                     if_out=internal_interface,
                                     rulespec=self._rule_incoming)
            cmd2 = self.iptables_add(if_in=internal_interface,
                                     if_out=external_interface,
                                     rulespec=self._rule_outgoing)
            cmd3 = self.iptables_add(if_in=None,
                                     if_out=external_interface,
                                     rulespec=self._rule_nat)
            cmds = [ cmd1, cmd2, cmd3 ]

            for cmd in cmds:
                (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
                if len(stdout):
                    debug(stdout)

                if (rc != 0):
                    self.error("start(): failed to configure internal: %s external: %s" %(internal_interface, external_interface))
                    for line in stderr.splitlines():
                        error(" %s" %line)
                    final_rc = rc
                    break

            yield self._parent._dbpool.startedService(config,
                                                      rc, message=stderr)
        defer.returnValue(final_rc)

    @defer.inlineCallbacks
    def stop(self):
        """This function shuts down masquerading on an interface pair."""

        if not self._configs:
            self.warn("stop(): not initialized with configs")
            defer.returnValue(2)

        final_rc = 0
        for config in self._configs:
            internal_interface = config["internal_interface"]
            external_interface = config["external_interface"]

            self.info("Disabling masquerading for %s..." %internal_interface)
            cmd1 = self.iptables_del(if_in=external_interface,
                                     if_out=internal_interface,
                                     rulespec=self._rule_incoming)
            cmd2 = self.iptables_del(if_in=internal_interface,
                                     if_out=external_interface,
                                     rulespec=self._rule_outgoing)
            cmd3 = self.iptables_del(if_in=None,
                                     if_out=external_interface,
                                     rulespec=self._rule_nat)
            cmds = [ cmd1, cmd2, cmd3 ]

            for cmd in cmds:
                (stdout, stderr, rc) = yield twisted_execute(cmd, shell=False)
                if len(stdout):
                    debug(stdout)

                if (rc != 0):
                    self.error("stop(): failed to delete rules internal: %s external: %s" %(internal_interface, external_interface))
                    for line in stderr.splitlines():
                        error(" %s" %line)
                    final_rc = rc
                    break

            yield self._parent._dbpool.stoppedService(config,
                                                      rc, message=stderr)
        defer.returnValue(final_rc)
