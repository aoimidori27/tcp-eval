from logging import info, debug, warn, error, critical

# twisted imports
from twisted.web import xmlrpc




class Testrpc(xmlrpc.XMLRPC):
    """Test Class for the RPC Sever"""

    def __init__(self, parent = None):
        

        # Call super constructor
        xmlrpc.XMLRPC.__init__(self)


    def xmlrpc_add(self, a, b):
        return a + b

    def xmlrpc_times(self, a, b):
        return a * b
