#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import os
import imp
import sys
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.web import xmlrpc, server
from twisted.internet import reactor, defer
from twisted.enterprise import adbapi

from um_application import Application


class MeshDbPool(adbapi.ConnectionPool):
    """This class handles the database connection pool, for the mesh database"""

    def __init__(self):
        adbapi.ConnectionPool.__init__(self, "MySQLdb",
                                       user   = "rpcserver",
                                       host   = "www.umic-mesh.net",
                                       passwd = '2PZrfjNXYNBxwru',
                                       db     = "umic-mesh")

    def _getAssoc(self, txn, query):
        """ This function returns an associative array of the first row """

        txn.execute(query)
        res = dict()
        if txn.rowcount > 0:
            if txn.rowcount > 1:
                warn("_getAssoc(): query produced more then one row!")                
            row = txn.fetchone()
            for i in xrange(len(row)):                
                key = txn.description[i][0]
                res[key] = row[i]                
        return res    

    def fetchAssoc(self, query):
        """ Fetchas an associative array from the database, returns a defered """
        return self.runInteraction(self._getAssoc, query)
        

    @defer.inlineCallbacks
    def getCurrentServiceConfig(self, servicename, hostname):
        """ Returns the current config as an dictionary if available, else None """

        # first get serviceID and the service table
        query = "SELECT servID, servTable FROM services WHERE servName = '%s'" %servicename
        debug(query)
        result = yield self.runQuery(query)
        debug(result)
        if len(result) is not 1:
            warn("Service %s not found." %servicename)
            defer.returnValue(None)
        (servID, servTable) = result[0]

        # look which flavor is selected in current config for this host
        query = "SELECT flavorID FROM current_service_conf AS c, nodes " \
                "WHERE nodes.name='%s' AND c.nodeID=nodes.nodeID;" % hostname
        debug(query)
        result = yield self.runQuery(query)
        debug(result)
        if len(result) is not 1:
            info("No flavor of service %s activated for this host" %servicename)
            defer.returnValue(None)
        (flavorID,) = result[0]

        # get configuration out of service table
        query = "SELECT * FROM %s WHERE id=%u;" %(servTable, flavorID)
        debug(query)
        result = yield self.fetchAssoc(query)
        debug(result)
        if len(result) is 0:
            error("Database error: no flavor %u in %s!") %(flavorID, servTable)
            defer.returnValue(None)
        defer.returnValue(result)
        
        

class RPCServer(xmlrpc.XMLRPC):
    """RPC Server"""

    def __init__(self, module_path = None, parent = None):
        info("Starting up RPCServer...")
        self._module_path = module_path

        self._parent = parent

        # Call super constructor
        xmlrpc.XMLRPC.__init__(self)
       
        # No such file or directory
        if not self._module_path or not os.path.exists(self._module_path):
            raise OSError('%s: No such file or directory' %self._module_path)

        self._dbpool = None

        # create database connection pool        
        try:
            self._dbpool = MeshDbPool()
            
        except Exception, inst:
            error("Failed to establish database connection: ", inst )
    
            
        # find and load rpc modules
        for file in os.listdir(self._module_path):
            name, ext = os.path.splitext(os.path.basename(file))
               
            # Only handle python files 
            if not ext == '.py':
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
            self.putSubHandler(name, eval('module.%s(parent=self)' %name.capitalize()))
        info("Startup complete.")

    def xmlrpc_stats(self, service="olsr", hostname="mrouter1"):
        res = self._dbpool.getCurrentServiceConfig(service,hostname)
        debug("blub: %s" %type(res))
        debug("bla: %s" %res)
        return res

    def xmlrpc_ping(self):
        return 'OK'

    def xmlrpc_restart(self):
        info("Client requested restart...")
        if self._parent:
            self._parent.set_restart()
        reactor.callLater(1,reactor.stop)
        return 'OK'


class RPCServerApp(Application):

    def __init__(self):
        "Constructor of the object"
        self._restart = True
        Application.__init__(self)

    

    def set_option(self):
        "Set options"

        Application.set_option(self)

    def set_restart(self, flag = True):
        "Set restart flag"
        self._restart = flag
        
        
    def main(self):
        "Main method of the RPCServer Application"

        path = 'rpc-modules'
        self.parse_option()
        self.set_option()

        inst = RPCServer(module_path = path, parent=self )
        debug("calling reactor.listenTCP()")
        reactor.listenTCP(7080, server.Site(inst))
        self._restart = False
        debug("calling reactor.run()")
        rc = reactor.run()
        if self._restart:            
            debug("Requesting restart via sys.exit(0)")
            sys.exit(0)
        else:
            debug("Exiting...")
            sys.exit(1)



if __name__ == '__main__':
    RPCServerApp().main()
