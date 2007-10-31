#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

import socket
import os
from logging import info, debug, warn, error, critical

from twisted.internet import defer, utils, reactor
from twisted.enterprise import adbapi



class MeshDbPool(adbapi.ConnectionPool):
    """This class handles the database connection pool, for the mesh database"""

    def __init__(self, username, password):
        adbapi.ConnectionPool.__init__(self, "MySQLdb",
                                       user   = username,
                                       host   = "www.umic-mesh.net",
                                       passwd = password,
                                       db     = "umic-mesh", 
                                       cp_min = 1,
                                       cp_max = 3,
                                       cp_reconnect = True)

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
                   AND (nodeID, current_service_conf.servID, flavorID, version)
                   NOT IN (SELECT nodeID, servID,flavorID,version FROM current_service_status)
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
                   AND (nodeID, current_service_status.servID, flavorID, version)
                   NOT IN (SELECT nodeID, servID,flavorID,version FROM current_service_conf)
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

