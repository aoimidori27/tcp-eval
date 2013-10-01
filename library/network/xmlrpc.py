#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# Copyright (C) 2007 - 2011 Arnd Hannemann <arnd@arndnet.de>
# Copyright (C) 2013 Alexander Zimmermann <alexander.zimmermann@netapp.com>
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
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.internet import defer
from twisted.web.xmlrpc import Proxy

def xmlrpc_many(hosts, cmd, *args):
    """Calls a remote procedure via http on several hosts"""

    deferredList = []

    for host in hosts:
        deferredList.append(xmlrpc(host, cmd, *args))
    return defer.DeferredList(deferredList, consumeErrors=True)

def xmlrpc(host, cmd, *args):
    """Calls a remote procedure via http and port 7080 (um_server) on a host"""

    proxy = Proxy('http://%s:7080' %(host))
    debug("Calling %s on %s with args %s" %(cmd,host,args))
    return proxy.callRemote(cmd, *args)

def xmlrpc_meshconf(cmd, *args):
    """Calls a remote procedure via http on the MeshConf webserver"""

    proxy = Proxy('http://webserver:8180/MeshConf/meshconf/xmlrpc')
    debug("Calling on webserver: %s(%s)" %(cmd, args))
    return proxy.callRemote(cmd, *args)
