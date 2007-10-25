#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import os
import imp
import sys
import socket
from logging import info, debug, warn, error, critical

# twisted imports
from twisted.web import xmlrpc, server
from twisted.internet import reactor, defer
from twisted.enterprise import adbapi

from um_application import Application
from um_twisted_functions import twisted_call


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
        """ Fetches an associative array from the database, returns a defered """
        return self.runInteraction(self._getAssoc, query)

    def _fetchColumnAsList(self, txn, query, column):
        """ This function returns a list of the specified column """
        debug(query)
        txn.execute(query)
        res = list()
        if txn.rowcount > 0:
            for row in txn.fetchall():
                res.append(row[column])                
        return res                

    def fetchColumnAsList(self, query, column=0):
        """ Fetches a column of a query as a list """
        return self.runInteraction(self._fetchColumnAsList, query, column)

    @defer.inlineCallbacks
    def startedService(self, config, rc, message, hostname = socket.gethostname()):
        """ Updates the Database on startup of a service flavor. """

        # store record in database
        query = """INSERT INTO current_service_status (nodeID,servID,flavorID,version,prio,returncode,message) 
                   SELECT nodeID, %u, %u, %u, %u, %d,'%s' FROM nodes WHERE nodes.name='%s';
                """ %(config['servID'], config['flavorID'], config['version'], config['prio'],
                      rc, message, hostname)
        debug(query)
        result = yield self.runQuery(query)

    @defer.inlineCallbacks
    def stoppedService(self, config, rc, message, hostname = socket.gethostname()):
        """ Updates the Database on stop of a service flavor. """

        query = """DELETE FROM current_service_status USING current_service_status, nodes 
                   WHERE nodes.name='%s' AND nodes.nodeID=current_service_status.nodeID
                   AND servID=%d AND flavorID=%d;
                """  % (hostname, config['servID'], config['flavorID'])

        debug(query)
        result = yield self.runQuery(query)
                                           

    @defer.inlineCallbacks
    def getCurrentServiceConfigMany(self, servicename, hostname = socket.gethostname()):
        """ Returns the current configs as an list of dictionary if available, else None """

        # first get serviceID and the service table
        query = "SELECT servID, servTable FROM services WHERE servName = '%s'" %servicename
        debug(query)
        result = yield self.runQuery(query)
        debug(result)
        if len(result) is not 1:
            warn("Service %s not found." %servicename)
            defer.returnValue(None)
        (servID, servTable) = result[0]

        # look which flavors are selected in current config for this host
        query = "SELECT flavorID,prio FROM current_service_conf AS c, nodes " \
                "WHERE nodes.name='%s' AND c.nodeID=nodes.nodeID "\
                "AND c.servID='%s';" % (hostname, servID)
        debug(query)
        result = yield self.runQuery(query)
        debug(result)
        if len(result) < 1:
            info("No flavors of service %s activated for this host" %servicename)
            defer.returnValue(None)


        final_result = list()

        for row in result:
            (flavorID,prio) = row
            # get configuration out of service table
            query = "SELECT * FROM services_flavors LEFT JOIN %s USING (flavorID) WHERE flavorID=%d;" % (servTable, flavorID)
            debug(query)
            res = yield self.fetchAssoc(query)
            res["prio"] = prio
            debug(res)
            if len(res) is 0:
                error("Database error: no flavor %u in %s!") %(flavorID, servTable)
                defer.returnValue(None)
                
            final_result.append(res)

        defer.returnValue(final_result)
        
        

    @defer.inlineCallbacks
    def getCurrentServiceConfig(self, servicename, hostname = socket.gethostname()):
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
        query = "SELECT flavorID, prio FROM current_service_conf AS c, nodes " \
                "WHERE nodes.name='%s' AND c.nodeID=nodes.nodeID "\
                "AND c.servID='%s';" % (hostname, servID)
        debug(query)
        result = yield self.runQuery(query)
        debug(result)
        if len(result) is not 1:
            info("No flavor of service %s activated for this host" %servicename)
            defer.returnValue(None)
        (flavorID,prio) = result[0]

        # get configuration out of service table
        query = "SELECT * FROM services_flavors LEFT JOIN %s USING (flavorID) WHERE flavorID=%d;" % (servTable, flavorID)
        debug(query)
        result = yield self.fetchAssoc(query)
        result["prio"] = prio;
        debug(result)
        if len(result) is 0:
            error("Database error: no flavor %u in %s!") %(flavorID, servTable)
            defer.returnValue(None)
        defer.returnValue(result)

    @defer.inlineCallbacks
    def getServicesToStart(self, hostname = socket.gethostname()):
        """ Returns a list of servicenames, appropriate sorted. """
        
        query = """SELECT DISTINCT servName FROM current_service_conf,services
                   WHERE nodeID=(SELECT nodeID FROM nodes WHERE name='%s')
                   AND (current_service_conf.servID, flavorID, version)
                   NOT IN (SELECT servID,flavorID,version FROM current_service_status)
                   AND services.servID=current_service_conf.servID
                   ORDER BY current_service_conf.prio ASC;
                """ % hostname

        debug(query)        
        service_list = yield self.fetchColumnAsList(query)
        debug(service_list)
        
        defer.returnValue(service_list)

    @defer.inlineCallbacks
    def getServicesToStop(self, hostname = socket.gethostname()):
        """ Returns a list of servicenames, appropriate sorted. """


        query = """SELECT DISTINCT servName FROM current_service_status,services
                   WHERE nodeID=(SELECT nodeID FROM nodes WHERE name='%s')
                   AND (current_service_status.servID, flavorID, version)
                   NOT IN (SELECT servID,flavorID,version FROM current_service_conf)
                   AND services.servID=current_service_status.servID
                   ORDER BY current_service_status.prio DESC;
                """ % hostname
        debug(query)
        service_list = yield self.fetchColumnAsList(query)
        debug(service_list)
        
        defer.returnValue(service_list)

    @defer.inlineCallbacks
    def clearUpServiceStatus(self, hostname = socket.gethostname()):
        """ Clears the serivce status table from entries of this host. """
       
        query = """DELETE FROM current_service_status USING current_service_status, nodes 
                   WHERE nodes.name='%s' AND nodes.nodeID=current_service_status.nodeID;
                """  % hostname
        debug(query)
        result = yield self.runQuery(query)
        

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
            self._dbpool = MeshDbPool()
            
        except Exception, inst:
            error("Failed to establish database connection: ", inst )
    
            
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

    def xmlrpc_test(self):
        return self._dbpool.getServicesToStart();

    def xmlrpc_test2(self):
        return self._dbpool.getServicesToStop();


    @defer.inlineCallbacks
    def xmlrpc_apply(self):
        info("Applying configuration changes...")

        info("Stopping services...")
        services = yield self._dbpool.getServicesToStop()

        for service in services:
            text = "Stopping service %s" % service
            debug(text)
            yield twisted_call(["/sbin/usplash_write", "TEXT %s" % text ],
                shell=False)
            yield self._services[service].xmlrpc_stop()

        info("Starting services...")
        services = yield self._dbpool.getServicesToStart()

        for service in services:
            text = "Starting service %s" % service 
            info(text)
            yield twisted_call(["/sbin/usplash_write", "TEXT %s" % text ],
                shell=False)
            rc = yield self._services[service].xmlrpc_start()            
            info("RC=%s" %rc)      

        text = "Done."
        yield twisted_call(["/sbin/usplash_write", "TEXT %s" % text ],
                shell=False)

        defer.returnValue(0)
        


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

    @defer.inlineCallbacks
    def startup(self, inst):
        yield inst._dbpool.clearUpServiceStatus()
        yield inst.xmlrpc_apply()
        
        
    def main(self, path='rpc-modules'):
        "Main method of the RPCServer Application"

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
    path = os.path.join(os.path.dirname(sys.argv[0]), 'rpc-modules')
    RPCServerApp().main(path)
