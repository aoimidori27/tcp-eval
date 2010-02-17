#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

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
