from logging import info, debug, warn, error, critical

# twisted imports
from twisted.web import xmlrpc


class RPCService(xmlrpc.XMLRPC):
    """ Base class for services """


    def __init__(self, parent = None):
        
        # Call super constructor
        xmlrpc.XMLRPC.__init__(self)


        self._name = None
        self._flavor = None
        self._parent = parent


    def xmlrpc_getFlavor():
        return self._flavor



    
