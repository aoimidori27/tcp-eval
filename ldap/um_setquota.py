#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports
import ldap
import re

# umic-mesh imports
from um_application import Application
from um_functions import execute


class SetQuota(Application):
    """Class to set the user system quotas based on LDAP account information"""


    def __init__(self):
        Application.__init__(self)

        # initialization of the option parser
        usage = "usage: %prog [options]"
        self.parser.set_usage(usage)
        self.parser.set_defaults(server = "accountserver",
                                 baseDN = "ou=People,dc=umic-mesh,dc=net")

        self.parser.add_option("-s", "--server", metavar = "SERVER",
                               action = "store", dest = "server",
                               help = "The server at which the LDAP directory is located [default: %default]")
        self.parser.add_option("-d", "--baseDN", metavar = "baseDN",
                               action = "store", dest = "baseDN",
                               help = "The base DN define at which node the search should originate [default: %default]")


    def run(self):
        """Query LDAP server and set the user quotas """

        # parses a quota line from LDAP.
        # syntax definition: see quota.schema
        reg_ex = re.compile("([^:]+):([0-9]+),([0-9]+),([0-9]+),([0-9]+)$")

        # Query LDAP server for users with systemQuotas
        l = ldap.open(self.options.server)
        l.simple_bind_s("", "")
        mid = l.search(self.options.baseDN, ldap.SCOPE_SUBTREE, "objectClass=systemQuotas")

        (type, result) = l.result(msgid = mid)
        assert(type == ldap.RES_SEARCH_RESULT)

        # for each such user, apply quota settings
        for r in result:
            # r is a tuple, the dictionary with the ldap values is the second value.
            user = r[1]["uid"][0]
            for q in r[1]["quota"]:
                try:
                    # file system, soft blocks, hard blocks, soft inodes, hard inodes.
                    (fs, sblocks, hblocks, sinodes, hinodes) = reg_ex.match(q).groups()
                    
                    info("Set quota: user=%s, disk=%s, sblocks=%s, hblocks=%s, sinodes=%s, hinodes=%s"
                        % (user, fs, sblocks, hblocks, sinodes, hinodes))
                    
                    execute(["/usr/sbin/setquota", "-u", user, sblocks, hblocks, sinodes, hinodes, fs],
                            shell=False)
                
                except AttributeError, inst:
                    error("Syntax error in quota definition: user=%s, quota='%s'." % (user, quota))
                except CommandFailed, inst:
                    error("Setting quota failed")
                    error(inst)
                    error("Error message %s" % inst.stderr)


    def main(self):
        """Main method of the SetQuota object"""

        self.parse_option()
        self.set_option()
        self.run()



if __name__ == "__main__":
    SetQuota().main()
