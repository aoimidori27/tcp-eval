#!/usr/bin/env python
# -*- coding: utf-8 -*-

# XMLRPC Server to invoke rpc-modules.
#
# Copyright (C) 2007 - 2010 Arnd Hannemann <arnd@arndnet.de>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# python imports
import os
import imp
import socket
import sys
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.web import xmlrpc, server
from twisted.internet import reactor, defer
from twisted.enterprise import adbapi

# umic-mesh imports
from um_application import Application
from um_twisted_functions import twisted_call
from um_twisted_meshdb import MeshDbPool
from um_twisted_xmlrpc import xmlrpc_meshconf

class RPCServer(xmlrpc.XMLRPC):
    """RPC Server"""

    def __init__(self, module_path = None, parent = None):
        info("Starting up RPCServer...")
        self._module_path = module_path
        self._parent = parent
        self._services = dict()

        # Call super constructor
        xmlrpc.XMLRPC.__init__(self)

        # No such file or directory
        if not self._module_path or not os.path.exists(self._module_path):
            raise OSError('%s: No such file or directory' %self._module_path)

        self._dbpool = None

        # create database connection pool
        try:
            self._dbpool = MeshDbPool(username='rpcserver',
                                      password='2PZrfjNXYNBxwru')
        except Exception, inst:
            error("Failed to establish database connection: %s", inst)

        # find and load rpc modules
        for filename in os.listdir(self._module_path):
            name, ext = os.path.splitext(os.path.basename(filename))

            # Only handle python files
            if not ext == '.py':
                continue

            # check if this file is readable
            fpath = os.path.join(self._module_path, filename)
            if not os.access(fpath, os.R_OK):
                warn("Permission denied to read %s. Module skipped." %fpath)
                continue

            # Load module
            fp, pathname, description = imp.find_module(name, [self._module_path])
            try:
                module = imp.load_module(name, fp, pathname, description)
            finally:
                # Close fp explicitly.
                if fp:
                    fp.close()

            # Register modules
            info(" Registering rpc module %s" %name.capitalize())
            self._services[name] = eval('module.%s(parent=self)' %name.capitalize())
            self.putSubHandler(name, self._services[name])

        info("Startup complete.")

    def xmlrpc_ping(self):
        return 'OK'

    def xmlrpc_restart(self):
        info("Client requested restart...")

        if self._parent:
            self._parent.set_restart()
        reactor.callLater(1,reactor.stop)
        return 'OK'

    @defer.inlineCallbacks
    def xmlrpc_apply(self):
        info("Applying configuration changes...")

        info("Stopping services...")
        services = yield self._dbpool.getServicesToStop()

        for service in services:
            text = "Stopping service %s" % service
            debug(text)
            yield xmlrpc_meshconf("XmlRpcNodeEventHandler.serviceStopped", 
                                  socket.gethostname(), text)
            if self._services.has_key(service):
                yield self._services[service].xmlrpc_stop()
            else:
                error("I'm supposed to stop %s, which is not there!" %service)

        text = "Starting services..."
        info(text)
        yield xmlrpc_meshconf("XmlRpcNodeStatusHandler.nodeConfigChanged", 
                              socket.gethostname())


        services = yield self._dbpool.getServicesToStart()

        for service in services:
            text = "Starting service %s" % service
            info(text)
            yield xmlrpc_meshconf("XmlRpcNodeEventHandler.serviceStarted",
                                  socket.gethostname(), text)
            if self._services.has_key(service):
                rc = yield self._services[service].xmlrpc_start()
                info("Service returned RC=%s" %rc)
                # special case if configuration change needs a reboot
                if rc == "reboot":
                    info("Service is going to restart the node. Returning...") 
                    defer.returnValue(rc)
            else:
                error("I'm supposed to start %s, which is not there!" %service)
                rc = -1

        # set MeshConf bootmsg to "Done"
        yield xmlrpc_meshconf("XmlRpcNodeEventHandler.serviceStarted", 
                              socket.gethostname(), "Done")
        yield xmlrpc_meshconf("XmlRpcNodeStatusHandler.nodeOnlined", 
                              socket.gethostname())
        # forces MeshConf to update its data (expensive, don't do it often)
        yield xmlrpc_meshconf("XmlRpcNodeStatusHandler.nodeConfigChanged", 
                              socket.gethostname())

        defer.returnValue(0)


class RPCServerApp(Application):
    def __init__(self):
        """Constructor of the object"""
        self._restart = True
        Application.__init__(self)

    def set_option(self):
        """Set options"""
        Application.set_option(self)

    def set_restart(self, flag = True):
        """Set restart flag"""
        self._restart = flag

    @defer.inlineCallbacks
    def startup(self, inst):
        yield inst._dbpool.clearUpServiceStatus()
        yield inst.xmlrpc_apply()

    def main(self, path='rpc-modules'):
        """Main method of the RPCServer Application"""

        self.parse_option()
        self.set_option()

        inst = RPCServer(module_path = path, parent=self )
        debug("calling reactor.listenTCP()")
        reactor.listenTCP(7080, server.Site(inst))
        self._restart = False

        self.startup(inst)
        rc = reactor.run()
        if self._restart:
            debug("Requesting restart via sys.exit(0)")
            sys.exit(0)
        else:
            debug("Exiting...")
            sys.exit(1)


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(sys.argv[0]), 'rpc-modules-meshnode')
    RPCServerApp().main(path)
