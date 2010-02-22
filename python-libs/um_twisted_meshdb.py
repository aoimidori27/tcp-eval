#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# python imports
import socket
from logging import info, debug, warn, error, critical

from twisted.internet import defer, utils, reactor
from twisted.enterprise import adbapi

class MeshDbPool(adbapi.ConnectionPool):
    """This class handles the database connection pool, for the mesh database"""

    def __init__(self, username, password):
        def initConnection(conn):
            # turn on autocommit
            conn.autocommit(True)

        adbapi.ConnectionPool.__init__(self, "MySQLdb",
                                       user   = username,
                                       host   = "www.umic-mesh.net",
                                       passwd = password,
                                       db     = "umic-mesh",
                                       cp_min = 1,
                                       cp_max = 3,
                                       cp_openfun = initConnection,
                                       cp_reconnect = True)
    @staticmethod
    def _queryErrback(failure):
        error("Query failed: %s" %failure.getErrorMessage())
        return failure

    def runInteraction(self, interaction, query, *args, **kwargs):
        """Overrides ConnectionPool.runInteraction to improve logging"""
        # NOTE: this function will also get called from "runQuery" and similiar
        debug('SQL: %s' %query)
        d = adbapi.ConnectionPool.runInteraction(self, interaction, query, *args, **kwargs)
        d.addErrback(MeshDbPool._queryErrback)
        return d

    def _getAssoc(self, txn, query):
        """This function returns an associative array of the first row"""

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
        """Fetches an associative array from the first row, returns a deferred"""
        return self.runInteraction(self._getAssoc, query)

    def _getAssocList(self, txn, query):
        """This function returns a list of associative arrays"""

        txn.execute(query)
        res_list = list()
        if txn.rowcount > 0:
            while (1):
                row = txn.fetchone()
                if not row:
                    break
                res = dict()
                for i in xrange(len(row)):
                    key = txn.description[i][0]
                    res[key] = row[i]
                res_list.append(res)
        return res_list

    def fetchAssocList(self, query):
        """Fetches a list of associative arrays, returns a deferred"""
        return self.runInteraction(self._getAssocList, query)

    def _fetchColumnAsList(self, txn, query, column):
        """This function returns a list of the specified column"""

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
    def startedService(self, config, rc, message, hostname = socket.gethostname(), ignoreDups=False):
        """Updates the Database on startup of a service flavor."""

        if ignoreDups:
            tmp = "INSERT IGNORE "
        else:
            tmp = "INSERT "

        # store record in database
        query = tmp + """INTO current_service_status (nodeID,servID,flavorID,version,prio,returncode,message)
                         SELECT nodeID, %s, %s, %s, %s, %s,%s FROM nodes WHERE nodes.name=%s;
                      """
        result = yield self.runQuery(query, (config['servID'], config['flavorID'], config['version'], config['prio'], rc, message, hostname))

    @defer.inlineCallbacks
    def stoppedService(self, config, rc, message, hostname = socket.gethostname()):
        """Updates the Database on stop of a service flavor."""

        query = """DELETE FROM current_service_status USING current_service_status, nodes
                   WHERE nodes.name='%s' AND nodes.nodeID=current_service_status.nodeID
                   AND servID=%d AND flavorID=%d;
                """  % (hostname, config['servID'], config['flavorID'])
        result = yield self.runQuery(query)


    @defer.inlineCallbacks
    def getServiceInfo(self, servicename):
        """Returns the serviceID and the service Table as a tuple"""

        # first get serviceID and the service table
        query = "SELECT servID, servTable FROM services WHERE servName = %s"
        result = yield self.runQuery(query, (servicename))
        debug(result)
        if len(result) is not 1:
            warn("Service %s not found." %servicename)
            defer.returnValue(None)

        # (servID, servTable) = result[0]
        defer.returnValue(result[0])

    @defer.inlineCallbacks
    def getStaticRouting(self, hostname = socket.gethostname()):
        """Returns a list of dicts which have a version field and a list of routing table entries"""

        servicename = "static_routing"

        # first get serviceID and the service table
        servInfo = yield self.getServiceInfo(servicename)
        if not servInfo:
            defer.returnValue(None)
        (servID, servTable) = servInfo

        # look which flavors are selected in current config for this host
        query = "SELECT flavorID,prio,version FROM current_service_conf AS c, nodes " \
                "WHERE nodes.name='%s' AND c.nodeID=nodes.nodeID "\
                "AND c.servID='%s';" % (hostname, servID)
        result = yield self.runQuery(query)
        debug(result)
        if len(result) < 1:
            info("No flavors of service %s activated for this host" %servicename)
            defer.returnValue(None)

        final_result = list()

        for row in result:
            (flavorID,prio,version) = row
            # get configuration out of service table
            # convert packed ip adresses to strings
            query = """ SELECT services_flavors.*,
                        INET_NTOA(gw) AS gw,
                        INET_NTOA(dest) AS dest,
                        metric, nic, prefix, rt_table
                        FROM services_flavors
                        LEFT JOIN %s USING (flavorID)
                        WHERE flavorID=%d
                        AND nodeID=
                        (SELECT nodeID FROM nodes WHERE name='%s');
                        """ % (servTable, flavorID, hostname)
            debug(query)
            res = yield self.fetchAssocList(query)

            debug(res)
            tmp = dict()
            tmp["version"]  = version
            tmp["flavorID"] = flavorID
            tmp["prio"]     = prio
            tmp["servID"]   = servID
            tmp["rentries"] = res
            final_result.append(tmp)
            if len(res) is 0:
                warn("No rentries for %s in flavor %u!" %(hostname, flavorID))

        defer.returnValue(final_result)

    @defer.inlineCallbacks
    def getCurrentServiceConfigMany(self, servicename, hostname = socket.gethostname()):
        """Returns the current configs as an list of dictionary if available, else None"""

        # first get serviceID and the service table
        servInfo = yield self.getServiceInfo(servicename)
        if not servInfo:
            defer.returnValue(None)
        (servID, servTable) = servInfo

        # look which flavors are selected in current config for this host
        query = "SELECT flavorID,prio FROM current_service_conf AS c, nodes " \
                "WHERE nodes.name='%s' AND c.nodeID=nodes.nodeID " \
                "AND c.servID='%s' ORDER BY prio ASC;" % (hostname, servID)
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
                error("Database error: no flavor %u in %s!" %(flavorID, servTable))
                defer.returnValue(None)
            final_result.append(res)
        defer.returnValue(final_result)

    @defer.inlineCallbacks
    def getNetbootProfile(self, servicename, profilename):
        servInfo = yield self.getServiceInfo(servicename)
        if not servInfo:
            defer.returnValue(None)
        (servID, servTable) = servInfo

        str_profid = "SELECT `flavorID` FROM `services_flavors` WHERE `flavorName`=\"%s\" AND `servID`=%s" % (profilename, servID)
        str_profdat = "SELECT * FROM `%s` WHERE `flavorID`=( %s )" % (servTable, str_profid)
        profid = yield self.fetchAssoc(str_profdat)
        str_version = "SELECT `version` FROM `services_flavors` WHERE `flavorID` =( %s )" % str_profid
        version = yield self.fetchAssoc(str_version)
        profid['profile'] = profilename
        profid['version'] = version['version']
        defer.returnValue(profid)

    @defer.inlineCallbacks
    def getNetbootProfileNames(self, servicename):
        servInfo = yield self.getServiceInfo(servicename)
        if not servInfo:
            defer.returnValue(None)
        (servID, servTable) = servInfo
        str_profnames = "SELECT `flavorName` FROM `services_flavors` WHERE `servID` = %s" % servID
        profnames = yield self.fetchAssocList(str_profnames)
        defer.returnValue(profnames)

    @defer.inlineCallbacks
    def getCurrentServiceConfig(self, servicename, hostname = socket.gethostname()):
        """Returns the current config as an dictionary if available, else None"""

        # first get serviceID and the service table
        servInfo = yield self.getServiceInfo(servicename)
        if not servInfo:
            defer.returnValue(None)
        (servID, servTable) = servInfo

        # look which flavor is selected in current config for this host
        query = "SELECT flavorID, prio FROM current_service_conf AS c, nodes " \
                "WHERE nodes.name='%s' AND c.nodeID=nodes.nodeID "\
                "AND c.servID='%s';" % (hostname, servID)
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
            error("Database error: no flavor %u in %s!" %(flavorID, servTable))
            defer.returnValue(None)
        defer.returnValue(result)

    @defer.inlineCallbacks
    def getServicesToStart(self, hostname = socket.gethostname()):
        """Returns a list of servicenames, appropriate sorted."""

        query = """SELECT DISTINCT servName FROM current_service_conf,services
                   WHERE nodeID=(SELECT nodeID FROM nodes WHERE name='%s')
                   AND (nodeID, current_service_conf.servID, flavorID, version)
                   NOT IN (SELECT nodeID, servID,flavorID,version FROM current_service_status)
                   AND services.servID=current_service_conf.servID
                   ORDER BY current_service_conf.prio ASC;
                """ % hostname

        service_list = yield self.fetchColumnAsList(query)
        debug(service_list)

        defer.returnValue(service_list)

    @defer.inlineCallbacks
    def getServicesToStop(self, hostname = socket.gethostname()):
        """Returns a list of servicenames, appropriate sorted."""

        query = """SELECT DISTINCT servName FROM current_service_status,services
                   WHERE nodeID=(SELECT nodeID FROM nodes WHERE name='%s')
                   AND (nodeID, current_service_status.servID, flavorID, version)
                   NOT IN (SELECT nodeID, servID,flavorID,version FROM current_service_conf)
                   AND services.servID=current_service_status.servID
                   ORDER BY current_service_status.prio DESC;
                """ % hostname
        service_list = yield self.fetchColumnAsList(query)
        debug(service_list)

        defer.returnValue(service_list)

    @defer.inlineCallbacks
    def isNodeClean(self, hostname):
        """Checks if configuration matches started services"""
        tmp = yield self.getServicesToStop(hostname)
        if len(tmp) != 0:
            defer.returnValue(False)
        tmp = yield self.getServicesToStart(hostname)
        if len(tmp) != 0:
            defer.returnValue(False)

        defer.returnValue(True)
        

    @defer.inlineCallbacks
    def clearUpServiceStatus(self, hostname = socket.gethostname()):
        """Clears the service status table from entries of this host."""

        query = """DELETE FROM current_service_status USING current_service_status, nodes 
                   WHERE nodes.name='%s' AND nodes.nodeID=current_service_status.nodeID;
                """  % hostname
        debug(query)
        result = yield self.runOperation(query)

    def _getRowcount(self, txn, query):
        """ This function returns the number of rows effected by the transaction. """

        txn.execute(query)
        return txn.rowcount

    @defer.inlineCallbacks
    def switchTestbedProfile(self, name):
        """Switches the current used testbed profile
           Removes all colliding profiles.
           Returns a list of nodes affected by the change.
        """
        dirty_nodes = list()

        current_profiles = yield self.getCurrentTestbedProfiles()
        debug("Activated profiles: %s" %current_profiles)

        # get nodes used by current profiles
        current_nodes = dict()
        for profileName in current_profiles:
            profile_nodes = yield self.getProfileNodes(profileName)
            current_nodes[profileName] = profile_nodes
        debug("Current used nodes: %s"  %current_nodes.values())

        # get nodes used by the profile which is going to be activated
        new_nodes = yield self.getProfileNodes(name)
        debug("New nodes: %s" %new_nodes)
        dirty_nodes.extend(new_nodes)
        
        # compare current nodes with new nodes
        stop_profiles = list()
        for (profile, nodes) in current_nodes.iteritems():
            # check if intersection is not empty
            if len(set(nodes) &  set(new_nodes)) > 0:
                if profile not in stop_profiles:
                    stop_profiles.append(profile)
                
        # stop conflicting profiles
        info("Deactivating conflicting profiles: %s", stop_profiles)       
        for profile in stop_profiles:
            query = """DELETE FROM current_testbed_conf
                       WHERE current_testbed_profile = (SELECT id FROM testbed_profiles WHERE name = '%s')
                    """ %profile
            yield self.runQuery(query)

        # insert new profile
        query = """INSERT INTO current_testbed_conf (current_testbed_profile) 
                   SELECT testbed_profiles.id FROM testbed_profiles WHERE testbed_profiles.name = '%s'
                """ % name
        yield self.runQuery(query)

        defer.returnValue(dirty_nodes)

    def getCurrentTestbedProfiles(self):
        """Returns the names of the current used testbed profiles"""

        query = """SELECT testbed_profiles.name
                   FROM current_testbed_conf, testbed_profiles
                   WHERE testbed_profiles.ID = current_testbed_profile
                """
        return self.fetchColumnAsList(query)

    def getProfileNodes(self,profileName):
        """Return name of nodes used by a profile"""

        profileID = """SELECT id
                       FROM testbed_profiles
                       WHERE name = '%s'
                    """ % profileName
        query = """SELECT nodes.name
                   FROM nodes, testbed_profiles_data
                   WHERE testbed_profiles_data.tprofileID = (%s)
                   AND testbed_profiles_data.nodeID = nodes.nodeID;
                """ % profileID
        return self.fetchColumnAsList(query)

    def getTestbedNodes(self):
        """Returns a list of nodes which are in the current testbedprofile"""

        query = """SELECT nodes.name
                   FROM nodes, testbed_profiles_data, current_testbed_conf
                   WHERE testbed_profiles_data.tprofileID = current_testbed_profile
                   AND testbed_profiles_data.nodeID = nodes.nodeID;
                """
        return self.fetchColumnAsList(query)

