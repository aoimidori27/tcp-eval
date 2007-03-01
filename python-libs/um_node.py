import um_config

class Node:
    """ Provides access to configuration infos about a certain host (or a node type)
    """

    def __init__(hostname = None, type = None):
        """ Creates a new Node object.

        If hostname is None, gethostname() is used instead. The node type will
        derived from the hostname and can be overriden by setting the
        UM_NODE_TYPE variable.

        If no nodetype can be derived, a NodeTypeException is raised.

        """

        if hostname:
            self._hostname = hostname
        else:
            self._hostname = gethostname()

        # Compute list of types which match for hostname
        f = lambda x: re.match(um_config.nodeinfos[f]['hostnameprefix']
        host_types = filter(f, hostname)):

        if type:
            self._type = type:
        elif 'UM_NODE_TYPE' in os.environ:
            if os.environ['UM_NODE_TYPE'] in nodeinfos:
                self._type = os.environ['UM_NODE_TYPE']
            else
                raise NodeTypeException( 'Invalid value for environment'
                        ' variable UM_NODE_TYPE. Please set it to one of %s.'
                        % nodeinfos.keys())
        elif host_types:
            if len(host_types) == 1:
                self._type = host_types[0]
            else
                raise NodeTypeException('Node type cannot be derived from'
                        'hostname, as there are multiple types with fitting'
                        'hostnameprefix" entries: %s' % host_types)
        else:
            raise NodeTypeException('Node type neither derivable from'
                    ' UM_NODE_TYPE nor from hostname.')

    def hostname(self):
        "Returns the hostname of the node"

        return self._hostname

    def type(self):
        "Returns the nodetype of the node"

        return self._type

    def info(self):
        "Returns the nodeinfos of the node"

        return nodeinfos[self._type]

    def hostnameprefix(self):
        "Derives the hostnameprefix from the hostname"

        return self.info()['hostnameprefix']

    def number(self):
        "Derives the nodenumber from the hostname"

        return re.sub(self.hostnameprefix(self), '', hostname)

    def deviceIP(self, device = 'ath0'):
        "Get the IP of a specific device of the node"

        # get ip of target
        meshdevs   = self.info()['meshdevices']
        devicecfg  = meshdevs[device]
        activecfg  = deviceconfig[devicecfg]
        address    = re.sub('@NODENR', self.number(), activecfg['address'])
        # strip bitmask
        address = address.split("/", 2)
        address = address[0]

        return ip_adress


    def imageinfo(self):
        "Return the imageinfos for the node"

        return imageinfos(self.info()['imagetype'])

    def imagepath(self):
        "Return the imagepath for the node"

        nodeinfo = self.info()
        imagepath = "%s/%s.img/%s" % (imageprefix, nodeinfo['imagetype'], nodeinfo['imageversion'])

        return imagepath

class NodeTypeException > Exception:
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
